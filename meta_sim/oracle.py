"""Ground-truth stat oracle: calls the ROM's real CalcPkmnStats routine via
mGBA emulation, instead of reimplementing the Gen-2 stat formula by hand.

This loads the actual built ROM, injects a tiny trampoline into WRAM that
bankswitches to CalcPkmnStats's bank, sets up the minimal RAM state the
routine reads (species/form/level/options/EVs/nature), calls it, and reads
back the 6 resulting stats. Mirrors stats.py's baseline assumptions exactly
(DV=15 via PERFECT_IVS_OPT, EV=252/stat, L50, neutral nature) so the two can
be diffed directly.

Covers every species in three ways, matching how the ROM itself addresses them:
  - plain species (id 1-254) via wCurSpecies (query_stats_by_id);
  - MON_EXTSPECIES mons -- every gen4+ evolution this hack adds past the
    original Crystal roster, e.g. Togekiss/Honchkrow/Magnezone (id 256-509,
    split across wCurSpecies + an EXTSPECIES_MASK bit in wCurForm; see
    query_stats_by_id);
  - stat-affecting regional/variant forms (Alolan/Galarian/Hisuian/Paldean,
    plus Mewtwo-Armored, Gyarados-Red, Dudunsparce-3-segment, the Paldean
    Tauros sub-breeds, Ursaluna-Bloodmoon) via a direct BaseData row index
    (query_variant_index): we look the form's row up by its position in
    VariantSpeciesAndFormTable and call _GetBaseData with a precomputed index,
    bypassing the species+form matching in GetSpeciesAndFormIndex entirely.
Cosmetic forms (Unown letters, Arbok/Pikachu/Magikarp recolours, Pichu
Spiky-eared) share their base species' stats -- they live in a separate
CosmeticSpeciesAndFormTable that GetBaseData never consults -- so an ordinary
plain-species query already gives their correct stats; no special handling.

Addresses below were resolved from polishedcrystal-3.2.3.sym for this build;
they will need re-resolving if the ROM is rebuilt and symbols shift.
"""
import sys
import mgba.core
import mgba.log

mgba.log.silence()

ROM_PATH = 'polishedcrystal-3.2.3.gbc'

# WRAM addresses (bank 00 fixed addresses, from .sym)
W_CUR_SPECIES = 0xceb0
W_CUR_FORM = 0xceb4
W_INITIAL_OPTIONS = 0xcff6
W_INITIAL_OPTIONS2 = 0xcff7
W_CUR_PARTY_LEVEL = 0xd115
W_PARTY_MON1 = 0xdcd6

MON_EVS = W_PARTY_MON1 + 11      # 6 bytes
MON_PERSONALITY = W_PARTY_MON1 + 20  # nature = low byte

EVS_PTR = MON_EVS - 1            # hl input to CalcPkmnStats
OUT_PTR = W_PARTY_MON1 + 36      # de output: aliases MON_MAXHP.. (12 bytes)

GET_BASE_DATA_ADDR = 0x3160      # bank 00 (home): reads wCurSpecies/wCurForm
# GetBaseDataFromIndexBC (bank 00): takes bc as a *direct* BaseData row index,
# pushes hl/de/bc then falls into _GetBaseData (which pops them again), so it's
# register-balanced -- unlike calling _GetBaseData itself. We use it to address
# variant-form rows (>= NUM_SPECIES) without replaying the form-matching logic.
GET_BASE_DATA_FROM_INDEX_ADDR = 0x315b
CALC_PKMN_STATS_BANK = 0x14
CALC_PKMN_STATS_ADDR = 0x4dc6

TRAMPOLINE_ADDR = 0xc100

PERFECT_IVS_OPT = 0x08
EVS_OPT_MODERN = 0x02
EXTSPECIES_MASK = 0x20

# NUM_SPECIES (constants/pokemon_constants.asm:317, = $123). A variant form's
# BaseData row is NUM_SPECIES + its 0-indexed slot in VariantSpeciesAndFormTable.
NUM_SPECIES = 291

STAT_ORDER = ['hp', 'atk', 'defe', 'spe', 'spa', 'spd']


def build_trampoline(index=None):
    """Bytecode for the WRAM trampoline. With index=None it calls GetBaseData,
    which reads wCurSpecies/wCurForm (plain + extspecies paths). With an integer
    index it loads bc=index, calls GetBaseDataFromIndexBC to fetch that BaseData
    row directly, then reloads bc=$0100 (the apply-EVs bit CalcPkmnStats wants in
    b) before the stat calc -- variant/regional-form path."""
    a, b = CALC_PKMN_STATS_ADDR & 0xff, (CALC_PKMN_STATS_ADDR >> 8) & 0xff
    if index is None:
        g0, g1 = GET_BASE_DATA_ADDR & 0xff, (GET_BASE_DATA_ADDR >> 8) & 0xff
        return bytes([
            0x3E, CALC_PKMN_STATS_BANK,    # ld a, BANK
            0xCF,                          # rst $08 (Bankswitch: hROMBank + rROMB)
            0xCD, g0, g1,                  # call GetBaseData
            0xCD, a, b,                    # call CalcPkmnStats
            0x18, 0xFE,                    # jr $ (halt loop)
        ])
    g0, g1 = GET_BASE_DATA_FROM_INDEX_ADDR & 0xff, (GET_BASE_DATA_FROM_INDEX_ADDR >> 8) & 0xff
    lo, hi = index & 0xff, (index >> 8) & 0xff
    return bytes([
        0x3E, CALC_PKMN_STATS_BANK,        # ld a, BANK
        0xCF,                              # rst $08 (Bankswitch: hROMBank + rROMB)
        0x01, lo, hi,                      # ld bc, index
        0xCD, g0, g1,                      # call GetBaseDataFromIndexBC
        0x01, 0x00, 0x01,                  # ld bc, $0100 (apply-EVs bit -> b)
        0xCD, a, b,                        # call CalcPkmnStats
        0x18, 0xFE,                        # jr $ (halt loop)
    ])


_core = None


def _get_core():
    global _core
    if _core is None:
        _core = mgba.core.load_path(ROM_PATH)
        _core.reset()
    return _core


def query_stats(species_id, form=0, level=50, ev=252, nature=0, core=None,
                index=None):
    """Run the ROM's CalcPkmnStats for one mon and read back the 6 stats.
    Pass species_id/form for the plain + extspecies paths, or index for the
    direct variant-form-row path (species_id/form are then ignored by the ROM,
    since GetBaseDataFromIndexBC addresses BaseData straight from the index)."""
    core = core or _get_core()
    mem = core.memory

    code = build_trampoline(index)
    for i, byte in enumerate(code):
        mem.u8[TRAMPOLINE_ADDR + i] = byte

    mem.u8[W_CUR_SPECIES] = species_id
    mem.u8[W_CUR_FORM] = form
    mem.u8[W_CUR_PARTY_LEVEL] = level
    mem.u8[W_INITIAL_OPTIONS] = PERFECT_IVS_OPT
    mem.u8[W_INITIAL_OPTIONS2] = EVS_OPT_MODERN
    for i in range(6):
        mem.u8[MON_EVS + i] = ev
    mem.u8[MON_PERSONALITY] = nature

    cpu = core.cpu
    cpu.bc = 0x0100
    cpu.hl = EVS_PTR
    cpu.de = OUT_PTR
    cpu.sp = 0xdff0
    cpu._native.pc = TRAMPOLINE_ADDR

    halt_addr = TRAMPOLINE_ADDR + len(code) - 2  # the jr $ instruction
    for _ in range(200000):
        if cpu.pc == halt_addr:
            break
        core.step()
    else:
        raise RuntimeError('oracle did not reach halt loop')

    raw = [mem.u8[OUT_PTR + i] for i in range(12)]
    vals = [(raw[2 * i] << 8) | raw[2 * i + 1] for i in range(6)]
    return dict(zip(STAT_ORDER, vals))


def query_variant_index(position, core=None, **kw):
    """Stats for the form at 0-indexed `position` in VariantSpeciesAndFormTable
    (see load_variant_forms). Its BaseData row is NUM_SPECIES + position."""
    return query_stats(0, core=core, index=NUM_SPECIES + position, **kw)


def query_stats_by_id(national_id, **kw):
    """Query by the numeric id from pokemon_constants.asm's hex comments.
    Ids 1-254 address BaseData directly via wCurSpecies (plain species).
    Ids 256-509 are mons added via the two-byte MON_EXTSPECIES mechanism
    (every gen4+ evolution this hack adds, e.g. Togekiss/Honchkrow): the
    routine can't fit them in the single wCurSpecies byte, so it splits
    them across wCurSpecies (low part) and an EXTSPECIES_MASK bit (0x20)
    in wCurForm, reassembling them inside GetSpeciesAndFormIndex. Id 255
    is the EGG sentinel and isn't a real species. Stat-affecting regional/
    variant forms are addressed separately, by row index -- see
    query_variant_index / load_variant_forms."""
    if national_id <= 254:
        return query_stats(national_id, **kw)
    if national_id == 255:
        raise ValueError('255 is the EGG sentinel, not a real species')
    return query_stats(national_id - 256, form=EXTSPECIES_MASK, **kw)


def load_species_ids(const_path='constants/pokemon_constants.asm'):
    """name -> numeric species id, parsed from the hex comments in
    pokemon_constants.asm (not line position -- there's a gap at 0x100)."""
    import re
    ids = {}
    for line in open(const_path):
        m = re.match(r'\s*const\s+(\w+)\s*;\s*([0-9a-fA-F]+)', line)
        if m:
            ids[m.group(1).lower().rstrip('_')] = int(m.group(2), 16)
    return ids


# pokemon.json suffix -> the FORM constant used in VariantSpeciesAndFormTable.
# The regional keywords (alolan/galarian/hisuian/paldean) share one form byte
# each across many species; the rest are species-specific one-offs.
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
    """Parse VariantSpeciesAndFormTable into {(SPECIES, FORM): position}, the
    0-indexed slot order that GetSpeciesAndFormIndex turns into a BaseData row
    (NUM_SPECIES + position). The earlier CosmeticSpeciesAndFormTable is skipped:
    those forms share their base species' stats, so they need no row of their
    own. Order here is the single source of truth for the row indices."""
    table = {}
    pos, in_variant = 0, False
    for line in open(path):
        s = line.strip()
        if s.startswith('VariantSpeciesAndFormTable'):
            in_variant = True
            continue
        if not in_variant:
            continue
        if s.startswith('dp '):
            species, form = (t.strip() for t in s[3:].split(',', 1))
            table[(species, form)] = pos
            pos += 1
        elif s.startswith('assert_table_length'):
            break
    return table


def variant_position(name, variant_table):
    """Map a pokemon.json key (e.g. 'rattata_alolan', 'tauros_paldean_fire') to
    its VariantSpeciesAndFormTable position, or None if it isn't a stat-variant
    form. Plain/base names ('rattata_plain', 'gyarados', 'ho_oh') return None and
    are handled by the ordinary species-id path instead."""
    for suffix, form in _VARIANT_SUFFIXES.items():
        if name.endswith(suffix):
            species = name[:-len(suffix)].upper()
            return variant_table.get((species, form))
    return None


def validate(pokemon_json='meta_sim/data/pokemon.json'):
    """Diff stats.py's hand-rolled formula against the ROM's real CalcPkmnStats
    for every species in pokemon.json: plain species (id 1-254) and extspecies
    mons (256-509) by id, and stat-affecting regional/variant forms by their
    VariantSpeciesAndFormTable row index. '_plain'-suffixed entries resolve to
    their base species (cosmetic/plain forms share the base's stats). Only the
    EGG sentinel and any entry with no resolvable species id is skipped."""
    import json
    from stats import mon_stats

    ids = load_species_ids()
    variant_table = load_variant_forms()
    pokemon = json.load(open(pokemon_json))
    core = _get_core()
    checked, skipped, mismatches = 0, 0, []
    for name, m in pokemon.items():
        if 'stats' not in m:
            continue
        py_r = mon_stats(m['stats'])

        pos = variant_position(name, variant_table)
        if pos is not None:
            oracle_r = query_variant_index(pos, core=core)
        else:
            # base/plain species: drop a '_plain' suffix, then look up the id
            base = name[:-len('_plain')] if name.endswith('_plain') else name
            sid = ids.get(base.rstrip('_'))
            if not sid or sid == 255 or sid > 509:
                skipped += 1
                continue
            oracle_r = query_stats_by_id(sid, core=core)

        checked += 1
        if oracle_r != py_r:
            mismatches.append((name, oracle_r, py_r))
    return checked, skipped, mismatches


if __name__ == '__main__':
    if len(sys.argv) > 1:
        print(query_stats_by_id(int(sys.argv[1])))
    else:
        checked, skipped, mismatches = validate()
        print(f'checked {checked} species against the ROM, skipped {skipped}, '
              f'{len(mismatches)} mismatches')
        for name, o, p in mismatches:
            print(f'  {name}: oracle={o} stats.py={p}')
