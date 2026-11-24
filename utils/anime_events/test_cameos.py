#!/usr/bin/env python3
"""Check the anime cameos in the running game (PyBoy), from a save:

- before Red and the Orange League (Drake) are both beaten, none of them is
  there (with only one of them beaten, or the Elite Four and Drake, too);
- after both, each is there, and talking to them (yes to a battle) starts a
  battle with their trainer class and the team in data/trainers/parties.asm,
  which can be won and fought again.

The battles are won by setting the opposing team's HP to 0 in RAM.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_cameos.py SAVE.sav
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_wild_mons import Game, rgbasm_values  # noqa: E402

CAMEOS = (  # name, map, where they stand, where to stand to talk, which way to face, class
    ('Ash', 'PALLET_TOWN', (9, 12), (10, 12), 'left', 'ASH_T'),
    ('Tracey', 'OAKS_LAB', (8, 5), (8, 6), 'up', 'TRACEY_T'),
    ('Ritchie', 'SILVER_CAVE_OUTSIDE', (22, 15), (23, 15), 'left', 'RITCHIE_T'),
    ('Harrison', 'SILVER_CAVE_OUTSIDE', (25, 15), (24, 15), 'right', 'HARRISON_T'),
    ('Casey', 'NATIONAL_PARK', (23, 22), (24, 22), 'left', 'CASEY_T'),
)


def expected_parties():
    src = open(os.path.join(ROOT, 'data', 'trainers', 'parties.asm')).read()
    out = {}
    for m in re.finditer(r'def_trainer_class (\w+)\n\tdef_trainer 1, "\w+"\n(.*?)end_trainer', src, re.S):
        out[m.group(1)] = re.findall(r'tr_mon (\d+), (?:"\w+", )?(\w+)', m.group(2))
    return out


def main():
    save = open(sys.argv[1], 'rb').read()
    parties = expected_parties()
    species = sorted({sp for c in CAMEOS for _, sp in parties[c[5]]})
    names = species + ['PARTYMON_STRUCT_LENGTH', 'EXTSPECIES_MASK', 'EVENT_BEAT_ELITE_FOUR', 'EVENT_BEAT_DRAKE', 'EVENT_GOT_MYSTICTICKET_FROM_RED',
                       'EVENT_BEAT_RED', 'EVENT_BEAT_LEAF', 'EVENT_RESCUED_PROF_HALE',
                       'NUM_OBJECT_STRUCTS', 'OBJECT_LENGTH', 'OBJECT_MAP_X', 'OBJECT_MAP_Y', 'OBJECT_SPRITE']
    for c in CAMEOS:
        names += [c[5], 'GROUP_' + c[1], 'MAP_' + c[1]]
    K = rgbasm_values(names, None)
    L = K['PARTYMON_STRUCT_LENGTH']
    g = Game(save)
    g.boot()
    base = g.state()
    fails = []

    def setflag(name, on=True):
        n = K[name]
        v = g.rd('wEventFlags', n // 8)
        v = v | (1 << (n % 8)) if on else v & ~(1 << (n % 8))
        g.wr('wEventFlags', v, n // 8)

    def present(xy):
        for i in range(K['NUM_OBJECT_STRUCTS']):
            b = g.addr('wObjectStructs') + i * K['OBJECT_LENGTH']
            if (g.m[1, b + K['OBJECT_SPRITE']] and g.m[1, b + K['OBJECT_MAP_X']] == xy[0] + 4
                    and g.m[1, b + K['OBJECT_MAP_Y']] == xy[1] + 4):
                return True
        return False

    def visit(cameo, red, drake, e4=None):
        g.load(base)
        setflag('EVENT_BEAT_ELITE_FOUR', red if e4 is None else e4)
        setflag('EVENT_GOT_MYSTICTICKET_FROM_RED', red)
        # Leaf clears the rematch flag; it must not hide any cameo.
        setflag('EVENT_BEAT_RED', False)
        setflag('EVENT_BEAT_LEAF', red)
        setflag('EVENT_BEAT_DRAKE', drake)
        setflag('EVENT_RESCUED_PROF_HALE', False)  # Ash offers the friendly match here
        g.warp(K['GROUP_' + cameo[1]], K['MAP_' + cameo[1]], *cameo[3])
        g.tick(30)
        return present(cameo[2])

    def talk(facing):
        g.face(facing)
        g.tick(30)
        for _ in range(14):
            g.press('a', 40)
            if g.rd('wBattleMode'):
                break
        for _ in range(300):
            if g.rd('wBattleMode'):
                return True
            g.tick(2)
        return False

    def win():
        g.tick(400)
        for i in range(g.rd('wOTPartyCount')):
            g.wr('wOTPartyMon1HP', 0, i * L)
            g.wr('wOTPartyMon1HP', 0, i * L + 1)
        g.wr('wEnemyMonHP', 0)
        g.wr('wEnemyMonHP', 1, 1)
        g.wr('wBattleMonHP', 3)
        g.wr('wBattleMonHP', 0xe7, 1)
        for _ in range(300):
            g.press('a', 30)
            if not g.rd('wBattleMode'):
                break
        for _ in range(8):
            g.tick(60)
            g.press('b', 10)

    for cameo in CAMEOS:
        name, cls = cameo[0], cameo[5]
        if visit(cameo, False, False):
            fails.append((name, 'there before Red and Drake'))
        if visit(cameo, True, False):
            fails.append((name, 'there before the Orange League'))
        if visit(cameo, False, True):
            fails.append((name, 'there before Red'))
        if visit(cameo, False, True, e4=True):
            fails.append((name, 'there after the Elite Four and Drake, before Red'))
        if not visit(cameo, True, True):
            fails.append((name, 'not there after Red and Drake'))
            continue
        if not talk(cameo[4]):
            fails.append((name, 'no battle'))
            continue
        if g.rd('wOtherTrainerClass') != K[cls]:
            fails.append((name, f'trainer class {g.rd("wOtherTrainerClass")}, not {cls}'))
        got = []
        for i in range(g.rd('wOTPartyCount')):
            sp = g.rd('wOTPartyMon1Species', i * L)
            ext = g.rd('wOTPartyMon1Form', i * L) & K['EXTSPECIES_MASK']
            got.append((g.rd('wOTPartyMon1Level', i * L), sp | (0x100 if ext else 0)))
        want = [(int(lv), K[sp]) for lv, sp in parties[cls]]
        if got != want:
            fails.append((name, f'team {got}, not {want}'))
        win()
        if g.rd('wBattleMode'):
            fails.append((name, 'the battle did not end'))
        elif not talk(cameo[4]):
            fails.append((name, 'no battle again afterwards'))

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
