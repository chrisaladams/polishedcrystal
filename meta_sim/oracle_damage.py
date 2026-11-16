#!/usr/bin/env python3
"""Ground-truth damage oracle: runs the ROM's real damage routines under PyBoy,
instead of reimplementing the damage formula by hand like calc.py does.

calc.py is a readable first-order model (formula + STAB + type chart + a flat
average roll). This oracle is the arbiter: it sets up a clean battle state in
WRAM and calls the real BattleCommand_damagecalc and BattleCommand_stab,
returning the exact damage the game would deal, so changes to calc.py can be
checked against ground truth instead of argued about.

How it works (mirroring AIDamageCalc, the engine's own damage predictor):
  - hBattleTurn = 1, so the *enemy* mon attacks and the *player* mon defends:
    attacker data goes in wEnemyMon*, defender data in wBattleMon*, and the move
    in wEnemyMoveStruct (GetBattleVar reads the enemy move on the enemy's turn).
  - Attack/Defense/Power/Level go straight into b/c/d/e, the documented inputs
    to BattleCommand_damagecalc, with TruncateHL_BC pre-applied here, so no
    party structs are needed.
  - Everything else that could move the number is neutralised: stat stages at
    BASE_STAT_LEVEL, no crit, no items, NO_ABILITY, no status, no weather, no
    screens, no Future Sight. What's left is the formula + STAB + types.
  - damagecalc never applies the 85-100% roll (DamageVariation is a separate
    step), so the result is deterministic: the maximum roll.

Addresses come from the .sym beside the ROM (via test/rom_harness.py).

Usage (from the repo root, after `make`):
    python3 meta_sim/oracle_damage.py                  # self-test + fidelity
    python3 meta_sim/oracle_damage.py 200 100 100 fire special
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from oracle import StatOracle  # noqa: E402  (also sets up the test/ import path)

BASE_STAT_LEVEL = 7     # neutral stat stage
NO_ABILITY = 0
TYPE_NEUTRAL = 0x10     # wTypeMatchup/wTypeModifier x1.0

# constants/type_constants.asm
TYPE_ID = {
    'NORMAL': 0, 'FIGHTING': 1, 'FLYING': 2, 'POISON': 3, 'GROUND': 4,
    'ROCK': 5, 'BUG': 6, 'GHOST': 7, 'STEEL': 8, 'FIRE': 9, 'WATER': 10,
    'GRASS': 11, 'ELECTRIC': 12, 'PSYCHIC': 13, 'ICE': 14, 'DRAGON': 15,
    'DARK': 16, 'FAIRY': 17,
}
UNKNOWN_TYPE = 0x12     # UNKNOWN_T: never grants STAB, not in the chart
CATEGORY_ID = {'PHYSICAL': 0, 'SPECIAL': 1, 'STATUS': 2}


def truncate_hl_bc(attack, defense):
    """The ROM's TruncateHL_BC: halve both 16-bit values in lockstep until each
    fits in 8 bits, never letting either reach 0."""
    hl, bc = attack, defense
    while (hl >> 8) | (bc >> 8):
        bc = max(bc >> 1, 1)
        hl = max(hl >> 1, 1)
    return hl & 0xff, bc & 0xff


class DamageOracle(StatOracle):
    def _neutralise(self):
        h, a = self.h, self.h.addr
        for i in range(8):
            h.mem[a('wPlayerStatLevels') + i] = BASE_STAT_LEVEL
            h.mem[a('wEnemyStatLevels') + i] = BASE_STAT_LEVEL
        for name in ('wBattleMonAbility', 'wEnemyMonAbility',
                     'wBattleMonItem', 'wEnemyMonItem',
                     'wBattleMonStatus', 'wEnemyMonStatus',
                     'wMoveHitState', 'wBattleWeather',
                     'wPlayerScreens', 'wEnemyScreens',
                     'wPlayerFutureSightCount', 'wEnemyFutureSightCount'):
            h.mem[a(name)] = 0
        for i in range(4):
            h.mem[a('wPlayerSubStatus1') + i] = 0
            h.mem[a('wEnemySubStatus1') + i] = 0
        h.mem[a('wTypeMatchup')] = TYPE_NEUTRAL
        h.mem[a('wTypeModifier')] = TYPE_NEUTRAL
        h.write16(a('wCurDamage'), 0)

    def damage(self, attack, defense, power, move_type, category,
               attacker_types=(UNKNOWN_TYPE, UNKNOWN_TYPE),
               defender_types=(UNKNOWN_TYPE, UNKNOWN_TYPE), level=50):
        """Exact max-roll damage for one hit (0 on immunity).

        attack/defense: the relevant 16-bit L50 stats (atk/def for PHYSICAL,
        spa/spd for SPECIAL); types and category may be names or ids."""
        def tid(t):
            return TYPE_ID[t.upper()] if isinstance(t, str) else t

        h, a = self.h, self.h.addr
        h.prepare()
        self._neutralise()
        cat = CATEGORY_ID[category.upper()] if isinstance(category, str) \
            else category
        h.mem[a('hBattleTurn')] = 1
        h.mem[a('wEnemyMoveStructAnimation')] = 1     # not STRUGGLE
        h.mem[a('wEnemyMoveStructEffect')] = 0        # EFFECT_NORMAL_HIT
        h.mem[a('wEnemyMoveStructPower')] = power
        h.mem[a('wEnemyMoveStructType')] = tid(move_type)
        h.mem[a('wEnemyMoveStructCategory')] = cat
        h.mem[a('wEnemyMonType1')] = tid(attacker_types[0])
        h.mem[a('wEnemyMonType2')] = tid(attacker_types[1])
        h.mem[a('wBattleMonType1')] = tid(defender_types[0])
        h.mem[a('wBattleMonType1') + 1] = tid(defender_types[1])

        b, c = truncate_hl_bc(attack, defense)
        self._run('BattleCommand_damagecalc', bc=(b << 8) | c,
                  de=(power << 8) | level)
        self._run('BattleCommand_stab')
        return h.read16(a('wCurDamage'))


# Hand-computed ROM-faithful values (power 100, atk 200, def 100, L50):
# base = ((2*50/5+2) * 100 * 200) / 100 / 50 + 2 = 90, then STAB/effectiveness.
_SELF_TEST = [
    (dict(attack=200, defense=100, power=100, move_type=0, category=0),
     90, 'base'),
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


def self_test(oracle):
    ok = True
    for kw, expected, label in _SELF_TEST:
        got = oracle.damage(**kw)
        ok &= got == expected
        flag = 'ok' if got == expected else 'MISMATCH'
        print(f'  [{flag}] {label}: got {got}, expected {expected}')
    return ok


def validate_against_calc(oracle, power=100,
                          pokemon_json=os.path.join(HERE, 'data',
                                                    'pokemon.json')):
    """Sweep a neutral 100-BP physical move across every fully-evolved
    attacker/defender pair and count where calc.py's formula differs from the
    ROM."""
    import calc
    from stats import mon_stats

    pokemon = json.load(open(pokemon_json))
    mons = [(n, mon_stats(m['stats'])) for n, m in pokemon.items()
            if 'stats' in m and m.get('fully_evolved')]
    pairs = diffs = 0
    worst = (0, None)
    seen = {}
    for an, at in mons:
        for dn, de in mons:
            key = (at['atk'], de['defe'])
            if key not in seen:
                seen[key] = (oracle.damage(key[0], key[1], power, 0, 0),
                             calc.base_damage(key[0], key[1], power))
            got, want = seen[key]
            pairs += 1
            if got != want:
                diffs += 1
                if abs(got - want) > worst[0]:
                    worst = (abs(got - want), (an, dn, got, want))
    return pairs, diffs, worst


def main():
    oracle = DamageOracle()
    try:
        if len(sys.argv) == 6:
            a, d, p, t, cat = sys.argv[1:6]
            print(oracle.damage(int(a), int(d), int(p), t, cat))
            return 0
        print('damage oracle self-test:')
        ok = self_test(oracle)
        print('\nfidelity check vs calc.py (100-BP neutral move, all FE pairs):')
        pairs, diffs, worst = validate_against_calc(oracle)
        pct = 100.0 * diffs / pairs if pairs else 0
        print(f'  {diffs}/{pairs} pairs ({pct:.2f}%) where calc.py != ROM')
        if worst[1]:
            an, dn, got, want = worst[1]
            print(f'  worst gap: {an} vs {dn} -> ROM {got}, calc.py {want} '
                  f'(off by {worst[0]})')
        return 0 if ok else 1
    finally:
        oracle.h.stop()


if __name__ == '__main__':
    sys.exit(main())
