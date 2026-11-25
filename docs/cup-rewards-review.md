# Cup rewards, difficulty and healing: review

The last Phase 3 item. This is the state of each cup, as the map scripts give
it, with what deserves a change. **Decided and done:** the Rising Star Cup's
Rare Candy is now once a day (finding 1). Everything else stays as it is.

## Prizes and when each cup opens

| Cup | Opens | Level | First win | Each win after |
|---|---|---:|---|---|
| Rising Star (Route 36 gate) | from the start | 30 | Leftovers | Rare Candy once a day, else a Poké Ball |
| Kimono (Ecruteak) | from the start; three of the day's type | 50 | that type's item (18 in all) | Big Pearl |
| Rental (Goldenrod 6F) | from the start | 50 | Bottle Cap | Big Pearl |
| Dragon Masters (Blackthorn) | Rising Badge | 50 | Dragon Scale | PP Up |
| Whirl (Olivine Port) | after Red | 50 | Mystic Water | Bottle Cap |
| World (Indigo Plateau) | after Red | 50 | Ability Patch | Bottle Cap |
| Rudy, Luana (Orange Islands) | after Red | 50 | Orange Crew badges | |

A first prize that doesn't fit in a full Bag is held at the desk until
there's room.

## Findings

1. **Rare Candies from the start, without limit.** The Rising Star Cup is
   open from the first minutes. Each repeat win, three battles at level 30
   with your team raised to it, gives a Rare Candy. A player can farm levels
   long before the story expects them, skipping its difficulty curve. Link
   battles aren't affected, since every format but Unrestricted sets the
   level, but single-player progression is. *This is the one real problem.*
2. **Strong first prizes early.** Leftovers (Rising Star) and a Bottle Cap
   (Rental) can both be won near the start. Each is a single item, so this
   is a nice early goal rather than a break. Keep.
3. **Unlimited PP Ups (Dragon Masters) and Bottle Caps (Whirl, World).** PP
   Ups matter little. Bottle Caps allow hyper training without limit, but
   only after Red. In a family tournament that evens teams out, so everyone
   who plays can perfect a team. Keep.
4. **Big Pearls.** Money: harmless.
5. **Free healing.** Every cup heals your party when it ends, even after one
   lost battle, so a cup desk works as a free Pokémon Center. Every desk is in
   a town or gate near a real one, so it changes little. Keep, as the cups
   promise "losing costs nothing".
6. **Difficulty doesn't grow.** Cup levels are fixed (30 or 50), so a cup is
   as hard on day one as late in the game. Your Pokémon are raised or lowered
   to the cup's level, so early on a cup is easier than the story around it.
   The Kimono Cup's "three of the day's type" rule and the Dragon Masters'
   badge gate keep early players out. The Rising Star Cup is meant to be the
   first. Keep, apart from finding 1.

## Decision

The Rising Star Cup's repeat prize is a Rare Candy for the first win each
day, and a Poké Ball for any more that day. It uses `ENGINE_RISING_STAR_CANDY`,
a daily flag in a bit `wDailyFlags` had left unused, so older saves start
with it clear. `test_cups.py` wins four times: Leftovers, a Rare Candy, a
Poké Ball the same day, and a Rare Candy the next.
