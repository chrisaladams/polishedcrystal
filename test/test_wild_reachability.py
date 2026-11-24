#!/usr/bin/env python3
"""Execute the ROM's spawn path check on controlled collision maps.

These cases cover barriers that the permission table calls walkable, but
which cannot establish a reversible path to a visible wild Pokemon.
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
            'MAPOBJECT_SPRITE', 'MAPOBJECT_X_COORD', 'MAPOBJECT_Y_COORD'], None)

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

    def test_open_floor(self):
        self.assertFalse(self.blocked())

    def test_barriers_between_player_and_spawn(self):
        for collision in (0x07, 0x23, 0x24, 0x29, 0x33, 0x38, 0x60, 0x72, 0xa0, 0xb2):
            with self.subTest(collision=hex(collision)):
                self.tile(6, 8, collision)
                self.assertTrue(self.blocked())

    def test_second_path_can_go_around_wall(self):
        self.tile(6, 4, 0x07)
        self.assertFalse(self.blocked(player=(8, 8), spawn=(4, 4)))
        self.tile(4, 6, 0x07)
        self.assertTrue(self.blocked(player=(8, 8), spawn=(4, 4)))

    def test_water_stays_connected_by_water(self):
        self.h.mem[self.h.addr('wWildMonSpawnHabitat')] = self.K['HABITAT_WATER']
        for x in range(4, 9):
            self.tile(x, 8, 0x29)
        self.assertFalse(self.blocked())
        self.tile(6, 8, 0)
        self.assertTrue(self.blocked())

    def test_player_on_ledge_cannot_prove_a_return_path(self):
        self.tile(8, 8, 0xb2)
        self.assertTrue(self.blocked())

    def test_character_blocks_narrow_path(self):
        h, K = self.h, self.K
        addr = h.addr('wMapObjects') + K['MAPOBJECT_LENGTH']
        h.mem[addr + K['MAPOBJECT_SPRITE']] = 1
        h.mem[addr + K['MAPOBJECT_X_COORD']] = 6 + 4
        h.mem[addr + K['MAPOBJECT_Y_COORD']] = 8 + 4
        self.assertTrue(self.blocked())


if __name__ == '__main__':
    unittest.main()
