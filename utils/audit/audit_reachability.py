#!/usr/bin/env python3
"""Check in the running game (PyBoy) that what the Link Edition added to the
maps is where a player can use it, from a save:

- every person we added (Orange League, anime cameos, movie events, the Whirl
  Cup official; listed in ADDED) stands on a walkable tile, not on a warp or
  a coord event, can be walked up to and talked to from an entrance of the
  map, and doesn't cut any entrance off from another;
- with --wild, on every map with wild Pokemon, that none can appear out of
  reach: a tile of theirs (grass, cave floor, water) that can't be reached
  from an entrance, but that the game would pick as a spot for one while you
  stand somewhere you can get to (in range, and not walled off from you by
  the flood fill in ComputeWildMonReach).

The walkable tiles come from the map as loaded (blocks and the tileset's
collision, after the map's callbacks), and CollisionPermissionTable. The
player is taken to have every HM (Surf, Waterfall, Whirlpool, Cut,
Strength, Rock Smash), so cut trees, rocks and boulders don't block; other
people who stand still do. Ledges work as in the game (walking off a ledge
tile its way hops two tiles, so they're one-way); directional walls block
their side.

Usage (from the repository root, after make):
  python3 utils/audit/audit_reachability.py SAVE.sav [--wild] [--shots DIR]
"""
import argparse
import os
import re
import sys
from collections import deque

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_wild_mons import Game, rgbasm_values, wild_tables, map_sizes, ROM  # noqa: E402

# map label, x, y of each person the Link Edition added (and Mewtwo, whose
# script it changed)
ADDED = (
    ('WarmBeach', 9, 21), ('RockyBeach', 23, 27), ('BeautifulBeach', 16, 18),
    ('ValenciaHouse', 6, 3), ('ShamoutiHouse', 4, 1),
    ('PalletTown', 9, 12), ('OaksLab', 8, 5), ('SilverCaveOutside', 22, 15),
    ('SilverCaveOutside', 25, 15), ('NationalPark', 23, 22),
    ('OlivinePort', 13, 7), ('RuinsOfAlphResearchCenter', 2, 2),
    ('IlexForest', 11, 25), ('CeruleanCaveB1F', 7, 13),
    ('Route36NationalParkGate', 7, 2), ('DanceTheatre', 4, 12),
)
# The actual standing positions used to interact with each new story clue.
STORY_STOPS = (
    ('OaksLab', 2, 2, 'field book'), ('RuinsOfAlphInnerChamber', 5, 14, 'Hale statue'),
    ('OaksLab', 5, 1, 'championship sketch'),
    ('PokemonMansionB1F', 18, 21, 'Cinnabar flight log'),
    ('ShamoutiShrineRuins', 10, 18, 'shrine keeper'), ('ShamoutiShrineRuins', 8, 12, 'Lawrence'),
    ('FireIslandRoof', 5, 4, 'Fire beacon'), ('IceIslandRoof', 5, 4, 'Ice beacon'),
    ('LightningIslandRoof', 5, 4, 'Lightning beacon'),
)
# flags that make them all appear
SHOW = ('EVENT_BEAT_ELITE_FOUR', 'EVENT_BEAT_DRAKE', 'EVENT_TIME_TRAVEL_FINISHED', 'EVENT_GOT_MYSTICTICKET_FROM_RED')
HIDE = ('EVENT_OLIVINE_PORT_SPRITES_AFTER_HALL_OF_FAME', 'EVENT_CERULEAN_CAVE_MEWTWO',
        'EVENT_BEAT_IRON_MASK_MARAUDER')

LEDGES = {0xa0: 'r', 0xa1: 'l', 0xa2: 'u', 0xa3: 'd', 0xa4: 'dr', 0xa5: 'dl', 0xa6: 'ur', 0xa7: 'ul'}
EDGE_WALLS = {0xb0: 'r', 0xb1: 'l', 0xb2: 'u', 0xb3: 'd', 0xb4: 'dr', 0xb5: 'dl', 0xb6: 'ur', 0xb7: 'ul',
              0xb8: 'r', 0xb9: 'l'}
WARP_COLLS = {0x60, 0x61, 0x70, 0x71, 0x72, 0x76, 0x78, 0x7a, 0x7b, 0x7c, 0x7e}
DIRS = {'u': (0, -1), 'd': (0, 1), 'l': (-1, 0), 'r': (1, 0)}
OPPOSITE = {'u': 'd', 'd': 'u', 'l': 'r', 'r': 'l'}


def snake(label):
    s = re.sub(r'(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])', '_', label).upper()
    return s


def map_consts():
    """label -> MAP constant, from data/maps/attributes.asm"""
    out = {}
    for m in re.finditer(r'map_attributes (\w+), (\w+),', open(os.path.join(ROOT, 'data', 'maps', 'attributes.asm')).read()):
        out[m.group(1)] = m.group(2)
    return out


def connections():
    out = {}
    cur = None
    for line in open(os.path.join(ROOT, 'data', 'maps', 'attributes.asm')):
        m = re.match(r'\s*map_attributes (\w+),', line)
        if m:
            cur = m.group(1)
            out[cur] = []
        m = re.match(r'\s*connection (\w+),', line)
        if m and cur:
            out[cur].append(m.group(1))
    return out


def map_events(label):
    src = open(os.path.join(ROOT, 'maps', label + '.asm')).read()
    warps = [(int(x), int(y)) for x, y in re.findall(r'warp_event +(\d+), +(\d+),', src)]
    coords = [(int(x), int(y)) for x, y in re.findall(r'coord_event +(\d+), +(\d+),', src)]
    people = []
    for line in src.splitlines():
        m = re.match(r'\s*object_event +(\d+), +(\d+), \w+, (\w+),.*, (-1|\w+)\s*(;.*)?$', line)
        if m:
            people.append((int(m.group(1)), int(m.group(2)), m.group(3), m.group(4)))
    return warps, coords, people


class MapGrid:
    def __init__(self, g, perm, K):
        self.w = g.rd('wMapWidth') * 2
        self.h = g.rd('wMapHeight') * 2
        bw = g.rd('wMapWidth') + 6
        blocks = g.addr('wOverworldMapBlocks')
        cb, ca = g.sym['wDecompressedCollisions']
        self.coll = {}
        for y in range(self.h):
            for x in range(self.w):
                blk = g.m[blocks + (y // 2 + 3) * bw + (x // 2 + 3)]
                self.coll[x, y] = g.m[cb, ca + blk * 4 + (x & 1) + 2 * (y & 1)]
        self.perm = perm
        self.K = K

    def kind(self, p):
        c = self.coll.get(p)
        if c is None:
            return 'out'
        v = self.perm[c] & 3
        return {self.K['LAND_TILE']: 'land', self.K['WATER_TILE']: 'water'}.get(v, 'wall')

    def steps(self, p, blocked):
        """the tiles the player can get to in one step (or one ledge hop) from p"""
        c = self.coll[p]
        for d, (dx, dy) in DIRS.items():
            if c in LEDGES and d in LEDGES[c]:
                # standing on a ledge tile and walking its way hops two tiles
                n2 = (p[0] + 2 * dx, p[1] + 2 * dy)
                if n2 in self.coll and self.kind(n2) == 'land' and n2 not in blocked:
                    yield n2
                continue
            if d in EDGE_WALLS.get(c, ''):
                continue
            n = (p[0] + dx, p[1] + dy)
            nc = self.coll.get(n)
            if nc is None or n in blocked:
                continue
            if OPPOSITE[d] in EDGE_WALLS.get(nc, ''):
                continue
            if self.kind(n) == 'wall':
                continue
            yield n

    def window_reach(self, p, kind, blocked=(), left=7, up=6):
        """ComputeWildMonReach: the tiles in the window around p you can walk to
        and back within it: ordinary tiles of the Pokemon's kind ('land' or
        'water'), not across a wall along a side, not through anyone."""
        def ordinary(c):
            if 0xb0 <= c <= 0xb9:
                return True  # (a wall along one side: blocked by direction)
            return not (c >= 0x60 or c in (0x23, 0x24) or 0x30 <= c < 0x40)
        seen = {p}
        q = deque([p])
        while q:
            c = q.popleft()
            for d, (dx, dy) in DIRS.items():
                n = (c[0] + dx, c[1] + dy)
                if (n in seen or n not in self.coll or n in blocked
                        or not -left <= n[0] - p[0] <= left or not -up <= n[1] - p[1] <= up):
                    continue
                if d in EDGE_WALLS.get(self.coll[c], '') or OPPOSITE[d] in EDGE_WALLS.get(self.coll[n], ''):
                    continue
                if self.kind(n) != kind or not ordinary(self.coll[n]):
                    continue
                seen.add(n)
                q.append(n)
        return seen

    def reach(self, starts, blocked, warps):
        seen = set(s for s in starts if s in self.coll)
        q = deque(seen)
        while q:
            p = q.popleft()
            if p not in starts and (p in warps or self.coll[p] in WARP_COLLS):
                continue  # stepping on a warp takes you away
            for n in self.steps(p, blocked):
                if n not in seen:
                    seen.add(n)
                    q.append(n)
        return seen


def entrances(grid, label, warps, conns):
    out = set(w for w in warps if w in grid.coll)
    for side in conns.get(label, []):
        if side == 'north':
            edge = [(x, 0) for x in range(grid.w)]
        elif side == 'south':
            edge = [(x, grid.h - 1) for x in range(grid.w)]
        elif side == 'west':
            edge = [(0, y) for y in range(grid.h)]
        else:
            edge = [(grid.w - 1, y) for y in range(grid.h)]
        out |= {p for p in edge if grid.kind(p) != 'wall'}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('save')
    ap.add_argument('--wild', action='store_true')
    ap.add_argument('--shots')
    args = ap.parse_args()
    if args.shots:
        os.makedirs(args.shots, exist_ok=True)

    consts = map_consts()
    conns = connections()
    labels = sorted({a[0] for a in ADDED + STORY_STOPS})
    grass, water = wild_tables('grass'), wild_tables('water')
    wild_maps = sorted(set(grass) | set(water)) if args.wild else []
    by_const = {v: k for k, v in consts.items()}
    names = ['LAND_TILE', 'WATER_TILE', 'WALL_TILE', 'COLL_TALL_GRASS', 'COLL_LONG_GRASS', 'COLL_FLOOR',
             'COLL_WATER', 'NUM_OBJECT_STRUCTS', 'OBJECT_LENGTH', 'OBJECT_MAP_X', 'OBJECT_MAP_Y',
             'OBJECT_SPRITE', 'PLAYER_SURF', 'NUM_WILD_MONS', 'WILDMON_LENGTH',
             'MAPOBJECT_LENGTH', 'MAPOBJECT_X_COORD', 'MAPOBJECT_Y_COORD'] + list(SHOW) + list(HIDE)
    for mc in [consts[lb] for lb in labels] + wild_maps:
        names += ['GROUP_' + mc, 'MAP_' + mc]
    K = rgbasm_values(names, None)
    sizes = map_sizes()

    g = Game(open(args.save, 'rb').read())
    g.boot()
    rom = open(ROM, 'rb').read()
    pb, pa = g.sym['CollisionPermissionTable']
    off = pb * 0x4000 + (pa - 0x4000 if pb else pa)
    perm = rom[off:off + 256]

    def flag(name, value):
        n = K[name]
        v = g.rd('wEventFlags', n // 8)
        g.wr('wEventFlags', v | (1 << (n % 8)) if value else v & ~(1 << (n % 8)), n // 8)

    for f in SHOW:
        flag(f, True)
    for f in HIDE:
        flag(f, False)
    base = g.state()
    fails = []

    def load(mc, x, y, surf=False):
        g.load(base)
        if surf:
            g.wr('wPlayerState', K['PLAYER_SURF'])
            g.wr('wPlayerTileCollision', K['COLL_WATER'])
        g.warp(K['GROUP_' + mc], K['MAP_' + mc], x, y)
        g.tick(30)
        return MapGrid(g, perm, K)

    def shown(people):
        """people (x, y, movement) whose hide flag isn't set"""
        flags = rgbasm_values(sorted({f for *_, f in people if f != '-1'}), None) if people else {}
        out = []
        for x, y, mv, f in people:
            if f != '-1':
                n = flags[f]
                if (g.rd('wEventFlags', n // 8) >> (n % 8)) & 1:
                    continue
            out.append((x, y, mv))
        return out

    def present_people():
        out = set()
        for i in range(1, K['NUM_OBJECT_STRUCTS']):
            b = g.addr('wObjectStructs') + i * K['OBJECT_LENGTH']
            if g.m[1, b + K['OBJECT_SPRITE']]:
                out.add((g.m[1, b + K['OBJECT_MAP_X']] - 4, g.m[1, b + K['OBJECT_MAP_Y']] - 4))
        return out

    # 1. the people we added
    for label, ox, oy in ADDED:
        mc = consts[label]
        warps, coords, people = map_events(label)
        grid = load(mc, ox, min(oy + 1, sizes[mc][1] * 2 - 1))
        where = f'{label} ({ox},{oy})'
        if args.shots:
            g.pb.tick(1, True)
            g.pb.screen.image.save(os.path.join(args.shots, f'{label}_{ox}_{oy}.png'))
        if (ox, oy) not in present_people():
            fails.append((where, 'not there with every flag set'))
        # people who stand still block; wanderers, items and HM obstacles don't
        blockers = {(x, y) for x, y, mv in shown(people)
                    if 'STANDING' in mv or 'SPIN' in mv or 'POKEMON' in mv} - {(ox, oy)}
        if grid.kind((ox, oy)) != 'land':
            fails.append((where, f'stands on {grid.kind((ox, oy))} (collision {grid.coll.get((ox, oy), -1):#x})'))
        if (ox, oy) in warps or (ox, oy) in coords:
            fails.append((where, 'stands on a warp or coord event'))
        ents = entrances(grid, label, warps, conns)
        # The player must reach a talking position while the NPC is there.
        alone = grid.reach(ents, blockers | {(ox, oy)}, set(warps))
        talk = [(ox + dx, oy + dy) for dx, dy in DIRS.values()]
        if not any(t in alone and t not in blockers and t not in warps for t in talk):
            fails.append((where, 'nowhere reachable to talk to them from'))
        # cut off: an entrance that reaches another without them, but not with
        for e in sorted(ents):
            without = grid.reach({e}, blockers, set(warps)) & ents
            with_ = grid.reach({e}, blockers | {(ox, oy)}, set(warps)) & ents
            lost = without - with_
            if lost:
                fails.append((where, f'blocks the way from {e} to {sorted(lost)[:3]}'))
                break

    for label, x, y, clue in STORY_STOPS:
        warps, _, people = map_events(label)
        grid = load(consts[label], x, y)
        blockers = {(px, py) for px, py, mv in shown(people)
                    if 'STANDING' in mv or 'SPIN' in mv or 'POKEMON' in mv or 'STILL' in mv}
        reached = grid.reach(entrances(grid, label, warps, conns), blockers, set(warps))
        if (x, y) not in reached or (x, y) in warps:
            fails.append((clue, f'no walking route to {label} ({x},{y})'))

    # 2. wild Pokemon tiles out of reach
    for mc in wild_maps:
        label = by_const.get(mc)
        if not label:
            continue
        warps, coords, people = map_events(label)
        w, h = sizes[mc]
        grid = None
        for sx, sy in warps[:1] or [(w, h)]:
            grid = load(mc, sx, sy)
        if (g.rd('wMapGroup'), g.rd('wMapNumber')) != (K['GROUP_' + mc], K['MAP_' + mc]):
            fails.append((mc, 'could not get there'))
            continue
        still = {(x, y) for x, y, mv in shown(people) if 'STANDING' in mv or 'SPIN' in mv}
        # CheckWildMonObjects rejects reserved object coordinates, including
        # hidden objects and item balls. They cannot be candidate spawn tiles.
        src = open(os.path.join(ROOT, 'maps', label + '.asm')).read()
        occupied = {(int(x), int(y)) for x, y in re.findall(
            r'(?:object|itemball|cuttree|smashrock|strengthboulder)_event +(\d+), +(\d+),', src)}
        ents = entrances(grid, label, warps, conns)
        r = grid.reach(ents, still, set(warps))
        kinds = set()
        if mc in grass:
            kinds |= {K['COLL_TALL_GRASS'], K['COLL_LONG_GRASS']}
        if mc in water:
            kinds.add(K['COLL_WATER'])
        habitat = {p for p, c in grid.coll.items() if c in kinds}
        if mc in grass and not any(grid.coll[p] in (K['COLL_TALL_GRASS'], K['COLL_LONG_GRASS'])
                                   for p in grid.coll):
            habitat |= {p for p, c in grid.coll.items() if c == K['COLL_FLOOR']}  # caves
        # (you can't stand on a warp tile you walk onto: it takes you away;
        # only on the ones you arrive at)
        stands = {p for p in r if grid.kind(p) != 'wall'
                  and (grid.coll[p] not in WARP_COLLS or p in ents)}
        bad = []
        windows = {}
        for s in sorted(habitat - r - occupied):
            for dx in range(-5, 7):
                for dy in range(-5, 6):
                    if -2 <= dx <= 2 and -2 <= dy <= 2:
                        continue
                    pl = (s[0] - dx, s[1] - dy)
                    if pl not in stands:
                        continue
                    kind = 'water' if grid.coll[s] == K['COLL_WATER'] else 'land'
                    if (pl, kind) not in windows:
                        windows[pl, kind] = grid.window_reach(pl, kind, occupied)
                    if s in windows[pl, kind]:
                        bad.append((s, pl))
                        break
                else:
                    continue
                break
        # and in the game: the ones there when you arrive
        w, h = sizes[mc]
        for surf in ((False, True) if mc in water else (False,)):
            candidates = {p for p in stands - occupied - ents
                          if grid.kind(p) == ('water' if surf else 'land') and grid.coll[p] not in WARP_COLLS}
            if not candidates:
                continue
            for fx, fy in ((0.5, 0.5), (0.25, 0.5), (0.75, 0.5), (0.5, 0.25), (0.5, 0.75)):
                cx, cy = int(w * 2 * fx), int(h * 2 * fy)
                arrival = min(candidates, key=lambda p: (abs(p[0] - cx) + abs(p[1] - cy), p))
                load(mc, *arrival, surf=surf)
                for k in range(K['NUM_WILD_MONS']):
                    if not g.rd('wWildMons', k * K['WILDMON_LENGTH']):
                        continue
                    mo = g.addr('wWildMapObjects') + k * K['MAPOBJECT_LENGTH']
                    at = (g.m[mo + K['MAPOBJECT_X_COORD']] - 4, g.m[mo + K['MAPOBJECT_Y_COORD']] - 4)
                    if at not in r:
                        fails.append((mc, f'a wild Pokemon appeared out of reach at {at}'
                                          f'{" (surfing)" if surf else ""}'))
        if bad:
            fails.append((mc, f'{len(bad)} tiles a wild Pokemon can appear on out of reach, '
                              f'e.g. {bad[:3]} (tile, from where you stand)'))

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
