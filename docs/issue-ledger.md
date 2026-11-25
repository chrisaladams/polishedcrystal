# Issue ledger

The consolidation plan's (C0–C7) record of known defects and unverified risks,
with each one's E requirement (E1–E19). Severity: **critical** (save, link
or progression could break), **high** (wrong behavior a player will meet),
**medium** (limited or unlikely), **low** (cosmetic or tooling). Status:
open, mitigated (reduced, not closed), fixed (with regression evidence), or
needs-hardware.

Owner: the agent (Claude) unless noted. The project owner (christian) does the
hardware and natural-play work.

| ID | E | Severity | Issue | Reproduction / evidence | Status | Regression evidence |
|---|---|---|---|---|---|---|
| L1 | E4, E17 | critical | Championship prize persistence. The prize is committed at save time (`wWorldLinkClaimPending` → `WorldLinkCommitClaim` in `SaveGameData`). Not tested: a full Bag at the claim, repeat prizes, recovery through the backup save, or power loss during a save | `utils/linktest/test_world_link.py` covers claim, withdraw and closed records only | mitigated | `test_world_link.py` passes at the baseline (see `c0-baseline.md`) |
| L2 | E3, E17 | high | Generated-team loops (`CupMakeTeam`, `LinkRandomBattle_MakeTeam`) start over until a team fits: no finite bound, no fallback, no agreed safe failure between link peers. They end with today's sets | `test_team_generation.py`: 111 teams within a time limit. Sampling, not proof | mitigated | `test_team_generation.py` |
| L3 | E17 | high | Friend Team writes: an actual reset mid-write is untested. Only inferred from the marker staying clear throughout a write | `test_friend_records.py` (marker test) | mitigated | `test_friend_records.py` |
| L4 | E5 | medium | Scene lifecycle: a second `scene_begin` before `scene_end` overwrites the saved palettes with the current (tinted) ones. A script that leaves without `scene_end` leaves `wCinematicFlags` set, which keeps lightning off until the next scene ends. No current script does either; nothing guards against it | Source review of `engine/events/cinematic.asm` | open | none |
| L5 | E5 | medium | The sparkle emote hasn't been seen drawn in the running game (the tests play the scenes without capturing the screen) | Uses the same emote path as the eight existing emotes | needs-hardware | none |
| L6 | E3 | medium | Cup restore paths are tested byte for byte for the Rising Star and World cups only. Whirl, Kimono, Dragon, Rental, Rudy, Luana and Friend cups rely on the shared runner | `test_cups.py`, `test_whirl_cup.py`, `test_orange_league.py` (partial) | open | partial |
| L7 | E14 | medium | The Cup Trophy counts any Kimono win as that cup won; the Album shows the 18-type count, but mastery of all 18 isn't distinguished | `engine/events/achievements.asm` `CountCupsWon` | open | none |
| L8 | E19 | critical | Nothing has been verified on original hardware: GBC timing, real cable, cartridge saves | (owner: christian) | needs-hardware | none |
| L9 | E19 | high | The tests force battles and stage flags; no natural playthrough from New Bark to the postgame has been logged | — | open (owner: christian) | none |
| L10 | E18 | low | `make test`'s debug build prints three "jp can be jr" warnings (predating consolidation; the default and faithful builds are warning-free) | `make test` | open | none |
| L11 | E18 | medium | WRAM0 has 11 bytes free and HRAM 5; any new fixed-RAM state must come from elsewhere | `utils/memory_report.py` at the baseline | open | baseline report |
| L12 | E16 | medium | Simulator oracle reports haven't been re-run against the current ROM and rules (link version 4) | `meta_sim/` tools | open | none |
| L13 | E1 | low | Wild behavior profiles name 17 species; every other species is passive | `data/wild/behaviors.asm` | open | `test_wild_mons.py` (behavior of the 17) |
| L14 | E17, E19 | medium | The README contradicted the code: link version 2 (actually 4), a "Normal" format (now Standard), stale movie and scene claims | Fixed in the C0 commit | fixed | review |
| L15 | E5 | low | `scene_silhouette` blacks every sprite at once; individual clone reveals need per-sprite palettes | `docs/cinematics.md` | open | none |
| L16 | E19 | medium | Representative screenshots before visual changes: done for the scenes the tests play (contact sheets in `docs/c0-screens/`; `LE_SHOTS=dir` saves frames from any test). Not yet: video, or scenes no test reaches | `c0-baseline.md` | mitigated | `docs/c0-screens/` |
| L17 | E16, E17 | high | Random Battle sets pair an Assault Vest with status moves the vest blocks: at least Charizard, Clodsire, Cursola, Gengar, Slowbro and Bloodmoon Ursaluna (Toxic, Sleep Talk, Hypnosis, Thunder Wave and others), so those moves can never be used. The set optimizer evidently doesn't model the vest's restriction | Found at C0: the Random Battle link run drew Bloodmoon Ursaluna (Healing Light, Toxic + Assault Vest) | open | none |
| L18 | E19 | low | The link harness (`linktest.py`) keeps choosing a move the game refuses (here a status move under an Assault Vest) until it times out, instead of choosing another | C0 `link_random` timed out at 900 s on this | open | none |

