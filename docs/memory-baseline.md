# Build and memory baseline

## Cissy’s Surf checkpoints (2026-11-26)

An accepted buoy plays a chime and animates a splash at the player’s
feet. At the last buoy, the splash plays before the course-clear text.
The effect borrows the existing puddle graphics and a temporary object
slot. The build uses 51 additional ROM bytes and one byte of alignment
padding. Free ROM is 2,106,599 B in Default and 2,106,660 B in Faithful.
The map comparison showed zero change in static RAM or VRAM usage.

`make -j6 test` and the Orange League emulator suite passed. A separate
sprite trace found both animation frames at each buoy. The course test
also checked an approach from the east without passing the earlier
buoys, staying on course after revisiting the first buoy, and restarting
after returning to shore.

## Championship desk timeout (2026-11-26)

The Championship desk now limits how long it waits for the start of each
packet. Pulling the virtual cable at the start of either exchange caused
both peers to stay in the byte loop on the summit build. With the timeout,
both show the interruption and return control. The interrupted bracket
records match their inputs byte for byte. A clean retry registers a fresh
pair or synchronizes the existing bracket, depending on the test case.

The change costs 30 B of ROM per build and uses the existing save and
wire formats. Free ROM after the fix is 2,106,651 B in Default and
2,106,712 B in Faithful. Static RAM measurements are the same as in the
table below. `make -j6 test` passed, including all 1,513 save-address
guards. The Virtual Console patch built. The Championship plan and
prize-persistence suites passed. Standard synchronized across all eight
shared exchanges in a smoke test, and both peers reached the Trade Center
after choosing Championship in the previous session.

Both unplug phases passed on Default and the second phase also passed
on Faithful. One-sided registration and final-result cases used the exact
SRAM snapshots from before and after each successful virtual-cable
session. Both choices of surviving record recovered the same draw and
players' rounds. The older end-to-end scenarios passed in the broader run,
including a clean reconnect after heavy noise. The two desk cleanup checks
passed in separate reruns after the driver stopped pressing A once control
returned. These tests used staged emulator save copies.

## Current MBC5 build (2026-11-26)

Built `fbbc450253b4a2ecb7cab622e9c9598ec9e48cc2` and the Rocky Peak
scene change from isolated trees on `claude/sleepy-ramanujan-kc278b`.
RGBDS 1.0.4, GNU Make 3.81, Apple Clang, Python 3.14.6 and PyBoy 2.9.0.
The cartridge target is 4 MiB MBC5 with 32 KiB SRAM. Both ROM images are
2 MiB on disk and leave banks `$80–$ff` available as the game grows.

| Build | Free ROM at HEAD | With summit scene | Largest free gap below `$80` with scene |
|---|---:|---:|---:|
| Default | 2,106,704 B | 2,106,681 B | 9,309 B in `$7f` |
| Faithful | 2,106,765 B | 2,106,742 B | 9,355 B in `$7f` |

Both builds have 923 B of SRAM free (509/396/9/9 B by bank; largest
gap 393 B), 9 B of WRAM0, 3,561 B of WRAMX (largest gap 1,809 B), 5 B
of HRAM and 0 B of statically free VRAM. The summit scene adds 23 B of
ROM in each build and uses the existing weather tiles, OAM allocator and
scene state. Save layout and link protocol are unchanged by the scene.

| Build | SHA-256 at HEAD | SHA-256 with summit scene |
|---|---|---|
| Default | `adfc5d9b6f7827fa79515e02d2b12e99c3237eeed39734316cf7d3c8fc97cd57` | `976f6d5b6dc2f6cb8b18eed721aaa812f70395137f97ab9699e500c1f83c6733` |
| Faithful | `f9e8c059073a09d53d924bc29dd827064bd77aa7f7e6fc556b9c003a36add8f5` | `cc437e45f9795cf2df5a1bed29f81ef9a1a3da124344dfeec043b84388619f19` |

### Current verification

- `make -j6 test` and the Faithful build passed. The test target checked
  1,513 save addresses, text width, overworld palette rows, bank calls and
  battle AI scoring.
- `test_orange_league.py` followed the ice climb, exercised the snowfall
  renderer on the first visit, checked scene cleanup and confirmed that
  the slide continues past the trigger on later visits. The ascent and
  descent still lead to Danny's battle. A separate rendered sample showed
  up to 15 visible snow sprites at the summit.
- `test_software_clock.py` loaded a pre-MBC5 emulator save and exercised
  legacy and backup recovery. It now compares the exact clock and elapsed
  seconds at save and load, then checks that both counters advance
  together. The former UI timing allowance failed when Continue reached
  5,716 seconds, one second outside its range.
- `test_cinematic.py` stages its own quiet room and shared-palette actors,
  and `test_friend_battles.py` uses the same forced-faint driver as the
  Orange League tests. Both passed on the staged Violet save, including
  a finished battle and party restoration with the out-of-range form.
- All 25 checks from `run_checks.py --full` passed across the initial set
  and targeted reruns. The corrected encounter sweep checked 370 wild
  Pokémon. It checks the actual habitat at a warped-in tile and, if the
  initial placement attempts come up empty after Continue, verifies that
  ordinary steps bring the encounters back. The full reachability audit
  reported zero problems.
- The virtual cable matched 5 shared action exchanges in Standard, Rising
  Star, and Unrestricted and 7 in Random during four-turn smoke tests.
  Standard stayed synchronized through 7 injected bit flips in one run
  and a 120-frame disconnect in another. Both desks rejected a
  Rising Star/Unrestricted mismatch. Both peers reached the Trade Center
  with Championship as either one or both players' last battle rules.
- In a mixed session with pre-MBC5 commit `0234c132c`, both desks rejected
  a battle as a different build, with zero action exchanges. The new
  `--expect-rejection build` case checks that result directly. Both builds
  reached the Trade Center in the separate mixed trade session.
- The two-console World Championship suite returned zero problems. It
  finished the human final and NPC branches, checked withdrawal and
  result reconciliation, then recovered in a clean session after the
  deliberately noisy registration timed out. A separate final on the
  summit build finished with both original parties restored and all 27
  action exchanges synchronized. The patched PyBoy cable emitted its
  extension layout warning during the virtual-cable tests.
- The specific Togekiss Baton Pass failure from L12 completed on the
  current ROM using the recorded RNG bytes. The whole-turn 48-matchup run
  remains the previously recorded result in the issue ledger.

All save-based verification above used copies of staged emulator fixtures.
Flashing, save retention, frame pacing and physical link testing on the
family's cartridges remain release checks.

## Earlier 2 MiB MBC3 takeover baseline

Measured from the linker map at `b959d22ae5162aafd6488b90d0504f0d45465707`
on `claude/sleepy-ramanujan-kc278b`. The checkout was clean at takeover.
Builds ran from isolated copies of tracked files. Earlier measurements are
in the [C0 baseline](c0-baseline.md) and the history of this document.

### Build

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

### Free space

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

### Historical feature costs

The earlier per-commit linker comparison measured +815 B ROM for Bedroom
achievements (`47a86b55f`), +1,544 B ROM / +272 B SRAM for Friend Battles
(`d9466245e`), and +2,138 B ROM / +20 B SRAM for the linked Championship
(`b47b74a31`). Those deltas predate later changes and remain useful for
tracking how bank `$7f` filled.

### Test evidence

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
