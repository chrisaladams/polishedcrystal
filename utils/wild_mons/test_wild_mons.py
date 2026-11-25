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
- a roaming legendary on the map still comes when every slot is full (in
  place of the one furthest away), never twice, and battles as one;
- today's rare Pokemon (the TV news; day 0 in the emulator: Eevee on Route
  29) comes there, one at a time, also when every slot is full, and not on
  another route; the TV names it;
- with a Repel, a weaker one runs from you and runs off if you walk into it,
  and a stronger one still battles;
- a nearby Beedrill can start a battle without input, and a waiting player
  can start a battle with a Chansey they get close to;
- Sweet Honey can be used from the Bag and leaves a local scent;
- saving with some out, then Continue, leaves no stale ones;
- the Bug-Catching Contest's are from the contest's list;
- throughout, no wild Pokemon is told to stand still for 0 frames (which
  counts down from 256: over 4 seconds, as when one that had just spotted
  you froze);
- the behavior table lists no species twice, and only ones seen in the wild.

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
        # LE_SHOTS=dir: render every frame and keep one in 40 there (for
        # looking at scenes as the tests play them; slower)
        self.shots = os.environ.get('LE_SHOTS')
        self.frame = 0
        if self.shots:
            os.makedirs(self.shots, exist_ok=True)

    def tick(self, n=1):
        for _ in range(n):
            if self.shots:
                self.pb.tick(1, True)
                self.frame += 1
                if self.frame % 40 == 0:
                    self.pb.screen.image.convert('RGB').save(
                        os.path.join(self.shots, f'{os.getpid()}_{self.frame:07d}.png'))
            else:
                self.pb.tick(1, False)

    def press(self, b, wait=30, hold=5):
        self.pb.button_press(b)
        self.tick(hold)
        self.pb.button_release(b)
        self.tick(wait)

    def face(self, direction):
        """Turn without walking; wait out any remaining map/battle input delay."""
        facing = {'down': 0, 'up': 4, 'left': 8, 'right': 12}[direction]
        for _ in range(8):
            if self.rd('wPlayerDirection') & 12 == facing:
                return
            self.press(direction, 30, 1)
        raise AssertionError(f'could not face {direction} after loading the map')

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

    def highlight_start_option(self, symbol):
        """Open Start and highlight a plain-text label, wherever it appears."""
        self.press('start', 90)
        count = self.rd('wMenuItemsList')
        assert 0 < count <= 10, 'Start menu did not open'
        bank, addr = self.sym['StartMenu.' + symbol]
        label = bytes(self.m[bank, addr + i] for i in range(20)).split(b'\x53', 1)[0]  # @ terminator
        screen = bytes(self.rd('wTilemap', i) for i in range(20 * 18))
        offset = screen.find(label)
        assert label and offset >= 0, f'{symbol} missing from Start menu'
        row, column = divmod(offset, 20)
        assert column + len(label) < 20 and count < self.rd('wMenuBorderBottomCoord') < 18
        for _ in range(count):
            if self.rd('wMenuCursorY') == row:
                return
            self.press('down', 12)
        raise AssertionError(f'Start cursor did not reach {symbol}')

    def manual_save(self):
        self.highlight_start_option('SaveString')
        self.press('a', 120)
        self.press('a', 400)
        for _ in range(3):
            self.press('b', 60)

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
    # today's rare Pokemon (TV news): map -> species
    src = open(os.path.join(ROOT, 'engine', 'overworld', 'wild_mons.asm')).read()
    sightings = dict(re.findall(r'map_id (\w+)\n\tdb (\w+)', src))
    usual_max = int(re.search(r'DEF WILD_MON_USUAL_MAX +EQU (\d+)', src).group(1))
    species_names |= set(sightings.values())
    names = sorted(species_names) + [p + mp for mp in maps + ['NATIONAL_PARK_BUG_CONTEST']
                                     for p in ('GROUP_', 'MAP_')]
    names += ['NUM_WILD_MONS', 'WILDMON_LENGTH', 'MAPOBJECT_LENGTH', 'FIRST_WILD_OBJECT',
              'NUM_OBJECT_STRUCTS', 'OBJECT_LENGTH', 'OBJECT_MAP_OBJECT_INDEX', 'OBJECT_SPRITE',
              'OBJECT_MAP_X', 'OBJECT_MAP_Y', 'OBJECT_LAST_MAP_X', 'OBJECT_LAST_MAP_Y',
              'OBJECT_LAST_TILE', 'OBJECT_PALETTE', 'OBJECT_SPRITE_TILE', 'PLAYER_SURF',
              'COLL_WATER', 'COLL_TALL_GRASS', 'COLL_LONG_GRASS', 'COLL_FLOOR', 'HABITAT_GRASS',
              'HABITAT_FLOOR', 'HABITAT_WATER', 'EXTSPECIES_MASK', 'SHINY_MASK',
              'BATTLETYPE_ROAMING', 'STATUSFLAGS2_BUG_CONTEST_TIMER_F', 'PALSTATE_OVERCAST_INDEX', 'OBJECT_FLAGS1',
              'OBJECT_FLAGS2', 'NUM_OBJECTS', 'EEVEE', 'GROUP_ROUTE_30', 'MAP_ROUTE_30',
              'GROUP_PLAYERS_HOUSE_1F', 'MAP_PLAYERS_HOUSE_1F', 'WILDMON_SPECIES',
              'WILDMON_FORM', 'WILDMON_TRAITS', 'WILDMON_ALERT', 'PLAIN_FORM', 'BEEDRILL', 'CHANSEY',
              'WILD_AGGRESSIVE', 'WILD_ELUSIVE', 'STEP_TYPE_FROM_MOVEMENT', 'OBJECT_STEP_TYPE',
              'SWEET_HONEY']
    K = rgbasm_values(names, None)
    by_value = {K[n]: n for n in species_names}
    save = open(args.save, 'rb').read()
    g = Game(save)
    rom = open(ROM, 'rb').read()
    sym = g.sym
    fails = []
    # the behavior table (data/wild/behaviors.asm): no species twice, and
    # each one listed really appears in the wild (else its bytes are wasted)
    listed = re.findall(r'^\tdb (\w+), WILD_', open(os.path.join(WILD, 'behaviors.asm')).read(), re.M)
    for s in sorted({s for s in listed if listed.count(s) > 1}):
        fails.append(('behaviors', f'{s} listed twice'))
    for s in sorted(set(listed) - species_names):
        fails.append(('behaviors', f'{s} is never a wild Pokemon'))

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
        for _ in range(10):  # running can fail ("Can't escape!"): try again
            for b in ('down', 'right', 'a'):
                g.press(b, 30)
            for _ in range(40):
                g.press('b', 40)
                if not g.rd('wBattleMode'):
                    break
            if not g.rd('wBattleMode'):
                break
        g.tick(400)

    g.boot()
    base = g.state()
    # every wild Pokemon's pause (SetRandomStepDuration with bc = its object)
    long_pauses = []

    def pause_set(_):
        r = g.pb.register_file
        bc = r.B << 8 | r.C
        idx = g.m[1, bc + K['OBJECT_MAP_OBJECT_INDEX']]
        if K['FIRST_WILD_OBJECT'] <= idx < K['FIRST_WILD_OBJECT'] + K['NUM_WILD_MONS'] and r.A == 0:
            long_pauses.append(idx - K['FIRST_WILD_OBJECT'])
    g.pb.hook_register(*g.sym['SetRandomStepDuration'], pause_set, None)
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
                    if (x['name'] not in table[mp] and x['battletype'] != K['BATTLETYPE_ROAMING']
                            and sightings.get(mp) != x['name']):
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
            overcast = g.rd('wCurPalStates', K['PALSTATE_OVERCAST_INDEX'])
            table = 'OvercastOBPalette' if overcast else 'MapObjectPals'
            if not any(got == lc + dc for lc, dc in
                       (TF.ow_palette_colours(rom, sym, light, dark, tm, table=table)
                        for tm in range(4))):
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

    # 3a. Actual overworld input dispatch for new behavior, using two species
    # in the same predictable grass patch to isolate encounter timing.
    for species, profile, stays_quiet in (('BEEDRILL', 'WILD_AGGRESSIVE', False),
                                         ('CHANSEY', 'WILD_ELUSIVE', True)):
        g.load(route29)
        g.face('right')
        slot = wild()[0]['slot']
        b = struct_of(slot)
        assert put_next_to_player(slot, 1, 0)
        for name, v in (('WILDMON_SPECIES', K[species]), ('WILDMON_FORM', K['PLAIN_FORM']),
                        ('WILDMON_TRAITS', K[profile]), ('WILDMON_ALERT', 0)):
            g.wr('wWildMons', v, slot * K['WILDMON_LENGTH'] + K[name])
        g.m[1, b + K['OBJECT_STEP_TYPE']] = K['STEP_TYPE_FROM_MOVEMENT']
        g.m[1, b + K['OBJECT_LAST_TILE']] = K['COLL_TALL_GRASS']
        if stays_quiet:
            g.tick(120)
            if g.rd('wBattleMode') or sget(b, 'OBJECT_MAP_X') != g.rd('wPlayerMapX') + 1:
                fails.append((species, 'did not stay near a motionless player'))
            g.press('a', 1, 3)
        if not wait_battle() or g.rd('wTempWildMonSpecies') != K[species]:
            fails.append((species, 'did not start its expected battle'))

    g.load(route29)
    g.wr('wLastPocket', 0)
    g.wr('wNumItems', 1)
    for offset, value in enumerate((K['SWEET_HONEY'], 1, 0xff)):
        g.wr('wItems', value, offset)
    g.highlight_start_option('PackString')
    for _ in range(6):
        g.press('a', 90)
    if g.rd('wNumItems') or g.rd('wWildHoneySteps') != 12 or g.rd('wBattleMode') or g.rd('wScriptRunning'):
        fails.append(('Sweet Honey', 'Bag use did not finish with a scent and no battle'))

    # 3b. roaming legendaries: all three on Route 29, every slot kept full
    g.load(route29)
    roam_len = g.addr('wRoamMon2') - g.addr('wRoamMon1')
    roamers = {K[n]: n for n in ('RAIKOU', 'ENTEI', 'SUICUNE')}
    for i, sp in enumerate(roamers):
        for k, v in ((0, sp), (1, 40), (2, K['GROUP_ROUTE_29']), (3, K['MAP_ROUTE_29'])):
            g.wr('wRoamMon1', v, i * roam_len + k)
    roamer = None
    # (wild Pokemon also leave, freeing a slot: watch the way in for when all
    # are out, where one makes room)
    made_room = []
    rb, ra = sym['TrySpawnWildMon.roamer_habitat']
    g.pb.hook_register(rb, ra, lambda _: made_room.append(1), None)
    for i in range(400):
        for j in range(K['NUM_OBJECT_STRUCTS']):  # hide the people, so all 4 come out
            b = g.addr('wObjectStructs') + j * K['OBJECT_LENGTH']
            if 1 <= g.m[1, b + K['OBJECT_MAP_OBJECT_INDEX']] < K['NUM_OBJECTS'] - 1:
                g.m[1, b + K['OBJECT_FLAGS1']] |= 1
        full = len(wild()) == K['NUM_WILD_MONS']
        g.wr('wGrassEncounterRate', 255)
        g.press(['up', 'up', 'down', 'down'][i % 4], 6, 16)
        out = wild()
        names = [x['name'] for x in out if x['battletype'] == K['BATTLETYPE_ROAMING']]
        if len(names) != len(set(names)):
            fails.append(('roaming legendaries', f'one is out twice: {names}'))
            break
        if names and full and made_room and roamer is None:
            roamer = [x for x in out if x['battletype'] == K['BATTLETYPE_ROAMING']][0]
            break
        made_room.clear()
    g.pb.hook_deregister(rb, ra)
    if roamer is None:
        fails.append(('roaming legendaries', 'none came while every slot was full'))
    else:
        put_next_to_player(roamer['slot'], 0, -1)
        g.press('up', 2, 8)
        put_next_to_player(roamer['slot'], 0, -1)
        g.press('up', 2, 8)
        if not wait_battle():
            fails.append(('roaming legendaries', f'walking into {roamer["name"]} started no battle'))
        elif (g.rd('wBattleType'), g.rd('wTempWildMonSpecies')) != (K['BATTLETYPE_ROAMING'], roamer['sp']):
            fails.append(('roaming legendaries', f'{roamer["name"]} did not battle as a roaming legendary'))

    # 3c. Stage day 0 for the Eevee sighting, independent of the input save.
    def rare_walk(group, number, x, y, steps, only_when_full=False):
        g.load(base)
        g.wr('wRTCDayLo', 0)
        if only_when_full:
            # it comes the usual way most of the time, and then stays: to see
            # it come when every slot is full, that's the only way it can come
            ab, aa = sym['ApplyTodaysSighting']

            def skip(_):
                rf = g.pb.register_file
                sp = rf.SP
                rf.SP = sp + 2
                rf.PC = g.m[sp] | (g.m[sp + 1] << 8)
            g.pb.hook_register(ab, aa, skip, None)
        g.warp(group, number, x, y)
        seen = most = while_full = 0
        for i in range(steps):
            for j in range(K['NUM_OBJECT_STRUCTS']):
                b = g.addr('wObjectStructs') + j * K['OBJECT_LENGTH']
                if 1 <= g.m[1, b + K['OBJECT_MAP_OBJECT_INDEX']] < K['NUM_OBJECTS'] - 1:
                    g.m[1, b + K['OBJECT_FLAGS1']] |= 1
            before = [x['sp'] for x in wild()]
            g.wr('wGrassEncounterRate', 255)
            g.press(['up', 'up', 'down', 'down'][i % 4], 6, 16)
            n = [x['sp'] for x in wild()].count(K['EEVEE'])
            seen += n > 0
            most = max(most, n)
            # (with the usual way skipped, it can only come when there's no
            # room: every slot out, or as many as the screen allows)
            while_full += (n > 0 and len(before) >= usual_max and K['EEVEE'] not in before)
        if only_when_full:
            g.pb.hook_deregister(ab, aa)
        return seen, most, while_full
    seen, most, _ = rare_walk(K['GROUP_ROUTE_29'], K['MAP_ROUTE_29'], 16, 5, 120)
    if not seen:
        fails.append(("today's rare Pokemon", 'no Eevee on Route 29'))
    seen2, most2, while_full = rare_walk(K['GROUP_ROUTE_29'], K['MAP_ROUTE_29'], 16, 5, 200, True)
    if max(most, most2) > 1:
        fails.append(("today's rare Pokemon", 'two Eevee out at once'))
    if not while_full or seen2 and not while_full:
        fails.append(("today's rare Pokemon", 'never came while every slot was full'))
    if rare_walk(K['GROUP_ROUTE_30'], K['MAP_ROUTE_30'], 10, 30, 40)[0]:
        fails.append(("today's rare Pokemon", 'Eevee on Route 30'))
    g.load(base)
    g.wr('wRTCDayLo', 0)
    g.warp(K['GROUP_PLAYERS_HOUSE_1F'], K['MAP_PLAYERS_HOUSE_1F'], 6, 2)
    g.press('up', 2, 3)
    g.tick(20)
    g.press('a', 60)
    if g.rd('wNamedObjectIndex') != K['EEVEE']:
        fails.append(("today's rare Pokemon", 'the TV did not report Eevee'))

    # 4. Repel
    g.load(route29)
    g.wr('wRepelEffect', 200)
    x = wild()[0]
    put_next_to_player(x['slot'], 0, -3)
    b = struct_of(x['slot'])
    py = g.rd('wPlayerMapY')
    start = abs(sget(b, 'OBJECT_MAP_X') - g.rd('wPlayerMapX')) + abs(sget(b, 'OBJECT_MAP_Y') - py)
    furthest = start
    for _ in range(48):  # (its first try may be into the trees)
        g.tick(10)
        b = struct_of(x['slot'])
        if b is None:  # ran off the screen
            furthest = 99
            break
        furthest = max(furthest, abs(sget(b, 'OBJECT_MAP_X') - g.rd('wPlayerMapX'))
                       + abs(sget(b, 'OBJECT_MAP_Y') - py))
    if furthest <= start:
        fails.append(('Repel', f'a weaker one did not run (distance {start}, at most {furthest})'))
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
    g.manual_save()
    saved = g.sram() + save[0x8000:]
    if saved[:0x8000] == save[:0x8000]:
        fails.append(('save', 'the game was not saved'))
    else:
        g2 = Game(saved)
        g2.boot()
        g2.tick(120)
        gsave, g = g, g2
        expected_map = (K['GROUP_ROUTE_29'], K['MAP_ROUTE_29'])
        assert (g.rd('wMapGroup'), g.rd('wMapNumber')) == expected_map, 'Continue did not restore Route 29'
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
        g.wr('wBugContestMinsRemaining', 20)
        g.warp(K['GROUP_NATIONAL_PARK_BUG_CONTEST'], K['MAP_NATIONAL_PARK_BUG_CONTEST'], x0, y0)
        for x in wild():
            seen.add(x['name'])
            if x['name'] not in contest:
                fails.append(('Bug-Catching Contest', f'{x["name"]} is not a contest Pokemon'))
    if not seen:
        fails.append(('Bug-Catching Contest', 'none appeared'))

    if long_pauses:
        fails.append(('pauses', f'{len(long_pauses)} wild Pokemon told to stand still for 256 frames'))
    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
