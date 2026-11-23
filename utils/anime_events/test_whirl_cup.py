#!/usr/bin/env python3
"""Check the Whirl Cup in the running game (PyBoy), from a save:

- the official at Olivine Port is there only after Red;
- he turns away a party
  that isn't all Water-type;
- with an all-Water party, the three rounds are Swimmer Trinity, Sailor
  Jasper and Misty, with the teams in data/trainers/parties.asm;
- winning all three gives the Mystic Water the first time and a Bottle Cap
  each time after;
- losing a round ends the run with the party healed, without blacking out.

The battles are won (or lost) by setting HP in RAM.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_whirl_cup.py SAVE.sav
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_wild_mons import Game, rgbasm_values  # noqa: E402

ROUNDS = (('SWIMMERF', 33), ('SAILOR', 17), ('MISTY', 3))


def expected_party(cls, n):
    src = open(os.path.join(ROOT, 'data', 'trainers', 'parties.asm')).read()
    group = src[src.index(f'\tdef_trainer_class {cls}\n'):]
    group = group[:group.index('end_trainer', group.index(f'\tdef_trainer {n}, '))]
    group = group[group.index(f'\tdef_trainer {n}, '):]
    return re.findall(r'tr_mon (\d+), (\w+)', group)


def main():
    save = open(sys.argv[1], 'rb').read()
    parties = {r: expected_party(*r) for r in ROUNDS}
    species = sorted({sp for p in parties.values() for _, sp in p} | {'SQUIRTLE'})
    names = species + [c for c, _ in ROUNDS] + [
        'PARTYMON_STRUCT_LENGTH', 'EXTSPECIES_MASK', 'GROUP_OLIVINE_PORT', 'MAP_OLIVINE_PORT',
        'EVENT_OLIVINE_PORT_SPRITES_AFTER_HALL_OF_FAME', 'EVENT_WON_WHIRL_CUP', 'EVENT_BEAT_RED',
        'NUM_OBJECT_STRUCTS', 'OBJECT_LENGTH', 'OBJECT_MAP_X', 'OBJECT_MAP_Y', 'OBJECT_SPRITE', 'MYSTIC_WATER', 'BOTTLE_CAP']
    K = rgbasm_values(names, None)
    L = K['PARTYMON_STRUCT_LENGTH']
    g = Game(save)
    g.boot()
    fails = []

    def flag(name, value=None):
        n = K[name]
        v = g.rd('wEventFlags', n // 8)
        if value is None:
            return (v >> (n % 8)) & 1
        g.wr('wEventFlags', v | (1 << (n % 8)) if value else v & ~(1 << (n % 8)), n // 8)

    def items(item):
        for i in range(g.rd('wNumItems')):
            if g.rd('wItems', 2 * i) == K[item]:
                return g.rd('wItems', 2 * i + 1)
        return 0

    flag('EVENT_OLIVINE_PORT_SPRITES_AFTER_HALL_OF_FAME', False)  # after the Hall of Fame

    def official_there():
        for i in range(K['NUM_OBJECT_STRUCTS']):
            b = g.addr('wObjectStructs') + i * K['OBJECT_LENGTH']
            if (g.m[1, b + K['OBJECT_SPRITE']] and g.m[1, b + K['OBJECT_MAP_X']] == 13 + 4
                    and g.m[1, b + K['OBJECT_MAP_Y']] == 7 + 4):
                return True
        return False

    flag('EVENT_BEAT_RED', False)
    g.warp(K['GROUP_OLIVINE_PORT'], K['MAP_OLIVINE_PORT'], 13, 8)
    if official_there():
        fails.append(('before Red', 'the official is there'))
    flag('EVENT_BEAT_RED', True)
    base = g.state()

    def talk():
        g.warp(K['GROUP_OLIVINE_PORT'], K['MAP_OLIVINE_PORT'], 13, 8)
        if not official_there():
            fails.append(('after Red', 'the official is not there'))
        g.press('up', 2, 3)
        g.tick(30)

    def until_battle(presses=20):
        for _ in range(presses):
            g.press('a', 40)
            if g.rd('wBattleMode'):
                break
        for _ in range(200):
            if g.rd('wBattleMode'):
                return True
            g.tick(2)
        return False

    def finish(win):
        g.tick(400)
        if win:
            for i in range(g.rd('wOTPartyCount')):
                g.wr('wOTPartyMon1HP', 0, i * L)
                g.wr('wOTPartyMon1HP', 0, i * L + 1)
            g.wr('wEnemyMonHP', 0)
            g.wr('wEnemyMonHP', 1, 1)
            g.wr('wBattleMonHP', 3)
            g.wr('wBattleMonHP', 0xe7, 1)
        else:
            for i in range(g.rd('wPartyCount')):
                g.wr('wPartyMon1HP', 0, i * L)
                g.wr('wPartyMon1HP', 0, i * L + 1)
            g.wr('wBattleMonHP', 0)
            g.wr('wBattleMonHP', 1, 1)
            g.wr('wEnemyMonHP', 3)
            g.wr('wEnemyMonHP', 0xe7, 1)
        for _ in range(300):
            g.press('a', 30)
            if not g.rd('wBattleMode'):
                break

    def settle():
        # through the last texts (and any evolution): B clears text, and
        # can't talk to him again
        for _ in range(120):
            g.tick(30)
            g.press('b', 10)
            if not g.rd('wScriptRunning') and not g.rd('wBattleMode'):
                g.tick(60)
                if not g.rd('wScriptRunning'):
                    return

    def check_round(r):
        cls, n = r
        if g.rd('wOtherTrainerClass') != K[cls] or g.rd('wOtherTrainerID') != n:
            fails.append((f'{cls} {n}', f'battled class {g.rd("wOtherTrainerClass")} #{g.rd("wOtherTrainerID")}'))
        got = []
        for i in range(g.rd('wOTPartyCount')):
            sp = g.rd('wOTPartyMon1Species', i * L)
            ext = g.rd('wOTPartyMon1Form', i * L) & K['EXTSPECIES_MASK']
            got.append((g.rd('wOTPartyMon1Level', i * L), sp | (0x100 if ext else 0)))
        want = [(int(lv), K[sp]) for lv, sp in parties[r]]
        if got != want:
            fails.append((f'{cls} {n}', f'team {got}, not {want}'))

    # not all Water-type: turned away
    g.load(base)
    talk()
    if until_battle(12):
        fails.append(('entry', 'a party that is not all Water-type was let in'))

    # all Water-type: three rounds, then the prize
    def water_party():
        for i in range(g.rd('wPartyCount')):
            g.wr('wPartyMon1Species', K['SQUIRTLE'], i * L)

    def run_cup(expect_item, before):
        talk()

        for k, r in enumerate(ROUNDS):
            if not until_battle(30):
                fails.append((f'the cup (for the {expect_item})', f'round {k + 1} did not start'))
                return
            check_round(r)
            finish(True)
        settle()
        if items(expect_item) != before + 1:
            fails.append(('the cup', f'{expect_item}: {before} -> {items(expect_item)}, not +1'))

    g.load(base)
    water_party()
    run_cup('MYSTIC_WATER', items('MYSTIC_WATER'))
    if not flag('EVENT_WON_WHIRL_CUP'):
        fails.append(('the cup', 'the win was not recorded'))
    run_cup('BOTTLE_CAP', items('BOTTLE_CAP'))

    # losing round one
    g.load(base)
    water_party()
    talk()
    if until_battle():
        finish(False)
        settle()
        if (g.rd('wMapGroup'), g.rd('wMapNumber')) != (K['GROUP_OLIVINE_PORT'], K['MAP_OLIVINE_PORT']):
            fails.append(('losing', 'blacked out (left Olivine Port)'))
        if not all(g.rd('wPartyMon1HP', i * L) or g.rd('wPartyMon1HP', i * L + 1)
                   for i in range(g.rd('wPartyCount'))):
            fails.append(('losing', 'the party was not healed'))
    else:
        fails.append(('losing', 'round one did not start'))

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
