#!/usr/bin/env python3
"""Exercise manual saves, legacy Magikarp forms and the revised Pokédex."""
import sys
from pathlib import Path

from test_orange_league import ROOT
from test_wild_mons import Game, rgbasm_values


def main(path):
    original = Path(path).read_bytes()
    k = rgbasm_values(('MAGIKARP', 'MAGIKARP_DAPPLES_FORM', 'MAGIKARP_CALICO1_FORM',
                       'MAGIKARP_SKELLY_FORM', 'MAGIKARP_MASK1_FORM', 'FORM_MASK',
                       'MON_SHINY_F', 'PARTYMON_STRUCT_LENGTH'), None)
    g = Game(original)
    try:
        g.boot()
        assert g.rd('wPartyCount')
        g.wr('wPartyMon1Species', k['MAGIKARP'])
        extra = g.rd('wPartyMon1Form') & 0x80
        g.wr('wPartyMon1Form', extra | k['MAGIKARP_DAPPLES_FORM'])
        personality = g.rd('wPartyMon1Shiny') | (1 << k['MON_SHINY_F'])
        g.wr('wPartyMon1Shiny', personality)
        item = g.rd('wPartyMon1Item')
        assert 'StartMenu.BoxesString' not in g.sym and 'Options_Autosave' not in g.sym
        before = g.sram()
        g.press('left', 130)
        assert g.sram() == before, 'overworld movement wrote a save'
        g.manual_save()
        saved = g.sram()
        assert saved != before, 'manual save did not write'
        g.pb.stop(save=False)
        g = Game(saved + original[0x8000:])
        g.boot()
        assert g.rd('wPartyMon1Species') == k['MAGIKARP']
        assert g.rd('wPartyMon1Form') == extra | k['MAGIKARP_CALICO1_FORM']
        assert g.rd('wPartyMon1Shiny') == personality and g.rd('wPartyMon1Item') == item

        # Encode a legacy box entry using the real storage routine and decode
        # it again, exercising its checksum and stats calculations.
        for i in range(k['PARTYMON_STRUCT_LENGTH']):
            g.wr('wTempMonSpecies', g.rd('wPartyMon1Species', i), i)
        g.wr('wTempMonForm', k['MAGIKARP_SKELLY_FORM'])
        snap = g.state()
        m, r = g.m, g.pb.register_file
        m[0xffff] = m[0xff0f] = 0
        for fn in ('EncodeTempMon', 'DecodeTempMon'):
            bank, pc = g.sym[fn]
            m[0x2000] = m[g.addr('hROMBank')] = bank
            m[0xff90], m[0xff91] = 0x18, 0xfe
            m[0xdff0], m[0xdff1] = 0x90, 0xff
            r.SP, r.PC = 0xdff0, pc
            for _ in range(60):
                g.tick()
                if r.PC in (0xff90, 0xff91):
                    break
            else:
                raise AssertionError(fn + ' did not return')
        assert g.rd('wTempMonSpecies') == k['MAGIKARP']
        assert g.rd('wTempMonForm') & k['FORM_MASK'] == k['MAGIKARP_MASK1_FORM']
        assert g.rd('wTempMonShiny') == personality
        g.load(snap)

        seen = []
        g.pb.hook_register(*g.sym['Pokedex_Description'], seen.append, True)
        g.press('start', 90)  # The Pokédex is the first item after receiving it.
        g.press('a', 120)
        g.press('a', 110)
        g.press('a', 100)
        assert seen, 'Pokédex description did not open'
        assert all(g.rd('wTilemap', 20*y+x) not in range(0x79, 0x7d)
                   for y in (2, 3, 4) for x in (18, 19)), 'old footprint tiles are visible'
        # The three screens previously used the footprint tile IDs in a 2x2
        # box. Confirm the adjacent two 2x2 type icons still exist.
        for filename in ('main', 'description', 'stats'):
            tiles = (Path(ROOT) / 'gfx/pokedex' / (filename + '.tilemap')).read_bytes()
            assert all(0x71 + i in tiles for i in range(8)), filename
        print('Passed manual saving, legacy party and box forms, shiny and item preservation, and Pokédex assets.')
    finally:
        g.pb.stop(save=False)


if __name__ == '__main__':
    main(sys.argv[1])
