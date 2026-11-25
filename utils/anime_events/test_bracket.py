#!/usr/bin/env python3
"""Check the World Championship brackets' trainer-vs-trainer results
(WorldCupWinner, engine/events/world_cup.asm) in the running game (PyBoy):

- for many seeds, matches and pairs, the game picks the same winner as
  utils/world_cup/bracket.py, so the odds that model reports are the game's;
- the same seed and match give the same winner every time, and the order the
  two trainers are given in doesn't matter;
- the offline Indigo cup's WorldCupAdvance uses it, match by match, from the
  draw's seed (wWorldCupSeed).

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
from test_friend_records import Caller, Game  # noqa: E402
from bracket import winner  # noqa: E402


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

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
