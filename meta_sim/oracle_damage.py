"""Ground-truth damage oracle: drives the ROM's real damage routine via mGBA,
instead of reimplementing the damage formula by hand like calc.py does.

calc.py is a readable first-order model (formula + STAB + type chart + a flat
average roll). This oracle is the arbiter: it sets up a clean battle state in
WRAM and calls the actual damagecalc + stab routines, returning the exact
damage the game would deal. Running validate_against_calc() below confirms
calc.py's base formula is faithful -- the one thing the ROM does that calc.py
doesn't, truncating a mon's 16-bit Attack/Defense to 8 bits (TruncateHL_BC)
before the divide, only moves the result on ~0.05% of fully-evolved matchups
and never by more than 1 HP. So the formula isn't where calc.py loses
fidelity; its documented simplifications (the flat roll, ability/item/status
modelling) are. Having the arbiter on hand means future calc.py changes can be
checked against ground truth instead of argued about.

How it works (mirroring AIDamageCalc's call chain, which is the engine's own
"what would this move do" predictor):
  - hBattleTurn = 1, so the *enemy* mon is the attacker and the *player* mon is
    the defender; we write attacker data into wEnemyMon*, defender into
    wBattleMon*, and the move into wEnemyMoveStruct (GetBattleVar reads the
    enemy move struct on the enemy's turn).
  - we pass Attack/Defense/Power/Level directly in registers b/c/d/e (the
    documented inputs to BattleCommand_damagecalc), having pre-applied
    TruncateHL_BC ourselves -- so we don't need to stand up full party structs
    just to let BattleCommand_damagestats read them back out.
  - everything that would perturb the number is neutralised to a no-op:
    stat stages at BASE_STAT_LEVEL (7), no crit (wMoveHitState=0), no item,
    no held-ability damage mods (NO_ABILITY), no burn/status, no weather, no
    screens, no Future Sight. What's left is exactly the formula + stat-stage
    framework + STAB + type effectiveness.
  - BattleCommand_damagecalc never applies the 85-100% random roll (that's a
    separate DamageVariation step), so the result is deterministic: the maximum
    roll. Compare against calc.py with ROLL=1.0 in mind.

Addresses are from polishedcrystal-3.2.3.sym; re-resolve if the ROM is rebuilt.
"""
import sys

from oracle import _get_core, TRAMPOLINE_ADDR

# --- routine entry points (bank 0d, called after an rst $08 bankswitch) ---
DAMAGE_BANK = 0x0d
DAMAGECALC_ADDR = 0x6ee7          # BattleCommand_damagecalc (b/c/d/e -> wCurDamage)
STAB_ADDR = 0x5ef3                # BattleCommand_stab (type matchup + STAB + weather)

# --- move struct (wEnemyMoveStruct) + field offsets (constants/battle_constants.asm) ---
W_ENEMY_MOVE_STRUCT = 0xc47f
MOVE_ANIM, MOVE_EFFECT, MOVE_POWER, MOVE_TYPE, MOVE_CATEGORY = 0, 1, 2, 3, 7

# --- attacker = enemy mon (wEnemyMon*, WRAM bank 1) / defender = player (wBattleMon*) ---
W_ENEMY_MON_TYPE1 = 0xd22a         # +1 = Type2
W_BATTLE_MON_TYPE1 = 0xc4c6        # +1 = Type2
W_ENEMY_MON_ABILITY = 0xd212
W_BATTLE_MON_ABILITY = 0xc4ae
W_ENEMY_MON_ITEM = 0xd20a
W_BATTLE_MON_ITEM = 0xc4a6
W_ENEMY_MON_STATUS = 0xd21a
W_BATTLE_MON_STATUS = 0xc4b6

# --- battle-wide state to neutralise ---
W_PLAYER_STAT_LEVELS = 0xc529      # 8-byte span up to wEnemyStatLevels
W_ENEMY_STAT_LEVELS = 0xc531
W_PLAYER_SUBSTATUS1 = 0xc4e1       # ..4 are consecutive
W_ENEMY_SUBSTATUS1 = 0xc4e5
W_MOVE_HIT_STATE = 0xc4df
W_BATTLE_WEATHER = 0xc561
W_PLAYER_SCREENS = 0xc559
W_ENEMY_SCREENS = 0xc55d
W_PLAYER_FUTURE_SIGHT_COUNT = 0xc573
W_ENEMY_FUTURE_SIGHT_COUNT = 0xc574

# --- outputs / scratch ---
W_TYPE_MATCHUP = 0xd26b
W_TYPE_MODIFIER = 0xc4de
W_CUR_DAMAGE = 0xd25d               # big-endian 16-bit result
H_BATTLE_TURN = 0xffd1

BASE_STAT_LEVEL = 7                 # neutral stat stage (constants/battle_constants.asm)
NO_ABILITY = 0
TYPE_NEUTRAL = 0x10                 # wTypeMatchup base (= x1.0 before the /$10 divide)
UNKNOWN_TYPE = 0x12                 # never grants STAB / never in the chart -> inert filler

# type / category id <-> name (constants/type_constants.asm)
TYPE_ID = {
    'NORMAL': 0, 'FIGHTING': 1, 'FLYING': 2, 'POISON': 3, 'GROUND': 4,
    'ROCK': 5, 'BUG': 6, 'GHOST': 7, 'STEEL': 8, 'FIRE': 9, 'WATER': 10,
    'GRASS': 11, 'ELECTRIC': 12, 'PSYCHIC': 13, 'ICE': 14, 'DRAGON': 15,
    'DARK': 16, 'FAIRY': 17,
}
CATEGORY_ID = {'PHYSICAL': 0, 'SPECIAL': 1, 'STATUS': 2}


def truncate_hl_bc(attack, defense):
    """Replicate the ROM's TruncateHL_BC: halve both 16-bit values in lockstep
    until each fits in 8 bits (flooring to 1, never 0). damagecalc takes the
    truncated bytes, so the oracle must pre-apply this to match the game."""
    hl, bc = attack, defense
    while True:
        if (hl >> 8) | (bc >> 8):       # ld a,h / or b -> nonzero: keep halving
            bc >>= 1
            if bc == 0:
                bc = 1                  # FloorBC
            hl >>= 1
            if hl == 0:
                hl = 1                  # inc l on underflow
        if (hl >> 8) | (bc >> 8):       # still doesn't fit -> loop
            continue
        return hl & 0xff, bc & 0xff


def _neutralise(mem):
    """Zero/neutralise every bit of battle state damagecalc + stab would read,
    so the only inputs left are the move, the stats, and the types."""
    for i in range(8):
        mem.u8[W_PLAYER_STAT_LEVELS + i] = BASE_STAT_LEVEL
        mem.u8[W_ENEMY_STAT_LEVELS + i] = BASE_STAT_LEVEL
    mem.u8[W_BATTLE_MON_ABILITY] = NO_ABILITY
    mem.u8[W_ENEMY_MON_ABILITY] = NO_ABILITY
    mem.u8[W_BATTLE_MON_ITEM] = 0
    mem.u8[W_ENEMY_MON_ITEM] = 0
    mem.u8[W_BATTLE_MON_STATUS] = 0
    mem.u8[W_ENEMY_MON_STATUS] = 0
    for i in range(4):
        mem.u8[W_PLAYER_SUBSTATUS1 + i] = 0
        mem.u8[W_ENEMY_SUBSTATUS1 + i] = 0
    mem.u8[W_MOVE_HIT_STATE] = 0
    mem.u8[W_BATTLE_WEATHER] = 0
    mem.u8[W_PLAYER_SCREENS] = 0
    mem.u8[W_ENEMY_SCREENS] = 0
    mem.u8[W_PLAYER_FUTURE_SIGHT_COUNT] = 0
    mem.u8[W_ENEMY_FUTURE_SIGHT_COUNT] = 0
    mem.u8[W_TYPE_MATCHUP] = TYPE_NEUTRAL
    mem.u8[W_TYPE_MODIFIER] = TYPE_NEUTRAL
    mem.u8[W_CUR_DAMAGE] = 0
    mem.u8[W_CUR_DAMAGE + 1] = 0


def _build_trampoline(b, c, d, e):
    g0, g1 = DAMAGECALC_ADDR & 0xff, DAMAGECALC_ADDR >> 8
    s0, s1 = STAB_ADDR & 0xff, STAB_ADDR >> 8
    return bytes([
        0x3E, DAMAGE_BANK,             # ld a, BANK
        0xCF,                          # rst $08 (bankswitch)
        0x06, b,                       # ld b, attack  (truncated)
        0x0E, c,                       # ld c, defense (truncated)
        0x16, d,                       # ld d, power
        0x1E, e,                       # ld e, level
        0xCD, g0, g1,                  # call BattleCommand_damagecalc
        0xCD, s0, s1,                  # call BattleCommand_stab
        0x18, 0xFE,                    # jr $ (halt loop)
    ])


def query_damage(attack, defense, power, move_type, category,
                 attacker_types=(UNKNOWN_TYPE, UNKNOWN_TYPE),
                 defender_types=(UNKNOWN_TYPE, UNKNOWN_TYPE),
                 level=50, core=None):
    """Exact (max-roll) damage the ROM deals for one hit.

    attack/defense  : the relevant 16-bit L50 stats (atk+def for PHYSICAL,
                      spa+spd for SPECIAL) -- truncation is applied internally.
    power           : move base power.
    move_type       : type id or name (see TYPE_ID).
    category        : 'PHYSICAL'/'SPECIAL' or its id.
    attacker_types  : (type, type) ids/names -- drives STAB.
    defender_types  : (type, type) ids/names -- drives type effectiveness.
    Returns the integer in wCurDamage (0 on immunity)."""
    core = core or _get_core()
    mem = core.memory

    def tid(t):
        return TYPE_ID[t] if isinstance(t, str) else t

    move_type = tid(move_type)
    category = CATEGORY_ID[category] if isinstance(category, str) else category
    at = [tid(t) for t in attacker_types]
    dt = [tid(t) for t in defender_types]

    _neutralise(mem)
    b, c = truncate_hl_bc(attack, defense)

    mem.u8[H_BATTLE_TURN] = 1
    mem.u8[W_ENEMY_MOVE_STRUCT + MOVE_ANIM] = 1          # not STRUGGLE
    mem.u8[W_ENEMY_MOVE_STRUCT + MOVE_EFFECT] = 0        # EFFECT_NORMAL_HIT
    mem.u8[W_ENEMY_MOVE_STRUCT + MOVE_POWER] = power
    mem.u8[W_ENEMY_MOVE_STRUCT + MOVE_TYPE] = move_type
    mem.u8[W_ENEMY_MOVE_STRUCT + MOVE_CATEGORY] = category
    mem.u8[W_ENEMY_MON_TYPE1] = at[0]
    mem.u8[W_ENEMY_MON_TYPE1 + 1] = at[1]
    mem.u8[W_BATTLE_MON_TYPE1] = dt[0]
    mem.u8[W_BATTLE_MON_TYPE1 + 1] = dt[1]

    code = _build_trampoline(b, c, power, level)
    for i, byte in enumerate(code):
        mem.u8[TRAMPOLINE_ADDR + i] = byte

    cpu = core.cpu
    cpu.sp = 0xdff0
    cpu._native.pc = TRAMPOLINE_ADDR
    halt = TRAMPOLINE_ADDR + len(code) - 2
    for _ in range(300000):
        if cpu.pc == halt:
            break
        core.step()
    else:
        raise RuntimeError('damage oracle did not reach halt loop')

    return (mem.u8[W_CUR_DAMAGE] << 8) | mem.u8[W_CUR_DAMAGE + 1]


# self-test cases: hand-computed ROM-faithful values (power 100, atk 200,
# def 100, L50). base = ((2*50/5+2)*100*200)/100/50 + 2 = 90, then STAB/effect.
_SELF_TEST = [
    # (kw, expected, label)
    (dict(attack=200, defense=100, power=100, move_type=0, category=0), 90, 'base'),
    (dict(attack=200, defense=100, power=100, move_type='NORMAL', category=0,
          attacker_types=('NORMAL', UNKNOWN_TYPE)), 135, 'STAB x1.5'),
    (dict(attack=200, defense=100, power=100, move_type='FIRE', category=1,
          defender_types=('GRASS', UNKNOWN_TYPE)), 180, 'super-effective x2'),
    (dict(attack=200, defense=100, power=100, move_type='FIRE', category=1,
          defender_types=('WATER', UNKNOWN_TYPE)), 45, 'resisted x0.5'),
    (dict(attack=200, defense=100, power=100, move_type='NORMAL', category=0,
          defender_types=('GHOST', UNKNOWN_TYPE)), 0, 'immune'),
    (dict(attack=200, defense=100, power=100, move_type='ROCK', category=0,
          defender_types=('FLYING', 'BUG')), 360, '4x'),
    (dict(attack=200, defense=100, power=100, move_type='FIRE', category=1,
          attacker_types=('FIRE', UNKNOWN_TYPE),
          defender_types=('GRASS', UNKNOWN_TYPE)), 270, 'STAB + 2x'),
]


def self_test():
    core = _get_core()
    ok = True
    for kw, expected, label in _SELF_TEST:
        got = query_damage(core=core, **kw)
        flag = 'ok' if got == expected else 'MISMATCH'
        if got != expected:
            ok = False
        print(f'  [{flag}] {label}: got {got}, expected {expected}')
    return ok


def _formula_no_truncate(attack, defense, power, level=50):
    """calc.py's core damage formula WITHOUT the ROM's 8-bit stat truncation
    (and without roll/STAB/effect -- those are applied identically both sides).
    This is exactly what calc.py computes for the raw hit, so diffing it against
    the oracle isolates the truncation gap calc.py silently ignores."""
    return (((2 * level) // 5 + 2) * power * attack) // defense // 50 + 2


def validate_against_calc(pokemon_json='meta_sim/data/pokemon.json', power=100):
    """Quantify where calc.py's hand-rolled formula diverges from the ROM, by
    sweeping a fixed neutral move (no STAB, no type effect) across every
    fully-evolved mon as attacker vs every other as defender and diffing the
    untruncated formula against the oracle. The only difference in play is the
    engine's 8-bit Attack/Defense truncation, so this measures exactly how much
    fidelity calc.py loses on high-stat mons. Returns (pairs, diffs, worst)."""
    import json
    from stats import mon_stats

    pokemon = json.load(open(pokemon_json))
    core = _get_core()
    mons = [(n, mon_stats(m['stats'])) for n, m in pokemon.items()
            if 'stats' in m and m.get('fully_evolved')]

    # oracle damage depends only on (atk, def) here, so cache by that pair.
    pairs = diffs = 0
    worst = (0, None)
    seen = {}
    for an, a in mons:
        for dn, d in mons:
            key = (a['atk'], d['defe'])
            if key not in seen:
                o = query_damage(a['atk'], d['defe'], power, 0, 0, core=core)
                f = _formula_no_truncate(a['atk'], d['defe'], power)
                seen[key] = (o, f)
            o, f = seen[key]
            pairs += 1
            if o != f:
                diffs += 1
                if abs(o - f) > worst[0]:
                    worst = (abs(o - f), (an, dn, o, f))
    return pairs, diffs, worst


if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('damage oracle self-test:')
        ok = self_test()
        print('\nfidelity check vs calc.py (100-BP neutral move, all FE pairs):')
        pairs, diffs, worst = validate_against_calc()
        pct = 100.0 * diffs / pairs if pairs else 0
        print(f'  {diffs}/{pairs} pairs ({pct:.1f}%) where calc.py != ROM '
              f'(cause: 8-bit Atk/Def truncation)')
        if worst[1]:
            an, dn, o, f = worst[1]
            print(f'  worst gap: {an} vs {dn} -> ROM {o}, calc.py {f} '
                  f'(off by {worst[0]})')
        sys.exit(0 if ok else 1)
    # ad-hoc: attack defense power type category
    a, d, p, t, cat = sys.argv[1:6]
    print(query_damage(int(a), int(d), int(p), t.upper(), cat.upper()))
