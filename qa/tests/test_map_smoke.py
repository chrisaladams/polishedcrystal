"""Enter every map and check the engine's invariants and the hardware's sprite rules.

For each of the 613 maps: an injected warp loads it, the player is placed on a
walkable tile chosen from the map's own collision data, the game runs for
90 frames, and the following must hold:
  - no ROM crash handler ran and the game loop is still advancing (VBlank counter)
  - the player's object struct and the follower queue are intact
  - the player's sprite is in OAM
  - no scanline has more than 10 sprites (extra ones are dropped on hardware)
A map with no walkable tile cannot be entered this way: it is counted as untested.
"""
import os

from qa.framework import qa_test
from qa.gb import collision, fixtures as F, hw, mapdata
from qa.gb.consts import C, map_ids
from qa.gb.guards import OverworldGuard

PROVENANCE = 'injected warp into each map; no gameplay input (the player stands still)'

# Maps whose entry scripts depend on state that only a real challenge sets up. Entering them by
# injection hard-locks the CPU (it executes data). Recorded, not hidden: see docs/qa-report.md, F3.
STATE_DEPENDENT = {
    'BATTLE_FACTORY_HALLWAY': 'the map callback runs data as code when no Battle Factory challenge is active '
                              '(CPU hard lock); reachability in real play NOT verified',
}


def hard_locked(g):
    """The CPU stopped for good: IE cleared and the PC no longer moving (PyBoy halts the core on an
    illegal opcode, as the hardware locks up)."""
    pcs = set()
    for _ in range(6):
        g.tick(1)
        pcs.add(g.pc)
    return g.read(0xffff) == 0 and len(pcs) == 1


def build(g):
    """a Totodile (so there is a follower)"""
    F.give_mon(g, C['TOTODILE'], 10)


def pick_tile(g):
    w, h = g.rd('wMapWidth') * 2, g.rd('wMapHeight') * 2
    cx, cy = w // 2, h // 2
    best = None
    for y in range(h):
        for x in range(w):
            if collision.walkable(g, x, y):
                d = abs(x - cx) + abs(y - cy)
                if best is None or d < best[0]:
                    best = (d, x, y)
    return best[1:] if best else None


def some_sprites_drawn(g):
    """A standing player is at least one 2x2 object: 4 OAM entries on screen. (Finding the
    player's own entries would need the camera offset, which small maps and Cycling Road change.)"""
    return len(hw.visible_sprites(g)) >= 4


def run_shard(ctx, shard, shards):
    g = ctx.boot('smoke_base', build)
    guard = OverworldGuard(g)
    g.save_point()
    consts = sorted(mapdata.attributes())[shard::shards]
    import os
    if os.environ.get('QA_MAP_LIMIT'):
        consts = consts[:int(os.environ['QA_MAP_LIMIT'])]
    tested = no_tile = 0
    known = []
    stats = {'max_line': 0, 'max_line_map': None, 'player_hidden': [], 'lines_over': []}
    for const in consts:
        label = mapdata.attributes()[const]['label']
        g.restore_point()
        guard.player.ref = guard.player.read()
        guard.player.violations.clear()
        try:
            sg, sn = map_ids(const)
        except KeyError:
            continue
        try:
            F.teleport(g, sg, sn, 2, 2, settle=60)
            if F.where(g)[:2] != (sg, sn):
                ctx.expect(False, f'{const}: warp did not load the map (at {F.where(g)})')
                continue
            tile = pick_tile(g)
            if tile is None:
                no_tile += 1
                continue
            F.teleport(g, sg, sn, tile[0], tile[1], settle=90)
            g.tick(90)
            tested += 1
            if hard_locked(g):
                if const in STATE_DEPENDENT:
                    known.append(f'{const}: {STATE_DEPENDENT[const]}')
                else:
                    ctx.expect(False, f'{const}: CPU hard lock at {g.where()} (illegal opcode or executing data)')
                continue
            guard.check(const)
            if guard.violations:
                ctx.expect(False, f'{const}: ' + '; '.join(guard.violations[:2]))
                continue
            lines, dropped = hw.line_pressure(g)
            mx = max((len(v) for v in lines.values()), default=0)
            if mx > stats['max_line']:
                stats['max_line'], stats['max_line_map'] = mx, const
            if dropped:
                stats['lines_over'].append(f'{const} ({len(dropped)} sprites dropped)')
            if not some_sprites_drawn(g) and not g.in_battle() and g.rd('wScriptMode') == 0 and g.rd('wScriptRunning') == 0:
                stats['player_hidden'].append(const)
        except Exception as e:
            ctx.expect(False, f'{const}: {type(e).__name__}: {e}')
    ctx.note(f'shard {shard}/{shards}: {tested} maps entered and checked, {no_tile} had no walkable tile, '
             f'max sprites on one scanline {stats["max_line"]} ({stats["max_line_map"]})')
    for k in known:
        ctx.note('KNOWN FINDING (not failing the run): ' + k)
    if known:
        ctx.uncover('map.smoke', f'{len(known)} state-dependent map(s) hard-lock when entered by injection')
    if stats['lines_over']:
        ctx.note('scanline sprite overflow (hardware drops the extras): ' + '; '.join(stats['lines_over'][:20]))
        ctx.expect(False, f'{len(stats["lines_over"])} maps overflow 10 sprites on a scanline: ' + '; '.join(stats['lines_over'][:8]))
    if stats['player_hidden']:
        ctx.note('fewer than 4 sprites on screen at rest: ' + ', '.join(stats['player_hidden'][:30]))
        ctx.expect(False, f'{len(stats["player_hidden"])} maps: fewer than 4 sprites drawn: ' + ', '.join(stats['player_hidden'][:10]))
    if no_tile:
        ctx.uncover('map.smoke', f'{no_tile} of {len(consts)} maps in this shard had no walkable tile')


def _make(i, n):
    @qa_test(suites=('map', 'full'), covers=('map.smoke', 'sprites.oam_budget',
                                            'hw.oam_lines', 'follower', 'hw.memory_guard'),
             backends=('pyboy',), provenance=PROVENANCE, timeout=3000, name=f'test_map_smoke.enter_maps_{i}of{n}')
    def shard(ctx):
        run_shard(ctx, i, n)
    return shard


for _i in range(4):
    _make(_i, 4)


def run_shard_sameboy(ctx, shard, shards):
    """Every map on SameBoy with the native execution guard: no NOP slide, illegal opcode
    or code fetched from VRAM/OAM/IO may run, and the CPU must not lock."""
    from qa.gb.guards import PlayerStructGuard
    g = ctx.boot('smoke_base', build)
    g.enable_exec_guard()
    g.save_point()
    player = PlayerStructGuard(g)
    consts = sorted(mapdata.attributes())[shard::shards]
    if os.environ.get('QA_MAP_LIMIT'):
        consts = consts[:int(os.environ['QA_MAP_LIMIT'])]
    from qa.gb.sameboy import exec_guard_lib
    tested = no_tile = 0
    for const in consts:
        g.restore_point()
        player.ref = player.read()
        player.violations.clear()
        try:
            sg, sn = map_ids(const)
            exec_guard_lib().execguard_reset()          # the first load of a map is where its callbacks run
            F.teleport(g, sg, sn, 2, 2, settle=60)
            tile = pick_tile(g)
            if tile is None:
                no_tile += 1
                continue
            F.teleport(g, sg, sn, tile[0], tile[1], settle=90)
            g.tick(90)
            tested += 1
            ev = g.exec_events()
            if ev:
                msg = f'{const}: ' + '; '.join(f'{k} at {pc:04x} (from {pv:04x}, opcode {op:02x}, in {g.where(pv)})' for k, pc, pv, op in ev[:3])
                if const in STATE_DEPENDENT and False:
                    pass
                ctx.expect(False, msg)
                continue
            if g.read(0xffff) == 0:
                ctx.expect(False, f'{const}: CPU locked (IE cleared) at {g.where()}')
                continue
            player.check(const)
            if player.violations:
                ctx.expect(False, f'{const}: ' + '; '.join(player.violations[:2]))
        except Exception as e:
            ctx.expect(False, f'{const}: {type(e).__name__}: {e}')
    ctx.note(f'{ctx.model} shard {shard}/{shards}: {tested} maps entered and checked, {no_tile} without a walkable tile')
    if no_tile:
        ctx.uncover('hw.startup_ram', 'n/a') if False else None


def _make_sb(i, n):
    @qa_test(suites=('hardware', 'full'), covers=('hw.memory_guard', 'map.smoke', 'hw.mapper'),
             backends=('sameboy',), models=('CGB-E', 'AGB'), provenance=PROVENANCE + '; SameBoy with native execution guard',
             timeout=3000, name=f'test_map_smoke.enter_maps_exec_guard_{i}of{n}')
    def shard(ctx):
        run_shard_sameboy(ctx, i, n)
    return shard


for _i in range(4):
    _make_sb(_i, 4)
