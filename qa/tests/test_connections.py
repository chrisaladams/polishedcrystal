"""Cross every map connection on foot, with a follower, and check the object
engine's invariants on the far side.

This is the generalisation of the Lake of Rage defect: the follow link survived a
map connection. For each connection (A -> B) the player is placed one tile inside
A at the edge, walks across, then walks on for several steps while the player's
object struct, follower queue, stack pointer and crash handlers are watched.

A connection whose edge tiles are all blocked (water, trees, ledges) cannot be
crossed on foot: it is reported as NOT crossed, and the test withdraws its
'map.connections' coverage instead of claiming it.
"""
import os

from qa.framework import qa_test
from qa.gb import collision, fixtures as F, mapdata
from qa.gb.consts import C, map_ids
from qa.gb.guards import OverworldGuard

PROVENANCE = 'walking across each connection: gameplay input; party, start map and position: injected'
DIR = {'north': 'up', 'south': 'down', 'west': 'left', 'east': 'right'}


def build(g):
    """a Totodile (so there is a follower), on Route 43"""
    F.give_mon(g, C['TOTODILE'], 10)
    F.teleport(g, *map_ids('ROUTE_43'), 10, 8)


def candidates(g, src, dst, direction, offset):
    """Edge tiles of src (the loaded map) that are walkable on the edge and one tile in,
    and line up with dst's width/height."""
    ws, hs = g.rd('wMapWidth') * 2, g.rd('wMapHeight') * 2
    wd, hd = (2 * v for v in mapdata.dims(dst))
    out = []
    if direction in ('north', 'south'):
        rng = [x for x in range(ws) if 0 <= x - 2 * offset < wd]
        for x in rng:
            e, i = (0, 1) if direction == 'north' else (hs - 1, hs - 2)
            if collision.walkable(g, x, e, edge=True) and collision.walkable(g, x, i):
                out.append(x)
        mid = (rng[0] + rng[-1]) // 2 if rng else 0
    else:
        rng = [y for y in range(hs) if 0 <= y - 2 * offset < hd]
        for y in rng:
            e, i = (0, 1) if direction == 'west' else (ws - 1, ws - 2)
            if collision.walkable(g, e, y, edge=True) and collision.walkable(g, i, y):
                out.append(y)
        mid = (rng[0] + rng[-1]) // 2 if rng else 0
    return sorted(out, key=lambda v: abs(v - mid))[:4]


def load_map(g, src):
    """Make src the loaded map (INJECTED warp to any tile); returns False if it won't load."""
    sg, sn = map_ids(src)
    F.teleport(g, sg, sn, 2, 2, settle=150)
    return F.where(g)[:2] == (sg, sn)


class Interrupted(Exception):
    """A wild or trainer battle started: the walk cannot continue from here."""


def hold(g, button, frames):
    g.hold(button, frames)
    g.tick(8)
    g.wr('wRepelEffect', 250)          # INJECTED: keeps wild encounters off
    if g.in_battle():
        raise Interrupted()


def attempt(g, src, dst, direction, along):
    sg, sn = map_ids(src)
    w, h = g.rd('wMapWidth') * 2, g.rd('wMapHeight') * 2
    pos = {'north': (along, 1), 'south': (along, h - 2), 'west': (1, along), 'east': (w - 2, along)}[direction]
    F.teleport(g, sg, sn, pos[0], pos[1], settle=150)
    if F.where(g)[:2] != (sg, sn):
        return False
    for _ in range(5):
        hold(g, DIR[direction], 16)
        if F.where(g)[:2] == map_ids(dst):
            return True
    return False


def run_shard(ctx, shard, shards):
    g = ctx.boot('connections_base', build)
    guard = OverworldGuard(g)
    attrs = mapdata.attributes()
    todo = [(m['const'], d, c, o) for m in attrs.values() for (d, _, c, o) in m['connections']]
    todo = todo[shard::shards]
    limit = int(os.environ.get('QA_CONNECTION_LIMIT', '0')) or None
    if limit:
        todo = todo[:limit]
    crossed, blocked, broken, interrupted = 0, [], [], 0
    g.save_point()
    for src, direction, dst, offset in todo:
        label = f'{src} -{direction}-> {dst}'
        g.restore_point()                      # every crossing starts from the same clean state
        guard.player.ref = guard.player.read()
        guard.player.violations.clear()
        try:
            if not load_map(g, src):
                blocked.append(label + ' (source map did not load)')
                continue
            cands = candidates(g, src, dst, direction, offset)
            ok = False
            for along in cands:
                guard.player.violations.clear()
                guard.player.ref = guard.player.read()
                if attempt(g, src, dst, direction, along):
                    ok = True
                    for step in range(8):          # walk on, watching the object engine
                        hold(g, DIR[direction], 16)
                        guard.check(f'{label} step {step}')
                    break
            if ok:
                crossed += 1
                if guard.violations:
                    broken.append(label + ': ' + '; '.join(guard.violations[:2]))
                    guard.player.violations.clear()
            else:
                blocked.append(label + (' (no walkable aligned edge tile)' if not cands else ''))
        except Interrupted:
            interrupted += 1
            blocked.append(label + ' (a battle started; restored)')
            g.restore_point()
            guard.player.ref = guard.player.read()
            guard.player.violations.clear()
        except KeyError as e:               # a destination with no map constants (placeholder map)
            blocked.append(label + f' (static: {e})')
        except Exception as e:          # a hung or crashed game
            broken.append(f'{label}: {type(e).__name__}: {e}')
    ctx.note(f'shard {shard}/{shards}: {crossed} of {len(todo)} connections crossed on foot, {len(blocked)} not')
    for b in blocked[:30]:
        ctx.note('not crossed: ' + b)
    for b in broken:
        ctx.expect(False, b)
    if blocked or limit:
        ctx.uncover('map.connections', f'{len(blocked)} of {len(todo)} in shard {shard} not crossed on foot')
    ctx.expect(crossed > 0, 'no connection in this shard could be crossed at all')


def _make(i, n):
    @qa_test(suites=('map', 'full'), covers=('map.connections', 'follower', 'sprites.player',
                                            'hw.memory_guard'),
             backends=('pyboy',), provenance=PROVENANCE, timeout=3000, name=f'test_connections.cross_connections_{i}of{n}')
    def shard(ctx):
        run_shard(ctx, i, n)
    return shard


for _i in range(4):
    _make(_i, 4)
