# C0 baseline: evidence at the start of consolidation

Work package C0 (E18, E19) of the consolidation plan. This records what was
built, measured and run, on which commit, with which tools. Defects found are
in [`issue-ledger.md`](issue-ledger.md).

## Baseline commit and toolchain

| | |
|---|---|
| Commit | `a245fbb9203b1230c55f62f5fbd9a31a5c7139a7` (branch `claude/sleepy-ramanujan-kc278b`) |
| Assembler | RGBDS v1.0.4 |
| Python | 3.13.18 |
| Emulator for tests | PyBoy 2.9.0 (with the two-console cable build for link tests) |
| Builds | `make` (default) and `make faithful`, each from `make tidy` |

| ROM | SHA-1 | Free (rgbfix) |
|---|---|---:|
| `polishedcrystal-3.2.3.gbc` | `d2d3f76ae057990a0809cf0fa55106b758b1b716` | 11,019 B |
| `polishedcrystal-faithful-3.2.3.gbc` | `3ba94304d972097ae123755e75094809336be908` | 11,080 B |

Both builds were warning-free. `make test`'s debug build prints three "jp can be jr"
warnings (L10).

## Memory (both builds, `utils/memory_report.py`)

| Region | Default free | Faithful free | Largest gap | Note |
|---|---:|---:|---:|---|
| ROM0 | 200 | 214 | 199 / 213 | |
| ROMX | 10,820 | 10,867 | 10,783 / 10,818 | One gap in bank `$7f` |
| ROM total | 11,020 | 11,081 | | 3.8 KB above the 7 KiB reserve |
| SRAM | 923 | 923 | 393 | Fragmented: `$bd84` 393, `$ab84` 392, `$bfac` 84 |
| WRAM0 | 11 | 11 | 11 | Tight (L11) |
| WRAMX | 3,590 | 3,590 | 1,822 | Banks 3, 4, 6, 7 full; 2 and 5 have room |
| HRAM | 5 | 5 | 5 | Tight |
| VRAM | 0 (statically) | 0 | | Allocated per screen; not audited per screen yet |

All 1,513 guarded SRAM labels were unchanged (`check_sram_layout.py`).

## Tests run at the baseline

Run by `c0/run_suite.sh` (scratchpad) on Ben's, Sam's and Dereck's saves:

| Test | Result | Time |
|---|---|---:|
| `make test` (debug and default builds, farcall check, SRAM layout, AI scoring) | pass | 71 s |
| `utils/anime_events/run_checks.py` (22 checks: story, quest map, clock, Orange League, cameos, Whirl, movies, campaigns, shadow encounters, cups, spotlight, achievements, Friend Battles and records, link rules, bracket, cinematic, team generation, wild mons, reachability) | 22/22 pass | 403 s |
| Link battle, Standard, 3 a side | pass, in sync | 16 s |
| Link battle, Random teams | **timeout** (L17, L18: a set's status move under an Assault Vest, which the harness kept choosing) | 900 s |
| Link battle, Rising Star | pass, in sync | 18 s |
| Link battle, Unrestricted (own levels) | pass, in sync | 16 s |
| Link, different rules chosen | **timeout**: invoked without `--party-size 3`, so the Rising Star side refused its six (rerun below) | 900 s |
| Link battle with the cable unplugged mid-battle | pass, recovered | 16 s |
| Link battle with corrupted bytes | pass, recovered | 16 s |
| `utils/linktest/test_world_link.py` (every linked Championship scenario) | 0 problems* | 395 s |

\* Its last scenarios ran after the C0 text fixes were rebuilt: those
changed only text, not link code, and the suite is rerun on the C0 commit
below.

## Defects found by C0

- **Text overflow (fixed in the C0 commit):** 12 Link Edition text lines were
  19 columns wide, one more than the text box, so their last letter wrote
  over the box's frame and stayed. `utils/check_text_width.py`, now in
  `make test`, scans every text line in `maps/` and `data/`.
- **Random Battle sets (L17, open):** Assault Vest sets with status moves.
- **Link harness (L18, open):** stuck on a refused move.
- **README (L14, fixed):** link version, the Standard format's name, stale
  movie and scene claims. `docs/rules-matrix.md`'s stale "not yet decided"
  section too.

## After the C0 fixes (the C0 commit)

Run by `c0/run_post.sh` (scratchpad):

| Test | Result |
|---|---|
| `make test`, now with `utils/check_text_width.py` | pass (0 text lines wider than 18 columns) |
| `test_quest_map.py` (Field Book texts), `test_cups.py` (Rising Star texts), `test_orange_league.py` (Rudy's rounds), `test_link_rules.py` | pass |
| Link, different rules chosen, 3 a side | pass: both desks report "different rules" |
| Link, Rising Star with an ineligible party | pass: both desks refuse it |
| `test_movie_events.py`, `test_orange_league.py`, `test_campaigns.py` with `LE_SHOTS` (frames saved) | pass |

### Scenes as they play (before any visual change)

With `LE_SHOTS`, the tests saved 3,146 frames: 885 from the movie events,
1,556 from the Orange League, 705 from the campaigns. The contact sheets in
[`c0-screens/`](c0-screens/) are frames picked by color (tinted scenes),
spread across each test. They're the "before" pictures for C4 and C5. They
show, for example, the Mewtwo scene's purple cave while it speaks and its
"shadows" frame. That frame blacks only the player's sprite (no clone
sprites), as L15 says: a global silhouette isn't a clone reveal.

## Not done in C0

- **Hardware** (L8): needs the owner's GBC, cartridge and cable.
- **Natural playthrough** (L9): needs a human player.
- **Simulator oracle reports** at link version 4 (L12).
