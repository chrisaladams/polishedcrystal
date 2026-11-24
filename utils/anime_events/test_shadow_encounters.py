#!/usr/bin/env python3
"""Check the movie stories' battles you can't catch from, in the emulator:

- Celebi: Voice of the Forest: while the Iron Mask Marauder waits in Ilex
  Forest (after Red and the time travel), three forest Pokemon his black
  ball holds stand by the shrine (Beedrill, Ariados, Noctowl); none before
  the time travel or after he's beaten;
- Spell of the Unown: after Molly's battle and until Prof. Hale is free, two
  of the Unown's illusions (Teddiursa, Phanpy) guard the statue in the Ruins
  of Alph's inner chamber; none before her battle or after the rescue;
- each starts a wild battle of the type no ball can catch (BATTLETYPE_SHADOW)
  with that Pokemon at its level; beaten, it's gone, and back when you come
  back while the story still needs it.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_shadow_encounters.py SAVE.sav
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_wild_mons import Game, rgbasm_values  # noqa: E402

# name, map, where it stands, where to talk from, facing, species, level
ILEX = (('Beedrill', (8, 25), (8, 26), 'up', 'BEEDRILL', 64),
        ('Ariados', (9, 25), (9, 26), 'up', 'ARIADOS', 65),
        ('Noctowl', (11, 26), (10, 26), 'right', 'NOCTOWL', 66))
ALPH = (('Teddiursa', (4, 14), (3, 14), 'right', 'TEDDIURSA', 62),
        ('Phanpy', (6, 14), (7, 14), 'left', 'PHANPY', 62))


def main():
    save = open(sys.argv[1], 'rb').read()
    species = sorted({s[4] for s in ILEX + ALPH})
    K = rgbasm_values(species + [
        'GROUP_ILEX_FOREST', 'MAP_ILEX_FOREST', 'GROUP_RUINS_OF_ALPH_INNER_CHAMBER',
        'MAP_RUINS_OF_ALPH_INNER_CHAMBER', 'EVENT_GOT_MYSTICTICKET_FROM_RED', 'EVENT_TIME_TRAVEL_FINISHED',
        'EVENT_BEAT_IRON_MASK_MARAUDER', 'EVENT_BEAT_MOLLY', 'EVENT_RESCUED_PROF_HALE', 'BATTLETYPE_SHADOW',
        'NUM_OBJECT_STRUCTS', 'OBJECT_LENGTH', 'OBJECT_MAP_X', 'OBJECT_MAP_Y', 'OBJECT_SPRITE',
        'PARTYMON_STRUCT_LENGTH'], None)
    g = Game(save)
    g.boot()
    fails = []

    def flag(name, value):
        n = K[name]
        v = g.rd('wEventFlags', n // 8)
        g.wr('wEventFlags', v | (1 << (n % 8)) if value else v & ~(1 << (n % 8)), n // 8)

    def present(xy):
        for i in range(K['NUM_OBJECT_STRUCTS']):
            b = g.addr('wObjectStructs') + i * K['OBJECT_LENGTH']
            if (g.m[1, b + K['OBJECT_SPRITE']] and g.m[1, b + K['OBJECT_MAP_X']] == xy[0] + 4
                    and g.m[1, b + K['OBJECT_MAP_Y']] == xy[1] + 4):
                return True
        return False

    def visit(mp, xy):
        g.warp(K['GROUP_' + mp], K['MAP_' + mp], *xy)
        g.tick(30)

    def battle(facing):
        g.press(facing, 2, 3)
        g.tick(20)
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
        # (keep yours standing: the test save's team is far weaker)
        g.tick(300)
        # (and through the many level-ups a weak team gets for winning)
        for i in range(1500):
            if i < 20:
                g.wr('wEnemyMonHP', 0)
                g.wr('wEnemyMonHP', 1, 1)
                g.wr('wBattleMonHP', 3)
                g.wr('wBattleMonHP', 0xe7, 1)
                g.wr('wEnemyMonSpeed', 0)  # (you move first)
                g.wr('wEnemyMonSpeed', 1, 1)
            g.press('a', 20)
            if not g.rd('wBattleMode'):
                break
        for _ in range(10):
            g.tick(40)
            g.press('b', 10)

    base = g.state()

    def run(story, mp, mons, shown, hidden_cases):
        # not there outside the story's window
        for why, flags in hidden_cases:
            g.load(base)
            for f, v in flags:
                flag(f, v)
            visit(mp, mons[0][2])
            for m in mons:
                if present(m[1]):
                    fails.append((story, f'{m[0]} is there {why}'))
        # there in it, and each battles as one you can't catch
        for m in mons:
            g.load(base)
            for f, v in shown:
                flag(f, v)
            visit(mp, m[2])
            others = [o for o in mons if o is not m]
            if not all(present(o[1]) for o in mons):
                fails.append((story, f'not all there: {[o[0] for o in mons if not present(o[1])]}'))
                continue
            if not battle(m[3]):
                fails.append((story, f'{m[0]}: no battle'))
                continue
            got = (g.rd('wBattleType'), g.rd('wTempEnemyMonSpecies'), g.rd('wCurPartyLevel'))
            want = (K['BATTLETYPE_SHADOW'], K[m[4]], m[5])
            if got != want:
                fails.append((story, f'{m[0]}: battle (type, species, level) {got}, not {want}'))
            win()
            if g.rd('wBattleMode'):
                fails.append((story, f'{m[0]}: the battle did not end'))
                continue
            if present(m[1]):
                fails.append((story, f'{m[0]} still there after the battle'))
            if not all(present(o[1]) for o in others):
                fails.append((story, f'beating {m[0]} took away another'))
            visit(mp, m[2])
            if not present(m[1]):
                fails.append((story, f'{m[0]} not back after coming back'))

    run('Ilex Forest', 'ILEX_FOREST', ILEX,
        [('EVENT_GOT_MYSTICTICKET_FROM_RED', True), ('EVENT_TIME_TRAVEL_FINISHED', True),
         ('EVENT_BEAT_IRON_MASK_MARAUDER', False)],
        [('before Red', [('EVENT_GOT_MYSTICTICKET_FROM_RED', False), ('EVENT_TIME_TRAVEL_FINISHED', True)]),
         ('before the time travel', [('EVENT_GOT_MYSTICTICKET_FROM_RED', True),
                                     ('EVENT_TIME_TRAVEL_FINISHED', False)]),
         ('after the Marauder', [('EVENT_GOT_MYSTICTICKET_FROM_RED', True), ('EVENT_TIME_TRAVEL_FINISHED', True),
                                 ('EVENT_BEAT_IRON_MASK_MARAUDER', True)])])
    run('Ruins of Alph', 'RUINS_OF_ALPH_INNER_CHAMBER', ALPH,
        [('EVENT_GOT_MYSTICTICKET_FROM_RED', True), ('EVENT_BEAT_MOLLY', True),
         ('EVENT_RESCUED_PROF_HALE', False)],
        [('before Molly', [('EVENT_GOT_MYSTICTICKET_FROM_RED', True), ('EVENT_BEAT_MOLLY', False)]),
         ('after the rescue', [('EVENT_GOT_MYSTICTICKET_FROM_RED', True), ('EVENT_BEAT_MOLLY', True),
                               ('EVENT_RESCUED_PROF_HALE', True)])])

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
