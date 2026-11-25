# ROM reclamation audit

Measured from the linker map and `.sym` at the commit after `7abb897ac`
(`make`, RGBDS 1.0.4). Free ROM: **12,852 B** (with a one-byte `farcall` fix), of which 12,602 B is one gap in
bank `$7f`. Sizes are bytes in the ROM, compressed where the asset is
compressed.

## Done (lossless)

| Change | Saved | How checked |
|---|---:|---|
| Nidorina's walking sprite is Nidoran♀'s | 249 B | The two pictures were byte-for-byte identical. They are now shared through `SHARE` in `utils/followers/make_tables.py`, so regenerating keeps it. Nidorina keeps its own colours. |

A hash of every `INCBIN` file found no other duplicate worth merging. Twelve
tilesets share the same 1-byte empty VRAM1 block, which would save 11 B. Fonts,
the Random Battle table, duplicate graphics and text were already squeezed
earlier.

## Candidates (all reachable; each changes what players see or hear)

| Candidate | Measured | Reachable from | Notes |
|---|---:|---|---|
| Music-player-only tracks (Dewford Town, XY Legendary, four Prism battles) | 4,962 B | Jukebox only | Added by the earlier jukebox swap. No map, battle or script plays them. |
| Optional fonts (Bold, Italic, Serif, Chicago, MICR) | 3,414 B data + option code | Options | Keep Normal, Narrow and Unown. An old save that chose a removed font falls back to Normal. |
| Cosmetic Pikachu forms (Chuchu, Pika, Spark) | ~1,975 B pics, plus animations | Gift/trainer forms | Spark is used by one trainer (`data/trainers/parties.asm`). Fly and Surf are mechanical: keep them. |
| Game Boy Printer | 1,824 B section, plus VBlank and serial hooks | The Game Freak artist's diploma print in Celadon Mansion 3F | Needs a real printer. Showing the diploma on screen stays. |
| Textbox frames, 20 → 8 | 768 B | Options | An old save's frame choice wraps to a kept frame. |
| Title music after the Hall of Fame (XY title) | 1,089 B | Title screen once the game is beaten | The normal title music stays. |
| Unown graphics | not measured | | Forms and the Ruins of Alph must stay. |
| Shared cup and battle routines | not measured | | Belongs with Phase 3 (rules unification). |

Taking all of them except Unown and the routines would free about 14 KiB.
That would bring free ROM to about 27 KiB, short of the roadmap's 30–40 KiB
stretch goal.

## Bank packing

All free ROM except 199 B in ROM0 and a few bytes per bank is in bank `$7f`.
New code and data that can be reached with `farcall` or a `BANK()` lookup can go
anywhere, so one large gap is the most useful shape. Bytes freed in other banks
let the linker repack and grow that gap: the 249 B above is all in it now.
