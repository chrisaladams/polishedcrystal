#!/usr/bin/env python3
"""Execute the ROM's spawn path check on controlled collision maps.

A new wild Pokemon may appear only where you can walk to and back: the
flood fill (ComputeWildMonReach) goes around walls, but not through tiles
with special movement (which the permission table calls walkable), across
a wall along a tile's side, or through someone standing in the way.
"""
from pathlib import Path
import sys
import unittest

from rom_harness import Harness, find_build, load_symbols

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'meta_sim'))
from oracle_pipeline import rgbasm_values


class SpawnPathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom, sym = find_build(str(ROOT))
        symbols = load_symbols(sym)
        # Collision reads switch WRAM banks: the stack must be unbanked.
        cls.h = Harness(rom, symbols, stack=symbols['wStackTop'][1] - 16)
        cls.K = rgbasm_values([
            'HABITAT_FLOOR', 'HABITAT_WATER', 'NUM_OBJECTS', 'MAPOBJECT_LENGTH',
            'NUM_OBJECT_STRUCTS', 'OBJECT_LENGTH', 'NUM_WILD_MONS',
            'MAPOBJECT_SPRITE', 'MAPOBJECT_X_COORD', 'MAPOBJECT_Y_COORD',
            'MAPOBJECT_OBJECT_STRUCT_ID', 'FIRST_WILD_OBJECT', 'FOLLOWER_OBJECT', 'SPRITE_FOLLOWER_MON',
            'WILDMON_LENGTH', 'WILDMON_TRAITS', 'WILDMON_ALERT',
            'WILDMON_SPECIES', 'WILDMON_HABITAT', 'WILDMON_LEVEL',
            'WILD_STEP_ATTACK_F', 'WILD_STEP_TERRITORY_F',
            'WILD_PASSIVE', 'WILD_TIMID', 'WILD_CURIOUS', 'WILD_AGGRESSIVE',
            'WILD_TERRITORIAL', 'WILD_STATIONARY', 'WILD_ELUSIVE', 'WILD_SCHOOLING',
            'WILD_HONEY', 'WILD_NOCTURNAL', 'EXTSPECIES_MASK',
            'PLAYER_NORMAL', 'PLAYER_RUN', 'PLAYER_BIKE', 'NITE', 'DAY',
            'STEP_WALK', 'STEP_BIKE', 'DOWN', 'LEFT', 'RIGHT', 'PAD_RIGHT',
            'SENTRET', 'EEVEE', 'BEEDRILL', 'URSARING', 'SLOWPOKE', 'GEODUDE',
            'CHANSEY', 'MAGIKARP', 'HOOTHOOT', 'HABITAT_GRASS', 'COLL_WALL',
            'COLL_LEFT_WALL', 'WILD_STEP_QUICK_F',
            'GROUP_ROUTE_29', 'MAP_ROUTE_29', 'COLL_TALL_GRASS',
            'GROUP_PLAYERS_HOUSE_1F', 'MAP_PLAYERS_HOUSE_1F'], None)

    @classmethod
    def tearDownClass(cls):
        cls.h.stop()

    def setUp(self):
        h, K = self.h, self.K
        h.prepare()
        h.mem[h.addr('wMapWidth')] = 8
        h.mem[h.addr('wMapHeight')] = 8
        h.mem[h.addr('wWildMonSpawnHabitat')] = K['HABITAT_FLOOR']
        # A padded 14x14 block grid, each block with its own collision entry.
        for i in range(196):
            h.mem[h.addr('wOverworldMapBlocks') + i] = i
        bank, addr = h.symbols['wDecompressedCollisions']
        for i in range(1024):
            h.mem[bank, addr + i] = 0
        for name, count in (
                ('wMapObjects', K['NUM_OBJECTS'] * K['MAPOBJECT_LENGTH']),
                ('wWildMapObjects', K['NUM_WILD_MONS'] * K['MAPOBJECT_LENGTH']),
                ('wWildMons', K['NUM_WILD_MONS'] * K['WILDMON_LENGTH']),
                ('wObjectStructs', K['NUM_OBJECT_STRUCTS'] * K['OBJECT_LENGTH'])):
            for i in range(count):
                h.mem[h.addr(name) + i] = 0

    def tile(self, x, y, collision):
        block = (y // 2 + 3) * 14 + x // 2 + 3
        bank, addr = self.h.symbols['wDecompressedCollisions']
        self.h.mem[bank, addr + block * 4 + (x & 1) + 2 * (y & 1)] = collision

    def blocked(self, player=(8, 8), spawn=(4, 8)):
        h = self.h
        h.mem[h.addr('wPlayerMapX')] = player[0] + 4
        h.mem[h.addr('wPlayerMapY')] = player[1] + 4
        h.reg.D, h.reg.E = spawn[0] + 4, spawn[1] + 4
        h.call('CheckWildMonPath')
        self.assertEqual((h.reg.D, h.reg.E), (spawn[0] + 4, spawn[1] + 4))
        return bool(h.reg.F & 0x10)

    def wall_with_gap(self, x=6, gap=8, gap_collision=0):
        """A wall down column x, all the way across the map, but for one tile."""
        for y in range(16):
            self.tile(x, y, self.K['COLL_WALL'] if y != gap else gap_collision)

    def test_open_floor(self):
        self.assertFalse(self.blocked())

    def test_only_ordinary_tiles_make_a_way(self):
        # Through a gap in a wall: ordinary floor, yes; anything with special
        # movement (ice, whirlpool, water on land, waterfall, current, hole,
        # stairs, ledge) can't prove a way back.
        self.wall_with_gap()
        self.assertFalse(self.blocked())
        for collision in (0x07, 0x23, 0x24, 0x29, 0x33, 0x38, 0x60, 0x72, 0xa0):
            with self.subTest(collision=hex(collision)):
                self.wall_with_gap(gap_collision=collision)
                self.assertTrue(self.blocked())

    def test_walls_along_one_side(self):
        # Crossing the gap from right to left: a wall along its right side
        # blocks, one along its top doesn't.
        self.wall_with_gap(gap_collision=0xb0)  # COLL_RIGHT_WALL
        self.assertTrue(self.blocked())
        self.wall_with_gap(gap_collision=0xb2)  # COLL_TOP_WALL
        self.assertFalse(self.blocked())

    def test_walks_around_a_wall(self):
        # One wall on the straight line doesn't hide a spot you can walk
        # around to; a wall all the way around it does.
        self.tile(6, 8, 0x07)
        self.assertFalse(self.blocked())
        for x in range(3, 6):
            for y in range(7, 10):
                if (x, y) != (4, 8):
                    self.tile(x, y, 0x07)
        self.assertTrue(self.blocked())

    def test_water_stays_connected_by_water(self):
        self.h.mem[self.h.addr('wWildMonSpawnHabitat')] = self.K['HABITAT_WATER']
        for x in range(4, 9):
            self.tile(x, 8, 0x29)
        self.assertFalse(self.blocked())
        self.tile(6, 8, 0)
        self.assertTrue(self.blocked())

    def test_ledges_cannot_prove_a_way_back(self):
        for y in range(16):
            self.tile(6, y, 0xa0)  # COLL_LEDGE_RIGHT
        self.assertTrue(self.blocked())

    def test_character_blocks_narrow_path(self):
        h, K = self.h, self.K
        self.wall_with_gap()
        addr = h.addr('wMapObjects') + K['MAPOBJECT_LENGTH']
        h.mem[addr + K['MAPOBJECT_SPRITE']] = 1
        h.mem[addr + K['MAPOBJECT_X_COORD']] = 6 + 4
        h.mem[addr + K['MAPOBJECT_Y_COORD']] = 8 + 4
        self.assertTrue(self.blocked())
        h.mem[addr + K['MAPOBJECT_SPRITE']] = 0
        self.assertFalse(self.blocked())

    def wild(self, species, profile, pos, *, slot=0, home=None, habitat='HABITAT_FLOOR'):
        slot_addr = self.h.addr('wWildMons') + slot * self.K['WILDMON_LENGTH']
        for member, value in (('SPECIES', self.K[species]), ('LEVEL', 5),
                              ('TRAITS', profile), ('HABITAT', self.K[habitat])):
            self.h.mem[slot_addr + self.K['WILDMON_' + member]] = value
        assoc = self.h.addr('wWildMapObjects') + slot * self.K['MAPOBJECT_LENGTH']
        self.h.mem[assoc + self.K['MAPOBJECT_OBJECT_STRUCT_ID']] = slot + 1
        for member, value in (('MapObjectIndex', self.K['FIRST_WILD_OBJECT'] + slot),
                              ('MapX', pos[0]), ('MapY', pos[1]),
                              ('LastMapX', pos[0]), ('LastMapY', pos[1]),
                              ('InitX', (home or pos)[0]), ('InitY', (home or pos)[1]),
                              ('Walking', 0xff)):
            self.write(f'wObject{slot + 1}{member}', value)
        return slot_addr + self.K['WILDMON_ALERT']

    def write(self, name, value):
        self.h.mem[self.h.addr(name)] = value

    def read(self, name):
        return self.h.mem[self.h.addr(name)]

    def player(self, state='PLAYER_NORMAL', *, x=12, y=12, moving=False):
        for name, value in (('wPlayerMapX', x), ('wPlayerMapY', y),
                            ('wPlayerState', self.K[state]), ('wPlayerWalking', 0xff),
                            ('hJoyDown', self.K['PAD_RIGHT'] if moving else 0),
                            ('wScriptRunning', 0), ('wRepelEffect', 0),
                            ('wWildHoneySteps', 0), ('wWildMonBumped', 0)):
            self.write(name, value)

    def move_wild(self, routine='GetWildMonStep', slot=0):
        obj = self.h.addr(f'wObject{slot + 1}Struct')
        self.h.reg.B, self.h.reg.C = obj >> 8, obj & 0xff
        direction = self.h.call(routine)
        return None if self.h.reg.F & 0x10 else direction

    def test_species_select_their_profile(self):
        profiles = dict(SENTRET='TIMID', EEVEE='CURIOUS', BEEDRILL='AGGRESSIVE',
                        URSARING='TERRITORIAL', SLOWPOKE='PASSIVE', GEODUDE='STATIONARY',
                        CHANSEY='ELUSIVE', MAGIKARP='SCHOOLING')
        self.write('wCurForm', 0)
        for species, profile in profiles.items():
            self.write('wTempWildMonSpecies', self.K[species])
            self.assertEqual(self.h.call('GetWildMonTraits') & 7, self.K['WILD_' + profile])
        self.write('wCurForm', self.K['EXTSPECIES_MASK'])
        self.assertEqual(self.h.call('GetWildMonTraits'), self.K['WILD_PASSIVE'])

    def test_walk_run_bike_and_elusive_speed(self):
        k = self.K
        for state, distance in (('PLAYER_NORMAL', 1), ('PLAYER_RUN', 3), ('PLAYER_BIKE', 4)):
            with self.subTest(state=state):
                self.player(state, moving=True)
                self.wild('SENTRET', k['WILD_TIMID'], (12 + distance, 12))
                self.assertEqual(self.move_wild(), 4 * k['STEP_WALK'] + k['RIGHT'])
        self.wild('CHANSEY', k['WILD_ELUSIVE'], (14, 12))
        self.player('PLAYER_BIKE')
        self.assertIsNone(self.move_wild())
        self.player(moving=True)
        self.assertEqual(self.move_wild(), 4 * k['STEP_BIKE'] + k['RIGHT'])
        self.write('wScriptRunning', 1)
        self.assertIsNone(self.move_wild())

    def test_curious_night_and_honey(self):
        k = self.K
        self.player()
        self.wild('EEVEE', k['WILD_CURIOUS'] | k['WILD_HONEY'], (15, 12))
        self.assertEqual(self.move_wild(), k['LEFT'])
        self.player(moving=True)
        self.assertIsNone(self.move_wild())
        self.write('wWildHoneySteps', 12)
        self.write('wWildHoneyX', 15)
        self.write('wWildHoneyY', 14)
        self.assertEqual(self.move_wild(), k['DOWN'])
        self.player()
        self.wild('HOOTHOOT', k['WILD_CURIOUS'] | k['WILD_NOCTURNAL'], (15, 12))
        self.write('wTimeOfDay', k['NITE'])
        self.assertEqual(self.move_wild(), k['LEFT'])
        self.write('wTimeOfDay', k['DAY'])
        # Daytime has stationary odds and never triggers a directed approach.
        for _ in range(16):
            self.move_wild()
            self.assertEqual(self.read('wObject1Range'), 0)

    def test_schooling_follows_and_leaves_space(self):
        k = self.K
        self.player()
        for slot, x in enumerate((12, 15)):
            self.wild('MAGIKARP', k['WILD_SCHOOLING'], (x, 14), slot=slot,
                      habitat='HABITAT_WATER')
        self.assertEqual(self.move_wild(slot=1), k['LEFT'])
        self.write('wObject2MapX', 14)
        self.assertIsNone(self.move_wild(slot=1))
        self.write('wObject1Walking', 4 * k['STEP_WALK'] + k['RIGHT'])
        self.assertEqual(self.move_wild(slot=1), k['RIGHT'])

    def test_lunge_keeps_tiles_clear_and_cannot_cross_barriers(self):
        k = self.K
        self.player()
        alert = self.wild('BEEDRILL', k['WILD_AGGRESSIVE'], (13, 12))
        self.assertIsNone(self.move_wild())
        self.assertEqual(self.h.mem[alert], 1)
        self.assertEqual(self.read('wObject1Direction'), 4 * k['LEFT'])
        for collision, origin, bump in ((k['COLL_WALL'], 0, 0), (0, k['COLL_LEFT_WALL'], 0),
                                        (0, 0, k['FIRST_WILD_OBJECT'])):
            with self.subTest(collision=collision, origin=origin):
                self.tile(8, 8, collision)
                self.write('wObject1LastTile', origin)
                self.move_wild('StepFunction_FromMovement.WildMon')
                self.assertEqual(self.read('wWildMonBumped'), bump)
                self.assertEqual(self.read('wObject1MapX'), 13)
        self.write('wWildMonBumped', 0)
        self.wild('BEEDRILL', k['WILD_AGGRESSIVE'], (13, 12), habitat='HABITAT_GRASS')
        self.move_wild('StepFunction_FromMovement.WildMon')
        self.assertEqual(self.read('wWildMonBumped'), 0)
        self.tile(8, 8, k['COLL_TALL_GRASS'])
        # The follower can temporarily share the player's tile, for example
        # after turning. A battle request doesn't move the wild Pokémon there.
        follower = self.h.addr('wMapObjects') + k['FOLLOWER_OBJECT'] * k['MAPOBJECT_LENGTH']
        self.h.mem[follower + k['MAPOBJECT_SPRITE']] = k['SPRITE_FOLLOWER_MON']
        self.h.mem[follower + k['MAPOBJECT_OBJECT_STRUCT_ID']] = 2
        self.write('wObject2MapX', 12)
        self.write('wObject2MapY', 12)
        self.move_wild('StepFunction_FromMovement.WildMon')
        self.assertEqual(self.read('wWildMonBumped'), k['FIRST_WILD_OBJECT'])
        self.assertEqual(self.read('wObject1MapX'), 13)

    def test_territorial_return_and_limit(self):
        k = self.K
        self.player(x=14, y=12)
        alert = self.wild('URSARING', k['WILD_TERRITORIAL'], (13, 12), home=(12, 12))
        self.h.mem[alert] = 1
        self.assertEqual(self.move_wild(), 4 * k['STEP_WALK'] + k['RIGHT'])
        flags = sum(1 << k['WILD_STEP_' + flag + '_F'] for flag in ('TERRITORY', 'ATTACK', 'QUICK'))
        self.assertEqual(self.read('wObject1Range'), flags)
        self.write('wPlayerMapX', 15)
        self.assertEqual(self.move_wild(), 4 * k['STEP_WALK'] + k['LEFT'])
        self.assertEqual(self.h.mem[alert], 0)
        self.write('wObject1MapY', 14)
        self.move_wild('CheckWildMonStepTile')
        self.assertTrue(self.h.reg.F & 0x10)
        self.write('wObject1LastMapY', 15)
        self.move_wild('CheckWildMonStepTile')
        self.assertFalse(self.h.reg.F & 0x10)

    def test_sweet_honey_lure_lasts_twelve_steps_and_uses_player_tile(self):
        k = self.K
        self.player()
        self.write('wStatusFlags', 0)
        self.write('wStatusFlags2', 0)
        self.write('wMapGroup', k['GROUP_ROUTE_29'])
        self.write('wMapNumber', k['MAP_ROUTE_29'])
        self.write('wPlayerTileCollision', k['COLL_TALL_GRASS'])
        self.write('wGrassEncounterRate', 20)
        self.h.call('_SweetHoney')
        self.assertEqual(self.read('wFieldMoveSucceeded'), 1)
        bank, address = self.h.symbols['SweetHoneyLureScript']
        self.assertEqual(self.read('wQueuedScriptBank'), bank)
        script = self.h.addr('wQueuedScriptAddr')
        self.assertEqual(self.h.mem[script] | self.h.mem[script + 1] << 8, address)
        self.assertEqual((self.read('wWildHoneySteps'), self.read('wWildHoneyX'),
                          self.read('wWildHoneyY')), (12, 12, 12))
        self.write('wWildMonSpawnPending', 0)
        self.write('wGrassEncounterRate', 0)
        for remaining in (*range(11, -1, -1), 0):
            self.h.call('WildMonStep')
            self.assertEqual(self.read('wWildHoneySteps'), remaining)
        self.write('wMapGroup', k['GROUP_PLAYERS_HOUSE_1F'])
        self.write('wMapNumber', k['MAP_PLAYERS_HOUSE_1F'])
        self.h.call('SetWildHoneyLure')
        self.assertFalse(self.h.reg.F & 0x10)


if __name__ == '__main__':
    unittest.main()
