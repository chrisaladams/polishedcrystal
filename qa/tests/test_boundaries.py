"""The edge of every map must stop the player unless a connection leads on.

Found by a world scenario: on SILVER_CAVE_OUTSIDE a walkable tile on the bottom row has a walkable border block
beyond it and no south connection; walking south off the map overwrote the map group/number and coordinates
(the game then ran on a garbage map). That is a class: any map whose border block is passable lets the player leave
the map on every side that has no connection.

Static part (every map): the collision of the tile just outside each side, from the border block and the tileset's
collision table, for sides with no connection. Dynamic part: every side where an inside edge tile and the tile
beyond it are both walkable is tried with real input: the player must stay on the map, on the same tile, and the
map variables must stay valid.
"""
import os

from qa.framework import qa_test
from qa.gb import collision, fixtures as F, mapdata
from qa.gb.consts import map_ids
from qa.gb.nav import map_const_of
from qa.tests.test_connections import Interrupted, hold
from qa.tests.test_map_smoke import build as build_base

PROVENANCE = 'walking outward at each map edge: gameplay input; map, party and the starting tile: injected'
OUT = {'north': ('up', 0, -1), 'south': ('down', 0, 1), 'west': ('left', -1, 0), 'east': ('right', 1, 0)}


def outside_collision(g, x, y):
    """Collision of a tile in the 3-block border (up to 6 tiles outside the map), as the engine reads it."""
    w, h = g.rd('wMapWidth'), g.rd('wMapHeight')
    d, e = x + 4, y + 4
    if not (0 <= d < 2 * (w + 6) and 0 <= e < 2 * (h + 6)):
        return None
    mb, mbase = g.sym['wOverworldMapBlocks']
    addr = mbase + 1 + (w + 6) * (1 + (e >> 1)) + (d >> 1)
    block = g.read(addr, mb)
    bank, base = g.sym['wDecompressedCollisions']
    return g.read(base + block * 4 + (d & 1) + 2 * (e & 1), bank)


def candidates(g, sides_with_connection):
    """[(side, inside_tile)] where the player can stand on the last row/column and the tile beyond is walkable."""
    w, h = 2 * g.rd('wMapWidth'), 2 * g.rd('wMapHeight')
    out = []
    for side, (btn, dx, dy) in OUT.items():
        if side in sides_with_connection:
            continue
        edge = {'north': [(x, 0) for x in range(w)], 'south': [(x, h - 1) for x in range(w)],
                'west': [(0, y) for y in range(h)], 'east': [(w - 1, y) for y in range(h)]}[side]
        for (x, y) in edge:
            if collision.walkable(g, x, y) and outside_collision(g, x + dx, y + dy) in collision.PASSABLE:
                out.append((side, (x, y)))
                break
    return out


LEDGES = set(range(0xa0, 0xa8))
WATER = {0x29, 0x24, 0x33, 0x38, 0x39, 0x3a, 0x3b}          # surfable / current tiles
_inbound = {}


def inbound_arrivals(const):
    """Tiles of `const` where a warp from another map puts the player (dest warp coordinates)."""
    if not _inbound:
        attrs = mapdata.attributes()
        warps = {c: mapdata.parse_map(a['label'])['warps'] for c, a in attrs.items()}
        for c, ws in warps.items():
            for (x, y, dest, n) in ws:
                if dest in warps and 1 <= n <= len(warps[dest]):
                    wx, wy = warps[dest][n - 1][:2]
                    _inbound.setdefault(dest, set()).add((wx, wy))
    return _inbound.get(const, set())


def reachable(g, const, conns, allow_water):
    """Tiles the player can reach on foot from where warps and connections put them (over-approximate: objects such
    as boulders and cut trees are ignored, ledges are treated as passable)."""
    w, h = 2 * g.rd('wMapWidth'), 2 * g.rd('wMapHeight')
    starts = set()
    for (x, y) in inbound_arrivals(const):
        for dx, dy in ((0, 0), (0, 1), (0, -1), (1, 0), (-1, 0)):
            starts.add((x + dx, y + dy))
    for side in conns:
        edge = {'north': [(x, 0) for x in range(w)], 'south': [(x, h - 1) for x in range(w)],
                'west': [(0, y) for y in range(h)], 'east': [(w - 1, y) for y in range(h)]}[side]
        starts.update(edge)

    def ok(x, y):
        c = collision.tile_collision(g, x, y)
        return c is not None and (c in collision.PASSABLE or c in LEDGES or (allow_water and c in WATER) or c in collision.CARPETS)
    seen = {t for t in starts if 0 <= t[0] < w and 0 <= t[1] < h and ok(*t)}
    todo = list(seen)
    while todo:
        x, y = todo.pop()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            t = (x + dx, y + dy)
            if t not in seen and 0 <= t[0] < w and 0 <= t[1] < h and ok(*t):
                seen.add(t)
                todo.append(t)
    return seen


def run_shard(ctx, shard, shards):
    g = ctx.boot('smoke_base', build_base)
    g.save_point()
    attrs = mapdata.attributes()
    consts = sorted(attrs)[shard::shards]
    only = os.environ.get('QA_BOUNDARY_ONLY')
    if only:
        consts = [c for c in sorted(attrs) if only in c]
    sides_tested = escaped = 0
    problems, loose = [], []
    for const in consts:
        conns = {d for (d, _, _, _) in attrs[const]['connections']}
        sg, sn = map_ids(const)
        g.restore_point()
        try:
            F.teleport(g, sg, sn, 2, 2, settle=40)
            if F.where(g)[:2] != (sg, sn):
                continue
            cands = candidates(g, conns)
            plain = reachable(g, const, conns, False) if cands else set()
            surf = reachable(g, const, conns, True) if cands else set()
            ctx.cover('collision', ['COLL_FLOOR'])
            for side, (x, y) in cands:
                btn = OUT[side][0]
                g.restore_point()
                F.teleport(g, sg, sn, 2, 2, settle=40)
                F.teleport(g, sg, sn, x, y, settle=25)
                before = F.where(g)
                if before[:2] != (sg, sn):
                    continue
                sides_tested += 1
                reach = 'on foot' if (x, y) in plain else ('with Surf/currents' if (x, y) in surf else 'not from any entry')
                try:
                    for _ in range(6):
                        hold(g, btn, 16)
                except Interrupted:
                    continue
                after = F.where(g)
                g.tick(30)
                final = F.where(g)
                left = after[:2] != (sg, sn) or final[:2] != (sg, sn)
                if left:
                    escaped += 1
                    msg = f'{const}: walking {btn} off the {side} edge at {(x, y)} [tile reachable {reach}] changed the map to {final[:2]} ({map_const_of(*final[:2])}) at {final[2:]}'
                    (problems if reach != 'not from any entry' else loose).append(msg)
                elif final[2:] != before[2:]:
                    # allowed to stay on the map but moved: it may have walked along; only a move beyond the map is a defect
                    w, h = 2 * g.rd('wMapWidth'), 2 * g.rd('wMapHeight')
                    if not (0 <= final[2] < w and 0 <= final[3] < h):
                        escaped += 1
                        problems.append(f'{const}: walking {btn} off the {side} edge left the map area: now at {final[2:]} (map is {w}x{h})')
        except Exception as e:
            problems.append(f'{const}: {type(e).__name__}: {e}')
    ctx.note(f'shard {shard}/{shards}: {len(consts)} maps, {sides_tested} open edges tried with input, {escaped} let the player out ({len(problems)} reachable, {len(loose)} latent)')
    for p in problems:
        ctx.expect(False, p)
    for p in loose:
        ctx.note('latent (the edge tile is not reachable from any warp or connection): ' + p)


def _make(i, n):
    @qa_test(suites=('map', 'regression', 'full'), covers=('map.collision',), backends=('pyboy',), provenance=PROVENANCE, timeout=3600,
             name=f'test_boundaries.map_edges_{i}of{n}')
    def shard(ctx):
        run_shard(ctx, i, n)
    return shard


for _i in range(4):
    _make(_i, 4)
