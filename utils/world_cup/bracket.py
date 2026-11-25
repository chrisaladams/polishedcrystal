#!/usr/bin/env python3
"""The World Championship brackets' trainer-vs-trainer results, as the game
works them out (WorldCupWinner, engine/events/world_cup.asm), for tests and
for seeing how the odds play out.

The stronger trainer (the larger WorldCupTrainers index) wins with 50% plus
10% for each place between them, at most 90%, from the bracket's seed and the
match's number alone (0-3 the quarterfinals, slot / 2; 4 and 5 the
semifinals; 6 the final).

Usage:
  python3 utils/world_cup/bracket.py   (a report over every seed: how often
                                        each trainer reaches the final, wins)
"""
ODDS = (128, 154, 179, 205, 230)  # out of 256, by places between them


def xorshift(x):
    """One step of the 16-bit xorshift (7, 9, 8), as the game does it."""
    x ^= (x << 7) & 0xffff
    x ^= x >> 9
    x ^= (x << 8) & 0xffff
    return x


def winner(seed, match, b, c):
    x = seed or 1
    for _ in range(match + 1):
        x = xorshift(x)
    strong, weak = max(b, c), min(b, c)
    return strong if x >> 8 < ODDS[min(strong - weak, 4)] else weak


def draw(seed):
    """The linked bracket's draw (WorldLinkDraw): slots 0 and 4 are the players."""
    order = list(range(1, 8))
    s = seed
    for c in range(6, 0, -1):
        s = (s * 5 + 1) & 0xffff
        j = (s >> 8) % (c + 1)
        order[c], order[j] = order[j], order[c]
    return [0] + order[:3] + [0] + order[3:6]


def report():
    """With both players out in the quarterfinals, every match is the
    trainers': how often each reaches the final and wins it, over all seeds."""
    from collections import Counter
    finals, wins, upsets, matches = Counter(), Counter(), 0, 0
    for seed in range(1, 0x10000):
        b = draw(seed)
        # the players lose their quarterfinals to slots 1 and 5
        semis = []
        for half in (0, 4):
            qf = winner(seed, half // 2 + 1, b[half + 2], b[half + 3])
            sf = winner(seed, 4 + half // 4, b[half + 1], qf)
            for x, y, w in ((b[half + 2], b[half + 3], qf), (b[half + 1], qf, sf)):
                matches += 1
                upsets += w != max(x, y)
            semis.append(sf)
        champion = winner(seed, 6, *semis)
        matches += 1
        upsets += champion != max(semis)
        finals.update(semis)
        wins[champion] += 1
    n = 0xffff
    print('trainer (1 weakest .. 7 strongest): reaches the final, wins it')
    for t in range(1, 8):
        print(f'  {t}: {100 * finals[t] / n:5.1f}%  {100 * wins[t] / n:5.1f}%')
    print(f'upsets: {100 * upsets / matches:.1f}% of trainers\' matches')


if __name__ == '__main__':
    report()
