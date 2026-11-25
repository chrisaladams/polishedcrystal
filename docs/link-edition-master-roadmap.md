# Pokémon Polished Crystal: Link Edition — Master Development Roadmap

**Status:** Core systems implemented; stabilization, optimization, presentation, and release validation remain.

**Review baseline:** [`b47b74a31590fbcee1576f80b66a949052b60d52`](https://github.com/chrisaladams/polishedcrystal/commit/b47b74a31590fbcee1576f80b66a949052b60d52)

**Repository:** `chrisaladams/polishedcrystal`  
**Branch at review:** `claude/sleepy-ramanujan-kc278b`  
**Repository path:** `docs/link-edition-master-roadmap.md`

This roadmap supersedes the original 11-phase roadmap as the forward development plan. Retain the original document for historical context. It also consolidates the earlier supplemental enhancement proposals. The release divisions, estimates, and future features below are proposals, not claims of completed implementation.

## Instructions for Codex / Claude

1. Inspect the current branch, `git status`, latest commits, `README.md`, the existing roadmap, build instructions, and repository agent instructions before changing anything. Reconcile this baseline with any work completed since the review.
2. Work on one phase or independently testable task at a time. Do not implement the entire roadmap in one change. Preserve unrelated user changes; do not reset, rewrite history, or force-push.
3. Before each task, identify affected modules, memory impact, save compatibility, test plan, and acceptance criteria. Prefer existing routines, data tables, assets, and shared engines over duplicate implementations.
4. Preserve original Game Boy Color hardware support, existing gameplay, save integrity, and compatible trading. Do not change the mapper, save layout, storage capacity, or link wire protocol silently. Document and test migrations and increment protocol versions when appropriate.
5. Measure actual ROM, SRAM, WRAM, HRAM, and VRAM implications where applicable. Use the repository's supported build targets, linker map and symbols; do not estimate compressed asset size from source-file length. Check bank-local capacity and fragmentation as well as totals.
6. Run focused regression tests, then the relevant broader suite. Keep artificial battle-outcome tests separate from natural gameplay and physical hardware evidence. Never claim tests passed if they were not executed.
7. At the end of each task, report changed files, actual memory deltas, tests and results, remaining risks, and the next recommended task. Update this roadmap's checkboxes only when acceptance criteria are met; distinguish implementation from verification.
8. Treat the release scope and the deferred expansions below as separate milestones. Do not pull 2.1 or 3.0 features into 2.0 without explicit approval. Ask before destructive changes, asset removal affecting player data, or major scope changes.

## Design pillars

- **Adventure:** Johto, Kanto, Orange League, movie campaigns, meaningful exploration and cinematic storytelling.
- **Collection:** Pokémon ecology, followers, team building, rare sightings, trophies and achievements.
- **Competition:** Accessible formats, repeatable cups, reliable physical multiplayer, Friend Battles and linked championships.

Protect these pillars when making memory trade-offs. Favor meaningful gameplay over padding playtime. Preserve Pokémon animation, battle effects, story music, trainer diversity and player collections where practical.

## Current baseline (source review)

| Original phase | Implementation status | Remaining work |
|---|---|---|
| 1. Engine cleanup | Implemented | Optimization and save/hardware validation |
| 2. Software clock and living world | Implemented | Hardware persistence; optional recurring activities |
| 3. Pokémon ecology | Eight profiles implemented | Pacing, broader roster coverage, hardware testing |
| 4. Narrative campaigns | Four movie campaigns implemented | Cinematic polish and alternate paths |
| 5. Regional tournaments | Six solo cups implemented | Balance, consistency, natural playthroughs |
| 6. Orange League | Four specialized challenges implemented | Presentation and hardware testing |
| 7. Cable Club and Friend Battles | Implemented | Rule consistency and robustness |
| 8. Linked World Championship | Six-on-six L50 implementation | Reconciliation, persistence, extra formats deferred |
| 9. Bedroom achievements | Implemented | Validation and later expansion |
| 10. Presentation | Partial | Shared effects, artwork, story staging |
| 11. Release testing | Partial | Full regression, natural play and physical hardware |

Core systems exist, but this does **not** establish release readiness. The baseline was reviewed through repository source, commit diffs and documentation; no independent builds or test execution were performed during the review.

### Implemented player-facing systems

- Software world clock: 90 minutes of gameplay per day, 10.5 hours per week, persisted with manual saves; no RTC hardware required.
- Field Book, next-stop guidance, quest map, radio/TV announcements and rotating rare sightings.
- Visible wild Pokémon, eight behavior profiles, noise reactions, Sweet Honey, followers and retained encounter/shiny rules.
- Four movie campaigns: Mewtwo, Lugia, Molly/Hale, Celebi/Sammy.
- Six regional cups: Rising Star, Whirl, Kimono (18 types), Dragon Masters, Rental and World Championship.
- Orange League: Cissy's Surf course, Danny's Rocky Peak ice puzzle, Rudy's three typed singles, Luana's two-Pokémon singles, Drake and Pallet Invitational.
- Cable Club: Standard, Random, Rising Star, Unrestricted and Championship; synchronization safeguards and trainer history for 65 opponents.
- Two persistent Friend Battle snapshots, 136 bytes each, with preview and removal; generated teams excluded.
- Linked World Championship: shared seed and bracket, offline quarterfinals and semifinals, reconnect to reconcile, human final or NPC final; 20-byte persistent record.
- Bedroom Orange Trophy, tiered Cup Trophy and three-page Adventure Album derived from existing flags and cup records.

## Memory baseline and accounting

Current target: **2 MiB ROM, MBC3, 32 KiB battery-backed SRAM, 32 KiB console WRAM, 16 KiB VRAM**.

Measured from the linker map at `b47b74a31` (RGBDS 1.0.4, `make` from a tidy tree; details, faithful figures and per-feature costs in [`memory-baseline.md`](memory-baseline.md), regenerated with `utils/memory_report.py`):

| Resource | Free | Largest gap | Qualification |
|---|---:|---:|---|
| ROM free | 12,993 B (12.69 KiB) | 12,741 B | Measured. 12,741 B in ROMX bank $7f; other ROMX banks 0-4 B; ROM0 199 B. Achievements, Friend Battles and the linked championship cost 4,497 B (measured) since the 17,489 B figure |
| ROM reserve | 7 KiB | | Planning target, not an allocation: 5,825 B usable after it |
| SRAM free | 152 B | 84 B | Measured (matches 444 - 2 × 136 - 20) |
| Fixed WRAM free | 16 B | 16 B | Measured; the "Misc 404" union holding the championship buffers did not grow (404 B) |
| WRAMX bank 1 free | 13 B | 13 B | Measured |
| WRAMX bank 2 free | 1,643 B | 1,628 B | Measured |
| WRAMX bank 5 free | 2,062 B | 1,950 B | Measured |
| HRAM free | 5 B | 5 B | Measured |
| VRAM | Existing allocations | | Static map shows both banks allocated; audit per screen; no assumed spare global pool |

SRAM bank 0 at baseline:

| Allocation / range | Bytes |
|---|---:|
| Friend Team 1 (`$b14d`) | 136 |
| Linked World record (`$b1d5`) | 20 |
| Remaining before backup save (`$b1e9–$b1ff`) | 23 |
| Friend Team 2 (`$bf24`) | 136 |
| Remaining after Friend Team 2 (`$bfac–$bfff`) | 84 |
| Other original bank 0 gap (`$a5e9–$a5ff`) | 23 |
| Other banks' original gaps | 22 |
| Total calculated remaining | 152 |

The checksum and save marker locations must remain compatible. SRAM is fragmented; a total of 152 free bytes does not mean there is a contiguous 152-byte region. The world link exchange buffers use an existing WRAM union; verify lifetime overlap and union size rather than assuming no cost.

### Initial measurement task

- [x] Record exact commit, toolchain and build targets; build the current ROM using the documented toolchain.
- [x] Run `make freespace` if supported, inspect `bank_ends.txt` and linker `.map` / `.sym` files.
- [x] Produce per-bank ROM/SRAM/WRAM/HRAM allocation and largest contiguous gaps (`utils/memory_report.py`, `docs/memory-baseline.md`).
- [ ] Inspect screen-specific VRAM use.
- [x] Update stale budget documentation, replacing estimates with measured values.

---

# Version 2.0 — Complete Edition

**Goal:** Finish the existing game, make core systems reliable, and add essential presentation without exceeding the 2 MiB cartridge target. Do not add new major gameplay systems to this release.

## Phase 1 — Engine stabilization (critical)

### Friend Battles

Relevant files: `engine/link/friend_teams.asm`, `engine/events/cups.asm`, `engine/battle/read_trainer_party.asm`, `constants/serial_constants.asm`, `maps/PokeCenter2F.asm`, `ram/sram.asm`, `utils/anime_events/test_friend_battles.py`, `utils/linktest/linktest.py`.

- [ ] Validate record markers, checksum, allowed format, count (1–6, exactly three for Rising Star), gender, legal species/forms, items, moves and relevant packed fields before preview or unpacking. Fail safely on invalid records.
- [ ] Test six-Pokémon records with sentinel bytes around both allocations. The header's `- 1` compensates for the `FRIEND_TEAM_MONS rb` placeholder; do not change the record length without proving an error.
- [ ] Verify full snapshot round trips, PP Ups, EVs, DVs, nature, ability, happiness, hyper training, calculated stats, HP and PP.
- [ ] Make writes interruption-safe (invalidate marker first, checksum and commit last; use a backup/journal if budget permits). Document what survives a partial write.
- [ ] Test two occupied slots, third-friend behavior, rematch replacement, deletion, random exclusion, Unrestricted and Championship capture, corrupt records and power cycles.
- [ ] Verify that offline fights use the advertised eligibility and balance rules; phase 3 implements any necessary unification.
- [ ] Confirm win/loss/draw/disconnect and cancellation behavior, party restoration and independence from lifetime opponent records.

### Linked championship

Relevant files: `engine/link/world_link.asm`, `engine/events/world_cup.asm`, `engine/link/link_rules.asm`, `engine/link/link.asm`, `maps/IndigoPlateauPokecenter1F.asm`, `maps/PokeCenter2F.asm`, `ram/sram.asm`, `ram/wram0.asm`, `utils/linktest/test_world_link.py`.

- [x] Resolve completed-bracket reconciliation. A champion or runner-up clearing a record must not cause an old partner record to recreate the tournament. Retain a compact completion receipt/tombstone or equivalent until safe retirement. *(Finished brackets keep their record with a closed bit (`WORLDLINK_CLOSED_F`); a closed record syncs with the partner's open one instead of being rejoined, and is replaced only when both players register a new bracket. Tested: champion closed vs runner-up open, then a new bracket with a new ID.)*
- [ ] Make rewards transactional across direct SRAM records and normal game saves. Prevent loss or duplication if power is interrupted before/after claiming, saving, or clearing. Test full bags and repeat prizes. *(Implemented: claiming only marks the session; `SaveGameData` closes the record after the save completes (`WorldLinkCommitClaim`). Tested: a second claim before saving is refused, a power cut before saving leaves the prize claimable, and saving closes it. Remaining: full bag and repeat-prize tests; a power cut in the few cycles between the save's checksum and the record update can still allow one duplicate.)*
- [x] Define withdrawal semantics, partner notification, abandoned brackets and stale-session handling. An explicit withdrawal must not be mistaken for incomplete registration. *(Leaving, offered at the Indigo desk when declining a round or while waiting, closes the record at its current status; the partner hears it as a forfeit of the next match (quarterfinal → out in the quarterfinal; semifinal or final → out in the semifinal). Tested: withdrawal before the quarterfinal, then the survivor's NPC final.)*
- [ ] Validate incoming state, status, ID, seed, bracket half, partner identity, rule and legal state transitions. Compare full shared tournament identity, including seed and opposite halves. Add checksum/version improvements if needed. *(Implemented: out-of-range state, half or status yields no plan, so neither side changes; brackets match only on ID, seed, opposite halves and each other's ID; the message grew to 24 bytes with separate new-bracket proposals. Tested: mismatched partners and a noisy session. Remaining: injected out-of-range values.)*
- [ ] Test one-sided registration, one-sided final result, interrupted exchanges on either side, retries, mismatched partners, draws, duplicate exchanges, stale/replayed results and disconnect at each commit boundary. A two-exchange protocol is not proof of atomic distributed commit.
- [x] Specify whether changing teams between rounds is allowed. If prohibited, store and validate a registration fingerprint; if allowed, document it explicitly. Preserve player-owned Pokémon. *(Allowed: each round takes whatever six the player brings, at level 50; documented in the README. Parties are restored by the cup runner.)*
- [ ] Verify Championship is gated or clearly directed to the appropriate post-Red progression point; avoid trapping early players in inaccessible brackets. *(Implemented: the battle desk refuses Championship rules before `EVENT_GOT_MYSTICTICKET_FROM_RED`, matching the Indigo desk. Not yet verified in the emulator.)*
- [ ] Verify trading immediately after Championship (and other formats) cannot accidentally invoke the championship session via stale `wLinkBattleRules`. Check room mode as well as rule ID where necessary. *(Implemented: the desk runs the session only when `wChosenCableClubRoom` is the Colosseum. Not yet verified with a trade in the link harness.)*
- [ ] Verify union-buffer lifetime, serial timeouts, bank restoration and protocol compatibility. Keep build fingerprints and link version behavior coherent.
- [x] Add regression scenarios for survivor losing the NPC final, eliminated partner hearing the final result, completed record retirement, natural save/reload and power loss. Ensure both participants can finish or leave without resurrecting a bracket. *(`utils/linktest/test_world_link.py`: all of these, plus mismatched partners and noise, pass over the virtual cable.)*

### General stability

- [ ] Bound generated-team retry loops in the cup and random-team generators; provide legal deterministic fallbacks or a graceful error for impossible constraints.
- [ ] Audit event-flag exhaustion, reusable flags and persistent state migration. Do not reuse flags still needed by older saves.
- [ ] Verify all CupBegin/CupEnd paths restore party data, nicknames, OT, held items, stats, moves, PP and intended healing. Check cancel, loss, reset, full bag and repeated entry.
- [ ] Audit Orange Surf checkpoint bypasses, ice-puzzle exits, out-of-order badges, and legacy badge saves.
- [ ] Verify achievement navigation, graphics restoration and legacy trophies/customization.

**Acceptance:** No reproducible save corruption, party loss, unintended duplicate/lost prizes or unrecoverable tournament sessions in the tested scenarios. All focused regression tests pass. Document residual hardware risks.

## Phase 2 — ROM and SRAM reclamation (critical)

### ROM audit and reduction

Measure net savings individually; historic numbers are rough gross estimates, not current linker measurements. Prefer removing unreachable code and little-used cosmetic options over meaningful gameplay.

| Candidate | Historical estimate | Action |
|---|---:|---|
| Remaining Game Boy Printer routines/music | ~2 KiB | Check reachability; upstream describes printer support as removed |
| Music-player-exclusive tracks | ~5.1 KiB | Preserve any story/overworld/battle tracks and required song IDs |
| Optional selectable fonts | ~3.9 KiB | Retain readable Normal/Narrow and story-required Unown; migrate old option values |
| Cosmetic Pikachu graphics | ~2.4 KiB | Share assets; preserve mechanical forms and identity |
| Alternate title music | ~1.1 KiB | Keep the selected opening and title identity |
| Textbox frame options | TBD | Reduce 20 to a smaller set only after checking saved selections |
| Unown graphics | TBD | Deduplicate/compress while preserving forms and Ruins of Alph |
| Shared battle/cup routines | TBD | Unify redundant team generation, rounds, rewards and text |
| Sprite/animation/music data | TBD | Hash identical assets; deduplicate frames/patterns; preserve animation |

- [ ] Audit current linker sections, references and compressed binary sizes.
- [ ] Remove/alias one candidate at a time, rebuild and record measured net savings.
- [ ] Test menus, legacy saves, forms, trade data and visual/audio regressions after each change.
- [ ] Preserve front-sprite animations, move animations, cries, environmental tile animation and story-specific music unless explicitly approved otherwise.
- [ ] Audit ROM bank packing; an empty bank may be more valuable than scattered bytes.

### SRAM reclamation

| Candidate | Estimated potential | Constraints |
|---|---:|---|
| Primary save padding | 392 B | Outside main checksum region; audit all writes, initialization and migration |
| Backup save padding | 393 B | Same; preserve fixed marker/checksum locations |
| Hall of Fame, 10 → 3 teams | ~686 B | Preserve most recent entries and lifetime count; verify layout/migrate safely |
| PC mailbox capacity | TBD | Measure; preserve held mail, compatibility and existing messages or provide migration |
| Obsolete legacy link rows | TBD | Confirm no remaining readers/writers; keep 65-opponent history |
| Pokémon database record compression | 414 B per byte at current 414 records | Audit 49-byte format, extra/OT fields, checksum, migration and copy-on-write slack |
| PC storage reduction | ~1,046 B per box (gross) | Last resort; do not discard existing Pokémon; preserve 400 slots if possible |

- [ ] Inspect `ram/sram.asm`, `layout.link`, `macros/ram.asm`, `constants/pokemon_data_constants.asm`, `engine/menus/save.asm`, PC database routines and save upgrade code. Verify historic layout documentation against current constants (older newbox docs describe a smaller database).
- [ ] Establish ownership of reserved bytes before reuse. Keep fixed addresses unchanged where possible; do not just delete `ds` padding and shift later fields.
- [ ] Add a named, versioned allocation plan with integrity checks, reset/erase policy and migration tests. Distinguish cartridge-lifetime records from adventure-specific state.
- [ ] Preserve primary and backup saves, existing box contents, original trainer data, nicknames, capture metadata and corruption safeguards.
- [ ] Reassess cache expansion only after championship recovery and maintenance reserves are secured.

**Planning targets:** 30–40 KiB total free ROM before presentation (stretch goal); 2–3 KiB free SRAM before expansion; 7 KiB final ROM reserve; 256–512 B final SRAM reserve. These targets may be unattainable without additional trade-offs. Reclaiming both padding regions and the estimated Hall of Fame reduction would yield ~1,623 B total free SRAM before other allocations. Do not treat theoretical totals as contiguous storage or guaranteed savings.

**Acceptance:** Measured before/after memory report; safe migration and regression tests; agreed release budget. If targets cannot be met, reduce optional presentation scope before compromising save safety.

## Phase 3 — Competitive rules unification

| Cable Club format | Level | Team size |
|---|---:|---:|
| Standard | 50 | 1–6 |
| Random | 50 | 6 generated |
| Rising Star | 30 | 3 |
| Unrestricted | 50 | 1–6 |
| Championship | 50 | 6, no eggs |

- [ ] Define one authoritative rules policy covering level, team size, eggs, species/form eligibility, duplicate species, held-item duplication, legendary/mythical restrictions, evasion and healing.
- [ ] Reuse rules validation across link registration, received teams, Friend Battles and compatible cups. Keep intentional differences (typed cups, rental generation, etc.) explicit.
- [ ] Decide whether Unrestricted's full evasion boosts are intentional; preserve universal bug fixes and synchronization protections in every format.
- [ ] Verify Rising Star offline selection and live link eligibility are consistent or clearly documented.
- [ ] Keep battle RNG deterministic on both consoles; avoid cosmetic or NPC bracket RNG interfering with combat.
- [ ] Replace fixed stronger-index NPC victories with deterministic weighted outcomes, seeded per bracket and match ID. Use the same results on both cartridges; allow upsets and provide regression fixtures. Calibrate probabilities later with simulation.
- [ ] Review early cup rewards, repeated rewards, difficulty progression, free healing and team-generation constraints.

**Acceptance:** Documented rules matrix and cross-format legality tests. Equal seeds yield identical NPC bracket outcomes regardless of clock or order of calculation. No change to link outcomes from cosmetic RNG.

## Phase 4 — Reusable cinematic engine

**Initial provisional ROM budget:** 1.5–3 KiB excluding substantial new graphics. Audit and reuse existing camera, movement, palette, sound, tile animation and battle-effect helpers before writing replacements.

- [ ] Shared begin/end scene API; safely lock input, restore camera, movement, palettes, sprites, audio and state on completion or interruption.
- [ ] Camera focus, pan, offscreen reveal and return; optional scene framing/title cards where affordable.
- [ ] Palette fade, tint, pulse, darkness and silhouette reveals.
- [ ] Configurable screen shake, flashes and dramatic pauses; optional reduced-flash/reduced-motion settings, budget permitting.
- [ ] Music fades, silence, Pokémon cries and environmental sounds.
- [ ] Reusable `!`, `?`, sleep, heart and other emotes; basic sparkles, dust, magical particles and water effects.
- [ ] Use shared graphics, temporary tile allocations and sprite budgets; gracefully degrade crowded scenes.
- [ ] Prove one representative cinematic before applying it to multiple maps.

Illustrative API (not existing assembly commands):

```text
cinematic_begin
music_fade 30
camera_focus CELEBI
palette_tint GREEN
particle_effect SPARKLES
play_sound SFX_SHINE
camera_return
palette_restore
cinematic_end
```

**Acceptance:** Reusable effects library with measured memory footprint, clean restoration, stable original-hardware timing, and no change to battle RNG or link synchronization.

## Phase 5 — Cinematic story presentation

Apply phase 4 to the existing campaigns first; do not duplicate captures or rewrite established progression unnecessarily.

- [ ] **Mewtwo Strikes Back:** Cinnabar research logs, flickering laboratory lights, cloning chamber reveals, individual clone appearances, psychic distortion, silence, Mewtwo silhouette/reveal, resolution and existing-capture echo.
- [ ] **The Power of One:** escalating storm, legendary-bird silhouettes/cries, animated elemental beacons, Melody's staging, Lawrence confrontation, Lugia emergence and restoration of daylight. Preserve alternate beacon order and original capture path.
- [ ] **Spell of the Unown:** establish Molly/Hale, spreading crystal motifs, dream palettes, floating Unown, illusion transitions, optional encounters, rescue and environmental cleanup.
- [ ] **Voice of the Forest:** dark forest palette, corrupted Pokémon, Sammy, time distortion, shrine pulse, green particles, Marauder confrontation, forest healing, departure and Oak reveal. Preserve existing Celebi capture.
- [ ] **Orange League:** water splashes and buoy feedback for Cissy; wind, ice and cold summit palette for Danny; typed battle introductions for Rudy; partnership staging for Luana; Dragonite reveal and trophy ceremony for Drake.
- [ ] **Pallet Invitational:** distinctive introductions, Tracey's sketch and a satisfying conclusion.
- [ ] **Battle presentation:** selectively enhance legendary/champion/shadow entrances and victory moments; consider critical-hit feedback, hit-stop and final-Pokémon music only if timing and memory permit.
- [ ] **Audio direction:** reuse suitable themes, offscreen cries, wind/thunder, discovery cues and fanfares; restore normal music correctly after each scene.

**Acceptance:** Campaigns remain playable in every supported order and on legacy saves. Effects terminate cleanly. No extra captures, broken scripts, or unrecoverable map/graphics/audio state. Validate reduced-flash behavior and crowded scenes.

## Phase 6 — Character artwork and presentation

Prioritize recognizable characters and consistent Generation II visual style over costly dedicated backgrounds.

| Priority | Characters |
|---|---|
| Highest | Ash, Tracey |
| High | Drake, Cissy, Danny, Rudy, Luana, Molly, Iron Mask Marauder |
| Medium | Melody, Lawrence III, Sammy and other visiting trainers |

- [ ] Audit existing assets and record artist/source/license/permission before importing or adapting external artwork.
- [ ] Create or acquire authorized overworld sprites and trainer portraits; reuse frames and palettes where practical.
- [ ] Add selective cinematic tiles for lab, crystals, forest, tournament scenes and bedroom.
- [ ] Improve tournament introductions, trophies and results using shared layouts and existing assets.
- [ ] Verify palette readability and animations at 160×144 on the GBC screen.
- [ ] Optional: custom introduction/title screen after mandatory features fit. Retain a single coherent opening and title track.

**Acceptance:** Every imported asset has documented provenance and appropriate permission; artwork fits the measured budget and original hardware constraints.

## Phase 7 — Release validation

- [ ] Build all supported release variants using a reproducible toolchain; record ROM hashes, linker maps, symbols and final free-space report.
- [ ] Run repository-supported build/test commands, `utils/anime_events/run_checks.py`, encounter/reachability suites, battle simulator ROM-oracle checks and link harness scenarios as applicable. Consult actual usage instructions rather than assuming arguments.
- [ ] Complete a natural playthrough from New Bark through Johto, Kanto, Red, all four movie campaigns, Orange League and Pallet Invitational.
- [ ] Test alternate quest order, losses, retries, pending prizes, full bags, existing legendary catches, manual saving and resuming.
- [ ] Complete all six cups and all 18 Kimono types; test rotation at clock wrap, eligibility, balance and restoration.
- [ ] Verify all achievement pages, trophy tiers, legacy decorations and diploma.
- [ ] Test every Cable Club format and compatible trading, including mismatched versions/formats, differing clocks, disconnect/reconnect and full-party normalization.
- [ ] Test Friend Battles after power cycling and every linked championship outcome, interrupted registration/finals/rewards, repeated synchronization and withdrawals.
- [ ] Verify old primary/backup saves, legacy boxed forms, save migration, software clock and cartridge-lifetime records.
- [ ] Test on actual supported GBC cartridges and physical link cables (not just emulator serial). Check normal/double-speed behavior, frame pacing, OAM limits and graphics restoration.
- [ ] Publish release notes, supported hardware/builds, save backup/migration instructions, known limitations, credits and patch distribution instructions. Avoid distributing copyrighted base ROMs.

**Release gate:** Feature implementation alone is insufficient. Ship only after required regressions and physical hardware validation are documented, critical issues are resolved, the ROM fits 2 MiB, and memory reserves or any approved deviations are recorded.

---

# Version 2.1 — Living World & Cinematic Update

**Goal:** Deepen exploration, atmosphere and repeatable competition without abandoning the original hardware target. Start after 2.0 is stable. Scope each feature against measured memory; not all proposals need to ship in one update.

## Phase 8 — Advanced Pokémon ecology

- [ ] Expand the eight existing behavior profiles across the roster using compact defaults, overrides and form-specific rules where justified.
- [ ] Improve schooling and aquatic movement, nocturnal activity/sleep, curiosity, territorial warnings/pursuit, aggressive and elusive reactions, stationary species and movement speeds.
- [ ] Expand Sweet Honey compatibility and reactions to player noise (standing, walking, running, cycling, surfing).
- [ ] Add reusable behavioral emotes: `!`, `?`, sleep, heart, ellipsis and musical note where sprite capacity permits.
- [ ] Preserve encounter tables, time/swarm/roamer rules, shiny odds, repel behavior and nonblocking movement.
- [ ] Test reachable tiles, boundaries, directional walls, ledges, ice, water, warps and NPC interactions; degrade gracefully with followers and crowded routes.

**Acceptance:** Meaningful observable behavior variety with no encounter distribution regressions, trapping or unacceptable frame-time increase.

## Phase 9 — Environmental presentation

- [ ] Stylized lighting: windows, caves, torches, shrines and palette-based light shafts.
- [ ] Weather: rain, fog, lightning, snow and storm intensity, reusing existing weather systems where available.
- [ ] Tile animation: water, flowers, machinery, flags and crystals.
- [ ] Reusable location title cards.
- [ ] Running dust, grass rustle, surf ripples, fishing splashes, item/shiny sparkles, honey cues and legendary cries.
- [ ] Audit existing effects before duplicating them; allocate tiles per screen and share assets with phase 4.

**Hardware limits:** 160×144 display, 40 OAM sprites total, 10 sprites per scanline, 16 KiB VRAM across two banks. Reserve capacity for the player, follower, NPCs and wild Pokémon. Prioritize gameplay readability over decorative effects.

**Acceptance:** Stable framerate, no persistent tile corruption or excessive sprite flicker, and correct state restoration after menus, maps and battles.

## Phase 10 — Recurring living world

- [ ] Daily/weekly rotating specialty merchants and stock.
- [ ] Traveling trainers and rotating opponents.
- [ ] Expanded rare sightings and time-dependent NPC appearances.
- [ ] Regional weekly events and optional daily/weekly challenges.
- [ ] Radio/TV reports and Field Book activity directory: today's events, upcoming cups, incomplete quests, pending rewards and legendary leads.
- [ ] Derive schedules and stock from the software clock and deterministic seeds when possible; avoid unnecessary saved state.
- [ ] Preserve clock migration and wrap consistency with all 18 Kimono types and seven weekdays.
- [ ] Defer full seasons until the clock, art and map budget is approved.

**Acceptance:** Recurring activities remain deterministic where required, work after save/reload, and provide useful reasons to revisit locations without forcing excessive waiting or grinding.

## Phase 11 — Tournament evolution

- [ ] **Rising Star:** rotating opponents, suitable early difficulty and explicitly documented eligibility.
- [ ] **Whirl:** Water-type opponent pool, rain strategies and diverse competitive teams.
- [ ] **Kimono:** upcoming type, all 18 completion view, distinct celebration of full mastery.
- [ ] **Dragon Masters:** varied Dragon teams with complementary support Pokémon.
- [ ] **Rental:** preview moves, held items, abilities and stats; improve legal generated-team variety.
- [ ] **World Championship:** visual bracket, deterministic weighted NPC upsets, opponent introductions, results and standings even after elimination; reuse the shared seed and match outcomes.
- [ ] Generalize round, reward, selection and result helpers across cups. Preserve party restoration and bounded generation.
- [ ] Add opening ceremonies, versus cards, crowd/fanfare and trophy scenes using the cinematic library.
- [ ] Add optional repeatable Cissy/Danny challenges and rotating Rudy opponents; preserve Luana singles until doubles exist.
- [ ] Extend linked championships to Rising Star, Random and Unrestricted after the standard Championship is stable. Define team locks, shared rules and generated-team persistence as needed.
- [ ] Add compact entries/wins/streaks and championship statistics, with per-type Kimono records only as budget permits.

**Acceptance:** Distinct tournament identities, legal and balanced teams, stable deterministic linked brackets, no duplicated rewards, measured runtime and storage costs.

## Phase 12 — Persistent multiplayer expansion

Prioritize only after SRAM reclamation, recovery metadata and save safety are proven. Example allocations, not commitments:

| Feature | Provisional SRAM budget |
|---|---:|
| Four additional friend slots (six total) | 544 B at 136 B/slot |
| Championship recovery/history | 128–256 B |
| Trainer Card aggregate format stats | 50–200 B |
| Seasonal competitive history | 100–250 B |
| Regional cup statistics | 50–100 B |

- [ ] Expand Friend Battle cache, add favorites/protection and clear replacement/update notifications.
- [ ] Improve preview with moves, abilities, items and stats; add configurable AI difficulty if meaningful.
- [ ] Extend Trainer Card aggregate stats and personal records without deleting the existing 65-opponent history.
- [ ] Preserve the distinction between real link results, offline practice and generated rentals.
- [ ] Add season archive and personal bests using the existing manually reset yearly records, if capacity permits.
- [ ] Maintain validity markers, checksums, safe writes and migration policy; measure fragmented capacity, not just totals.

**Acceptance:** Persistent features survive restarts and safe upgrades, do not compromise existing records, and remain within an explicit SRAM budget.

## Phase 13 — Advanced Adventure Album and Pokémon achievements

- [ ] Extend the current Leagues, Stories and Cups pages with Pallet Invitational, Legends, Link, Records and Exploration as appropriate.
- [ ] Improve navigation (left/right page selection; B exits), layout, trophy tiers and descriptions.
- [ ] Use existing flags/records and derived counters before allocating new saved bits.
- [ ] Distinguish one Kimono victory from mastery of all 18 types.
- [ ] Investigate individual Pokémon ribbons (Indigo, Orange, Kimono Master, World Champion) and compact achievement bitfields. Audit existing extra fields and link/save formats first; do not assume bytes marked extra are unused.
- [ ] Optional lifetime Pokémon statistics only if storage and identity semantics permit; four extra bytes across 414 records would cost 1,656 B before other overhead.
- [ ] Preserve earned trophies, bedroom customization and Pokédex diploma on legacy saves.

**Acceptance:** Accurate retrospective progress from older saves, meaningful persistent achievements, no loss of existing Pokémon data, and clear display on the GBC screen.

## Phase 14 — Short legendary investigations

- [ ] Mew: research documents, sightings and Faraway Island investigation.
- [ ] Ho-Oh: Burned Tower history, the beasts and a cinematic Tin Tower appearance.
- [ ] Entei: sightings, volcanic imagery and Johto folklore.
- [ ] Raikou: electrical disturbances, storms and radio reports.
- [ ] Suicune: Eusine, water purification and investigation.
- [ ] Connect quest hints to the Field Book and existing capture routes. Keep these atmospheric and concise; avoid duplicate captures and preserve story flags.

**Acceptance:** Quests work with previously caught legendaries and existing saves, and integrate cleanly with the current adventure rather than replacing it.

## Phase 15 — Competitive simulation and AI

- [ ] Audit existing `meta_sim` tools, assumptions, coverage and ROM-oracle tests before extending them.
- [ ] Support family, rental and legal competitive stat profiles; respect actual EV/DV and hyper-training rules.
- [ ] Increase simulation samples where useful, measure uncertainty, evaluate type matchups, team roles/synergy and switching.
- [ ] Calibrate tournament difficulty and deterministic NPC win probabilities using documented inputs.
- [ ] Regression-report damage, accuracy, status, speed, stats and competitive balance after engine changes.
- [ ] Incrementally improve switching, hazards, setup, recovery, team awareness and endgame decisions; profile on original hardware.
- [ ] Keep major AI overhaul separate from routine balancing and preserve link determinism.

**Acceptance:** Reproducible simulator results validated against the ROM; measurable AI improvements without excessive CPU time or regressions. Confirm with natural gameplay.

### 2.1 release gate

Repeat the relevant 2.0 regression and physical tests, especially scene restoration, ecology/clock interactions, all tournament formats, legacy saves and memory usage. Do not ship optional systems that exceed hardware limits or compromise compatibility.

---

# Version 3.0 — Expanded Link Edition (experimental)

**Goal:** Investigate larger architectural changes in separate branches. These are optional future projects, not prerequisites for 2.0 or 2.1. Prove each subsystem before committing to a combined release.

## Phase 16 — Expanded cartridge architecture

| Resource | Current | Eventual MBC5 target ceiling |
|---|---:|---:|
| ROM | 2 MiB | 8 MiB |
| SRAM | 32 KiB | 128 KiB |
| Console WRAM | 32 KiB | Unchanged |
| VRAM | 16 KiB | Unchanged |

- [ ] Start with a 4 MiB MBC5 proof of concept; confirm supported physical cartridges and RAM configuration.
- [ ] Audit mapper initialization, ROM/SRAM bank selectors, far pointers, bank stack, interrupt handling, bank-0 behavior, linker rules and cartridge header.
- [ ] Audit 8-bit bank assumptions before considering 8 MiB (requires 9-bit bank numbers).
- [ ] Design explicit save migration, backup/rollback strategy and compatibility tests; do not overwrite existing saves blindly.
- [ ] Validate actual cartridge save retention, normal/double speed, physical cable, emulators and any flash cart targets.
- [ ] Re-budget ROM/SRAM for new content. Larger cartridge capacity does not solve WRAM, VRAM, CPU or OAM limitations.

**Acceptance:** Reproducible build and physical hardware proof of expanded bank access and safe persistence. Maintain a stable 2 MiB release branch independently.

## Phase 17 — Link Adventure Mode

**Core design:** Two linked players see one another in the overworld while retaining independent worlds. Do not synchronize entire story state, inventory, NPCs, wild encounters, clocks or saves. Each player's collision and progression remain independent. A remote avatar is non-solid and visible only in the same map.

- [ ] Prototype nonblocking background serial communication with clear clock roles, bounded packet handling, sequence/checksum validation and timeout/reconnect behavior.
- [ ] Synchronize same-map presence, coordinates, facing, movement/step phase and appearance; interpolate remote movement.
- [ ] Handle map transitions, menus, dialogue, battles, disconnects, inactive peers and different story geometry gracefully.
- [ ] Verify remote avatars cannot block local movement or trigger local events.
- [ ] Add remote followers only after sprite/VRAM budget is proven; add emotes and a Pokégear locator as optional enhancements.
- [ ] Introduce explicit battle/trade/card invitations and clean transitions into the existing blocking link protocol.
- [ ] Stress-test two physical consoles, cable noise, different clocks and progression, rapid map transitions, sprite limits and frame performance.

**Acceptance:** Minimal two-player same-map prototype works on physical cable without damaging local gameplay or saves; later enhancements remain optional. Do not assume emulator-only multiplayer implementations translate directly to hardware.

## Phase 18 — Double battles

- [ ] Audit current two-battler assumptions and investigate reusable implementations only with appropriate source access and licensing.
- [ ] Prototype four active battler slots and target selection, turn ordering, spread moves, friendly fire and switches.
- [ ] Implement partner/target-aware abilities, move effects, AI, HP/status displays, animations and victory conditions.
- [ ] Budget four battlers in WRAM/VRAM and verify GBC timing and readability.
- [ ] Extend link action/target exchange, RNG synchronization, fingerprints and disconnect recovery; increment protocol version as appropriate.
- [ ] Extend simulator and automated regression suite to doubles.
- [ ] Introduce authentic doubles with Luana first; consider doubles tournaments, rental doubles and linked doubles after proof of stability.

**Acceptance:** Correct single-player doubles and regression-safe singles before enabling linked doubles. Physical validation and measured performance are required.

## Phase 19 — Hoenn expansion (optional)

**Proposed regional challenge:** A fresh adventure in Hoenn using the 135 Pokémon introduced in Generation III, not simply another area traversed by an overleveled Johto team.

- [ ] Confirm expanded mapper, memory budget, species/form IDs, data tables and save support before committing to full region development.
- [ ] Design Littleroot start with Treecko, Torchic and Mudkip; define a clear regional team policy.
- [ ] Preserve existing Pokémon, items, records and progress safely outside the regional challenge; design import/export eligibility and reunification after completion.
- [ ] Plan maps, routes, towns, eight gyms, Team Magma/Aqua, Hoenn League, regional encounters, quests and postgame.
- [ ] Create or acquire authorized assets, map tooling and data conversion workflows; do not assume other ROM hacks' source or assets are reusable.
- [ ] Consider Tate & Liza doubles and expanded cross-region competition only once doubles are stable.
- [ ] Extend Field Book, quest maps, Pokédex, achievements, simulator, save migration and hardware validation.

**Acceptance:** A coherent regional adventure with safe preservation of existing teams and progress. Treat the region as a separate milestone with its own scope, budget, and validation.

---

## Master phase tracker

### 2.0 — Complete Edition

- [ ] 1. Engine stabilization
- [ ] 2. ROM and SRAM reclamation
- [ ] 3. Competitive rules unification
- [ ] 4. Reusable cinematic engine
- [ ] 5. Cinematic story presentation
- [ ] 6. Character artwork
- [ ] 7. Release validation

### 2.1 — Living World & Cinematic Update

- [ ] 8. Advanced Pokémon ecology
- [ ] 9. Environmental presentation
- [ ] 10. Recurring living world
- [ ] 11. Tournament evolution
- [ ] 12. Persistent multiplayer expansion
- [ ] 13. Advanced Adventure Album and Pokémon achievements
- [ ] 14. Short legendary investigations
- [ ] 15. Competitive simulation and AI

### 3.0 — Expanded Link Edition (experimental)

- [ ] 16. Expanded cartridge architecture
- [ ] 17. Link Adventure Mode
- [ ] 18. Double battles
- [ ] 19. Hoenn expansion (optional)

## Immediate next work order

1. Establish a fresh build and exact memory baseline.
2. Fix/verify championship completion, reward persistence, withdrawal and stale-session reconciliation; add targeted regression tests.
3. Harden Friend Battle record validation and safe updates.
4. Audit and reclaim SRAM padding, followed by approved storage reductions if necessary; audit ROM savings one feature at a time.
5. Unify competitive rules and add deterministic weighted bracket outcomes.
6. Implement a minimal reusable cinematic engine, then apply it to existing campaigns and artwork within measured limits.
7. Complete release validation on actual hardware before expanding the scope.

## Per-task completion report template

```markdown
### Task / phase
- Status: planned | implemented | verified | blocked
- Commit / changed files:
- Behavior implemented:
- Compatibility and migration implications:
- ROM free before / after / delta:
- SRAM free before / after / delta (per bank and largest gap):
- WRAM/HRAM/VRAM impact:
- Tests executed and results:
- Tests not executed / hardware validation outstanding:
- Known limitations and follow-up:
- Next recommended task:
```

## Reference paths

- `README.md`
- `docs/link-edition-2.0-roadmap.md`
- `docs/newbox_format.md` (verify against current constants)
- `ram/sram.asm`, `ram/wram0.asm`, `layout.link`, `macros/ram.asm`
- `constants/serial_constants.asm`, `constants/cup_constants.asm`, `constants/pokemon_data_constants.asm`
- `engine/link/link.asm`, `engine/link/link_rules.asm`, `engine/link/link_failsafe.asm`, `engine/link/friend_teams.asm`, `engine/link/world_link.asm`
- `engine/events/cups.asm`, `engine/events/cup_teams.asm`, `engine/events/world_cup.asm`, `engine/events/achievements.asm`
- `engine/menus/save.asm`, `engine/menus/link_card.asm`
- `engine/overworld/wild_behavior.asm`, `data/wild/behaviors.asm`
- `maps/PokeCenter2F.asm`, `maps/IndigoPlateauPokecenter1F.asm`
- `utils/anime_events/`, `utils/linktest/`, `utils/wild_mons/`, `utils/audit/`, `meta_sim/`

**Final principle:** Finish and protect what already works. Optimize, unify, and polish the existing experience before adding another major gameplay system.
