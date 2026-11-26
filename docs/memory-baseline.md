# Takeover build and memory baseline

Measured from the linker map at `b959d22ae5162aafd6488b90d0504f0d45465707`
on `claude/sleepy-ramanujan-kc278b`. The checkout was clean at takeover.
Builds ran from isolated copies of tracked files. Earlier measurements are
in the [C0 baseline](c0-baseline.md) and the history of this document.

## Build

RGBDS 1.0.4, GNU Make 3.81, Apple Clang, Python 3.14.6, and PyBoy 2.9.0.
The virtual cable extension was built with Cython 3.3.1. The ROM title contains
the build year. These SHA-256 hashes are for 2026 builds.

| Target | Takeover SHA-256 | SHA-256 with Quest Map fix |
|---|---|---|
| Default | `787bbf71fae4699053581372a5e54c5db5f888472e0fdae23290a6b4d9d2680f` | `27ad4a5747e39b83e9be8ce41faf49719d365cf5b90563b4db4bd527e059167f` |
| Faithful | `103dc764651c3d6c970e277af7f1e26fd0e51bf5992e56de7cb776120844b191` | `5acc23576c5ab7277cdd1f2fe3c960eca673d1bef9ba1b0405fcc28bfd0faa35` |

Default was built by `make test` and measured with `make freespace`.
Faithful was built separately with `make faithful freespace`. The ROM names
use the upstream version `3.2.3`. Run the same commands from separate clean
trees to preserve each map, or copy the maps before cleaning. Compare with
`python3 utils/memory_report.py NEW.map --compare OLD.map`.

## Free space

| Region | C0 default | Takeover default | Fixed default | Takeover faithful | Fixed faithful |
|---|---:|---:|---:|---:|---:|
| Total ROM | 11,020 B | 9,675 B | 9,668 B | 9,736 B | 9,729 B |
| ROM0 | 200 B | 200 B | 200 B | 214 B | 214 B |
| Largest ROM0 gap | 199 B | 199 B | 199 B | 213 B | 213 B |
| ROMX | 10,820 B | 9,475 B | 9,468 B | 9,522 B | 9,515 B |
| Largest ROMX gap (bank `$7f`) | 10,783 B | 9,434 B | 9,431 B | 9,476 B | 9,470 B |
| SRAM | 923 B | 923 B | 923 B | 923 B | 923 B |
| WRAM0 | 11 B | 9 B | 9 B | 9 B | 9 B |
| WRAMX | 3,590 B | 3,574 B | 3,574 B | 3,574 B | 3,574 B |
| HRAM | 5 B | 5 B | 5 B | 5 B | 5 B |
| VRAM (static map) | 0 B | 0 B | 0 B | 0 B | 0 B |

The build's free-space line is one byte below the linker totals
(9,674/9,735 B at takeover, 9,667/9,728 B with the fix). Of default ROMX
space at takeover, 41 B lay outside the largest gap. The historical 7 KiB
reserve was a planning illustration.

| Bank | SRAM free | Largest SRAM gap | WRAMX free | Largest WRAMX gap |
|---:|---:|---:|---:|---:|
| 0 | 509 B | 393 B at `$bd84` | | |
| 1 | 396 B | 392 B at `$ab84` | 13 B | 13 B at `$dff3` |
| 2 | 9 B | 9 B at `$bff7` | 1,627 B | 1,612 B at `$d9b4` |
| 3 | 9 B | 9 B at `$bff7` | 0 B | |
| 4 | | | 0 B | |
| 5 | | | 1,934 B | 1,822 B at `$d5e2` |
| 6 | | | 0 B | |
| 7 | | | 0 B | |

The 7-byte Quest Map fix uses the stack to carry the linked bracket result.
It adds no static allocations, saved bytes, tiles, or sprites. The link
protocol and save schema are unchanged. Dynamic VRAM and OAM still need
per-scene checks. See the [SRAM allocation plan](sram-allocation.md) for each
gap and the lifetime of each record.

## Historical feature costs

The earlier per-commit linker comparison measured +815 B ROM for Bedroom
achievements (`47a86b55f`), +1,544 B ROM / +272 B SRAM for Friend Battles
(`d9466245e`), and +2,138 B ROM / +20 B SRAM for the linked Championship
(`b47b74a31`). Those deltas predate later changes and remain useful for
tracking how bank `$7f` filled.

## Test evidence

The fixtures started as new games. Healthy parties, Pokédex flags, and
progression milestones were staged in the emulator, then saved through
the Start menu and reloaded through Continue. Cable players used distinct
trainer names and IDs. An initial Pokédex failure passed when the fixture
was regenerated to retain its seen and caught flags.

| Check | Result |
|---|---|
| `make test` | Passed before and after the fix, including all 1,513 guarded save addresses, no text over 18 columns, and all AI scoring cases. |
| Additional builds at takeover | Monochrome, noir, HGSS, Pocket, and both VC targets built. |
| `utils/anime_events/test_quest_map.py` | The original build replaced three of 19 leads with Starter. The fix passed the expanded suite, including simultaneous solo and linked prizes, one Indigo entry, and byte-for-byte linked record preservation. |
| `utils/linktest/test_link_card.py` and `utils/linktest/test_random_teams.py` | Passed Trainer Card tests and 300 generated teams. |
| `utils/anime_events/test_cups.py` | Passed after correcting the test driver. An A press could enter the move picker while it was trying to forfeit. The driver now backs out and waits for the actual No/Yes prompt. |
| `utils/wild_mons/test_wild_mons.py` | Full wild Pokémon sweep passed. It checked 405 encounters across all encounter maps. |
| `utils/linktest/test_world_prize.py` | Passed full-Bag handling, saved and unsaved interruption cases, and primary checksum fallback to the completed backup. L1 records two other reproduced edge cases. |
| `utils/audit/audit_reachability.py --wild` | Story reachability and the full wild-map audit completed with zero problems. |
| Virtual cable battle formats | Standard, Rising Star, and Unrestricted completed in 3, 13, and 3 synchronized exchanges, respectively. Random synchronized through 17 exchanges before the test limit. Both sides rejected a Rising Star/Unrestricted rules mismatch. |
| `utils/linktest/test_world_link.py` | Full two-console Championship suite completed with zero problems, including registration, finals, result synchronization, withdrawal, mismatched partners, and cable noise recovery. |
| Battle oracles | Matched 333 species, 30,276 damage pairs, 3,000 pipeline scenarios, 2,000 damage rolls, 2,000 accuracy cases, 4,000 status cases, and 3,000 speed cases. The interrupted whole-turn run logged 45 matching cases and reproduced one known Baton Pass stall (L12). |

Original hardware and natural playthrough evidence remain open. See the
[issue ledger](issue-ledger.md) for investigation details.
