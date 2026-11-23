#!/usr/bin/env python3
"""Check in the running game that the wild Pokemon you can see work.

In the emulator (PyBoy), from a save:
- every map with wild Pokemon (in the grass, and on the water while surfing):
  the ones there when you arrive are from that map's table, inside the map,
  on their kind of tile (grass; floor in caves; water), with an object struct;
- Route 29: their walking sprite's frames are in VRAM exactly as in
  gfx/followers/<name>.2bpp and they're drawn in the table's colours, on
  arrival, after the start menu, and in shiny colours for a shiny one;
- walking into one starts a battle with that Pokemon (species, level, and
  shininess), and afterwards it's gone and the others stay; so does facing one
  and pressing A;
- with a Repel, a weaker one runs from you and runs off if you walk into it,
  and a stronger one still battles;
- saving with some out, then Continue, leaves no stale ones;
- the Bug-Catching Contest's are from the contest's list.

Usage (from the repository root, after make):
  python3 utils/wild_mons/test_wild_mons.py SAVE.sav [--quick]
(--quick skips the every-map sweep, which takes several minutes.)
"""
import argparse
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'linktest'))
sys.path.insert(0, os.path.join(ROOT, 'meta_sim'))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'followers'))
import linktest as L                                      # noqa: E402
from oracle_pipeline import rgbasm_values                 # noqa: E402
import test_followers as TF                               # noqa: E402

ROM = os.path.join(ROOT, 'polishedcrystal-3.2.3.gbc')
WILD = os.path.join(ROOT, 'data', 'wild')


def wild_tables(kind):
    out = {}
    for reg in ('johto', 'kanto', 'orange'):
        src = open(os.path.join(WILD, f'{reg}_{kind}.asm')).read()
        for m in re.finditer(r'def_%s_wildmons (\w+)(.*?)end_%s_wildmons' % (kind, kind), src, re.S):
            out[m.group(1)] = set(re.findall(r'wildmon [^,\n]+, (\w+)', m.group(2)))
    return out


def map_sizes():
    out = {}
    for line in open(os.path.join(ROOT, 'constants', 'map_constants.asm')):
        m = re.match(r'\tmap_const (\w+),\s*(\d+),\s*(\d+)', line)
        if m:
            out[m.group(1)] = (int(m.group(2)), int(m.group(3)))
    return out


class Game:
    def __init__(self, save_bytes):
        from pyboy import PyBoy
        self.sym = L.load_sym(ROM[:-4] + '.sym')
        self.pb = PyBoy(ROM, window='null', ram_file=io.BytesIO(save_bytes))
        self.pb.set_emulation_speed(0)
        self.m = self.pb.memory

    def tick(self, n=1):
        for _ in range(n):
            self.pb.tick(1, False)

    def press(self, b, wait=30, hold=5):
        self.pb.button_press(b)
        self.tick(hold)
        self.pb.button_release(b)
        self.tick(wait)

    def addr(self, name, k=0):
        return self.sym[name][1] + k

    def wr(self, name, v, k=0):
        a = self.addr(name, k)
        if 0xd000 <= a < 0xe000:
            self.m[1, a] = v
        else:
            self.m[a] = v

    def rd(self, name, k=0):
        a = self.addr(name, k)
        return self.m[1, a] if 0xd000 <= a < 0xe000 else self.m[a]

    def boot(self):
        self.tick(900)
        for b in ('start', 'start', 'a', 'a', 'a'):
            self.press(b, 200)
        for _ in range(4):
            self.press('b', 30)
        self.tick(60)

    def warp(self, group, number, x, y):
        for nm, v in (('wMapGroup', group), ('wMapNumber', number), ('wXCoord', x),
                      ('wYCoord', y), ('wDefaultSpawnpoint', 255), ('wMapStatus', 1)):
            self.wr(nm, v)
        self.m[0xff92] = 0xf1  # hMapEntryMethod = MAPSETUP_WARP
        self.tick(600)

    def state(self):
        s = io.BytesIO()
        self.pb.save_state(s)
        return s

    def load(self, s):
        s.seek(0)
        self.pb.load_state(s)

    def sram(self):
        return b''.join(bytes(self.m[b, 0xa000:0xbfff]) + bytes([self.m[b, 0xbfff]]) for b in range(4))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('save')
    ap.add_argument('--quick', action='store_true')
    args = ap.parse_args()

    grass, water = wild_tables('grass'), wild_tables('water')
    sizes = map_sizes()
    maps = sorted(set(grass) | set(water))
    contest = set(re.findall(r'contest_mon +\d+, (\w+)', open(os.path.join(WILD, 'bug_contest_mons.asm')).read()))
    species_names = set()
    for t in list(grass.values()) + list(water.values()):
        species_names |= t
    species_names |= contest | {'RAIKOU', 'ENTEI', 'SUICUNE'}
    names = sorted(species_names) + [p + mp for mp in maps + ['NATIONAL_PARK_BUG_CONTEST']
                                     for p in ('GROUP_', 'MAP_')]
    names += ['NUM_WILD_MONS', 'WILDMON_LENGTH', 'MAPOBJECT_LENGTH', 'FIRST_WILD_OBJECT',
              'NUM_OBJECT_STRUCTS', 'OBJECT_LENGTH', 'OBJECT_MAP_OBJECT_INDEX', 'OBJECT_SPRITE',
              'OBJECT_MAP_X', 'OBJECT_MAP_Y', 'OBJECT_LAST_MAP_X', 'OBJECT_LAST_MAP_Y',
              'OBJECT_LAST_TILE', 'OBJECT_PALETTE', 'OBJECT_SPRITE_TILE', 'PLAYER_SURF',
              'COLL_WATER', 'COLL_TALL_GRASS', 'COLL_LONG_GRASS', 'COLL_FLOOR', 'HABITAT_GRASS',
              'HABITAT_FLOOR', 'HABITAT_WATER', 'EXTSPECIES_MASK', 'SHINY_MASK',
              'BATTLETYPE_ROAMING', 'STATUSFLAGS2_BUG_CONTEST_TIMER_F']
    K = rgbasm_values(names, None)
    by_value = {K[n]: n for n in species_names}
    save = open(args.save, 'rb').read()
    g = Game(save)
    rom = open(ROM, 'rb').read()
    sym = g.sym
    fails = []

    def species_of(sp, form):
        return by_value.get(sp | (0x100 if form & K['EXTSPECIES_MASK'] else 0), f'#{sp}')

    def wild():
        WL, ML = K['WILDMON_LENGTH'], K['MAPOBJECT_LENGTH']
        out = []
        for k in range(K['NUM_WILD_MONS']):
            e = [g.rd('wWildMons', k * WL + i) for i in range(WL)]
            mo = [g.rd('wWildMapObjects', k * ML + i) for i in range(ML)]
            if e[0]:
                out.append(dict(slot=k, sp=e[0], form=e[1], shiny=e[2], level=e[3], battletype=e[4],
                                habitat=e[5], x=mo[3], y=mo[2], name=species_of(e[0], e[1])))
        return out

    def struct_of(slot):
        for i in range(K['NUM_OBJECT_STRUCTS']):
            b = g.addr('wObjectStructs') + i * K['OBJECT_LENGTH']
            if g.m[1, b + K['OBJECT_MAP_OBJECT_INDEX']] == K['FIRST_WILD_OBJECT'] + slot:
                return b
        return None

    def sget(b, field):
        return g.m[1, b + K[field]]

    def put_next_to_player(slot, dx, dy):
        b = struct_of(slot)
        if b is None:
            return False
        px, py = g.rd('wPlayerMapX'), g.rd('wPlayerMapY')
        for f, v in (('OBJECT_MAP_X', px + dx), ('OBJECT_LAST_MAP_X', px + dx),
                     ('OBJECT_MAP_Y', py + dy), ('OBJECT_LAST_MAP_Y', py + dy)):
            g.m[1, b + K[f]] = v
        return True

    def wait_battle(frames=400):
        for _ in range(frames):
            g.tick(1)
            if g.rd('wBattleMode'):
                return True
        return False

    def run_from_battle():
        g.tick(900)
        g.press('a', 400)
        for b in ('down', 'right', 'a'):
            g.press(b, 30)
        for _ in range(40):
            g.press('b', 40)
            if not g.rd('wBattleMode'):
                break
        g.tick(400)

    g.boot()
    base = g.state()
    tile_ok = {K['HABITAT_GRASS']: {K['COLL_TALL_GRASS'], K['COLL_LONG_GRASS']},
               K['HABITAT_FLOOR']: {K['COLL_TALL_GRASS'], K['COLL_LONG_GRASS'], K['COLL_FLOOR']},
               K['HABITAT_WATER']: {K['COLL_WATER']}}

    # 1. every map
    checked = 0
    if not args.quick:
        for mp in maps:
            for kind, table in (('grass', grass), ('water', water)):
                if mp not in table:
                    continue
                w, h = sizes[mp]
                found = []
                for fx, fy in ((0.5, 0.5), (0.25, 0.5), (0.75, 0.5), (0.5, 0.25), (0.5, 0.75)):
                    g.load(base)
                    if kind == 'water':
                        g.wr('wPlayerState', K['PLAYER_SURF'])
                        g.wr('wPlayerTileCollision', K['COLL_WATER'])
                    g.warp(K['GROUP_' + mp], K['MAP_' + mp], int(w * 2 * fx), int(h * 2 * fy))
                    if (g.rd('wMapGroup'), g.rd('wMapNumber')) != (K['GROUP_' + mp], K['MAP_' + mp]):
                        fails.append((mp, 'the warp there did not arrive'))
                        break
                    # (a warp can leave the player standing on water: not a real case)
                    if kind == 'grass' and g.rd('wPlayerTileCollision') == K['COLL_WATER']:
                        continue
                    found = wild()
                    if found:
                        break
                for x in found:
                    checked += 1
                    where = f'{mp} ({kind}): {x["name"]}'
                    if x['name'] not in table[mp] and x['battletype'] != K['BATTLETYPE_ROAMING']:
                        fails.append((where, 'not in its table'))
                    if not (4 <= x['x'] < 4 + 2 * w and 4 <= x['y'] < 4 + 2 * h):
                        fails.append((where, f'outside the map at {x["x"]},{x["y"]}'))
                    if (kind == 'water') != (x['habitat'] == K['HABITAT_WATER']):
                        fails.append((where, f'habitat {x["habitat"]}'))
                    b = struct_of(x['slot'])
                    # (no object struct: it wandered out of range since it
                    # appeared, and goes at the player's next step)
                    if b is not None and sget(b, 'OBJECT_LAST_TILE') not in tile_ok[x['habitat']]:
                        fails.append((where, f'on tile {sget(b, "OBJECT_LAST_TILE"):#x}'))
        print(f'every map: {checked} wild Pokemon checked')

    # 2. Route 29: sprites and colours
    stems = TF.camel_to_stem()
    pals_src = open(os.path.join(ROOT, 'data', 'pokemon', 'overworld_icon_pals.asm')).read()

    def shiny_colours(name):
        m = re.search(r'\ticonpal \w+, (\w+?)_(\w+) ; %s\s*$' % name, pals_src, re.M)
        light, dark = m.group(1), m.group(2)
        for n in TF.MON_NAMES:
            both = light + '_' + dark
            if both.startswith(n + '_') and both[len(n) + 1:] in TF.MON_NAMES:
                return n, both[len(n) + 1:]
        return light, dark

    def check_drawn(tag):
        vram = bytes(g.m[0, 0x8000:0x9800]) + bytes(g.m[1, 0x8000:0x9800])
        n = 0
        for x in wild():
            where = f'{tag}: {x["name"]}{" (shiny)" if x["shiny"] else ""}'
            sprite = TF.expected_sprite(x['name'], 'PLAIN_FORM', stems)
            two = open(os.path.join(ROOT, 'gfx', 'followers', sprite + '.2bpp'), 'rb').read()
            b = struct_of(x['slot'])
            if b is None:
                fails.append((where, 'no object struct'))
                continue
            t = sget(b, 'OBJECT_SPRITE_TILE')
            vb = 0 if t & 0x80 else 1
            first = vb * 0x1800 + (t & 0x7f) * 16
            if vram[first:first + 192] != TF.tiles(two, (0, 2, 4)):
                fails.append((where, 'standing frames not in its tiles'))
            walk = first + (0x800 if vb == 0 else 0x400)
            if vram[walk:walk + 192] != TF.tiles(two, (1, 3, 5)):
                fails.append((where, 'walking frames not in its tiles'))
            p = sget(b, 'OBJECT_PALETTE') & 7
            got = tuple(g.m[5, sym['wOBPals2'][1] + p * 8 + k] for k in range(2, 6))
            light, dark = (shiny_colours if x['shiny'] else
                           (lambda nm: TF.expected_colours(nm, 'PLAIN_FORM')))(x['name'])
            if not any(got == (lc[0], lc[1], dc[0], dc[1]) for lc, dc in
                       (TF.ow_palette_colours(rom, sym, light, dark, tm) for tm in range(4))):
                fails.append((where, f'palette {got} is not {light}/{dark}'))
            n += 1
        if not n:
            fails.append((tag, 'no wild Pokemon there'))

    g.load(base)
    g.warp(K['GROUP_ROUTE_29'], K['MAP_ROUTE_29'], 16, 5)
    g.tick(60)
    route29 = g.state()
    check_drawn('Route 29')
    g.press('start', 60)
    g.press('b', 120)
    check_drawn('Route 29 after the start menu')
    bank, addr = sym['RollWildMonShininess']

    def force_shiny(_):
        rf = g.pb.register_file
        rf.A = K['SHINY_MASK']
        sp = rf.SP
        rf.SP = sp + 2
        rf.PC = g.m[sp] | (g.m[sp + 1] << 8)
    g.pb.hook_register(bank, addr, force_shiny, None)
    g.load(base)
    g.warp(K['GROUP_ROUTE_29'], K['MAP_ROUTE_29'], 16, 5)
    g.tick(60)
    check_drawn('Route 29, shiny')
    shiny29 = g.state()
    g.pb.hook_deregister(bank, addr)

    # 3. walking into one, and pressing A
    for tag, st in (('walked into', route29), ('walked into a shiny', shiny29)):
        g.load(st)
        x = wild()[0]
        put_next_to_player(x['slot'], 0, -1)
        g.press('up', 2, 8)
        put_next_to_player(x['slot'], 0, -1)
        g.press('up', 2, 8)
        if not wait_battle():
            fails.append((tag, 'no battle'))
            continue
        g.tick(900)
        got = (g.rd('wEnemyMonSpecies'), g.rd('wEnemyMonLevel'),
               g.rd('wEnemyMonPersonality') & K['SHINY_MASK'])
        if got != (x['sp'], x['level'], x['shiny']):
            fails.append((tag, f'battled {got}, not {(x["sp"], x["level"], x["shiny"])}'))
        others = [o['slot'] for o in wild() if o['slot'] != x['slot']]
        run_from_battle()
        after = [o['slot'] for o in wild()]
        if x['slot'] in after:
            fails.append((tag, 'still there after the battle'))
        if not set(others) <= set(after):
            fails.append((tag, 'the others are gone after the battle'))
        if g.rd('wWildMonForcedShiny') or g.rd('wWildMonBattling'):
            fails.append((tag, 'battle state not cleared'))
    g.load(route29)
    x = wild()[0]
    g.press('up', 2, 3)
    g.tick(40)
    put_next_to_player(x['slot'], 0, -1)
    g.tick(2)
    put_next_to_player(x['slot'], 0, -1)
    g.press('a', 2, 4)
    if not wait_battle(300) or g.rd('wTempWildMonSpecies') != x['sp']:
        fails.append(('pressed A facing one', 'no battle with it'))

    # 4. Repel
    g.load(route29)
    g.wr('wRepelEffect', 200)
    x = wild()[0]
    put_next_to_player(x['slot'], 0, -3)
    b = struct_of(x['slot'])
    py = g.rd('wPlayerMapY')
    start = abs(sget(b, 'OBJECT_MAP_X') - g.rd('wPlayerMapX')) + abs(sget(b, 'OBJECT_MAP_Y') - py)
    g.tick(240)
    b = struct_of(x['slot'])
    if b is not None:
        now = abs(sget(b, 'OBJECT_MAP_X') - g.rd('wPlayerMapX')) + abs(sget(b, 'OBJECT_MAP_Y') - py)
        if now <= start:
            fails.append(('Repel', f'a weaker one did not run (distance {start} -> {now})'))
    g.load(route29)
    g.wr('wRepelEffect', 200)
    x = wild()[0]
    put_next_to_player(x['slot'], 0, -1)
    g.press('up', 2, 8)
    if struct_of(x['slot']) is not None:
        put_next_to_player(x['slot'], 0, -1)
        g.press('up', 2, 8)
    g.tick(200)
    if g.rd('wBattleMode') or x['slot'] in [o['slot'] for o in wild()]:
        fails.append(('Repel', 'walking into a weaker one did not make it run off'))
    g.load(route29)
    g.wr('wRepelEffect', 200)
    x = wild()[0]
    g.wr('wWildMons', 100, x['slot'] * K['WILDMON_LENGTH'] + 3)  # WILDMON_LEVEL
    put_next_to_player(x['slot'], 0, -1)
    g.press('up', 2, 8)
    put_next_to_player(x['slot'], 0, -1)
    g.press('up', 2, 8)
    if not wait_battle(300):
        fails.append(('Repel', 'a stronger one did not battle'))

    # 5. save with some out, then Continue
    g.load(route29)
    if not wild():
        fails.append(('save', 'none out to save with'))
    g.press('start', 60)
    for _ in range(5):
        g.press('down', 10)
    g.press('a', 120)
    g.press('a', 400)
    for _ in range(3):
        g.press('b', 60)
    saved = g.sram() + save[0x8000:]
    if saved[:0x8000] == save[:0x8000]:
        fails.append(('save', 'the game was not saved'))
    else:
        g2 = Game(saved)
        g2.boot()
        g2.tick(120)
        gsave, g = g, g2
        for i in range(K['NUM_OBJECT_STRUCTS']):
            sb = g.addr('wObjectStructs') + i * K['OBJECT_LENGTH']
            idx = g.m[1, sb + K['OBJECT_MAP_OBJECT_INDEX']]
            if K['FIRST_WILD_OBJECT'] <= idx < K['FIRST_WILD_OBJECT'] + K['NUM_WILD_MONS']:
                slot = idx - K['FIRST_WILD_OBJECT']
                if slot not in [o['slot'] for o in wild()]:
                    fails.append(('Continue', f'stale object struct {i} for wild Pokemon {slot}'))
        check_drawn('Route 29 after Continue')
        g.pb.stop(save=False)
        g = gsave

    # 6. the Bug-Catching Contest
    seen = set()
    for x0, y0 in ((20, 20), (16, 30), (24, 36)):
        g.load(base)
        g.wr('wStatusFlags2', g.rd('wStatusFlags2') | (1 << K['STATUSFLAGS2_BUG_CONTEST_TIMER_F']))
        g.warp(K['GROUP_NATIONAL_PARK_BUG_CONTEST'], K['MAP_NATIONAL_PARK_BUG_CONTEST'], x0, y0)
        for x in wild():
            seen.add(x['name'])
            if x['name'] not in contest:
                fails.append(('Bug-Catching Contest', f'{x["name"]} is not a contest Pokemon'))
    if not seen:
        fails.append(('Bug-Catching Contest', 'none appeared'))

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
