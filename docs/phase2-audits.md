# Phase 2 audits: duplicated routines and frame time

Two of the [2.1 roadmap](roadmap-2.1.md)'s Phase 2 audits, measured in the
emulator (PyBoy) on the family's saves, November 2026.

## Duplicated tournament and link routines

A scan of the Link Edition files (cups, World Championship, linked
Championship, Friend teams, link rules, achievements, the link and failsafe
code, cinematics, visible wild Pokémon, followers, quest map, Random Battle,
Orange League) for any run of 10 instructions that appears twice found 20
groups. All are short:

- the byte-to-nybble encoding and decoding of link messages, in `link.asm`,
  `link_failsafe.asm` and `world_link.asm` (about 50 bytes could be shared);
- the attribute-map clear before a full-screen menu (bracket, Album, Friend
  preview), three times;
- menu cursor setup and party-slot reads in the trade screens (upstream);
- the cup party backup and restore, which are each other's mirror.

**Not merged.** The ROM has about 2 MiB free on the 4 MiB carts, and the
largest saving touches three link protocol paths that the cable tests cover
byte for byte; a shared routine would save tens of bytes at that risk.

## Frame time

A frame the main loop misses (a "lag frame") shows as a hitch. Counting them
(`hVBlankCounter` steps between calls to `DelayFrame`) while walking a loop
for 1,152 frames, with a Repel so no battle interrupts:

| Map | Visible wild Pokémon | Lag frames |
|---|---|---:|
| Pokémon Center 2F (link room) | none there | 0.2% |
| Route 29 | off | 0.4% |
| Route 29 | on | 3.2–3.6% |
| Route 32 | off | 0.0% |
| Route 32 | on | 3.0–5.4% |

So visible wild Pokémon cost about one dropped frame every few steps in the
grass. Timing their step work (in scanlines, 154 a frame):

| Part | Before | After the change below |
|---|---:|---:|
| A step with no spawn | about 40 | about 19 |
| `ChooseWildMon` (the species, from the encounter table) | 28 on every step | 28, on about 1 step in 6 |
| `FindWildMonSpot` (a free, reachable tile) | 270–300 | the same |
| Creating its object (palette, graphics) | 135–160 | the same |

**Changed:** `TryWildSpawn` used to choose the species and then roll the
encounter chance, so the choice was wasted on most steps. It now draws the
same single roll first and stops if it's at or above the most the chance can
be (the map's rate after the music and a Cleanse Tag, at most doubled by the
lead's ability: no ability raises it further); otherwise it chooses as
before and compares that roll with the real chance. The odds are exactly
the same (3,000 rolls on Route 29: 10.5% against the map's 9.8% ± 1.1%),
and every map's spawns pass `test_wild_mons.py`.

**Still costly:** a spawn attempt spends about two frames in
`ComputeWildMonReach`, which rebuilds a 15×13-tile map of where you can walk
(so a Pokémon never appears behind a wall) from the map's collision data,
and then fills it. That is the remaining hitch, about once every six steps
in grass. Ways to remove it, not yet done: build the window over a few
frames after the step that asks for a spawn, or update it by one row or
column as the player moves instead of rebuilding it.

Not yet measured: battles, menus and the link screens (each is paced by its
own loop), and the VRAM and OAM budget of each screen.
