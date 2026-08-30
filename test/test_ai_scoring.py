#!/usr/bin/env python3
"""Tests for the battle AI's scoring helpers, run against the built ROM.

Each case executes the real assembled routine under PyBoy rather than
reimplementing its arithmetic in Python, so the test fails if the asm is wrong
even when the intent was right.

Run via `make test`, or directly with `python3 test/test_ai_scoring.py` once a
ROM has been built.
"""

import sys

from rom_harness import Harness, STRUCT, find_build, load_symbols

BASE_AI_SWITCH_SCORE = 10


def test_damage_scaled_by_accuracy(h, report):
    """AIScaleDamageByAccuracy turns raw damage into expected damage.

    Accuracy is stored 0-100, with 255 meaning "ignores accuracy checks"; both
    100 and 255 must leave the damage untouched.
    """
    cases = [
        # (damage, accuracy, expected)
        (100, 100, 100),
        (100, 255, 100),   # always-hit moves are not penalised
        (100,  90,  90),
        (100,  80,  80),
        (100,  70,  70),
        (200,  70, 140),
        (255,  85, 216),
        (1000, 70, 700),   # 16-bit damage
        (300,  50, 150),
        (0,    70,   0),   # no damage stays no damage
    ]
    acc_addr = h.addr('wEnemyMoveStruct') + h.offset('wEnemyMoveStruct',
                                                     'wEnemyMoveStructAccuracy')
    dmg_addr = h.addr('wCurDamage')

    for damage, accuracy, expected in cases:
        h.write16(dmg_addr, damage)
        h.mem[acc_addr] = accuracy
        h.call('AIScaleDamageByAccuracy')
        got = h.read16(dmg_addr)
        report(got == expected,
               f'damage {damage:4d} at {accuracy:3d}% accuracy -> {got} '
               f'(expected {expected})')


def test_switch_score_drops_with_hp(h, report):
    """AIApplyHPToSwitchScore penalises nearly-fainted switch-in candidates.

    -1 below half HP, -2 below a quarter. The boundaries matter: the routine
    compares 2*HP and 4*HP against max HP with 16-bit arithmetic, which is easy
    to get wrong by one, and 4*HP must not overflow.
    """
    cases = [
        # (hp, max_hp, expected score)
        (100, 100, 10),   # full
        ( 51, 100, 10),   # just above half
        ( 50, 100, 10),   # exactly half -> no penalty
        ( 49, 100,  9),   # just below half
        ( 25, 100,  9),   # exactly a quarter -> half penalty only
        ( 24, 100,  8),   # just below a quarter
        (  1, 100,  8),   # nearly fainted
        (350, 700, 10),   # exact half, larger pool
        (200, 700,  9),
        (174, 700,  8),
        (999, 999, 10),   # 4 * HP must not overflow 16 bits
        (200, 999,  8),
    ]
    hp_off = h.offset('wPartyMon1', 'wPartyMon1HP')
    max_off = h.offset('wPartyMon1', 'wPartyMon1MaxHP')

    for hp, max_hp, expected in cases:
        h.write16(STRUCT + hp_off, hp)
        h.write16(STRUCT + max_off, max_hp)
        got = h.call('AIApplyHPToSwitchScore', a=BASE_AI_SWITCH_SCORE, hl=STRUCT)
        report(got == expected,
               f'{hp:4d}/{max_hp:4d} HP ({100 * hp // max_hp:3d}%) -> score '
               f'{got} (expected {expected})')


TESTS = [
    test_damage_scaled_by_accuracy,
    test_switch_score_drops_with_hp,
]


def main():
    rom, sym = find_build()
    print(f'ROM: {rom}')
    harness = Harness(rom, load_symbols(sym))
    failures = []

    try:
        for test in TESTS:
            print(f'\n{test.__name__}')
            def report(ok, message, _test=test):
                print(f'  {"ok  " if ok else "FAIL"} {message}')
                if not ok:
                    failures.append(f'{_test.__name__}: {message}')
            test(harness, report)
    finally:
        harness.stop()

    if failures:
        print(f'\n{len(failures)} failure(s):')
        for failure in failures:
            print(f'  {failure}')
        return 1
    print('\nAll cases passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
