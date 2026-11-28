# Pre-expansion baseline (end of the QA phase)

The state of the build and of the QA results when the project switched to content-first development through 2.1.
Everything here is emulation or static analysis. Nothing is physical-hardware evidence, and nothing here says the game is
bug-free. The raw summaries are preserved in [`qa/baseline/2.1-pre/`](../qa/baseline/2.1-pre/); the git tag
`qa-baseline-2.1-pre` marks the commit (the ROM is reproducible with `make` at that commit).

## Build

| | |
|---|---|
| ROM | `polishedcrystal-3.2.3.gbc`, MBC5+RAM+BATTERY, CGB flag $80, 2 MiB image in a 4 MiB map |
| SHA-1 | `53dc05aafe9a2e325f13044d6c4bfe2bcc7d6aeb` |
| Engine changes in this phase | map-edge walls (`home/map.asm`, +54 bytes ROM0), Violet Outskirts House scene (`maps/`, `data/maps/scenes.asm`), Lake of Rage, Rising Cup and Battle Factory Hallway fixes from the first phase |

## Resource use (`utils/memory_report.py`)

| Region | Used | Free | Largest gap | Note |
|---|---:|---:|---:|---|
| ROM0 (home bank) | 16,238 | **146** | 145 | the map-edge fix took 54 bytes; the tightest region for engine work |
| ROMX (255 banks) | 2,078,132 | 2,099,788 | 16,384 | 128 empty banks |
| WRAM0 | 4,087 | **9** | 9 | unchanged |
| WRAMX (7 banks) | 25,111 | 3,561 | 1,809 | bank 5 holds the large gap; banks 3, 4, 6, 7 are full |
| HRAM | 122 | **5** | 5 | unchanged |
| SRAM (4 banks) | 31,845 | 923 | 393 | scattered over eight gaps; the save layout is checked by `sram_layout_unchanged` |
| VRAM | 16,384 | 0 | 0 | |

Full report: [`memory_report.md`](../qa/baseline/2.1-pre/memory_report.md). Before new engine code goes into the home bank,
plan where it will live: 146 bytes is two or three small routines.

## Critical regression suite (`make qa-regression`): 23 of 23 pass

One test per fixed defect, on every backend that applies: Lake of Rage approach (PyBoy; SameBoy CGB-0, CGB-E, AGB), Rising Cup
replacement HUD, follower queue bounds, follower slot budget, Battle Factory Hallway callback lint, map callbacks that wait,
Violet Outskirts House warp entry and the class check, the map-edge boundary sweep (4 shards), party-menu enemy pic restore,
SRAM layout, and the battle-policy egg-bit fix. The boundary sweep **fails on the old ROM (198 of 347 open edges let the player
off the map) and passes on the fixed one (0 of 347)**, on PyBoy in the cloud and on a MacBook.

## Confirmed defects fixed since the first QA phase

| | Defect | Class | Evidence |
|---|---|---|---|
| L33 | Freeze when entering Violet Outskirts House by Fly or a script warp (a callback waited for a frame with the LCD off) | one map; the scan of all callbacks found no other | static class test + dynamic test |
| L34 | Walking off a map edge with no connection loaded a map that does not exist (74 maps had a passable border) | engine-wide | boundary sweep old/new |

Earlier: L28 Lake of Rage player corruption, L29 Rising Cup status icons over the enemy sprite, L30 Battle Factory Hallway callback
(see [`qa-report.md`](qa-report.md)). Unresolved findings (L35 to L41) are in the [issue ledger](issue-ledger.md).

## What was run

| Area | Result |
|---|---|
| Maps entered | 612 of 613 on PyBoy; 1,224 of 1,226 map-model pairs on SameBoy CGB-E and AGB with the native execution guard (no illegal opcode, NOP slide, or code in VRAM/OAM/IO) |
| Warps | 2,090 in the repository; 1,722 taken on foot and verified (destination map, first-frame arrival); 373 not taken (puzzle gyms, large caves) |
| Map connections | 131 of 212 crossed on foot (the rest need Surf, Cut, a ledge or a story event) |
| Interaction sweep (worker track) | 603 maps; 2,508 of 2,965 object events, 1,331 of 1,407 background events, 268 of 288 trigger tiles interacted with; 1,695 script labels reached |
| World scenarios (MacBook, fixed ROM) | 4,000 attempted, **3,962 completed** (3,823 ok, 139 fail), 29 hang, 7 skip, 2 interrupted; 3,962 unique combinations, no repeats. The 168 failing/hung replayed on the final harness: 72 ok, 87 skipped (entry scene needs the real arrival), 7 interrupted, 2 benign, 0 hangs |
| Music | 193 songs: 154 loop, 5 loop on independent channel lengths (authored), 34 not decided in 9,000 frames; no engine/hardware mismatch in the APU monitor |
| Sound effects, cries | 216 of 216 effects leave the music engine on its path; 289 of 289 cries audible and plausible on CGB-E and AGB |
| Wild zones | 201 of 270 verified against the tables; 16 returned the other terrain's species (probably the harness), 40 not stood on, 13 produced none; roaming Pokemon correct |
| Saves | round trip, backup recovery, power cuts at 44 points of a 7,340-write save: all loaded a consistent state |
| Detector validation | partial: the control build raised no false alarms on 11 of 13 detectors; the interesting rows (reverted fixes, injected faults) were run only in part |
| Hardware | not tested: no physical console, BGB or Emulicious |

## Known gaps (documented, deferred to stabilization)

Scene scripts, collision types, event flags set by played scripts, trading and link battles in the runner, long-duration play,
cinematic timing, the remaining ~15% of object events and ~18% of warps, the 16 wild zones above, and the rest of the
detector-validation matrix. See the inventory coverage table (`qa/baseline/2.1-pre/inventory-coverage.md`).

## Reproducing

```sh
sh qa/setup.sh
make -j8
python3 qa/run.py regression --jobs 4                         # the critical suite
python3 -m qa.inventory report                                # content coverage table
python3 -m qa.gb.world_scenarios --start 0 --count 4000 --seed 1 --jobs 8 --out DIR   # resumable
```

A MacBook (M1 Max, 10 workers) ran the 4,000 world scenarios in roughly 40 minutes (from its progress lines); this container (4 shared cores) needs several
times as long. PyBoy intermittently wedges (about 0.7% of scenarios); the runner kills and retries and never counts a hang as a pass.
