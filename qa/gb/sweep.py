"""Interaction sweep: poke every NPC, sign, hidden item and trigger tile of every map.

For each map (under a chosen flag state) the sweep enters the map by injected warp, then for
every target found in the running game's object table (and the repository's bg/coord events):
  * places the player next to it (INJECTED position), faces it, presses A (real input), and
    advances the resulting dialogue/scene/battle with controller input until control returns;
  * watches oracles throughout: ROM crash handlers, CPU hard lock, a softlock (control never
    returns while the screen is static), the player's object struct and follower queue, the
    stack pointer, and on SameBoy the native execution guard (NOP slides, illegal opcodes,
    code in VRAM/OAM/IO).
Failures are deduplicated by signature (kind + routine + map). The first examples of each
signature get a screenshot, the pre-interaction machine state, the input log and a replay
command. Results are appended per map to a JSONL file, so an interrupted sweep resumes.

    python3 -m qa.gb.sweep replay DIR/failures/<signature>      # reproduce one failure
"""
import bisect
import hashlib
import json
import os
import re
import sys

from . import collision, fixtures as F, mapdata
from .consts import C, map_ids
from .emu import ROOT
from .guards import OverworldGuard, PlayerStructGuard
from .nav import DIRS, Navigator

FACE = {'down': 0, 'up': 4, 'left': 8, 'right': 12}
N_FLAG_BYTES = 288
ADVANCE_BUDGET = 3600          # frames of dialogue/scene before a static screen is called a softlock
MAX_EXAMPLES = 3               # artifact sets kept per signature
STATES = ('default', 'allflags', 'noflags', 'party')


# ---- flag states --------------------------------------------------------------------------
def build_base(g):
    """a Totodile (so there is a follower)"""
    F.give_mon(g, C['TOTODILE'], 10)


def build_party(g):
    """six strong Pokemon, all badges, Pokegear cards and the Pokedex"""
    for sp in ('TYRANITAR', 'DRAGONITE', 'CHARIZARD', 'SNORLAX', 'GYARADOS', 'ALAKAZAM'):
        F.give_mon(g, C[sp], 100)
    g.wr('wJohtoBadges', 0xff)
    g.wr('wKantoBadges', 0xff)
    g.wr('wPokegearFlags', 0x1f)
    g.wr('wStatusFlags', g.rd('wStatusFlags') | 1)


def fixture_for(state):
    return ('sweep_party', build_party) if state == 'party' else ('sweep_base', build_base)


def apply_state(g, state):
    """Mutate the booted game for the flag state (INJECTED)."""
    base = g.sym['wEventFlags'][1]
    if state == 'allflags':
        for i in range(N_FLAG_BYTES):
            g.write(base + i, 0xff, 1)
    elif state == 'noflags':
        for i in range(N_FLAG_BYTES):
            g.write(base + i, 0x00, 1)


# ---- symbolising script positions ----------------------------------------------------------
_syms = {}


def sym_near(g, bank, addr):
    key = id(g.sym)
    if key not in _syms:
        by_bank = {}
        for n, (b, a) in g.sym.items():
            if not n.startswith('.'):
                by_bank.setdefault(b, []).append((a, n))
        for v in by_bank.values():
            v.sort()
        _syms[key] = {b: ([a for a, _ in v], [n for _, n in v]) for b, v in by_bank.items()}
    addrs, names = _syms[key].get(bank if addr >= 0x4000 else 0, ([], []))
    i = bisect.bisect_right(addrs, addr) - 1
    return names[i] if i >= 0 else '%02x:%04x' % (bank, addr)


# ---- oracles ------------------------------------------------------------------------------
class Oracles:
    def __init__(self, g, backend):
        self.g, self.backend = g, backend
        self.player = PlayerStructGuard(g)
        self.crash = None
        if backend == 'pyboy':
            self.crash = OverworldGuard(g).crash
        else:
            g.enable_exec_guard()
        self.hits = 0

    def start(self):
        self.player.ref = self.player.read()
        self.player.violations.clear()
        if self.crash:
            self.hits = len(self.crash.hits)
        else:
            from .sameboy import exec_guard_lib
            exec_guard_lib().execguard_reset()

    def hard_locked(self):
        g = self.g
        pcs = set()
        for _ in range(4):
            g.tick(1)
            pcs.add(g.pc)
        return g.read(0xffff) == 0 and len(pcs) == 1

    def check(self):
        """[(kind, routine, detail)] problems since start()."""
        g = self.g
        out = []
        if self.crash and len(self.crash.hits) > self.hits:
            out.append(('crash-handler', self.crash.hits[-1][1], 'ROM crash handler ran: %s' % (self.crash.hits[-1],)))
        if self.hard_locked():
            out.append(('hard-lock', g.where(), 'CPU stopped (IE=0, PC frozen) at %s' % g.where()))
        self.player.check('sweep')
        for v in self.player.violations:
            out.append(('corruption', 'player-struct', v))
        if g.sp < 0xc000 and g.sp != 0:
            out.append(('stack', 'sp', 'stack pointer %04x outside RAM' % g.sp))
        if self.backend == 'sameboy':
            for kind, pc, prev, op in g.exec_events():
                out.append(('exec-' + kind.split()[0].lower(), g.where(prev), '%s at %04x from %04x (%s), opcode %02x' % (
                    kind, pc, prev, g.where(prev), op)))
        return out


# ---- targets ------------------------------------------------------------------------------
class Target:
    def __init__(self, kind, x, y, need=None, label=''):
        self.kind, self.x, self.y, self.need, self.label = kind, x, y, need, label

    def key(self):
        return '%s@%d,%d' % (self.kind, self.x, self.y)


def read_targets(g, const):
    """Targets on the loaded map: objects (from the running game, minus those a set event flag hides),
    bg events and coord events (from the repository)."""
    out = []
    base = g.sym['wMapObjects'][1]
    stride = C['MAPOBJECT_LENGTH']
    flags = g.sym['wEventFlags'][1]
    for i in range(1, C['FOLLOWER_OBJECT']):
        a = base + i * stride
        sprite, y, x = g.read(a + 1, 1), g.read(a + 2, 1), g.read(a + 3, 1)
        if not sprite or y < 4 or x < 4:
            continue
        flag = g.read(a + 12, 1) | g.read(a + 13, 1) << 8
        if flag != 0xffff and flag < 2304 and g.read(flags + (flag >> 3), 1) >> (flag & 7) & 1:
            continue                                  # hidden by an event flag
        out.append(Target('npc', x - 4, y - 4, label='object %d' % i))
    attrs = mapdata.attributes()
    if const in attrs:
        info = mapdata.parse_map(attrs[const]['label'])
        need = {'BGEVENT_UP': 'up', 'BGEVENT_DOWN': 'down', 'BGEVENT_RIGHT': 'right', 'BGEVENT_LEFT': 'left'}
        for x, y, kind in info['bg']:
            out.append(Target('bg', x, y, need=need.get(kind), label=kind))
        for x, y, scene in info['coord']:
            out.append(Target('coord', x, y, label=scene))
    return out


def stand_tiles(g, t, occupied):
    """[(tile, direction to face)] next to the target."""
    res = []
    for d, (dx, dy) in DIRS.items():
        s = (t.x - dx, t.y - dy)               # we stand at s and face direction d toward the target
        if s in occupied:
            continue
        if not collision.walkable(g, s[0], s[1]):
            continue
        if t.need and d != t.need:             # a bg event that must be faced from one side only
            continue
        res.append((s, d))
    return res


# ---- the interaction ----------------------------------------------------------------------
def advance(nav, budget=ADVANCE_BUDGET, answer='a'):
    """Hand control back like Navigator.settle, but tell a long scene from a softlock: if the
    screen was still changing when the budget ran out it is 'long', not 'softlock'."""
    g = nav.g
    start = g.frame
    last, same, k = None, 0, 0
    order = [answer, 'b', 'down', 'a', 'up', 'a', 'start']
    changed_at = g.frame
    while not nav.ready():
        if g.frame - start > budget:
            return 'long' if g.frame - changed_at < 300 else 'softlock'
        if g.in_battle():
            nav.play_battle()
            changed_at = g.frame
            last, same = None, 0
            continue
        h = nav.screen_hash()
        if h != last:
            changed_at = g.frame
        same = same + 1 if h == last else 0
        last = h
        key = answer
        if same >= 6:
            k += 1
            same = 0
            key = order[k % len(order)]
        nav.press(key, 4, 16)
    g.tick(4)
    return 'ok'


def set_facing(g, direction):
    v = FACE[direction]
    g.wr('wPlayerDirection', v)
    base = g.sym['wPlayerStruct'][1]
    g.write(base + 8, v, 1)
    g.write(base + 13, v, 1)


class Result:
    def __init__(self):
        self.interactions = 0
        self.by_kind = {}
        self.outcomes = {'ok': 0, 'long': 0, 'softlock': 0, 'entry': 0}
        self.problems = []              # (signature, kind, routine, detail, map, target)
        self.untested = []              # (map, target key, why)


def signature(kind, routine, const):
    routine = re.sub(r'\+\d+$', '', routine)
    return hashlib.sha1(f'{kind}|{routine}|{const}'.encode()).hexdigest()[:12]


class Sweeper:
    def __init__(self, g, out, backend, model, state, seed=1):
        self.g, self.out, self.backend, self.model, self.state, self.seed = g, out, backend, model, state, seed
        self.nav = Navigator(g, seed=seed)
        self.oracles = Oracles(g, backend)
        self.base = None
        self.examples = {}
        os.makedirs(os.path.join(out, 'failures'), exist_ok=True)

    def prepare(self):
        apply_state(self.g, self.state)
        self.base = self.g.snap()

    # one map
    def sweep_map(self, const, max_targets=60):
        g, nav = self.g, self.nav
        res = Result()
        g.unsnap(self.base)
        try:
            sg, sn = map_ids(const)
        except KeyError:
            res.untested.append((const, '-', 'no map ids'))
            return res
        self.oracles.start()
        F.teleport(g, sg, sn, 2, 2, settle=60)
        if F.where(g)[:2] != (sg, sn):
            res.untested.append((const, '-', 'warp did not load the map'))
            return res
        if advance(nav, 2400) != 'ok':
            res.outcomes['entry'] += 1
        # a walkable tile to be "inside" the map, then the map-level snapshot
        w, h = g.rd('wMapWidth') * 2, g.rd('wMapHeight') * 2
        inside, best = None, 1e9
        for y in range(h):
            for x in range(w):
                if collision.walkable(g, x, y):
                    d = abs(x - w // 2) + abs(y - h // 2)
                    if d < best:
                        best, inside = d, (x, y)
        if inside is None:
            res.untested.append((const, '-', 'no walkable tile'))
            return res
        F.teleport(g, sg, sn, inside[0], inside[1], settle=60)
        if advance(nav, 2400) != 'ok':
            res.outcomes['entry'] += 1
        for kind, routine, detail in self.oracles.check():
            self.record(res, const, Target('entry', inside[0], inside[1]), kind, routine, detail, None)
        mapsnap = g.snap()
        targets = read_targets(g, const)[:max_targets]
        for t in targets:
            self.interact(res, const, sg, sn, mapsnap, t)
        return res

    def interact(self, res, const, sg, sn, mapsnap, t):
        g, nav = self.g, self.nav
        g.unsnap(mapsnap)
        stands = stand_tiles(g, t, set(nav.objects()))
        if not stands:
            res.untested.append((const, t.key(), 'no walkable adjacent tile'))
            return
        tried = False
        for tile, d in stands[:2]:
            g.unsnap(mapsnap)
            self.oracles.start()
            F.teleport(g, sg, sn, tile[0], tile[1], settle=40)
            if F.where(g)[:2] != (sg, sn) or F.where(g)[2:] != tile:
                continue
            if advance(nav, 1200) != 'ok':
                res.untested.append((const, t.key(), 'map-entry scene did not hand back control'))
                return
            pre = g.snap()
            pre_frame = g.frame
            log0 = len(nav.log)
            self.oracles.start()
            if t.kind == 'coord':
                nav.hold(d, 16)
                g.tick(4)
            else:
                if not collision.walkable(g, t.x, t.y):
                    nav.face(d)
                else:
                    set_facing(g, d)
                nav.press('a', 4, 20)
            res.interactions += 1
            res.by_kind[t.kind] = res.by_kind.get(t.kind, 0) + 1
            outcome = advance(nav)
            res.outcomes[outcome] = res.outcomes.get(outcome, 0) + 1
            g.tick(30)
            problems = self.oracles.check()
            if outcome == 'softlock':
                bank, pos = g.read(0xff89), g.read(0xff8a) | g.read(0xff8b) << 8
                routine = sym_near(g, bank & 0x7f, pos)
                problems.append(('softlock', routine, 'no control after %d frames, static screen; script %02x:%04x (%s), map %s' % (
                    ADVANCE_BUDGET, bank & 0x7f, pos, routine, F.where(g))))
            art = (pre, pre_frame, nav.log[log0:], g.frame - pre_frame, d, tile)
            for kind, routine, detail in problems:
                self.record(res, const, t, kind, routine, detail, art)
            tried = True
            break
        if not tried:
            res.untested.append((const, t.key(), 'could not place the player next to it'))

    def record(self, res, const, t, kind, routine, detail, art):
        sig = signature(kind, routine, const)
        res.problems.append((sig, kind, routine, detail, const, t.key()))
        n = self.examples.get(sig, 0)
        if n >= MAX_EXAMPLES:
            return
        self.examples[sig] = n + 1
        d = os.path.join(self.out, 'failures', sig + ('' if n == 0 else '_%d' % n))
        os.makedirs(d, exist_ok=True)
        self.g.screenshot(os.path.join(d, 'after'))
        meta = dict(signature=sig, kind=kind, routine=routine, detail=detail, map=const, target=t.key(), state=self.state,
                    backend=self.backend, model=self.model, seed=self.seed, provenance='injected: position, flag state')
        if art:
            pre, pre_frame, log, frames, face, tile = art
            open(os.path.join(d, 'pre.state'), 'wb').write(pre)
            json.dump([(f - pre_frame, b, h) for f, b, h in log], open(os.path.join(d, 'inputs.json'), 'w'))
            meta.update(pre_frame=pre_frame, run_frames=frames, face=face, stand=tile,
                        replay='python3 -m qa.gb.sweep replay %s' % os.path.relpath(d, ROOT))
        json.dump(meta, open(os.path.join(d, 'meta.json'), 'w'), indent=1)


# ---- shards, resume, aggregation ------------------------------------------------------------
def map_list(shard, shards):
    return sorted(mapdata.attributes())[shard::shards]


def run_shard(g, out, backend, model, state, shard, shards, seed=1, limit=None, resume=True, results_dir=None):
    """Sweep one shard's maps; returns a summary dict. Failure artifacts go under out/failures;
    per-map results go to results_dir/results.jsonl (default: out), which makes a rerun resume."""
    os.makedirs(out, exist_ok=True)
    results_dir = results_dir or out
    os.makedirs(results_dir, exist_ok=True)
    path = os.path.join(results_dir, 'results.jsonl')
    done = {}
    if resume and os.path.exists(path):
        for line in open(path):
            r = json.loads(line)
            done[r['map']] = r
    sw = Sweeper(g, out, backend, model, state, seed)
    sw.prepare()
    maps = map_list(shard, shards)
    if limit:
        maps = maps[:limit]
    with open(path, 'a') as f:
        for const in maps:
            if const in done:
                continue
            r = sw.sweep_map(const)
            rec = dict(map=const, interactions=r.interactions, by_kind=r.by_kind, outcomes=r.outcomes,
                       problems=[dict(sig=p[0], kind=p[1], routine=p[2], detail=p[3][:400], target=p[5]) for p in r.problems],
                       untested=[list(u) for u in r.untested])
            f.write(json.dumps(rec) + '\n')
            f.flush()
            done[const] = rec
    return summarize([done[m] for m in maps if m in done], maps)


def summarize(recs, maps):
    s = dict(maps_total=len(maps), maps_done=len(recs), interactions=0, by_kind={}, outcomes={}, signatures={}, untested=[])
    for r in recs:
        s['interactions'] += r['interactions']
        for k, v in r['by_kind'].items():
            s['by_kind'][k] = s['by_kind'].get(k, 0) + v
        for k, v in r['outcomes'].items():
            s['outcomes'][k] = s['outcomes'].get(k, 0) + v
        for p in r['problems']:
            e = s['signatures'].setdefault(p['sig'], dict(kind=p['kind'], routine=p['routine'], map=r['map'], detail=p['detail'], count=0, targets=[]))
            e['count'] += 1
            if len(e['targets']) < 5:
                e['targets'].append('%s %s' % (r['map'], p['target']))
        s['untested'] += [(r['map'],) + tuple(u[1:]) for u in r['untested']]
    return s


# ---- replay ----------------------------------------------------------------------------------
def replay(d, model=None):
    meta = json.load(open(os.path.join(d, 'meta.json')))
    backend = meta['backend']
    if backend == 'sameboy':
        from .sameboy import SBGame
        g = SBGame(workdir=d, model=model or meta['model'] or 'CGB-E', seed=meta['seed'])
    else:
        from .emu import Game
        g = Game(workdir=d, seed=meta['seed'])
    g.tick(30)
    g.load_state_file(os.path.join(d, 'pre.state'))
    g.frame = 0
    ora = Oracles(g, backend)
    ora.start()
    for rel, b, hold in json.load(open(os.path.join(d, 'inputs.json'))):
        while g.frame < rel:
            g.tick(1)
        g.hold(b, hold)
    while g.frame < meta['run_frames']:
        g.tick(1)
    probs = ora.check()
    print('replayed %s on %s: %d problem(s)' % (meta['signature'], backend, len(probs)))
    for p in probs:
        print('  ', p)
    return probs


if __name__ == '__main__':
    if len(sys.argv) >= 3 and sys.argv[1] == 'replay':
        replay(sys.argv[2])
