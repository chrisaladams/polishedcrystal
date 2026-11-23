#!/usr/bin/env python3
"""Check the movie events in the running game (PyBoy), from a save:

- Spell of the Unown: Molly is in the Ruins of Alph Research Center only after
  Red (not just the Elite Four); her battle (Lass Molly) has the team in
  data/trainers/parties.asm; the first win gives an Ability Patch, and she can
  be battled again without giving another;
- Celebi: Voice of the Forest: the Iron Mask Marauder is by the Ilex Forest
  shrine only after Red and the time travel (not after just one); his battle has his team; winning gives a
  Big Nugget and he's gone for good;
- Mewtwo Strikes Back: before Red, talking to Mewtwo in Cerulean Cave starts
  the plain Mewtwo battle; after Red, a battle with its clones (Psychic Mewtwo): copies of your own team (not eggs; same
  species, level, item, moves and stats) at full HP with no status, even when
  yours are hurt; then the wild Mewtwo battle (level 80).

The battles are won by setting the opposing team's HP to 0 in RAM.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_movie_events.py SAVE.sav [SCREENSHOT_DIR]
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_wild_mons import Game, rgbasm_values  # noqa: E402

# name, map, where they stand, where to stand to talk, which way to face,
# class, trainer number (or its constant), prize
EVENTS = (
    ('Molly', 'RUINS_OF_ALPH_RESEARCH_CENTER', (2, 2), (2, 3), 'up', 'LASS', 'MOLLY_HALE', 'ABILITYPATCH'),
    ('Marauder', 'ILEX_FOREST', (11, 25), (12, 25), 'left', 'IRON_MASK_T', '1', 'BIG_NUGGET'),
    ('Mewtwo', 'CERULEAN_CAVE_B1F', (7, 13), (7, 14), 'up', 'MEWTWO_T', '1', None),
)


def expected_party(cls, n):
    src = open(os.path.join(ROOT, 'data', 'trainers', 'parties.asm')).read()
    group = src[src.index(f'\tdef_trainer_class {cls}\n'):]
    start = group.index(f'\tdef_trainer {n}, ')
    group = group[start:group.index('end_trainer', start)]
    return re.findall(r'tr_mon (\d+), (?:"\w+", )?(\w+)', group)


def main():
    save = open(sys.argv[1], 'rb').read()
    shots = sys.argv[2] if len(sys.argv) > 2 else None
    parties = {e[0]: expected_party(e[5], e[6]) for e in EVENTS if e[0] != 'Mewtwo'}
    species = sorted({sp for p in parties.values() for _, sp in p} | {'MEWTWO'})
    names = species + ['PARTYMON_STRUCT_LENGTH', 'EXTSPECIES_MASK', 'NUM_OBJECT_STRUCTS', 'OBJECT_LENGTH',
                       'OBJECT_MAP_X', 'OBJECT_MAP_Y', 'OBJECT_SPRITE', 'MOLLY_HALE', 'EVENT_BEAT_ELITE_FOUR',
                       'EVENT_TIME_TRAVEL_FINISHED', 'EVENT_BEAT_RED', 'EVENT_BEAT_MOLLY', 'EVENT_BEAT_IRON_MASK_MARAUDER',
                       'EVENT_CERULEAN_CAVE_MEWTWO', 'ABILITYPATCH', 'BIG_NUGGET', 'WILD_BATTLE',
                       'MON_SPECIES', 'MON_ITEM', 'MON_MOVES', 'MON_LEVEL', 'MON_FORM', 'MON_IS_EGG_F',
                       'MON_STATUS', 'MON_HP', 'MON_MAXHP', 'MON_STATS', 'MON_DVS', 'MON_EVS']
    for e in EVENTS:
        names += [e[5], 'GROUP_' + e[1], 'MAP_' + e[1]]
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

    def present(xy):
        for i in range(K['NUM_OBJECT_STRUCTS']):
            b = g.addr('wObjectStructs') + i * K['OBJECT_LENGTH']
            if (g.m[1, b + K['OBJECT_SPRITE']] and g.m[1, b + K['OBJECT_MAP_X']] == xy[0] + 4
                    and g.m[1, b + K['OBJECT_MAP_Y']] == xy[1] + 4):
                return True
        return False

    flag('EVENT_BEAT_ELITE_FOUR', True)
    flag('EVENT_BEAT_RED', False)
    flag('EVENT_TIME_TRAVEL_FINISHED', False)
    for f in ('EVENT_BEAT_MOLLY', 'EVENT_BEAT_IRON_MASK_MARAUDER', 'EVENT_CERULEAN_CAVE_MEWTWO'):
        flag(f, False)
    base = g.state()

    def visit(ev):
        g.warp(K['GROUP_' + ev[1]], K['MAP_' + ev[1]], *ev[3])
        g.tick(30)
        return present(ev[2])

    def until_battle(facing, presses=24):
        g.press(facing, 2, 3)
        g.tick(30)
        for _ in range(presses):
            g.press('a', 40)
            if g.rd('wBattleMode'):
                break
        for _ in range(300):
            if g.rd('wBattleMode'):
                return True
            g.tick(2)
        return False

    def mon(prefix, i, field, n=1):
        b = g.addr(prefix) + i * L + K[field]
        return tuple(g.m[1, b + k] for k in range(n))

    def check_clones():
        # each non-egg mon of yours, field by field
        mine = [i for i in range(g.rd('wPartyCount'))
                if not (mon('wPartyMon1', i, 'MON_FORM')[0] >> K['MON_IS_EGG_F']) & 1]
        if g.rd('wOTPartyCount') != len(mine):
            fails.append(('Mewtwo', f'{g.rd("wOTPartyCount")} clones for {len(mine)} of yours'))
            return
        fields = (('MON_SPECIES', 1), ('MON_FORM', 1), ('MON_ITEM', 1), ('MON_MOVES', 4), ('MON_LEVEL', 1),
                  ('MON_DVS', 3), ('MON_EVS', 6), ('MON_MAXHP', 2), ('MON_STATS', 10))
        for k, i in enumerate(mine):
            for f, n in fields:
                if mon('wOTPartyMon1', k, f, n) != mon('wPartyMon1', i, f, n):
                    fails.append(('Mewtwo', f'clone {k + 1} {f} {mon("wOTPartyMon1", k, f, n)}, '
                                            f'not {mon("wPartyMon1", i, f, n)}'))
            if mon('wOTPartyMon1', k, 'MON_HP', 2) != mon('wOTPartyMon1', k, 'MON_MAXHP', 2):
                fails.append(('Mewtwo', f'clone {k + 1} is not at full HP'))
            if mon('wOTPartyMon1', k, 'MON_STATUS')[0]:
                fails.append(('Mewtwo', f'clone {k + 1} has a status'))

    def check_trainer(ev):
        name, cls, n = ev[0], ev[5], ev[6]
        n = K[n] if n in K else int(n)
        if g.rd('wOtherTrainerClass') != K[cls] or g.rd('wOtherTrainerID') != n:
            fails.append((name, f'battled class {g.rd("wOtherTrainerClass")} #{g.rd("wOtherTrainerID")}, '
                                f'not {cls} #{n}'))
        got, want = [], [(int(lv), K[sp]) for lv, sp in parties.get(name, [])]
        for i in range(g.rd('wOTPartyCount')):
            sp = g.rd('wOTPartyMon1Species', i * L)
            ext = g.rd('wOTPartyMon1Form', i * L) & K['EXTSPECIES_MASK']
            got.append((g.rd('wOTPartyMon1Level', i * L), sp | (0x100 if ext else 0)))
        if name == 'Mewtwo':
            check_clones()
        elif got != want:
            fails.append((name, f'team {got}, not {want}'))

    def win(shot=None):
        g.tick(400)
        if shot and shots:
            g.pb.tick(1, True)
            g.pb.screen.image.save(os.path.join(shots, shot))
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

    def settle():
        for _ in range(120):
            g.tick(30)
            g.press('b', 10)
            if not g.rd('wScriptRunning') and not g.rd('wBattleMode'):
                g.tick(60)
                if not g.rd('wScriptRunning'):
                    return

    # Molly
    molly, marauder, mewtwo = EVENTS
    g.load(base)
    if visit(molly):
        fails.append(('Molly', 'there before Red'))
    g.load(base)
    flag('EVENT_BEAT_RED', True)
    if not visit(molly):
        fails.append(('Molly', 'not there after Red'))
    elif not until_battle(molly[4]):
        fails.append(('Molly', 'no battle'))
    else:
        check_trainer(molly)
        before = items('ABILITYPATCH')
        win('molly.png')
        settle()
        if items('ABILITYPATCH') != before + 1:
            fails.append(('Molly', f'Ability Patch {before} -> {items("ABILITYPATCH")}, not +1'))
        if not flag('EVENT_BEAT_MOLLY'):
            fails.append(('Molly', 'the win was not recorded'))
        if not until_battle(molly[4]):
            fails.append(('Molly', 'no battle again afterwards'))
        else:
            win()
            settle()
            if items('ABILITYPATCH') != before + 1:
                fails.append(('Molly', 'gave a second Ability Patch'))

    # the Iron Mask Marauder
    g.load(base)
    flag('EVENT_BEAT_RED', True)
    if visit(marauder):
        fails.append(('Marauder', 'there before the time travel'))
    g.load(base)
    flag('EVENT_TIME_TRAVEL_FINISHED', True)
    if visit(marauder):
        fails.append(('Marauder', 'there before Red'))
    g.load(base)
    flag('EVENT_BEAT_RED', True)
    flag('EVENT_TIME_TRAVEL_FINISHED', True)
    if not visit(marauder):
        fails.append(('Marauder', 'not there after the time travel'))
    elif not until_battle(marauder[4]):
        fails.append(('Marauder', 'no battle'))
    else:
        check_trainer(marauder)
        before = items('BIG_NUGGET')
        win('marauder.png')
        settle()
        if items('BIG_NUGGET') != before + 1:
            fails.append(('Marauder', f'Big Nugget {before} -> {items("BIG_NUGGET")}, not +1'))
        if not flag('EVENT_BEAT_IRON_MASK_MARAUDER'):
            fails.append(('Marauder', 'the win was not recorded'))
        if present(marauder[2]):
            fails.append(('Marauder', 'still there after losing'))
        if visit(marauder):
            fails.append(('Marauder', 'back after leaving and returning'))

    # before Red: just Mewtwo
    g.load(base)
    if not visit(mewtwo):
        fails.append(('Mewtwo', 'not there before Red'))
    elif not until_battle(mewtwo[4]):
        fails.append(('Mewtwo', 'no battle before Red'))
    elif g.rd('wBattleMode') != K['WILD_BATTLE']:
        fails.append(('Mewtwo', 'a clone battle before Red'))

    # Mewtwo and its clones (of your team, hurt and poisoned first)
    g.load(base)
    flag('EVENT_BEAT_RED', True)
    g.wr('wPartyMon1HP', 0)
    g.wr('wPartyMon1HP', 1, 1)
    g.wr('wPartyMon1Status', 1 << 3)
    if not visit(mewtwo):
        fails.append(('Mewtwo', 'not there'))
    elif not until_battle(mewtwo[4]):
        fails.append(('Mewtwo', 'no clone battle'))
    else:
        check_trainer(mewtwo)
        win('clones.png')
        # then the wild battle with Mewtwo itself
        for _ in range(40):
            if g.rd('wBattleMode'):
                break
            g.press('a', 40)
        for _ in range(300):
            if g.rd('wBattleMode'):
                break
            g.tick(2)
        if g.rd('wBattleMode') != K['WILD_BATTLE']:
            fails.append(('Mewtwo', f'no wild battle after the clones (battle mode {g.rd("wBattleMode")})'))
        else:
            g.tick(400)
            if shots:
                g.pb.tick(1, True)
                g.pb.screen.image.save(os.path.join(shots, 'mewtwo.png'))
            got = (g.rd('wEnemyMonSpecies'), g.rd('wEnemyMonLevel'))
            if got != (K['MEWTWO'], 80):
                fails.append(('Mewtwo', f'wild battle with species {got[0]} level {got[1]}, not Mewtwo 80'))

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
