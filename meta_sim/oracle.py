"""Ground-truth stat oracle: calls the ROM's real CalcPkmnStats routine via
mGBA emulation, instead of reimplementing the Gen-2 stat formula by hand.

This loads the actual built ROM, injects a tiny trampoline into WRAM that
bankswitches to CalcPkmnStats's bank, sets up the minimal RAM state the
routine reads (species/form/level/options/EVs/nature), calls it, and reads
back the 6 resulting stats. Mirrors stats.py's baseline assumptions exactly
(DV=15 via PERFECT_IVS_OPT, EV=252/stat, L50, neutral nature) so the two can
be diffed directly.

Covers plain species (id 1-254) and MON_EXTSPECIES mons -- every gen4+
evolution this hack adds past the original Crystal roster, e.g. Togekiss/
Honchkrow/Magnezone (id 256-509, split across wCurSpecies + an EXTSPECIES_MASK
bit in wCurForm; see query_stats_by_id). Cosmetic/regional forms (Unown
letters, Paldean Tauros, Hisuian Qwilfish, etc.) use a third mechanism, a
variant-species-and-form table lookup in GetSpeciesAndFormIndex, and are
not yet handled.

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

GET_BASE_DATA_ADDR = 0x3160      # bank 00 (home)
CALC_PKMN_STATS_BANK = 0x14
CALC_PKMN_STATS_ADDR = 0x4dc6

TRAMPOLINE_ADDR = 0xc100

PERFECT_IVS_OPT = 0x08
EVS_OPT_MODERN = 0x02
EXTSPECIES_MASK = 0x20

STAT_ORDER = ['hp', 'atk', 'defe', 'spe', 'spa', 'spd']


def build_trampoline():
    a, b = CALC_PKMN_STATS_ADDR & 0xff, (CALC_PKMN_STATS_ADDR >> 8) & 0xff
    g0, g1 = GET_BASE_DATA_ADDR & 0xff, (GET_BASE_DATA_ADDR >> 8) & 0xff
    return bytes([
        0x3E, CALC_PKMN_STATS_BANK,        # ld a, BANK
        0xCF,                              # rst $08 (Bankswitch: sets hROMBank + rROMB)
        0xCD, g0, g1,                      # call GetBaseData
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


def query_stats(species_id, form=0, level=50, ev=252, nature=0, core=None):
    core = core or _get_core()
    mem = core.memory

    code = build_trampoline()
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

    halt_addr = TRAMPOLINE_ADDR + 9  # the jr $ instruction
    for _ in range(200000):
        if cpu.pc == halt_addr:
            break
        core.step()
    else:
        raise RuntimeError('oracle did not reach halt loop')

    raw = [mem.u8[OUT_PTR + i] for i in range(12)]
    vals = [(raw[2 * i] << 8) | raw[2 * i + 1] for i in range(6)]
    return dict(zip(STAT_ORDER, vals))


def query_stats_by_id(national_id, **kw):
    """Query by the numeric id from pokemon_constants.asm's hex comments.
    Ids 1-254 address BaseData directly via wCurSpecies (plain species).
    Ids 256-509 are mons added via the two-byte MON_EXTSPECIES mechanism
    (every gen4+ evolution this hack adds, e.g. Togekiss/Honchkrow): the
    routine can't fit them in the single wCurSpecies byte, so it splits
    them across wCurSpecies (low part) and an EXTSPECIES_MASK bit (0x20)
    in wCurForm, reassembling them inside GetSpeciesAndFormIndex. Id 255
    is the EGG sentinel and isn't a real species. Cosmetic/regional forms
    (Unown letters, Paldean Tauros, etc.) use a third mechanism -- a
    variant-species-and-form table lookup -- not handled here."""
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


def validate(pokemon_json='meta_sim/data/pokemon.json'):
    """Diff stats.py's hand-rolled formula against the ROM's real
    CalcPkmnStats for every species addressable via plain species id or
    the MON_EXTSPECIES mechanism (covers ids 1-254 and 256-509). Cosmetic/
    regional forms (Unown letters, Paldean Tauros, Hisuian Qwilfish, etc.)
    use a third mechanism -- a variant-species-and-form table lookup --
    and are out of scope here: skipped, not silently assumed correct."""
    import json
    from stats import mon_stats

    ids = load_species_ids()
    pokemon = json.load(open(pokemon_json))
    core = _get_core()
    checked, skipped, mismatches = 0, 0, []
    for name, m in pokemon.items():
        if 'stats' not in m:
            continue
        sid = ids.get(name.rstrip('_'))
        if '_' in name or not sid or sid == 255 or sid > 509:
            skipped += 1
            continue
        checked += 1
        oracle_r = query_stats_by_id(sid, core=core)
        py_r = mon_stats(m['stats'])
        if oracle_r != py_r:
            mismatches.append((name, sid, oracle_r, py_r))
    return checked, skipped, mismatches


if __name__ == '__main__':
    if len(sys.argv) > 1:
        print(query_stats_by_id(int(sys.argv[1])))
    else:
        checked, skipped, mismatches = validate()
        print(f'checked {checked} species against the ROM, skipped {skipped} '
              f'(forms / extspecies), {len(mismatches)} mismatches')
        for name, sid, o, p in mismatches:
            print(f'  {name} (id {sid}): oracle={o} stats.py={p}')
