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
    python3 -m qa.gb.sweep coverage OUT.json RESULTS.jsonl...    # union coverage sets
"""
import bisect
import hashlib
import json
import os
import re
import sys

from . import collision, fixtures as F, mapdata, world
from .consts import C, map_ids
from .emu import ROOT
from .guards import OverworldGuard, PlayerStructGuard
from .nav import DIRS, Navigator, Softlock

FACE = {'down': 0, 'up': 4, 'left': 8, 'right': 12}
N_FLAG_BYTES = 288
STUCK_FRAMES = 900            # a script waiting at one position this long, with the screen still animating, is reported
ADVANCE_BUDGET = 3600          # frames of dialogue/scene before a static screen is called a softlock
MAX_EXAMPLES = 3               # artifact sets kept per signature
STATES = ('default', 'allflags', 'noflags', 'party')


# ---- flag states --------------------------------------------------------------------------
def build_base(g):
    """a level 100 Tyranitar (INJECTED): strong enough that line-of-sight trainers and story battles end in
    a win instead of a whiteout that would send the player home and hide the rest of the map. Flags are untouched."""
    F.give_mon(g, C['TYRANITAR'], 100)


def build_party(g):
    """six strong Pokemon, all badges, Pokegear cards and the Pokedex"""
    for sp in ('TYRANITAR', 'DRAGONITE', 'CHARIZARD', 'SNORLAX', 'GYARADOS', 'ALAKAZAM'):
        F.give_mon(g, C[sp], 100)
    g.wr('wJohtoBadges', 0xff)
    g.wr('wKantoBadges', 0xff)
    g.wr('wPokegearFlags', 0x1f)
    g.wr('wStatusFlags', g.rd('wStatusFlags') | 1)


def fixture_for(state):
    return ('sweep_party', build_party) if state == 'party' else ('sweep_base_t100', build_base)


def apply_state(g, state):
    """Mutate the booted game for the flag state (INJECTED). Wild encounters are switched off in every
    state (wStatusFlags bit 5, what the wildoff script command does): the sweep must not start random
    battles while it walks; trainer/story battles an interaction triggers are still fought."""
    g.wr('wStatusFlags', g.rd('wStatusFlags') | 0x20)
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
    def __init__(self, kind, x, y, need=None, label='', index=None):
        self.kind, self.x, self.y, self.need, self.label, self.index = kind, x, y, need, label, index

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
        out.append(Target('npc', x - 4, y - 4, label='object %d' % i, index=i - 1))
    attrs = mapdata.attributes()
    if const in attrs:
        info = mapdata.parse_map(attrs[const]['label'])
        need = {'BGEVENT_UP': 'up', 'BGEVENT_DOWN': 'down', 'BGEVENT_RIGHT': 'right', 'BGEVENT_LEFT': 'left'}
        for n, (x, y, kind) in enumerate(info['bg']):
            out.append(Target('bg', x, y, need=need.get(kind), label=kind, index=n))
        for n, (x, y, scene) in enumerate(info['coord']):
            out.append(Target('coord', x, y, label=scene, index=n))
    return out


GLOW_FLOOR = {0x03, 0x04, 0x05, 0x06, 0x08}   # campfire/aquarium/lantern/lava/shrine-lamp glow: LAND_TILE decoration
COLL_WATER, COLL_COUNTER = 0x29, 0x90


def _land(g, x, y):
    c = collision.tile_collision(g, x, y)
    return c in collision.PASSABLE or c in GLOW_FLOOR


def stand_tiles(g, t, occupied):
    """[(tile, direction to face, mode)] from which the target can be interacted with. mode is 'land'
    (walk there) or 'surf' (water: the player is injected in the surfing state). Land tiles come first;
    for an NPC behind a counter the player stands two tiles away (the game doubles the facing distance
    across COLL_COUNTER, see CheckFacingObject)."""
    res, water = [], []
    for d, (dx, dy) in DIRS.items():
        s = (t.x - dx, t.y - dy)               # we stand at s and face direction d toward the target
        if t.need and d != t.need:             # a bg event that must be faced from one side only
            continue
        if s in occupied:
            continue
        if _land(g, *s):
            res.append((s, d, 'land'))
        elif collision.tile_collision(g, *s) == COLL_WATER:
            water.append((s, d, 'surf'))
        elif t.kind == 'npc' and collision.tile_collision(g, *s) == COLL_COUNTER:
            s2 = (t.x - 2 * dx, t.y - 2 * dy)
            if s2 not in occupied and _land(g, *s2):
                res.append((s2, d, 'land'))
    return res + water


# ---- the interaction ----------------------------------------------------------------------
def advance(nav, budget=ADVANCE_BUDGET, answer='a'):
    """Hand control back like Navigator.settle, but tell a long scene from a softlock: if the
    screen was still changing when the budget ran out it is 'long', not 'softlock'."""
    g = nav.g
    start = g.frame
    last, same, k = None, 0, 0
    order = [answer, 'b', 'down', 'a', 'up', 'a', 'start']
    changed_at = g.frame
    bank_a, pos_a = g.sym['hScriptBank'][1], g.sym['hScriptPos'][1]
    spos, moved_at = None, g.frame
    nav.stuck_script = None
    while not nav.ready():
        p = (g.read(bank_a) & 0x7f, g.read(pos_a) | g.read(pos_a + 1) << 8)
        if p != spos:
            spos, moved_at = p, g.frame
        if g.frame - start > budget:
            if g.frame - moved_at >= STUCK_FRAMES and g.rd('wScriptRunning'):
                nav.stuck_script = p          # one script position for 15+ seconds of pressing buttons
            return 'long' if g.frame - changed_at < 300 else 'softlock'
        if g.in_battle():
            try:
                nav.play_battle()
            except Softlock:
                return 'battle-stall'
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
        self.expected = []              # (map, target key, reason): stalls that need link/challenge state
        self.entered = False            # the map was entered and its targets could be tried
        self.stuck = []                 # (map, target key, script label): animated screen but the script never advanced
        self.cov = dict(objects=set(), bg_events=set(), coord_events=set(), scripts=set())


def signature(kind, routine, const):
    routine = re.sub(r'\+\d+$', '', routine)
    return hashlib.sha1(f'{kind}|{routine}|{const}'.encode()).hexdigest()[:12]


def expected_stall(const):
    """Maps whose scripts legitimately wait on state a sweep cannot provide. Documented, never hidden:
    the sweep lists every one of these in its results as 'expected' with the reason."""
    if const in ('TRADE_CENTER', 'COLOSSEUM', 'TIME_CAPSULE', 'MOBILE_TRADE_ROOM', 'MOBILE_BATTLE_ROOM'):
        return 'needs a link partner: the room\'s script calls the link routines (Special_TradeCenter etc.) and waits for a cable'
    if const.startswith(('BATTLE_TOWER', 'BATTLE_FACTORY')):
        return 'needs an active Battle Tower/Factory challenge (the ROM has a dedicated crash code, ERR_BT_STATE, for an invalid state)'
    return None


class Sweeper:
    def __init__(self, g, out, backend, model, state, seed=1):
        out = os.path.abspath(out)
        self.g, self.out, self.backend, self.model, self.state, self.seed = g, out, backend, model, state, seed
        self.nav = Navigator(g, seed=seed)
        self.oracles = Oracles(g, backend)
        self.base = None
        self.examples = {}
        self.script_hits = set()
        self._install_script_hook()
        os.makedirs(os.path.join(out, 'failures'), exist_ok=True)

    def _install_script_hook(self):
        """Record every script position the script engine executes (bank, address); symbolised per map."""
        g = self.g
        bank_a, pos_a = g.sym['hScriptBank'][1], g.sym['hScriptPos'][1]

        def hit(_=None):
            self.script_hits.add((g.read(bank_a) & 0x7f, g.read(pos_a) | g.read(pos_a + 1) << 8))
        if self.backend == 'pyboy':          # SameBoy's per-instruction callback is too slow for this
            g.hook('RunScriptCommand', hit)

    def script_labels(self):
        out = {sym_near(self.g, b, a) for b, a in self.script_hits if a < 0x8000}
        self.script_hits.clear()
        return out

    def prepare(self):
        apply_state(self.g, self.state)
        self.base = self.g.snap()

    def inside_tile(self):
        g = self.g
        w, h = g.rd('wMapWidth') * 2, g.rd('wMapHeight') * 2
        best, tile = 1e9, None
        for y in range(h):
            for x in range(w):
                if collision.walkable(g, x, y):
                    d = abs(x - w // 2) + abs(y - h // 2)
                    if d < best:
                        best, tile = d, (x, y)
        return tile

    def real_arrival(self, const):
        """Walk into `const` for real (controller input through a door or across a connection) from
        a neighbouring map. A teleport enters a map by a different path than a door does, so entry
        scenes can behave differently (a callback that shows text while the LCD is still off hangs only
        under the injected entry). Returns (outcome, snapshot): outcome is ok/long/softlock/battle-stall,
        'ejected' (the entry scene sends the player away) or 'none' (no way in on foot)."""
        g, nav = self.g, self.nav
        target = map_ids(const)
        for src, edge in world.incoming(const)[:4]:
            try:
                s2 = map_ids(src)
            except KeyError:
                continue
            g.unsnap(self.base)
            self.oracles.start()
            F.teleport(g, s2[0], s2[1], 2, 2, settle=60)
            if F.where(g)[:2] != s2 or advance(nav, 3600) != 'ok' or F.where(g)[:2] != s2:
                continue
            tile = self.inside_tile()
            if tile is None:
                continue
            F.teleport(g, s2[0], s2[1], tile[0], tile[1], settle=60)
            if advance(nav, 3600) != 'ok' or F.where(g)[:2] != s2:
                continue
            nav.blocked_edges.clear()
            try:
                got = nav.take_edge(edge)
            except Exception:
                got = None
            if got != const:
                continue
            out = advance(nav, 3600)
            if F.where(g)[:2] != target:
                return 'ejected', None
            return out, (g.snap() if out in ('ok', 'long') else None)
        for src, x, y in world.incoming_script_warps(const)[:2]:
            # a story warp: `warp MAP, x, y` is newloadmap MAPSETUP_WARP, which is exactly what the injected
            # teleport does, so teleporting to the scripted arrival tile reproduces the game's own entry
            g.unsnap(self.base)
            self.oracles.start()
            F.teleport(g, target[0], target[1], x, y, settle=60)
            out = advance(nav, 3600)
            if F.where(g)[:2] != target:
                return 'ejected', None
            return out, (g.snap() if out in ('ok', 'long') else None)
        warps = world.warps(const)
        if warps:                               # no way in on foot: arrive on the map's own warp tile (weaker evidence)
            g.unsnap(self.base)
            self.oracles.start()
            F.teleport(g, target[0], target[1], warps[0][0], warps[0][1], settle=60)
            out = advance(nav, 3600)
            if F.where(g)[:2] != target:
                return 'ejected', None
            if out in ('ok', 'long'):
                return out, g.snap()
        return 'none', None

    def confirm_entry(self, res, const, tile, entry):
        """The entry scene failed with the player injected at `tile`. Repeat it the way the game does
        (a real walk in). Returns (verdict, snapshot): 'artifact' (real entry works; snapshot is the
        state after it), 'real' (fails for real: record it), or 'other' (already filed as untested or expected)."""
        why = expected_stall(const)
        out, snap = self.real_arrival(const)
        key = 'entry@%d,%d' % tile
        if out in ('ok', 'long'):
            res.untested.append((const, key, 'entry scene fails only with the injected entry (%s at %s); walking in through a door '
                                 'works: injected-entry artifact, explored from the real arrival instead' % (entry, tile)))
            return 'artifact', snap
        if out == 'ejected':
            res.untested.append((const, key, 'the entry scene sends the player away in this flag state (arriving for real)'))
            return 'other', None
        if why:
            res.expected.append((const, key, why))
            return 'other', None
        if out == 'none':
            res.untested.append((const, key, 'entry scene fails when injected (%s) and the map has no door or connection to walk in by: '
                                 'unconfirmed' % entry))
            return 'other', None
        res.untested.append((const, key, 'entry scene failed (%s) for real too (%s)' % (entry, out)))
        return 'real', None

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
        e1 = advance(nav, 3600)
        self.mode = 'teleport'
        if e1 != "ok":
            res.outcomes['entry'] += 1
        if F.where(g)[:2] != (sg, sn) or e1 in ('softlock', 'battle-stall'):
            # the injected entry went wrong (stalled, or a scene such as a gym's "away" warp used an unset
            # warp destination and left us on no map): judge the map by a real walk in instead
            verdict, snap = self.confirm_entry(res, const, (2, 2), e1 if e1 != 'ok' else 'ejected')
            if verdict == 'real':
                self.record(res, const, Target('entry', 2, 2), e1, 'entry',
                            'entry at (2, 2): %s, and again when walking in through a door; map %s' % (e1, F.where(g)), None)
            if verdict != 'artifact':
                return res
            g.unsnap(snap)
            self.mode = 'walk'
            inside = F.where(g)[2:]
            e0 = 'ok'
        else:
            # a walkable tile to be "inside" the map, then the map-level snapshot
            inside = self.inside_tile()
            if inside is None:
                res.untested.append((const, '-', 'no walkable tile'))
                return res
            F.teleport(g, sg, sn, inside[0], inside[1], settle=60)
            e0 = advance(nav, 3600)
            if e0 != "ok":
                res.outcomes['entry'] += 1
            if e0 in ('softlock', 'battle-stall') or F.where(g)[:2] != (sg, sn):
                verdict, snap = self.confirm_entry(res, const, inside, e0 if e0 != 'ok' else 'ejected')
                if verdict == 'real':
                    self.record(res, const, Target('entry', inside[0], inside[1]), e0, 'entry',
                                'entry at %s: %s, and again when walking in through a door; map %s' % (inside, e0, F.where(g)), None)
                if verdict != 'artifact':
                    return res
                g.unsnap(snap)                # continue from the real arrival: targets are reached by walking
                self.mode = 'walk'
        if F.where(g)[:2] != (sg, sn):
            res.untested.append((const, '-', 'the entry scene ejects the player to %s (the map cannot be explored in this flag state)' % (F.where(g)[:2],)))
            return res
        if self.mode == 'teleport':
            for kind, routine, detail in self.oracles.check():
                self.record(res, const, Target('entry', inside[0], inside[1]), kind, routine, detail, None)
        mapsnap = g.snap()
        res.entered = True
        targets = read_targets(g, const)[:max_targets]
        self.script_hits.clear()
        for t in targets:
            self.interact(res, const, sg, sn, mapsnap, t)
        res.cov['scripts'] |= self.script_labels()
        return res

    def interact(self, res, const, sg, sn, mapsnap, t):
        g, nav = self.g, self.nav
        g.unsnap(mapsnap)
        stands = stand_tiles(g, t, set(nav.objects()))
        if not stands:
            res.untested.append((const, t.key(), 'no walkable adjacent tile'))
            return
        if self.mode == 'walk':
            return self.interact_walking(res, const, mapsnap, t, stands)
        tried = False
        for tile, d, mode in stands[:2]:
            g.unsnap(mapsnap)
            self.oracles.start()
            g.wr('wPlayerState', 4 if mode == 'surf' else 0)         # INJECTED: PLAYER_SURF to stand on water
            F.teleport(g, sg, sn, tile[0], tile[1], settle=40)
            if F.where(g)[:2] != (sg, sn) or F.where(g)[2:] != tile:
                continue
            entry = advance(nav, 3600)
            if entry == 'ok' and F.where(g)[:2] != (sg, sn):
                res.untested.append((const, t.key(), 'the entry scene ejects the player to %s' % (F.where(g)[:2],)))
                return
            if entry != 'ok':
                res.untested.append((const, t.key(), 'map-entry scene did not hand back control (%s)' % entry))
                if entry in ('battle-stall', 'softlock'):
                    verdict, _snap = self.confirm_entry(res, const, tile, entry)
                    if verdict == 'real':
                        self.record(res, const, Target('entry', tile[0], tile[1]), entry, 'entry',
                                    'standing at %s: %s after entering the map, and again when walking in; map %s' % (
                                        tile, entry, F.where(g)), None)
                return
            self.run_interaction(res, const, t, d, tile)
            tried = True
            break
        if not tried:
            res.untested.append((const, t.key(), 'could not place the player next to it'))

    def interact_walking(self, res, const, mapsnap, t, stands):
        """Reach the target by walking (real input) from the real arrival state."""
        g, nav = self.g, self.nav
        for tile, d, mode in stands[:2]:
            if mode != 'land':
                continue
            g.unsnap(mapsnap)
            self.oracles.start()
            try:
                ok = nav.goto_tile({tile})
            except Exception:
                ok = False
            if not ok or F.where(g)[2:] != tile or F.where(g)[:2] != map_ids(const):
                continue
            if not nav.ready() and advance(nav, 1200) != 'ok':
                continue
            self.run_interaction(res, const, t, d, tile)
            return
        res.untested.append((const, t.key(), 'could not walk next to it'))

    def run_interaction(self, res, const, t, d, tile):
        """The player stands at `tile` with control: face the target, press A (or step onto a trigger
        tile), advance whatever follows, and judge the result."""
        g, nav = self.g, self.nav
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
        label = mapdata.attributes()[const]['label']
        if t.index is not None:
            res.cov[{'npc': 'objects', 'bg': 'bg_events', 'coord': 'coord_events'}[t.kind]].add('%s:%d' % (label, t.index))
        outcome = advance(nav)
        if getattr(nav, 'stuck_script', None):
            b, a = nav.stuck_script
            res.stuck.append((const, t.key(), sym_near(g, b, a)))
        g.tick(30)
        problems = self.oracles.check()
        why = expected_stall(const)
        if why and (outcome in ('softlock', 'battle-stall') or problems):
            res.expected.append((const, t.key(), why))
            problems, outcome = [], 'expected'
        res.outcomes[outcome] = res.outcomes.get(outcome, 0) + 1
        if outcome == 'battle-stall':
            problems.append(('battle-stall', 'battle', 'the battle did not end in 36000 frames of autoplay (the policy '
                             'only fights; a stalemate or a stuck menu): map %s, %s' % (const, F.where(g))))
        if outcome == 'softlock':
            bank, pos = g.read(0xff89), g.read(0xff8a) | g.read(0xff8b) << 8
            routine = sym_near(g, bank & 0x7f, pos)
            problems.append(('softlock', routine, 'no control after %d frames, static screen; script %02x:%04x (%s), map %s' % (
                ADVANCE_BUDGET, bank & 0x7f, pos, routine, F.where(g))))
        art = (pre, pre_frame, nav.log[log0:], g.frame - pre_frame, d, tile)
        for kind, routine, detail in problems:
            self.record(res, const, t, kind, routine, detail, art)

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
    """This shard's maps. QA_SWEEP_MAPS=<file with one map constant per line> restricts the sweep to those maps."""
    allm = sorted(mapdata.attributes())
    only = os.environ.get('QA_SWEEP_MAPS')
    if only:
        keep = {l.strip() for l in open(only) if l.strip()}
        allm = [m for m in allm if m in keep]
    return allm[shard::shards]


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
                       untested=[list(u) for u in r.untested], expected=[list(u) for u in r.expected],
                       entered=r.entered, stuck=[list(x) for x in r.stuck], covered={k: sorted(v) for k, v in r.cov.items()})
            f.write(json.dumps(rec) + '\n')
            f.flush()
            done[const] = rec
    return summarize([done[m] for m in maps if m in done], maps)


def summarize(recs, maps):
    s = dict(maps_total=len(maps), maps_done=len(recs), interactions=0, by_kind={}, outcomes={}, signatures={}, untested=[], expected=[])
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
        s['expected'] += [(r['map'],) + tuple(u[1:]) for u in r.get('expected', [])]
    return s


# ---- coverage sets ----------------------------------------------------------------------------
def coverage(results_files, out_path):
    """Union the per-map results of any number of sweeps into the inventory-coverage JSON:
    {"maps": [...], "objects": ["Label:index", ...], "bg_events": [...], "coord_events": [...], "scripts": [...]}.
    `Label` is the map's label (maps/<Label>.asm); an index is the 0-based position of the
    object_event / bg_event / coord_event line in that file. A map counts as swept when it was entered
    and its targets could be tried. An object/bg/coord event counts when an interaction was executed on it."""
    attrs = mapdata.attributes()
    cov = dict(maps=set(), objects=set(), bg_events=set(), coord_events=set(), scripts=set())
    runs = []
    for path in results_files:
        n = 0
        for line in open(path):
            r = json.loads(line)
            n += 1
            if r.get('entered'):
                cov['maps'].add(attrs[r['map']]['label'] if r['map'] in attrs else r['map'])
            for k, v in r.get('covered', {}).items():
                cov[k] |= set(v)
        runs.append('%s (%d maps)' % (path, n))
    doc = {k: sorted(v) for k, v in cov.items()}
    doc['sources'] = runs
    os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
    json.dump(doc, open(out_path, 'w'), indent=1)
    return {k: len(v) for k, v in cov.items()}


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
    elif len(sys.argv) >= 4 and sys.argv[1] == 'coverage':
        print(coverage(sys.argv[3:], sys.argv[2]))
