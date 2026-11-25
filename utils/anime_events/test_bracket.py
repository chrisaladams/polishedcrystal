#!/usr/bin/env python3
"""Check the World Championship brackets' trainer-vs-trainer results
(WorldCupWinner, engine/events/world_cup.asm) in the running game (PyBoy):

- for many seeds, matches and pairs, the game picks the same winner as
  utils/world_cup/bracket.py, so the odds that model reports are the game's;
- the same seed and match give the same winner every time, and the order the
  two trainers are given in doesn't matter;
- the offline Indigo cup's WorldCupAdvance uses it, match by match, from the
  draw's seed (wWorldCupSeed);
- the results the desks announce agree: after each round of the offline cup
  (WorldCupNextResult: winner, loser, upset), and before a linked semifinal
  or final, who the opponent beat (WorldLinkLastResult), the partner when
  the partner lost to them.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_bracket.py SAVE.sav
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'utils', 'world_cup'))
from test_friend_records import Caller, Game, rgbasm_values  # noqa: E402
from bracket import draw, winner  # noqa: E402

NAMES = ['Ash', 'Drake', 'Green', 'Blue', 'Lance', 'Cynthia', 'Red']  # WorldCupTrainers, from 1


def encode(name):
    return [0x80 + ord(ch) - 65 if ch.isupper() else 0xa0 + ord(ch) - 97 for ch in name] + [0x53]


def main():
    g = Game(open(sys.argv[1], 'rb').read())
    g.boot()
    caller = Caller(g)
    fails = []
    rng = random.Random(1)
    seed_addr = g.addr('wWorldCupSeed')

    def game_winner(seed, match, b, c):
        g.wr('wWorldCupSeed', seed & 0xff)
        g.wr('wWorldCupSeed', seed >> 8, 1)
        caller.call('WorldCupWinner', B=b, C=c, D=0, E=match, HL=seed_addr)
        return caller.out['A']

    cases = [(0, 0, 1, 2), (1, 6, 7, 1), (0xffff, 3, 4, 5)]
    cases += [(rng.randrange(0x10000), rng.randrange(7), *rng.sample(range(1, 8), 2)) for _ in range(200)]
    for seed, match, b, c in cases:
        want = winner(seed, match, b, c)
        got = game_winner(seed, match, b, c)
        if got != want:
            fails.append(f'seed {seed:04x} match {match} {b} v {c}: the game says {got}, the model {want}')
        elif game_winner(seed, match, c, b) != got:
            fails.append(f'seed {seed:04x} match {match}: {b} v {c} and {c} v {b} disagree')
        elif game_winner(seed, match, b, c) != got:
            fails.append(f'seed {seed:04x} match {match} {b} v {c}: not the same the second time')
    upsets = sum(winner(s, m, b, c) != max(b, c) for s, m, b, c in cases)
    if not 0.1 < upsets / len(cases) < 0.45:
        fails.append(f'{upsets} upsets in {len(cases)} matches: not the odds meant')

    # the offline cup: each round's trainers' matches, from the draw's seed
    for seed in (0x1234, 0xbeef, 0x0001):
        bracket = [0] + rng.sample(range(1, 8), 7)
        for k, v in enumerate(bracket):
            g.wr('wWorldCupBracket', v, k)
        g.wr('wWorldCupSeed', seed & 0xff)
        g.wr('wWorldCupSeed', seed >> 8, 1)
        size = 8
        g.wr('wWorldCupRoundSize', size)
        for round_ in range(2):
            caller.call('WorldCupAdvance')
            first = 8 - size + 1  # this round's first trainers' match
            want = [0] + [winner(seed, first + j, bracket[2 + 2 * j], bracket[3 + 2 * j])
                          for j in range(size // 2 - 1)]
            size //= 2
            got = [g.rd('wWorldCupBracket', k) for k in range(size)]
            if got != want:
                fails.append(f'offline seed {seed:04x} round {round_ + 1}: {got}, not {want}')
            bracket = got

    def buffer(label):
        out = []
        for k in range(19):
            out.append(g.rd(label, k))
            if out[-1] in (0x50, 0x53):
                break
        return out[:-1] + [0x53]

    # the offline cup's announced results, each round
    for seed in (0x2468, 0x0f0f, 0xa5a5):
        bracket = [0] + rng.sample(range(1, 8), 7)
        for k, v in enumerate(bracket):
            g.wr('wWorldCupBracket', v, k)
        g.wr('wWorldCupSeed', seed & 0xff)
        g.wr('wWorldCupSeed', seed >> 8, 1)
        size = 8
        g.wr('wWorldCupRoundSize', size)
        for round_ in range(2):
            g.wr('wWorldCupPairCursor', 2)
            heard = []
            while True:
                caller.call('WorldCupNextResult')
                kind = g.m[g.sym['hScriptVar'][1]]
                if not kind:
                    break
                heard.append((buffer('wStringBuffer4'), buffer('wStringBuffer5'), kind == 2))
            want = []
            for j in range(size // 2 - 1):
                b, c = bracket[2 + 2 * j], bracket[3 + 2 * j]
                w = winner(seed, 8 - size + 1 + j, b, c)
                lost = c if w == b else b
                want.append((encode(NAMES[w - 1]), encode(NAMES[lost - 1]), w < lost))
            if heard != want:
                fails.append(f'offline seed {seed:04x} round {round_ + 1}: announced {heard}, not {want}')
            caller.call('WorldCupAdvance')
            size //= 2
            bracket = [g.rd('wWorldCupBracket', k) for k in range(size)]

    # the linked desk: who the semifinal or final opponent beat
    K = rgbasm_values(['WORLD_LINK_SEED', 'WORLD_LINK_HALF', 'WORLD_LINK_STATUS', 'WORLD_LINK_PARTNER_STATUS',
                       'WORLDLINK_SEMIFINAL', 'WORLDLINK_FINAL', 'WORLDLINK_OUT_QF', 'WORLDLINK_OUT_SF'], None)
    partner = encode('Bob')
    for seed in (0x1357, 0x9abc, 0x0042, 0xfeed):
        for half in (0, 1):
            for status, partner_status in ((K['WORLDLINK_SEMIFINAL'], 0xff), (K['WORLDLINK_FINAL'], K['WORLDLINK_OUT_QF']),
                                           (K['WORLDLINK_FINAL'], K['WORLDLINK_OUT_SF'])):
                g.wr('wWorldLinkRecord', seed & 0xff, K['WORLD_LINK_SEED'])
                g.wr('wWorldLinkRecord', seed >> 8, K['WORLD_LINK_SEED'] + 1)
                g.wr('wWorldLinkRecord', half, K['WORLD_LINK_HALF'])
                g.wr('wWorldLinkRecord', status, K['WORLD_LINK_STATUS'])
                g.wr('wWorldLinkRecord', partner_status, K['WORLD_LINK_PARTNER_STATUS'])
                for k, v in enumerate(partner):
                    g.wr('wStringBuffer3', v, k)
                caller.call('WorldLinkLastResult')
                upset = g.m[g.sym['hScriptVar'][1]] != 0
                got = (buffer('wStringBuffer5'), upset)
                b, me = draw(seed), 4 * half
                other = me ^ 4
                if status == K['WORLDLINK_SEMIFINAL']:
                    x, y, m = b[me + 2], b[me + 3], (me + 2) // 2
                elif partner_status == K['WORLDLINK_OUT_SF']:
                    x = None
                else:
                    x = b[other + 1]
                    y = winner(seed, (other + 2) // 2, b[other + 2], b[other + 3])
                    m = 4 + other // 4
                if x is None:
                    want = (partner, False)
                else:
                    w = winner(seed, m, x, y)
                    lost = y if w == x else x
                    want = (encode(NAMES[lost - 1]), w < lost)
                if got != want:
                    fails.append(f'linked seed {seed:04x} half {half} status {status}/{partner_status}: '
                                 f'heard {got}, not {want}')

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
