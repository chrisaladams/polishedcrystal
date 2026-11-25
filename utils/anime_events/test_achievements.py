#!/usr/bin/env python3
"""Check the bedroom achievements in the running game (PyBoy), from a save:

- the Orange Trophy is among your decorations once Drake is beaten, and the
  Cup Trophy once you've won any cup (and neither before);
- set out in the bedroom, the Cup Trophy is bronze for one or two cups,
  silver for three to five and gold for all six, and says how many;
- the Adventure Album (the bedroom PC's "Album") stars what's done on its
  Leagues, Stories and Cups pages, with counts for the badges, the Orange
  Crew and the Kimono Cup's types.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_achievements.py SAVE.sav
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_wild_mons import Game, rgbasm_values  # noqa: E402

STAR, DASH = 0xec, 0xbc


def main():
    save = open(sys.argv[1], 'rb').read()
    K = rgbasm_values([
        'GROUP_PLAYERS_HOUSE_2F', 'MAP_PLAYERS_HOUSE_2F', 'EVENT_BEAT_DRAKE', 'EVENT_BEAT_ELITE_FOUR',
        'EVENT_BEAT_RED', 'EVENT_WON_WHIRL_CUP', 'EVENT_BEAT_ORANGE_CREW_CISSY', 'EVENT_BEAT_ORANGE_CREW_DANNY',
        'EVENT_RESCUED_PROF_HALE', 'CUPWON_RISING_STAR_F', 'CUPWON_DRAGON_F', 'CUPWON_RENTAL_F',
        'CUPWON_WORLD_F', 'CUP_RECORDS_MAGIC_1', 'CUP_RECORDS_MAGIC_2', 'DECO_ORANGE_TROPHY_DOLL',
        'DECO_CUP_TROPHY_DOLL', 'SPRITE_ORANGE_TROPHY', 'SPRITE_BRONZE_TROPHY', 'SPRITE_SILVER_TROPHY',
        'SPRITE_GOLD_TROPHY', 'SPRITE_DOLL_1', 'SPRITE_DOLL_2', 'SPRITE_VARS'], None)
    g = Game(save)
    g.boot()
    fails = []

    def flag(name, on=True):
        n = K[name]
        v = g.rd('wEventFlags', n // 8)
        g.wr('wEventFlags', v | (1 << (n % 8)) if on else v & ~(1 << (n % 8)), n // 8)

    def records(bits=0, kimono=0, whirl=False):
        g.wr('wCupRecordsMagic', K['CUP_RECORDS_MAGIC_1'])
        g.wr('wCupRecordsMagic', K['CUP_RECORDS_MAGIC_2'], 1)
        g.wr('wCupRecords', bits)
        for i in range(3):
            g.wr('wCupRecords', (kimono >> (8 * i)) & 0xff, 1 + i)
        g.wr('wCupRecords', 0, 4)
        flag('EVENT_WON_WHIRL_CUP', whirl)

    def cup_bits(*names):
        return sum(1 << K[n] for n in names)

    def room():
        g.warp(K['GROUP_PLAYERS_HOUSE_2F'], K['MAP_PLAYERS_HOUSE_2F'], 2, 2)
        g.tick(30)

    base = g.state()

    # owned trophies: the Decoration menu lists what you own
    owned = []
    g.pb.hook_register(*g.sym['AppendDecoIndex'], lambda _: owned.append(g.pb.register_file.A), None)

    def owned_trophies():
        owned.clear()
        room()
        g.face('up')
        for b in ['a', 'a', 'down', 'down', 'down', 'down', 'a']:
            g.press(b, 60 if b == 'a' else 15)
        got = {n for n in ('DECO_ORANGE_TROPHY_DOLL', 'DECO_CUP_TROPHY_DOLL') if K[n] in owned}
        for _ in range(6):
            g.press('b', 30)
        return got

    for drake, cups, want in ((False, 0, set()), (True, 0, {'DECO_ORANGE_TROPHY_DOLL'}),
                              (False, cup_bits('CUPWON_RENTAL_F'), {'DECO_CUP_TROPHY_DOLL'}),
                              (True, cup_bits('CUPWON_WORLD_F'), {'DECO_ORANGE_TROPHY_DOLL', 'DECO_CUP_TROPHY_DOLL'})):
        g.load(base)
        flag('EVENT_BEAT_DRAKE', drake)
        records(cups)
        got = owned_trophies()
        if got != want:
            fails.append(('trophies', f'Drake {drake}, cups {cups:#x}: own {sorted(got)}, not {sorted(want)}'))
    g.load(base)
    flag('EVENT_BEAT_DRAKE', False)
    records(0, kimono=1 << 5)
    if owned_trophies() != {'DECO_CUP_TROPHY_DOLL'}:
        fails.append(('trophies', 'a Kimono Cup win alone does not give the Cup Trophy'))
    g.load(base)
    records(0, whirl=True)
    if owned_trophies() != {'DECO_CUP_TROPHY_DOLL'}:
        fails.append(('trophies', 'a Whirl Cup win alone does not give the Cup Trophy'))

    # the Cup Trophy's look, set out on the left, the Orange Trophy on the right
    def sprites():
        room()
        v = g.addr('wVariableSprites')
        return (g.m[1, v + K['SPRITE_DOLL_1'] - K['SPRITE_VARS']], g.m[1, v + K['SPRITE_DOLL_2'] - K['SPRITE_VARS']])

    all_six = dict(bits=cup_bits('CUPWON_RISING_STAR_F', 'CUPWON_DRAGON_F', 'CUPWON_RENTAL_F', 'CUPWON_WORLD_F'),
                   kimono=1, whirl=True)
    for kw, tier in ((dict(bits=cup_bits('CUPWON_RISING_STAR_F')), 'BRONZE'),
                     (dict(bits=cup_bits('CUPWON_RISING_STAR_F'), whirl=True), 'BRONZE'),
                     (dict(bits=cup_bits('CUPWON_RISING_STAR_F', 'CUPWON_DRAGON_F'), whirl=True), 'SILVER'),
                     (dict(bits=cup_bits('CUPWON_RISING_STAR_F', 'CUPWON_DRAGON_F', 'CUPWON_RENTAL_F',
                                         'CUPWON_WORLD_F'), whirl=True), 'SILVER'),
                     (all_six, 'GOLD')):
        g.load(base)
        flag('EVENT_BEAT_DRAKE')
        records(**kw)
        g.wr('wDecoLeftOrnament', K['DECO_CUP_TROPHY_DOLL'])
        g.wr('wDecoRightOrnament', K['DECO_ORANGE_TROPHY_DOLL'])
        got = sprites()
        want = (K[f'SPRITE_{tier}_TROPHY'], K['SPRITE_ORANGE_TROPHY'])
        if got != want:
            fails.append(('cup trophy', f'{kw}: sprites {got}, not {want} ({tier})'))

    # its description counts the cups
    g.load(base)
    records(**all_six)
    g.wr('wDecoLeftOrnament', K['DECO_CUP_TROPHY_DOLL'])
    g.warp(K['GROUP_PLAYERS_HOUSE_2F'], K['MAP_PLAYERS_HOUSE_2F'], 4, 3)
    g.tick(30)
    g.face('down')
    g.press('a', 90)
    screen = bytes(g.rd('wTilemap', i) for i in range(20 * 18))
    g.press('a', 90)
    screen += bytes(g.rd('wTilemap', i) for i in range(20 * 18))
    text = ''.join(chr(c - 0x80 + 65) if 0x80 <= c < 0x9a else chr(c - 0xa0 + 97) if 0xa0 <= c < 0xba
                   else chr(c - 0xe0 + 48) if 0xe0 <= c <= 0xe9 else ' ' for c in screen)
    if 'gold Cup Trophy' not in text or '6 of 6 cups' not in text:
        fails.append(('cup trophy', f'description: {" ".join(text.split())[:120]}'))
    kimono = sum(bin(g.rd('wCupRecords', k)).count('1') for k in (1, 2, 3))
    if f'{kimono} of 18 Kimono' not in ' '.join(text.split()):
        fails.append(('cup trophy', f'no "{kimono} of 18 Kimono" types: {" ".join(text.split())[:160]}'))
    for _ in range(4):
        g.press('b', 30)

    # the album
    def album_pages():
        room()
        g.face('up')
        for b in ['a', 'a'] + ['down'] * 5 + ['a']:
            g.press(b, 60 if b == 'a' else 15)
        pages = []
        for _ in range(3):
            g.tick(60)
            rows = []
            for r in range(3, 15, 2):
                row = bytes(g.rd('wTilemap', r * 20 + c) for c in range(20))
                rows.append(row)
            pages.append(rows)
            g.press('a', 30)
        g.tick(120)
        return pages

    g.load(base)
    flag('EVENT_BEAT_ELITE_FOUR')
    flag('EVENT_BEAT_RED', False)
    flag('EVENT_BEAT_ORANGE_CREW_CISSY')
    flag('EVENT_BEAT_ORANGE_CREW_DANNY')
    flag('EVENT_RESCUED_PROF_HALE')
    records(cup_bits('CUPWON_RENTAL_F'), kimono=0b1011, whirl=True)
    pages = album_pages()
    marks = [[{STAR: '*', DASH: '-'}.get(row[1], '?') for row in page] for page in pages]
    want = [['*', None, '-', None, None, None], [None, None, None, '*', None, None],
            ['-', '*', None, '-', '*', '-']]
    for p, (got, exp) in enumerate(zip(marks, want)):
        for i, (m, e) in enumerate(zip(got, exp)):
            if e is not None and m != e:
                fails.append(('album', f'page {p + 1} line {i + 1}: {m}, not {e}'))
    crew = pages[0][4][14:19]
    kimono = pages[2][2][14:19]
    if crew[2:] != bytes([0xe2, 0xdc, 0xe4]):  # "2/4"
        fails.append(('album', f'Orange Crew count tiles {crew.hex()}'))
    if kimono[1:] != bytes([0xe3, 0xdc, 0xe1, 0xe8]):  # "3/18"
        fails.append(('album', f'Kimono count tiles {kimono.hex()}'))
    if g.rd('wMapGroup') != K['GROUP_PLAYERS_HOUSE_2F'] or g.rd('wMapNumber') != K['MAP_PLAYERS_HOUSE_2F']:
        fails.append(('album', 'not back in the bedroom afterwards'))

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
