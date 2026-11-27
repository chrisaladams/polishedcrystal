# Audiovisual and hardware-fidelity validation

Pictures and sound are checked **on their own**. A play session that reaches its goal says nothing
about whether the screen looked right or the music played correctly, so these tests do not depend
on gameplay succeeding, and gameplay succeeding is never taken as evidence for them.

Everything here is emulation. Nothing is marked hardware-verified; section 7 lists what only a
console can settle.

## 1. What is checked

| Area | Checks | Where |
|---|---|---|
| Frames | per-frame capture; blank-frame runs; flicker (A,B,A,B); frame-to-frame differences | `qa/av/monitor.py`, `frames.py` |
| Differential rendering | the same input sequence on PyBoy and on SameBoy CGB-0, CGB-E, AGB, compared pixel-wise at state-aligned checkpoints | `test_av.cross_emulator_frames` |
| References | known-good images **approved by a person**; comparison skips (never passes) without one | `qa/av/refs.py`, `test_av.reference_frames` |
| VRAM / tiles | tile-data stability across menus and battle screens (the Rising Cup bug class); tilemap attribute sanity | `test_av_graphics.battle_menus_keep_enemy_sprite`, `vram.py` |
| OAM / sprites | sprites using blank tiles, duplicate entries, palette index, sprites per scanline; OBJ palette colours all equal | `test_av.oam_vram_integrity_maps`, `test_av.sprite_palettes_maps_*` |
| PPU timing | CPU writes to VRAM during mode 3 and to OAM during modes 2-3, counted by a native hook in SameBoy; the line at which the VBlank handler returns | `qa/native/execguard.c`, `FrameMonitor` |
| Before/after | menus open and close back to the same picture; a door walk equals a clean warp to the same tile | `test_av_graphics.menus_restore_the_screen`, `transitions_leave_no_residue` |
| Audio capture | PCM from PyBoy (APU emulation, opt-in) and SameBoy (native sample callback), 48 kHz, WAV artifacts | `qa/av/audio.py` |
| Audio analysis | clipping, DC offset, silence while the engine reports music, whine / pitch glitches | `test_av.audio_boot_scan`, `AudioMonitor` |
| Music sequencing | every song either ends or loops with all channels in step, from the engine's own state | `test_av_audio.music_loops_*`, `qa/av/music.py` |
| Sound effects | an effect played over music leaves the music engine exactly where it would have been, and the music audible | `test_av_audio.sfx_keeps_music_*` |
| Cross-emulator audio | map music from PyBoy and from SameBoy compared after level normalisation and envelope alignment | `test_av_audio.audio_cross_emulator` |

`make qa-av` runs all of them on PyBoy and on SameBoy CGB-0, CGB-E and AGB and writes
`qa/reports/runs/<time>/av_review.md`. Short runs: `QA_MAP_LIMIT`, `QA_AUDIO_LIMIT`,
`QA_MUSIC_MAX_FRAMES`, `QA_AV_PLAY_SECONDS`.

The monitors also attach to the autonomous explorer: `python3 -m qa.gb.campaign --av --audio ...`.

## 2. Reviewing without watching a whole session

Every test that sees something suspicious writes a record (kind, where, frame, signature, artifacts).
`python3 -m qa.av.review RUN_DIR` merges them, **deduplicates by signature**, classifies them and lists
the suspicious events with their evidence: a frame strip around the event, the screenshot, the LCD
registers, the CPU routine, a state file to resume from, and (for audio) the WAV.

| Class | Meaning |
|---|---|
| confirmed | objective defect, e.g. a CPU write to VRAM the PPU is using |
| suspect | needs a person; evidence attached |
| emulator | appears on some emulators or hardware models and not others: an emulator or revision difference until proven otherwise |
| expected | a known legitimate case, with the reason (boot/intro black frames, battle flashes, intentionally blank trigger sprites) |

Nothing is hidden: expected and emulator-class events are listed with their reasons.

## 3. References are never approved automatically

A reference image from a build that already has a defect would bake the defect in. So:

* tests only **propose** candidates (`qa/av/reference/pending/`, git-ignored), with evidence: ROM hash,
  which emulators agreed, whether any monitor fired;
* `python3 -m qa.av.refs list|show NAME` to look at them, then
  `python3 -m qa.av.refs approve NAME --by "who" --note "why this is correct"`; approval is refused if the
  candidate was captured while the emulators disagreed or a monitor had fired;
* `reference_frames` compares only approved references; with none it **skips**, which counts as untested.

No reference is approved in this repository yet: they need a person's eyes.

## 4. Why a clean-looking result might still be wrong

* The checks are heuristics with thresholds. A blank-frame run shorter than 45 frames, a flicker
  that is not a strict A,B,A,B pattern, or silence while the engine reports no music are not detected.
* PPU access monitoring catches writes at the moment they happen in SameBoy's model of the PPU; a
  bad write that SameBoy's timing places in a legal window would be missed on that revision.
* Pixel differences between emulators below the tolerance (24-40/255 per channel, a few percent of
  pixels) are accepted, which would hide a small palette error.
* Audio is compared by envelope and band energy, not sample by sample: a pitch error of a few cents
  would pass.

## 5. Triage log (things that looked wrong and were not defects)

These are recorded so the same false alarm is not chased twice. Each was investigated.

| Observation | Cause | Verdict |
|---|---|---|
| PyBoy and SameBoy title screens differ in 86 % of pixels | PyBoy skips the boot ROM, so "frame 900" is a different moment; aligned by game state the difference is 0.00 % | test artefact, fixed |
| DC offset 0.15 in SameBoy PCM | capture ran without the hardware-style high-pass filter | capture configuration, fixed |
| Every song reports the same 7,582-frame loop | the test game idled on the title screen, whose attract timer restarts the title sequence (and music) about every 126 s | test artefact, fixed (quiet indoor map) |
| Every sound effect "breaks" the music | the routine call itself takes a few frames, so the music is a few frames further on than the control | test artefact, fixed (compare at equal frame counts) |
| Channels "desync" | comparing loop lengths in events instead of frames | analysis bug, fixed |
| Pack menu "never opens" in the cup | cup battles disable the Pack on purpose (`wCupLevel`) | not a defect; the Pack is not tested there |
| Visible sprites using blank tiles on `BATTLE_TOWER_OUTSIDE` | `SPRITE_BLANK_FRUIT` objects: invisible door triggers | expected; they do occupy OAM slots |
| BG attribute bit 4 set on most maps | bit 4 is unused on the CGB and ignored by the hardware | expected |
| VBlank handler returns up to dozens of lines after VBlank ends | the handler does its VRAM-critical copy first, then runs the sound engine | normal for this engine; illegal VRAM/OAM writes are what matters (counted separately) |
| PyBoy hangs after a direct `PlayMusic` call | an interaction between the routine-call shim and PyBoy's breakpoint stepping | harness limitation; song validation runs on SameBoy |

## 6. Results

See the generated `av_review.md` of the latest run and the numbers in [`qa-report.md`](qa-report.md).
The headline counts are in section 8 of this file, filled from the canonical run.

## 7. Physical hardware: what emulation cannot show

Emulators model the console's logic, not its analogue parts or every silicon revision. These need a
console (a Game Boy Color, and a Game Boy Advance or SP in its Game Boy Color mode where marked).
Record the console, revision if known, and the cartridge.

| # | Check | How | Expect |
|---|---|---|---|
| A1 | Picture integrity after a forced switch | Rising Star Cup: let the lead faint and send in the next Pokemon | the enemy sprite is intact (fix for the Rising Cup report) |
| A2 | Real LCD behaviour | walk quickly across a town, then through a route, watching text, the player and the follower | no ghost trails beyond the LCD's normal blur; sprites do not flicker |
| A3 | Palette fidelity | towns by day and night, caves, the Orange Islands, battle screens, on a GBC and on a GBA/SP | colours readable; on the GBA/SP (brighter, different gamma) nothing washes out or disappears |
| A4 | Sprite pressure | stand in a busy place (Goldenrod, the Battle Tower outside, a cup crowd) | no sprite vanishes or blinks; at most the engine's own dropped sprites on a crowded scanline |
| A5 | Screen transitions | enter and leave buildings, caves, the Battle Factory, cable-car, warps with the follower | no stray tiles, wrong colours or one-frame flashes beyond a normal fade |
| A6 | VRAM timing on silicon | Pokemon summary, party screen, Pack, Start menu opened and closed repeatedly while a battle animation or weather plays | no corrupted tiles; these are the places an illegal VRAM write would show on hardware |
| A7 | Speaker and headphone audio | listen to a town theme, a battle theme, a cry, a menu beep on the console speaker and on headphones | no pops louder than the engine's design, no stuck tone, stereo as intended |
| A8 | Music continuity | walk between maps with different music; trigger sound effects (menu, item, Surf) over music | music resumes correctly after every effect; no silence; no restart |
| A9 | Long-running audio | leave a looping theme playing for ten minutes | it loops without a gap, drift or channel falling out of step |
| A10 | GBA vs GBC audio | play the same scene on both | volume and tone differ as the hardware does; nothing is missing |
| A11 | Battle Factory hallway on a GBA | walk between the lobby and the hallway several times | never freezes (L30) |
| A12 | Double-speed mode | if any option or feature switches the CPU to double speed, repeat A2, A6 and A7 in it | unchanged |

Defects in this table that emulation cannot reproduce are the reason the diagnostic proposal
([`diagnostics-proposal.md`](diagnostics-proposal.md)) exists.

## 8. Headline numbers (canonical run)

Filled in from `qa/reports/runs/av-canonical` when the full `make qa-av` run completed.
