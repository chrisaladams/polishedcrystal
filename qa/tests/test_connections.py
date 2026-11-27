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
from qa.framework import qa_test
from qa.gb import fixtures as F, mapdata
from qa.gb.consts import C, map_ids
from qa.gb.guards import OverworldGuard

PROVENANCE = 'walking across each connection: gameplay input; party, start map and position: injected'
DIR = {'north': 'up', 'south': 'down', 'west': 'left', 'east': 'right'}


def build(g):
    """a Totodile (so there is a follower), on Route 43"""
    F.give_mon(g, C['TOTODILE'], 10)
    F.teleport(g, *map_ids('ROUTE_43'), 10, 8)


def candidates(src, dst, direction, offset):
    """Edge tiles in src (x or y along the edge) that line up with dst."""
    ws, hs = (2 * v for v in mapdata.dims(src))
    wd, hd = (2 * v for v in mapdata.dims(dst))
    out = []
    if direction in ('north', 'south'):
        lo, hi = max(0, 2 * offset), min(ws, wd + 2 * offset)
        span = range(lo, hi)
    else:
        lo, hi = max(0, 2 * offset), min(hs, hd + 2 * offset)
        span = range(lo, hi)
    span = list(span)
    # middle first, then outward, a bounded number of tries
    order = sorted(span, key=lambda v: abs(v - (lo + hi) // 2))
    return order[:10]


def attempt(g, guard, src, dst, direction, along):
    """Place the player one tile inside src, walk to the edge and across. True if the
    map changed to dst."""
    sg, sn = map_ids(src)
    w, h = (2 * v for v in mapdata.dims(src))
    pos = {'north': (along, 1), 'south': (along, h - 2), 'west': (1, along), 'east': (w - 2, along)}[direction]
    F.teleport(g, sg, sn, pos[0], pos[1], settle=150)
    if F.where(g)[:2] != (sg, sn):
        return None
    g.hold(DIR[direction], 40)
    g.tick(20)
    for _ in range(4):
        if F.where(g)[:2] == map_ids(dst):
            break
        g.hold(DIR[direction], 16)
        g.tick(8)
    return F.where(g)[:2] == map_ids(dst)


@qa_test(suites=('map', 'full'), covers=('map.connections', 'follower', 'sprites.player', 'hw.memory_guard'),
         backends=('pyboy',), provenance=PROVENANCE, timeout=3000)
def cross_all_connections(ctx):
    g = ctx.boot('connections_base', build)
    guard = OverworldGuard(g)
    attrs = mapdata.attributes()
    limit = int(__import__('os').environ.get('QA_CONNECTION_LIMIT', '0')) or None
    todo = [(m['const'], d, c, o) for m in attrs.values() for (d, _, c, o) in m['connections']]
    if limit:
        todo = todo[::max(1, len(todo) // limit)][:limit]
    crossed, blocked, broken = 0, [], []
    for src, direction, dst, offset in todo:
        if src not in attrs or dst not in attrs:
            continue
        ok = None
        for along in candidates(src, dst, direction, offset):
            guard.player.violations.clear()
            guard.player.ref = guard.player.read()
            try:
                ok = attempt(g, guard, src, dst, direction, along)
            except Exception as e:           # a hung or crashed game
                broken.append(f'{src} -{direction}-> {dst}: {e}')
                break
            if ok:
                # walk on a few steps on the far side with the guards on
                for step in range(8):
                    g.hold(DIR[direction], 16)
                    g.tick(6)
                    guard.check(f'{src} -{direction}-> {dst} step {step}')
                break
        if ok:
            crossed += 1
            if guard.violations:
                broken.append(f'{src} -{direction}-> {dst}: ' + '; '.join(guard.violations[:2]))
                guard.player.violations.clear()
        elif ok is None or not broken or not broken[-1].startswith(f'{src} -{direction}-> {dst}'):
            blocked.append(f'{src}-{direction}->{dst}')
    ctx.note(f'{crossed} of {len(todo)} connections crossed on foot; {len(blocked)} not crossable by walking from the tried edge tiles')
    for b in broken:
        ctx.expect(False, b)
    if blocked:
        ctx.uncover('map.connections', f'{len(blocked)} of {len(todo)} connections not crossed (first: {", ".join(blocked[:4])})')
    if limit:
        ctx.uncover('map.connections', f'sampled {len(todo)} connections (QA_CONNECTION_LIMIT)')
    ctx.expect(crossed > 0, 'no connection could be crossed at all')
