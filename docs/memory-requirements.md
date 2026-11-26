# Memory requirements for the rest of the roadmap

Phase 2's last item in the [2.1 roadmap](roadmap-2.1.md): what the remaining
phases need, against what the cartridge has. Measured at commit `b63ee4f9a`
(after the upstream merge and the fixed game settings) with
`utils/memory_report.py`; estimates use unit costs measured in this ROM.

## What's free now

(Before the move to 4 MiB; with it, about 2 MiB more ROM is free: the free
space report shows 2,107,323 of 4,194,304 bytes.)

| Memory | Free | Largest gap | Notes |
|---|---:|---:|---|
| ROM (2 MiB, MBC3) | 10,171 B | 9,954 B (bank `$7f`) | ROM0 has 200 B; ROMX 9,972 B |
| SRAM (32 KiB, 4 banks) | 923 B | 393 B | bank 0: 509 B (gaps 393, 84, 23, 9); bank 1: 396 B (gap 392) |
| WRAM0 | 9 B | 9 B | no room for new fixed state: use WRAMX |
| WRAMX | 3,574 B | 1,822 B | where recent features put their state (bracket history, bank 2) |
| HRAM | 5 B | 5 B | |
| VRAM | 0 B on the map | — | screens and effects must borrow tiles (the bracket screen borrows the tileset area; `ExitAllMenus` reloads it) |

## Unit costs measured in this ROM

| Item | Size |
|---|---:|
| Trainer portrait, compressed (154 in the ROM) | 358 B average, 586 B largest |
| Overworld sprite, uncompressed (218 in the ROM) | 345 B average, 480 B largest |
| Walking mini | 128 B |
| Cinematic library (scene lifecycle, tints, pulses, flash) | 255 B, plus 57 B sparkle and 429 B of scene scripts for the first pass |
| World Championship line bracket (code, history, 18 tiles) | about 900 B |
| Kimono next-type guidance | about 130 B |
| Orange Crew badge tally | about 90 B |
| Rental and Friend previews | about 95 B |
| Flash & Shake option | about 100 B |
| A Friend Battle slot (SRAM) | 136 B |

## Estimated needs by phase

ROM ranges are estimates from those unit costs and the scope each phase
describes; the low end is a restrained version, the high end the roadmap's
full description.

| Phase | ROM | Other | Basis |
|---|---:|---|---|
| 4. Cinematic engine (reveals, particles, transformations, title cards; camera if feasible) | 1.5–3.5 KB | VRAM borrowed per scene | the roadmap's own 1.5–3 KiB budget, plus particle tiles |
| 5. Story presentation (four campaigns, Orange, Pallet) | 5–12 KB | | 0.5–1.5 KB of scripts and text per campaign, and 0.5–1.5 KB of unique tiles (crystals, lab, forest) |
| 6. Character artwork (16 characters) | 11–14 KB | palettes | about 16 portraits × 360 B and 15 sprites × 345 B, plus 1–3 KB of scene tiles |
| 8. Ecology | 1–2 KB | | 2 B per species assignment, three emotes, behavior code |
| 9. Environment | 1.5–4 KB | | upstream's palette glow is already merged; fog, weather, title cards, particles |
| 10. Living world | 2–5 KB | 0–32 B SRAM if state can't come from the clock | merchants, travelers, weekly events |
| 11. Tournaments | 2–5 KB | protocol work for new linked formats | rosters, ceremonies, versus screens |
| 12. Multiplayer | 0.5–1.5 KB | 136 B SRAM per extra Friend slot; 50–200 B of stats | |
| 13. Achievements | 0.5–1 KB | per-Pokémon ribbons need a save and link format change | four more Album pages |
| 14. Legendary investigations (five) | 7.5–15 KB | a few event flags each (16 retired flags remain) | 1.5–3 KB of scripts and text each |
| 15. AI | 1–3 KB | CPU time per turn | |
| **Total** | **about 34–66 KB** | | |

## The finding

The remaining roadmap needs about **3 to 6 times the free ROM**. Each phase
fits on its own, but together they don't, even in their restrained form.
Artwork (phase 6) and the legendary investigations (phase 14) are the largest
single items.

SRAM is enough for small records and up to four more Friend slots (the two
largest gaps hold two each), but not for both those and new history or
statistics. WRAM0 and HRAM are full: new fixed state goes in WRAMX, as the
recent features do.

## Options (owner's decision)

1. **Prioritize within 2 MiB.** Choose which phases, or which parts of them,
   fit the 10 KB, plus whatever lossless savings come next.
2. **More lossless savings.** Still open in phase 2: duplicated tournament and
   link routines, text encoding, bank packing. Likely 1–4 KB more, not 30.
3. **A larger cartridge.** Polished Crystal is MBC3 at 2 MiB because MBC3 has
   the real-time clock. Link Edition no longer needs that clock (its world
   clock is software), so MBC5, which most flash carts support, would allow
   4 MiB or 8 MiB of ROM and up to 128 KiB of SRAM. The save layout and every
   cartridge the family uses would need checking first, and old saves would
   need moving across: a cartridge architecture decision the roadmap reserves
   for the owner.

## Decision: 4 MiB MBC5

The owner has 4 MiB cartridges, so Link Edition moves to MBC5 at 4 MiB (option
3). That gives about 2 MiB more ROM, room for the whole remaining roadmap
(34–66 KB) many times over. SRAM stays 32 KiB with the same layout (the carts
have exactly 32 KiB), so saves carry over unchanged.

What changed and how it was checked:

- The ROM header says MBC5 + RAM + battery (`Makefile`). The game never
  touches a real-time clock, and it switches banks by writing `$2000`, which
  selects any of 256 banks on MBC5 and on 4 MiB MBC3 (MBC30) alike, so one ROM
  runs on either kind of cart.
- `tools/bankends` and `utils/memory_report.py` count 4 MiB (256 banks).
- A stress build with 128 KiB of filler pushed 1,893 real sections (sprites,
  map data, trainer groups and more) into banks `$80`–`$87`, making a 4 MiB
  ROM. On it: run_checks 25/25 (once the software clock test expected the
  MBC5 header), the linked championship test with 0 problems, and a link
  battle in sync at all 33 exchanges.
- The ROM stays 2 MiB until its first 128 banks fill; the free-space report
  then counts the rest.

The family's carts (owner's listing): "NO RTC flash cart", ROM flash 32M
(4 MiB), SRAM 256K (32 KiB), battery-backed. That matches this build. The
listing doesn't name the mapper; these boards are MBC5 or MBC3-compatible,
and the ROM switches banks the same way on both. Their save RAM is exactly
32 KiB, so SRAM is **not** growing: it stays at 923 B free (largest gap 393 B),
and new saved data still has to fit there (phase 12's Friend slots and
statistics, phase 13's records). Still to check on hardware: flashing the 4 MiB
ROM, and a save copied onto a cart loads (owner).
