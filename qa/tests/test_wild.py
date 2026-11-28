"""Wild Pokemon: every encounter zone, every time of day, and the roaming Pokemon.

The tables are in data/wild/*.asm; what can go wrong is the code between them and the battle: the lookup by map and
region, the time-of-day selection, grass against water, the probability table. For every (map, grass or water) zone the
test stands the player on the right terrain, sets the clock, and asks the game's own `ChooseWildEncounter` for many
encounters. Every species it returns must be in that zone's table for that time of day (or a roamer/swarm: none is
active here), and the rows that came up are recorded as seen. A row counts only when the game produced it.

Roaming: `InitRoamMons`, then `UpdateRoamMons` many times: the roamers must stay on the maps in data/wild/roammon_maps.asm,
and must move.
"""
import os
import re

from qa.framework import qa_test
from qa.gb import collision, fixtures as F, mapdata
from qa.gb.consts import C, map_ids
from qa.tests.test_map_smoke import build, pick_tile

PROVENANCE = 'standing on the zone: injected warp and clock; the encounters are drawn by calling the game\'s own ChooseWildEncounter (injected call)'
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TODS = [('morn', 7), ('day', 13), ('nite', 22)]
WATER = 0x29


def parse_tables():
    """{(map, terrain): {tod: [species names]}} from data/wild/*.asm."""
    out = {}
    attrs = mapdata.attributes()
    for f in sorted(os.listdir(os.path.join(ROOT, 'data/wild'))):
        if not (f.endswith('_grass.asm') or f.endswith('_water.asm')):
            continue
        terrain = 'grass' if f.endswith('_grass.asm') else 'water'
        cur, tod = None, None
        for line in open(os.path.join(ROOT, 'data/wild', f), encoding='utf-8'):
            m = re.match(r'\s*def_(?:grass|water)_wildmons\s+(\w+)', line)
            if m:
                cur, tod = m.group(1), None
                if cur in attrs:
                    out.setdefault((cur, terrain), {})
                continue
            m = re.match(r'\s*;\s*(morn|day|nite)\b', line)
            if m:
                tod = m.group(1)
                continue
            m = re.match(r'\s*wildmon\s+[^,]+,\s*(\w+)', line)
            if m and cur in attrs:
                out[(cur, terrain)].setdefault(tod or 'all', []).append(m.group(1))
    return out


def water_tile(g):
    w, h = 2 * g.rd('wMapWidth'), 2 * g.rd('wMapHeight')
    best = None
    for y in range(h):
        for x in range(w):
            if collision.tile_collision(g, x, y) == WATER:
                d = abs(x - w // 2) + abs(y - h // 2)
                if best is None or d < best[0]:
                    best = (d, x, y)
    return best[1:] if best else None


def run_zones(ctx, shard, shards):
    g = ctx.boot('smoke_base', build)
    tables = parse_tables()
    zones = sorted(tables)[shard::shards]
    only = os.environ.get('QA_WILD_ONLY')
    if only:
        zones = [z for z in sorted(tables) if only in z[0]]
    draws_n = int(os.environ.get('QA_WILD_DRAWS', '150'))
    bad, no_tile, checked, empty = [], [], 0, []
    for (const, terrain) in zones:
        tbl = tables[(const, terrain)]
        sg, sn = map_ids(const)
        try:
            F.teleport(g, sg, sn, 2, 2, settle=40)
            if F.where(g)[:2] != (sg, sn):
                no_tile.append(f'{const}:{terrain} (map did not load)')
                continue
            tile = water_tile(g) if terrain == 'water' else pick_tile(g)
            if tile is None:
                no_tile.append(f'{const}:{terrain} (no {terrain} tile to stand on)')
                continue
            F.teleport(g, sg, sn, tile[0], tile[1], settle=25)
            tods = TODS if terrain == 'grass' else [('day', 13)]
            seen_any = False
            for tod, hour in tods:
                g.wr('wRTCHours', hour)
                g.wr('wRTCMinutes', 5)
                g.tick(30)
                allowed_names = tbl.get(tod) or tbl.get('all') or []
                allowed = {C.get(n) & 0xff for n in allowed_names if C.get(n)}
                seen = set()
                for _ in range(draws_n):
                    g.wr('wTempWildMonSpecies', 0)
                    g.call('ChooseWildEncounter')
                    sp = g.rd('wTempWildMonSpecies')
                    if sp:
                        seen.add(sp)
                if seen:
                    seen_any = True
                stray = seen - allowed
                if stray:
                    bad.append(f'{const}:{terrain}:{tod}: species {sorted(stray)} are not in the table {allowed_names}')
                for n in allowed_names:
                    if C.get(n) and (C.get(n) & 0xff) in seen:
                        ctx.cover('wild_row', f'{const}:{terrain}:{tod if tod in tbl else "all"}:{n}')
            if seen_any:
                ctx.cover('wild_zone', f'{const}:{terrain}')
                checked += 1
            else:
                empty.append(f'{const}:{terrain}')
        except Exception as e:
            bad.append(f'{const}:{terrain}: {type(e).__name__}: {e}')
    ctx.note(f'shard {shard}/{shards}: {len(zones)} zones, {checked} produced encounters from the right table, {len(no_tile)} could not be stood on, {len(empty)} produced none')
    for z in no_tile[:40]:
        ctx.note('not tested: ' + z)
    for z in empty[:40]:
        ctx.note('no encounter in %d draws (rate or table?): %s' % (draws_n, z))
    for b in bad:
        ctx.expect(False, b)
    ctx.expect(checked > 0, 'no zone produced an encounter (vacuous run)')
    if no_tile or empty:
        ctx.uncover('wild.zones', f'{len(no_tile)} zones could not be stood on, {len(empty)} produced no encounters')


def _make(i, n):
    @qa_test(suites=('map', 'full'), covers=('wild.zones',), backends=('sameboy',), models=('CGB-E',), provenance=PROVENANCE, timeout=3600,
             name=f'test_wild.wild_zones_{i}of{n}')
    def shard(ctx):
        run_zones(ctx, i, n)
    return shard


for _i in range(4):
    _make(_i, 4)


@qa_test(suites=('map', 'full'), covers=('wild.roaming',), backends=('sameboy',), models=('CGB-E', 'AGB'), provenance=PROVENANCE, timeout=1800)
def roaming_pokemon_stay_on_their_maps(ctx):
    g = ctx.boot('smoke_base', build)
    allowed, neighbours = set(), {}
    cur_list = []
    for line in open(os.path.join(ROOT, 'data/wild/roammon_maps.asm'), encoding='utf-8'):
        m = re.match(r'\s*roam_map\s+(\w+)\s*,\s*(.*)', line)
        if m:
            names = [m.group(1)] + [x.strip() for x in m.group(2).split(',') if x.strip()]
            neighbours[m.group(1)] = set(names[1:])
            allowed.update(names)
    ids = {map_ids(n): n for n in allowed if n in mapdata.attributes()}
    g.call('InitRoamMons')
    visited = {1: set(), 2: set(), 3: set()}
    moves = {1: 0, 2: 0, 3: 0}
    jumps = {1: 0, 2: 0, 3: 0}
    last = {}
    bad = []
    for step in range(600):
        g.call('UpdateRoamMons')
        if step % 25 == 24:
            g.call('JumpRoamMons')
        for k in (1, 2, 3):
            grp = g.rd(f'wRoamMon{k}MapGroup')
            num = g.rd(f'wRoamMon{k}MapNumber')
            if (grp, num) == (C['GROUP_N_A'], C['GROUP_N_A']) or grp == 0xff:
                continue
            name = ids.get((grp, num))
            if name is None:
                bad.append(f'roamer {k} is on map {(grp, num)}, which is not a roaming map (step {step})')
                break
            visited[k].add(name)
            if last.get(k) not in (None, name):
                moves[k] += 1
                prev = last[k]
                # UpdateRoamMons moves to a neighbour, except 1 time in 32 (a jump to any roaming map): count the others
                if name not in neighbours.get(prev, set()):
                    jumps[k] += 1
            last[k] = name
    ctx.note('visited: ' + '; '.join(f'roamer {k}: {len(v)} maps, {moves[k]} moves, {jumps[k]} jumps' for k, v in visited.items() if v))
    for k, v in visited.items():
        ctx.cover('roaming', sorted(v))
        if v:
            ctx.expect(moves[k] > 300, f'roamer {k} hardly moved in 600 updates ({moves[k]} moves)')
            ctx.expect(jumps[k] <= 0.12 * max(moves[k], 1), f'roamer {k}: {jumps[k]} of {moves[k]} moves were not to a neighbour (expected about 1 in 32 jumps)')
    ctx.expect(any(visited.values()), 'no roamer was on any map (vacuous run)')
    for b in bad[:5]:
        ctx.expect(False, b)
