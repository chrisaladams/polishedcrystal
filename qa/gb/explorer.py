"""Autonomous, game-aware exploration: the game is played with controller input only.

The explorer keeps going until it runs out of things to do or out of budget:
  1. interact with every NPC, item ball and sign it can reach on the current map
  2. otherwise walk (via the world graph) to the nearest map with something undone
  3. heal at a Pokemon Center when the party is hurt; grind in grass when it keeps losing
Progress is measured, not assumed: event flags set, badges, maps visited, party levels.
Checkpoints (full machine snapshots) are written when progress is made, so any later
run can branch from them. Failures (softlocks, crashes, corruption) are recorded with a
signature so repeats of the same defect are counted once.
"""
import hashlib
import json
import os
import time

from . import collision, mapdata, world
from .consts import C
from .guards import OverworldGuard
from .nav import DIRS, OPP, Navigator, Softlock, Stuck, map_const_of

N_FLAG_BYTES = 288


def flags_set(g):
    base = g.sym['wEventFlags'][1]
    return sum(bin(g.read(base + i, 1)).count('1') for i in range(N_FLAG_BYTES))


def badges(g):
    return bin(g.rd('wJohtoBadges')).count('1') + bin(g.rd('wKantoBadges')).count('1')


def party_levels(g):
    stride = g.sym['wPartyMon2'][1] - g.sym['wPartyMon1'][1]
    return [g.rd('wPartyMon1Level', i * stride) for i in range(g.rd('wPartyCount'))]


def party_hp_fraction(g):
    stride = g.sym['wPartyMon2'][1] - g.sym['wPartyMon1'][1]
    cur = mx = 0
    for i in range(g.rd('wPartyCount')):
        o = i * stride
        cur += g.rd('wPartyMon1HP', o) << 8 | g.rd('wPartyMon1HP', o + 1)
        mx += g.rd('wPartyMon1MaxHP', o) << 8 | g.rd('wPartyMon1MaxHP', o + 1)
    return cur / mx if mx else 1.0


class Failure:
    def __init__(self, kind, where, detail, shot=None):
        self.kind, self.where, self.detail, self.shot = kind, where, detail, shot
        # the signature ignores frame counters and screenshot paths: the same defect hashes the same
        import re
        d = re.sub(r'\d{3,}', 'N', detail.split(']')[-1])
        self.signature = hashlib.sha1(f'{kind}|{where}|{d}'.encode()).hexdigest()[:12]


class Explorer:
    def __init__(self, g, out, seed=1, label='run', provenance='gameplay'):
        self.g, self.out, self.label = g, out, label
        os.makedirs(out, exist_ok=True)
        self.nav = Navigator(g, seed=seed)
        self.guard = OverworldGuard(g)
        self.done = set()               # (map, x, y, epoch) interactions finished
        self.visited = set()
        self.epoch = 0
        self.failures = {}              # signature -> [Failure, count]
        self.timeline = []              # (frame, event)
        self.interactions = 0
        self.provenance = provenance    # 'gameplay' until something is injected
        self.assists = []               # what was injected, if anything
        self.checkpoints = []
        self.unreachable = set()
        self.bad_centers = set()
        self.no_heal_until = 0
        self.gated = {}
        self.last_progress = (0, 0)
        self.t0 = time.time()

    # ---- bookkeeping
    def note(self, what):
        self.timeline.append((self.g.frame, what))

    def fail(self, kind, detail, shot=None):
        f = Failure(kind, str(self.nav.here()[0]), detail, shot)
        slot = self.failures.setdefault(f.signature, [f, 0])
        slot[1] += 1
        if slot[1] == 1:
            self.note(f'FAILURE {kind} @ {f.where}: {detail[:120]}')
        return f

    def progress_key(self):
        g = self.g
        return (flags_set(g), badges(g), g.rd('wPartyCount'), len(self.visited))

    def checkpoint(self, name):
        import io
        path = os.path.join(self.out, f'{self.label}_{name}.state')
        self.g.dump_state(path)
        meta = dict(name=name, where=self.nav.pos(), frame=self.g.frame, flags=flags_set(self.g),
                    badges=badges(self.g), levels=party_levels(self.g), provenance=self.provenance,
                    assists=self.assists, visited=len(self.visited), inputs=len(self.nav.log))
        json.dump(meta, open(path[:-6] + '.json', 'w'))
        self.checkpoints.append(path)
        return path

    # ---- targets
    def targets_here(self):
        """Undone interactions on this map: [(tile_of_target, kind)]."""
        const, (px, py) = self.nav.here()
        out = []
        objs = self.nav.objects()
        for (x, y), sprite in objs.items():
            if (const, x, y, self.epoch) not in self.done:
                out.append(((x, y), 'npc'))
        if const:
            info = mapdata.parse_map(mapdata.attributes()[const]['label']) if const in mapdata.attributes() else {'bg': []}
            for x, y, kind in info['bg']:
                if (const, x, y, self.epoch) not in self.done and kind != 'BGEVENT_UP' :
                    out.append(((x, y), 'bg'))
        return out

    def interact(self, tile, kind):
        """Walk next to `tile`, face it and press A, then deal with whatever happens."""
        nav, g = self.nav, self.g
        const = nav.here()[0]
        self.done.add((const, tile[0], tile[1], self.epoch))
        # tiles from which the target can be faced
        stand = {}
        for d, (dx, dy) in DIRS.items():
            s = (tile[0] - dx, tile[1] - dy)
            if collision.walkable(g, s[0], s[1]):
                stand[s] = d
        if not stand:
            return False
        if not nav.goto_tile(set(stand)):
            return False
        pos = nav.here()[1]
        if pos not in stand:
            return False
        nav.face(stand[pos])
        if not nav.ready():
            nav.settle()
        nav.press('a', 4, 20)
        self.interactions += 1
        nav.settle()
        return True

    def heal(self):
        """Walk to a Pokemon Center and talk to the nurse. Centers are tried nearest first; one
        that cannot be reached, or does not heal, is not tried again this epoch."""
        g = self.g
        here = self.nav.here()[0]
        reach = world.reachable(here, self.nav.blocked_edges)
        centers = []
        for c in mapdata.attributes():
            if 'POKECENTER_1F' in c and c in reach and (c, self.epoch) not in self.bad_centers:
                r = world.route(here, c, self.nav.blocked_edges)
                if r is not None:
                    centers.append((len(r), c))
        for _, pc in sorted(centers)[:3]:
            self.note(f'healing at {pc}')
            try:
                self.nav.goto_map(pc)
            except Stuck:
                self.bad_centers.add((pc, self.epoch))
                continue
            objs = sorted(self.nav.objects().items(), key=lambda kv: kv[0][1])
            if objs:
                self.interact(objs[0][0], 'npc')
            if party_hp_fraction(g) > 0.9:
                return True
            self.bad_centers.add((pc, self.epoch))
        return False

    # ---- the loop
    def step_once(self):
        nav, g = self.nav, self.g
        const = nav.here()[0]
        if const:
            self.visited.add(const)
        if not nav.ready():
            nav.settle()
        if g.rd('wPartyCount') and party_hp_fraction(g) < 0.35 and self.interactions >= self.no_heal_until:
            if self.heal():
                return True
            self.no_heal_until = self.interactions + 15      # could not heal: carry on instead of looping
        todo = self.targets_here()
        if todo:
            _, (px, py) = nav.here()
            todo.sort(key=lambda t: abs(t[0][0] - px) + abs(t[0][1] - py))
            for tile, kind in todo[:3]:
                if self.interact(tile, kind):
                    return True
            return True
        return self.go_somewhere_new()

    def go_somewhere_new(self):
        """Walk toward the nearest map not yet visited. Maps that cannot be reached right now
        (gated by an HM or a story flag) are remembered per epoch and reported as gating, not
        as failures."""
        nav = self.nav
        here = nav.here()[0]
        reach = world.reachable(here, nav.blocked_edges)
        cands = []
        for c in reach:
            if c == here or c in self.visited or (c, self.epoch) in self.unreachable:
                continue
            r = world.route(here, c, nav.blocked_edges)
            if r:
                cands.append((len(r), c))
        cands.sort()
        for _, c in cands[:4]:
            try:
                nav.goto_map(c)
                return True
            except Stuck as e:
                self.unreachable.add((c, self.epoch))
                self.gated.setdefault(c, str(e))
        if not cands:
            self.epoch += 1
            nav.blocked_edges.clear()
            self.note(f'epoch {self.epoch}: nothing new reachable; re-interacting')
            return self.epoch < 3
        return True

    def run(self, budget_seconds=600, max_steps=100000, checkpoint_every=40):
        g, nav = self.g, self.nav
        steps = 0
        last_key = self.progress_key()
        while steps < max_steps and time.time() - self.t0 < budget_seconds:
            steps += 1
            try:
                alive = self.step_once()
            except Softlock as e:
                self.fail('softlock', str(e), (str(e).split(']')[0].lstrip('[') if str(e).startswith('[') else None))
                # recover: reload the most recent checkpoint if there is one
                if self.checkpoints:
                    g.load_state_file(self.checkpoints[-1])
                    self.note('restored last checkpoint after softlock')
                    self.nav.blocked_edges.clear()
                else:
                    return self.summary('softlock before any checkpoint')
                continue
            except Stuck as e:
                self.gated[str(self.nav.here()[0])] = str(e)
                self.epoch += 1
                continue
            self.guard.check('explorer')
            if self.guard.violations:
                self.fail('corruption', '; '.join(self.guard.violations[:2]))
                self.guard.player.violations.clear()
                self.guard.player.ref = self.guard.player.read()
            key = self.progress_key()
            if key[:3] != last_key[:3]:
                self.nav.blocked_edges.clear()      # the world may have changed: retry what failed before
            if key != last_key:
                if key[1] > last_key[1] or key[2] != last_key[2] or key[0] - last_key[0] >= checkpoint_every:
                    self.checkpoint(f'f{key[0]}_b{key[1]}_m{key[3]}')
                    last_key = key
            if not alive:
                break
        return self.summary('budget' if time.time() - self.t0 >= budget_seconds else 'done')

    def summary(self, why):
        g = self.g
        return dict(label=self.label, stopped=why, seconds=round(time.time() - self.t0), frames=g.frame,
                    maps_visited=len(self.visited), interactions=self.interactions, flags=flags_set(g),
                    badges=badges(g), levels=party_levels(g), battles=self.nav.stats['battles'],
                    inputs=len(self.nav.log), failures=[dict(sig=s, kind=f.kind, where=f.where, count=n, detail=f.detail[:300])
                                                         for s, (f, n) in self.failures.items()],
                    provenance=self.provenance, checkpoints=len(self.checkpoints), epoch=self.epoch, gated=len(self.gated))
