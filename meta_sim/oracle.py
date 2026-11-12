#!/usr/bin/env python3
"""Ground-truth stat oracle: runs the ROM's real CalcPkmnStats under PyBoy and
diffs the result against stats.py's hand-written formula.

This loads the built ROM, sets up the minimal RAM state the routine reads
(species/form/level/options/EVs/nature), calls GetBaseData and then
CalcPkmnStats directly, and reads the 6 resulting stats back. It mirrors
stats.py's baseline exactly (DV 15 via PERFECT_IVS_OPT, EV 252 per stat, L50,
neutral nature), so the two can be compared one-for-one.

Every species in pokemon.json is covered, addressed the way the ROM does it:
  - plain species (id 1-254) via wCurSpecies;
  - MON_EXTSPECIES mons (id 256-509: the gen4+ evolutions this hack adds),
    split across wCurSpecies and the EXTSPECIES_MASK bit in wCurForm;
  - stat-affecting regional/variant forms via a direct BaseData row index
    (NUM_SPECIES + slot in VariantSpeciesAndFormTable), fed to
    GetBaseDataFromIndexBC so the form-matching logic is bypassed.
Cosmetic forms share their base species' stats, so they need no special case.

Addresses come from the .sym rgblink writes next to the ROM (via
test/rom_harness.py), so nothing needs re-resolving after a rebuild.

Usage (from the repo root, after `make`):
    python3 meta_sim/oracle.py            # validate every species
    python3 meta_sim/oracle.py 149        # print one species id's stats
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'test'))
sys.path.insert(0, HERE)

from rom_harness import Harness, TRAP, STACK, MBC_ROM_BANK, H_ROM_BANK, \
    find_build, load_symbols  # noqa: E402

LEVEL = 50
EV = 252
PERFECT_IVS_OPT = 1 << 3   # constants/ram_constants.asm
EVS_OPT_MODERN = 0b10
EXTSPECIES_MASK = 0b00100000

STAT_ORDER = ['hp', 'atk', 'defe', 'spe', 'spa', 'spd']   # party struct order


def _const_value(path, name):
    """Evaluate `DEF NAME EQU const_value - 1` style constants by counting."""
    count = None
    for line in open(os.path.join(ROOT, path)):
        s = line.split(';')[0].strip()
        if s.startswith('const_def'):
            parts = s.split()
            count = int(parts[1]) if len(parts) > 1 else 0
        elif s.startswith('const ') and count is not None:
            count += 1
        elif s.startswith('const_skip') and count is not None:
            parts = s.split()
            count += int(parts[1]) if len(parts) > 1 else 1
        elif re.match(rf'DEF {name} EQU const_value - 1', s):
            return count - 1
    raise ValueError(f'{name} not found in {path}')


class StatOracle:
    def __init__(self, harness=None):
        if harness is None:
            rom, sym = find_build(ROOT)
            harness = Harness(rom, load_symbols(sym))
        self.h = harness
        self.num_species = _const_value('constants/pokemon_constants.asm',
                                        'NUM_SPECIES')

    def _run(self, routine, max_frames=30, **regs):
        """Jump to `routine` with the given registers and run it to its ret."""
        h = self.h
        bank, entry = h.symbols[routine]
        h.prepare()
        if bank:
            h.mem[MBC_ROM_BANK] = bank
            h.mem[H_ROM_BANK] = bank
        h.mem[TRAP] = 0x18          # jr -2
        h.mem[TRAP + 1] = 0xfe
        h.mem[STACK] = TRAP & 0xff
        h.mem[STACK + 1] = TRAP >> 8
        h.reg.SP = STACK
        for name, value in regs.items():
            if name == 'hl':
                h.reg.HL = value
            else:   # PyBoy only exposes 8-bit halves of bc/de
                setattr(h.reg, name[0].upper(), value >> 8)
                setattr(h.reg, name[1].upper(), value & 0xff)
        h.reg.PC = entry
        for _ in range(max_frames):
            h.pyboy.tick(1, False)
            if h.reg.PC in (TRAP, TRAP + 1):
                return
        raise RuntimeError(f'{routine} did not return (PC={h.reg.PC:04x})')

    def query(self, species=0, form=0, index=None, level=LEVEL, ev=EV,
              nature=0):
        """CalcPkmnStats for one mon. Pass species/form for the plain and
        extspecies paths, or index for a direct BaseData row (variant forms)."""
        h = self.h
        a = h.addr
        h.prepare()
        h.mem[a('wCurSpecies')] = species
        h.mem[a('wCurForm')] = form
        h.mem[a('wCurPartyLevel')] = level
        h.mem[a('wInitialOptions')] = PERFECT_IVS_OPT
        h.mem[a('wInitialOptions2')] = EVS_OPT_MODERN
        evs = a('wPartyMon1EVs')
        for i in range(6):
            h.mem[evs + i] = ev
        h.mem[a('wPartyMon1Personality')] = nature

        if index is None:
            self._run('GetBaseData')
        else:
            self._run('GetBaseDataFromIndexBC', bc=index)
        out = a('wPartyMon1MaxHP')
        # b bit 0 = apply EVs; hl = EVs - 1; de = destination for the 6 stats
        self._run('CalcPkmnStats', bc=0x0100, hl=evs - 1, de=out)
        vals = [h.read16(out + 2 * i) for i in range(6)]
        return dict(zip(STAT_ORDER, vals))

    def query_by_id(self, national_id, **kw):
        """Ids 1-254 are plain species; 256-509 are MON_EXTSPECIES mons."""
        if national_id <= 254:
            return self.query(national_id, **kw)
        if national_id == 255:
            raise ValueError('255 is the EGG sentinel, not a real species')
        return self.query(national_id - 256, form=EXTSPECIES_MASK, **kw)

    def query_variant(self, position, **kw):
        """Form at 0-indexed `position` in VariantSpeciesAndFormTable."""
        return self.query(index=self.num_species + position, **kw)


def load_species_ids(path='constants/pokemon_constants.asm'):
    """name -> numeric species id, from the hex comments in the constants."""
    ids = {}
    for line in open(os.path.join(ROOT, path)):
        m = re.match(r'\s*const\s+(\w+)\s*;\s*([0-9a-fA-F]+)', line)
        if m:
            ids[m.group(1).lower().rstrip('_')] = int(m.group(2), 16)
    return ids


# pokemon.json suffix -> the FORM constant used in VariantSpeciesAndFormTable.
_VARIANT_SUFFIXES = {
    '_alolan': 'ALOLAN_FORM',
    '_galarian': 'GALARIAN_FORM',
    '_hisuian': 'HISUIAN_FORM',
    '_paldean_fire': 'TAUROS_PALDEAN_FIRE_FORM',
    '_paldean_water': 'TAUROS_PALDEAN_WATER_FORM',
    '_paldean': 'PALDEAN_FORM',
    '_armored': 'MEWTWO_ARMORED_FORM',
    '_red': 'GYARADOS_RED_FORM',
    '_three_segment': 'DUDUNSPARCE_THREE_SEGMENT_FORM',
    '_bloodmoon': 'URSALUNA_BLOODMOON_FORM',
}


def load_variant_forms(path='data/pokemon/variant_forms.asm'):
    """{(SPECIES, FORM): slot} for VariantSpeciesAndFormTable, in table order."""
    table, pos, active = {}, 0, False
    for line in open(os.path.join(ROOT, path)):
        s = line.strip()
        if s.startswith('VariantSpeciesAndFormTable'):
            active = True
        elif active and s.startswith('dp '):
            species, form = (t.strip() for t in s[3:].split(',', 1))
            table[(species, form)] = pos
            pos += 1
        elif active and s.startswith('assert_table_length'):
            break
    return table


def variant_position(name, table):
    for suffix, form in _VARIANT_SUFFIXES.items():
        if name.endswith(suffix):
            return table.get((name[:-len(suffix)].upper(), form))
    return None


def validate(pokemon_json=os.path.join(HERE, 'data', 'pokemon.json')):
    from stats import mon_stats

    ids = load_species_ids()
    variants = load_variant_forms()
    pokemon = json.load(open(pokemon_json))
    oracle = StatOracle()
    checked, skipped, mismatches = 0, [], []
    for name, m in pokemon.items():
        if 'stats' not in m:
            continue
        pos = variant_position(name, variants)
        if pos is not None:
            got = oracle.query_variant(pos)
        else:
            base = name[:-len('_plain')] if name.endswith('_plain') else name
            sid = ids.get(base.rstrip('_'))
            if not sid or sid == 255 or sid > 509:
                skipped.append(name)
                continue
            got = oracle.query_by_id(sid)
        checked += 1
        want = mon_stats(m['stats'])
        if got != want:
            mismatches.append((name, got, want))
    oracle.h.stop()
    return checked, skipped, mismatches


def main():
    if len(sys.argv) > 1:
        oracle = StatOracle()
        print(oracle.query_by_id(int(sys.argv[1], 0)))
        oracle.h.stop()
        return 0
    checked, skipped, mismatches = validate()
    print(f'checked {checked} species against the ROM, skipped {len(skipped)}'
          f'{" " + str(skipped) if skipped else ""}, '
          f'{len(mismatches)} mismatches')
    for name, got, want in mismatches:
        print(f'  {name}: rom={got} stats.py={want}')
    return 1 if mismatches else 0


if __name__ == '__main__':
    sys.exit(main())
