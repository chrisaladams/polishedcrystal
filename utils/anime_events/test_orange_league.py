#!/usr/bin/env python3
"""Check the Orange League in the running game (PyBoy), from a save:

- talking to each Orange Crew leader (Cissy, Danny, Rudy, Luana) starts a
  battle with their trainer class and the team in data/trainers/parties.asm;
  winning gives their badge (event flag);
- Drake won't battle until all four are beaten; then he battles with his
  team, and winning gives the Winner's Trophy and 3 Bottle Caps, once;
- afterwards each of them can be battled again.

The battles are won by setting the opposing team's HP to 0 in RAM, so this
checks the scripts, not the battles themselves.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_orange_league.py SAVE.sav
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_wild_mons import Game, rgbasm_values  # noqa: E402

LEADERS = (  # tag, map, where to stand, which way to face, class, badge flag
    ('Cissy', 'WARM_BEACH', 9, 22, 'up', 'CISSY_T', 'EVENT_BEAT_ORANGE_CREW_CISSY'),
    ('Danny', 'ROCKY_BEACH', 22, 27, 'right', 'DANNY_T', 'EVENT_BEAT_ORANGE_CREW_DANNY'),
    ('Rudy', 'BEAUTIFUL_BEACH', 16, 19, 'up', 'RUDY_T', 'EVENT_BEAT_ORANGE_CREW_RUDY'),
    ('Luana', 'VALENCIA_HOUSE', 5, 3, 'right', 'LUANA_T', 'EVENT_BEAT_ORANGE_CREW_LUANA'),
)
DRAKE = ('Drake', 'SHAMOUTI_HOUSE', 4, 2, 'up', 'DRAKE_T', 'EVENT_BEAT_DRAKE')


def expected_parties():
    """class -> [(level, species)] from data/trainers/parties.asm"""
    src = open(os.path.join(ROOT, 'data', 'trainers', 'parties.asm')).read()
    out = {}
    for m in re.finditer(r'def_trainer_class (\w+)\n\tdef_trainer 1, "\w+"\n(.*?)end_trainer', src, re.S):
        out[m.group(1)] = re.findall(r'tr_mon (\d+), (\w+)', m.group(2))
    return out


def main():
    save = open(sys.argv[1], 'rb').read()
    parties = expected_parties()
    species = sorted({sp for c, _, _, _, _, c2, _ in LEADERS + (DRAKE,) for _, sp in parties[c2]})
    names = species + ['PARTYMON_STRUCT_LENGTH', 'BOTTLE_CAP', 'EVENT_GOT_ORANGE_LEAGUE_PRIZE', 'EXTSPECIES_MASK']
    for leader in LEADERS + (DRAKE,):
        names += [leader[5], leader[6], 'GROUP_' + leader[1], 'MAP_' + leader[1]]
    K = rgbasm_values(names, None)
    L = K['PARTYMON_STRUCT_LENGTH']
    g = Game(save)
    g.boot()
    base = g.state()
    fails = []

    def flag(name):
        n = K[name]
        return (g.rd('wEventFlags', n // 8) >> (n % 8)) & 1

    def setflag(name):
        n = K[name]
        g.wr('wEventFlags', g.rd('wEventFlags', n // 8) | (1 << (n % 8)), n // 8)

    def bottle_caps():
        for i in range(g.rd('wNumItems')):
            if g.rd('wItems', 2 * i) == K['BOTTLE_CAP']:
                return g.rd('wItems', 2 * i + 1)
        return 0

    def talk(leader):
        tag, mp, x, y, facing, cls, ev = leader
        g.warp(K['GROUP_' + mp], K['MAP_' + mp], x, y)
        g.press(facing, 2, 3)
        g.tick(30)
        for _ in range(12):
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
        for _ in range(300):  # (the experience can mean levels and new moves)
            g.press('a', 30)
            if not g.rd('wBattleMode'):
                break
        for _ in range(20):  # the badge and hint texts (not a rematch: B, not A)
            g.tick(60)
            g.press('b', 10)

    def check_party(tag, cls):
        if g.rd('wOtherTrainerClass') != K[cls]:
            fails.append((tag, f'trainer class {g.rd("wOtherTrainerClass")}, not {cls}'))
        n = g.rd('wOTPartyCount')
        got = []
        for i in range(n):
            sp = g.rd('wOTPartyMon1Species', i * L)
            ext = g.rd('wOTPartyMon1Form', i * L) & K['EXTSPECIES_MASK']
            got.append((g.rd('wOTPartyMon1Level', i * L), sp | (0x100 if ext else 0)))
        want = [(int(lv), K[sp]) for lv, sp in parties[cls]]
        if got != want:
            fails.append((tag, f'team {got}, not {want}'))

    # each leader: battle, badge
    for leader in LEADERS:
        tag, cls, ev = leader[0], leader[5], leader[6]
        g.load(base)
        if not talk(leader):
            fails.append((tag, 'talking to them started no battle'))
            continue
        check_party(tag, cls)
        win()
        if g.rd('wBattleMode'):
            fails.append((tag, 'the battle did not end'))
        elif not flag(ev):
            fails.append((tag, 'no badge after winning'))
        if not talk(leader):
            fails.append((tag, 'no rematch'))

    # Drake: not before the four badges
    g.load(base)
    caps = bottle_caps()
    if talk(DRAKE):
        fails.append(('Drake', 'battled without the four badges'))
    g.load(base)
    for leader in LEADERS:
        setflag(leader[6])
    if not talk(DRAKE):
        fails.append(('Drake', 'no battle with the four badges'))
    else:
        check_party('Drake', 'DRAKE_T')
        win()
        if not flag('EVENT_BEAT_DRAKE') or not flag('EVENT_GOT_ORANGE_LEAGUE_PRIZE'):
            fails.append(('Drake', 'no trophy and prize after winning'))
        if bottle_caps() != caps + 3:
            fails.append(('Drake', f'Bottle Caps {caps} -> {bottle_caps()}, not +3'))
        if not talk(DRAKE):
            fails.append(('Drake', 'no rematch'))
        else:
            win()
            if bottle_caps() != caps + 3:
                fails.append(('Drake', 'gave the prize again'))

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
