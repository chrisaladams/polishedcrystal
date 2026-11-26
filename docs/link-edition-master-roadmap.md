# Pokémon Polished Crystal: Link Edition — Master Development Roadmap

**Active milestones:** 2.0 Complete Edition and 2.1 Living World & Cinematic Update.

**Current plan:** the owner's [updated roadmap for 2.1](roadmap-2.1.md) sets the
phases and work order. This document keeps the per-item implementation evidence.

**Takeover baseline:** `b959d22ae5162aafd6488b90d0504f0d45465707` on
`claude/sleepy-ramanujan-kc278b`. Build and test evidence is in the
[memory and testing baseline](memory-baseline.md). The
[original 2.0 roadmap](link-edition-2.0-roadmap.md) records the earlier phases.

## Owner requirements and engineering judgment

- Finish the planned work through 2.1. Preserve current content and
  functionality while correcting demonstrated defects.
- Use engineering judgment for implementation, testing and lossless
  optimization. Consult the owner before significant product or architecture
  decisions, including cuts, reduced features, changed gameplay rules, mapper
  or save-layout changes, and incompatible link changes.
- Treat the feature ideas and estimates in this document as proposals where
  their approval is unrecorded. Keep existing player-facing rules and
  previously approved decisions, including the fixed competitive battle
  settings documented in [L20](issue-ledger.md).
- Use the current cartridge and protocol as the starting point for
  measurements. Record ROM bank fit and runtime scratch-space lifetimes.
  Document save and trade compatibility, migration, failure recovery and
  hardware evidence before calling a release ready.

## Design pillars

- **Adventure:** Johto, Kanto, Orange League, movie campaigns, meaningful exploration and cinematic storytelling.
- **Collection:** Pokémon ecology, followers, team building, rare sightings, trophies and achievements.
- **Competition:** Accessible formats, repeatable cups, reliable physical multiplayer, Friend Battles and linked championships.

Use these pillars to assess additions and polish. Preserve the existing adventure, collection and competition features.

## Current implementation

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

Core systems exist. Release validation still includes natural progression, existing saves and original GBC hardware.

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

The current standard builds use 2 MiB MBC3 ROM and four SRAM banks (32 KiB).
With RGBDS 1.0.4 at the takeover commit, default has **9,675 B** of free
ROM and faithful has **9,736 B**. The largest ROMX gaps are **9,434 B** and
**9,476 B** in bank `$7f`. Both have 923 B SRAM free across four banks
(largest gap 393 B), 9 B WRAM0 free, 3,574 B WRAMX free and 5 B HRAM free.
VRAM is fully assigned on the static map. Measure actual tile and OAM
use in the screens a feature touches. See the
[per-bank measurements and repair delta](memory-baseline.md).

The prior 7 KiB ROM reserve, 30–40 KiB stretch target and SRAM reserve targets
were planning illustrations. Set a release budget with the owner if measured
feature and compatibility requirements make it a product decision.

---

# Version 2.0 — Complete Edition

**Goal:** Stabilize the current adventure and linked competition, finish the essential presentation work, and verify release readiness on the current GBC builds.

## Phase 1 — Engine stabilization (critical)

### Friend Battles

Relevant files: `engine/link/friend_teams.asm`, `engine/events/cups.asm`, `engine/battle/read_trainer_party.asm`, `constants/serial_constants.asm`, `maps/PokeCenter2F.asm`, `ram/sram.asm`, `utils/anime_events/test_friend_battles.py`, `utils/linktest/linktest.py`.

- [ ] Validate record markers, checksum, allowed format, count (1–6, exactly three for Rising Star), gender, legal species/forms, items, moves and relevant packed fields before preview or unpacking. Fail safely on invalid records. *(Implemented in `CheckFriendTeamFields`: marker, checksum, rules (not Random, in range), gender, count (three for Rising Star), and per Pokémon a real species (not $00/$ff, extended ones up to `NUM_SPECIES`), no egg, an item, a first move and a nature. An unusable record reads as an empty slot. Tested field by field in `test_friend_records.py`. Form numbers aren't checked against each species, by evaluation: an unknown form falls back to the plain one, and `test_friend_battles.py` plays Look, the summary screen and a battle with a form-31 Pokémon (no species has it) to the end. All move IDs are valid because `NUM_ATTACKS` is $ff.)*
- [x] Test six-Pokémon records with sentinel bytes around both allocations. The header's `- 1` compensates for the `FRIEND_TEAM_MONS rb` placeholder; do not change the record length without proving an error. *(Writing a six-Pokémon record into either slot changes no byte of SRAM bank 0 outside it; the length is unchanged.)*
- [x] Verify full snapshot round trips, PP Ups, EVs, DVs, nature, ability, happiness, hyper training, calculated stats, HP and PP. *(Unpacked at level 50, every field and stat matches the game's own level-50 version of the original (`BT_SetLevel`). This found and fixed a bug: the hyper-training byte's two other bits were taken as hyper training, raising a stat.)*
- [x] Make writes interruption-safe (invalidate marker first, checksum and commit last; use a backup/journal if budget permits). Document what survives a partial write. *(Marker cleared first, checksum then marker written last; tested that the marker stays cleared throughout a write. A partial write leaves that slot empty, losing that friend's previous team; the other slot is untouched. The proposed 143 B journal fits a current SRAM gap and is a separate recovery design decision.)*
- [ ] Test two occupied slots, third-friend behavior, rematch replacement, deletion, random exclusion, Unrestricted and Championship capture, corrupt records and power cycles. *(Tested: two slots, a third friend not kept, a rematch replacing that friend's record, Random excluded, Unrestricted and Championship kept, corrupt records (`test_friend_records.py`), deletion (`test_friend_battles.py`). An emulated cartridge image captured mid-write verifies recovery for both slots. Physical power cycling remains open.)*
- [ ] Verify that offline fights use the advertised eligibility and balance rules; phase 3 implements any necessary unification.
- [ ] Confirm win/loss/draw/disconnect and cancellation behavior, party restoration and independence from lifetime opponent records.

### Linked championship

Relevant files: `engine/link/world_link.asm`, `engine/events/world_cup.asm`, `engine/link/link_rules.asm`, `engine/link/link.asm`, `maps/IndigoPlateauPokecenter1F.asm`, `maps/PokeCenter2F.asm`, `ram/sram.asm`, `ram/wram0.asm`, `utils/linktest/test_world_link.py`.

- [x] Resolve completed-bracket reconciliation. A champion or runner-up clearing a record must not cause an old partner record to recreate the tournament. Retain a compact completion receipt/tombstone or equivalent until safe retirement. *(Finished brackets keep their record with a closed bit (`WORLDLINK_CLOSED_F`); a closed record syncs with the partner's open one instead of being rejoined, and is replaced only when both players register a new bracket. Tested: champion closed vs runner-up open, then a new bracket with a new ID.)*
- [ ] Resolve two reproduced prize recovery edge cases. Normal Continue and backup checksum recovery preserve the saved prize and receipt. A restored older backup can disagree with the closed bracket record. New Game in the save-to-close window can inherit a bracket whose prize the previous adventure already saved. Preserve the cartridge-lifetime bracket and decide the intended recovery behavior before changing persistence. See L1 in the [issue ledger](issue-ledger.md).
- [x] Define withdrawal semantics, partner notification, abandoned brackets and stale-session handling. An explicit withdrawal must not be mistaken for incomplete registration. *(Leaving, offered at the Indigo desk when declining a round or while waiting, closes the record at its current status; the partner hears it as a forfeit of the next match (quarterfinal → out in the quarterfinal; semifinal or final → out in the semifinal). Tested: withdrawal before the quarterfinal, then the survivor's NPC final.)*
- [ ] Validate incoming state, status, ID, seed, bracket half, partner identity, rule and legal state transitions. Compare full shared tournament identity, including seed and opposite halves. Add checksum/version improvements if needed. *(Implemented: out-of-range state, half or status yields no plan, so neither side changes; brackets match only on ID, seed, opposite halves and each other's ID; the message grew to 24 bytes with separate new-bracket proposals. Tested: mismatched partners and a noisy session. Remaining: injected out-of-range values.)*
- [ ] Test one-sided registration, one-sided final result, interrupted exchanges on either side, retries, mismatched partners, draws, duplicate exchanges, stale/replayed results and disconnect at each commit boundary. A two-exchange protocol is not proof of atomic distributed commit.
- [x] Specify whether changing teams between rounds is allowed. If prohibited, store and validate a registration fingerprint; if allowed, document it explicitly. Preserve player-owned Pokémon. *(Allowed: each round takes whatever six the player brings, at level 50; documented in the README. Parties are restored by the cup runner.)*
- [ ] Verify Championship is gated or clearly directed to the appropriate post-Red progression point; avoid trapping early players in inaccessible brackets. *(Implemented: the battle desk refuses Championship rules before `EVENT_GOT_MYSTICTICKET_FROM_RED`, matching the Indigo desk. Not yet verified in the emulator.)*
- [x] Verify trading immediately after Championship (and other formats) cannot accidentally invoke the championship session via stale `wLinkBattleRules`. Check room mode as well as rule ID where necessary. *(The desk runs the session only when `wChosenCableClubRoom` is the Colosseum, and the trade room skips the options and rules checks. Verified over the virtual cable: `linktest.py --trade --last-rules world,normal` (one side's last battle Championship, the other's Standard) and `--last-rules world` (both): both reach the Trade Center.)*
- [ ] Verify union-buffer lifetime, serial timeouts, bank restoration and protocol compatibility. Keep build fingerprints and link version behavior coherent.
- [x] Add regression scenarios for survivor losing the NPC final, eliminated partner hearing the final result, completed record retirement, natural save/reload and power loss. Ensure both participants can finish or leave without resurrecting a bracket. *(`utils/linktest/test_world_link.py`: all of these, plus mismatched partners and noise, pass over the virtual cable.)*

### General stability

- [x] Bound team generation after eight restarts and test deterministic fallback under the current pools. See L2 and `test_team_generation.py`.
- [ ] Audit the second pass with a depleted typed pool. It currently relaxes the type rule. Confirm what the player sees and report options if graceful refusal would change an advertised rule.
- [x] Audit event-flag exhaustion, reusable flags and persistent state migration. Do not reuse flags still needed by older saves. *([`event-flags.md`](event-flags.md): 2,304 flags, all taken but 16 retired slots. The rules for reusing one say an old save may still have it set. The family's three saves have none set.)*
- [ ] Complete the CupBegin/CupEnd matrix for cancel, loss, reset, full bags and re-entry. Byte-for-byte party restoration apart from intended healing is exercised across all six cups plus Rudy, Luana and Friend Battles (L6).
- [ ] Audit Orange Surf checkpoint bypasses, ice-puzzle exits, out-of-order badges, and legacy badge saves.
- [ ] Validate graphics restoration and legacy trophies and customization. Album navigation and the Kimono mastery tally already exist.
- [x] Fix the Quest Map pin list being overwritten by the linked Championship lookup when many leads coexist. The regression checks the displayed order, a single Indigo entry and read-only SRAM behavior.

**Acceptance:** No reproducible save corruption, party loss, unintended duplicate/lost prizes or unrecoverable tournament sessions in the tested scenarios. All focused regression tests pass. Document residual hardware risks.

## Phase 2 — Lossless memory optimization

- [x] Measure current bank capacity and compare against the C0 build.
- [x] Reclaim 785 B from unused save padding without moving the guarded
  checksum addresses. Unrestricted Friend levels subsequently used 14 B.
- [x] Share the byte-identical Nidorina walking sprite, preserving its
  palette (249 B saved in the earlier build).
- [ ] Measure lossless compression, deduplication, shared routines and
  bank packing. Remove code only with a reachability and compatibility
  check. Compare both cartridge builds, behavior and save guards.
- [ ] Audit screen-specific VRAM/OAM and scratch lifetimes before allocating
  effects. Fixed WRAM and HRAM are particularly tight.
- [ ] For new persistence, audit the actual storage format, record lifetime,
  checksum, recovery and migration. Use the
  [current allocation plan](sram-allocation.md).

The [historical ROM audit](rom-reclamation-audit.md) records reachable
assets and their measured sizes. All existing assets, options, content and
storage capacities are part of the preservation requirement. If the 2.1
work exceeds measured capacity, quantify the constraint and bring lossless
or architectural options to the owner before committing to a trade-off.

## Phase 3 — Competitive rules unification

| Cable Club format | Level | Team size |
|---|---:|---:|
| Standard | 50 | 1–6 |
| Random | 50 | 6 generated |
| Rising Star | 30 | 3 |
| Unrestricted | Own levels | 1–6 |
| Championship | 50 | 6, no eggs |

- [x] Define one authoritative rules policy covering level, team size, eggs, species/form eligibility, duplicate species, held-item duplication, legendary/mythical restrictions, evasion and healing. *([`rules-matrix.md`](rules-matrix.md); one table, `LinkBattleRuleTable`, with a flags column. Decided: Standard is level 50 with one legendary at most, and Unrestricted keeps levels and allows anything. Link version 4.)*
- [x] Reuse rules validation across link registration, received teams, Friend Battles and compatible cups. Keep intentional differences (typed cups, rental generation, etc.) explicit. *(One checker for the desk, received teams and your Friend Battle team (`CheckFriendBattleTeam`, from the cup runner). The cups' deliberate differences are listed in the matrix. Tested: `test_link_rules.py`, 65 checks.)*
- [x] Decide whether Unrestricted's full evasion boosts are intentional; preserve universal bug fixes and synchronization protections in every format. *(Decided: no. Evasion stops at +2 in every link format and in Friend Battles. Tested: `test_link_rules.py` runs the accuracy check with +6 evasion in each case.)*
- [x] Verify Rising Star offline selection and live link eligibility are consistent or clearly documented. *(They differed: the cup's Battle Tower picker had the Species and Item Clauses, and the link desk didn't. Link Rising Star has them now.)*
- [x] Keep battle RNG deterministic on both consoles; avoid cosmetic or NPC bracket RNG interfering with combat. *(Bracket results use their own xorshift from the bracket seed, never the battle's or the overworld's random numbers. The offline draw takes its seed from `Random`, outside any battle.)*
- [x] Replace fixed stronger-index NPC victories with deterministic weighted outcomes, seeded per bracket and match ID. Use the same results on both cartridges; allow upsets and provide regression fixtures. Calibrate probabilities later with simulation. *(`WorldCupWinner`: 60–90% for the stronger, from the seed and match number, in the linked and offline brackets. Fixtures: `test_bracket.py` checks 203 cases against `utils/world_cup/bracket.py`, whose report gives the outcomes over every seed. `test_world_link.py` and `test_cups.py` follow the model. Calibration by battle simulation is still open.)*
- [x] Review early cup rewards, repeated rewards, difficulty progression, free healing and team-generation constraints. *([`cup-rewards-review.md`](cup-rewards-review.md). One change: the Rising Star Cup's repeat Rare Candy is once a day, since it was unlimited from the start. Everything else stays: one-time early prizes, post-game Bottle Caps, healing when a cup ends, and fixed cup levels with their gates. Tested in `test_cups.py`.)*

**Acceptance:** Documented rules matrix and cross-format legality tests. Equal seeds yield identical NPC bracket outcomes regardless of clock or order of calculation. No change to link outcomes from cosmetic RNG.

## Phase 4 — Reusable cinematic engine

**Initial provisional ROM budget:** 1.5–3 KiB excluding substantial new graphics. Audit and reuse existing camera, movement, palette, sound, tile animation and battle-effect helpers before writing replacements.

- [x] Shared begin/end scene API; safely lock input, restore camera, movement, palettes, sprites, audio and state on completion or interruption. *(`scene_begin` / `scene_end` ([`cinematics.md`](cinematics.md)). They restore the exact palettes, recompute sprite palettes, and restart the map's music only if the scene changed it. Lightning is held off. The script engine already locks input. Tested: `test_cinematic.py`.)*
- [ ] Camera focus, pan, offscreen reveal and return; optional scene framing/title cards where affordable. *(Not done: Gen 2's overworld has no camera; see [`cinematics.md`](cinematics.md).)*
- [x] Palette fade, tint, pulse, darkness and silhouette reveals. *(`scene_tint` (7 colors, compounding; two `TINT_DARK` for darkness), `scene_pulse`, `scene_silhouette`, faded with the engine's `FadePalettes`. Exact colors tested.)*
- [x] Implement Flash & Shake. Turning it off suppresses scene flashes and pulses, weather lightning visuals and earthquake motion while retaining scene timing where applicable. `test_cinematic.py` exercises the option and lifecycle.
- [x] Music fades, silence, Pokémon cries and environmental sounds. *(The engine's `musicfadeout`, `cry` and `playsound`; `scene_end` brings the map's music back.)*
- [ ] Reusable `!`, `?`, sleep, heart and other emotes; basic sparkles, dust, magical particles and water effects. *(The emotes exist (`showemote`). Added: a sparkle emote in gold, green and purple, one shared 48-byte graphic, used for Celebi, the Unown illusion, Drake's trophy and the Pallet finals. Not yet: dust and water.)*
- [ ] Use shared graphics, temporary tile allocations and sprite budgets; gracefully degrade crowded scenes.
- [x] Prove one representative cinematic before applying it to multiple maps. *(The Mewtwo clones' opening in Cerulean Cave B1F: silence, psychic pulses, purple light, cry and flash, then colors and music back before the battle. `test_movie_events.py` still plays it through.)*

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

- [ ] **Mewtwo Strikes Back:** Cinnabar research logs, flickering laboratory lights, cloning chamber reveals, individual clone appearances, psychic distortion, silence, Mewtwo silhouette/reveal, resolution and existing-capture echo. *(Done: the clones' opening (silence, psychic pulses, purple light, cry, flash). Also the Cinnabar log's flickering, dimming lights with a distant psychic answer, and the clones rising as black shadows at "Look." Not yet: individual clone sprites.)*
- [ ] **The Power of One:** escalating storm, legendary-bird silhouettes/cries, animated elemental beacons, Melody's staging, Lawrence confrontation, Lugia emergence and restoration of daylight. Preserve alternate beacon order and original capture path. *(Done: each beacon pulses in its guardian's color; blue light for Melody's song and a flash as Lugia answers. Also a gathering storm (darkness, thunder, flash) while Lawrence speaks. Not yet: bird silhouettes, an escalating weather storm.)*
- [ ] **Spell of the Unown:** establish Molly/Hale, spreading crystal motifs, dream palettes, floating Unown, illusion transitions, optional encounters, rescue and environmental cleanup. *(Done: the Entei illusion in purple dream light. Also the Unown's power gathering around Molly before her first battle (purple light and sparkle). Not yet: crystal motifs, floating Unown sprites.)*
- [ ] **Voice of the Forest:** dark forest palette, corrupted Pokémon, Sammy, time distortion, shrine pulse, green particles, Marauder confrontation, forest healing, departure and Oak reveal. Preserve existing Celebi capture. *(Done: the forest darkens for the Marauder, then Celebi's dim glow, green shrine pulses until the daylight returns, flashes for its departure; `BlindingFlash` (the Flash field move) replaced by `scene_flash`. Green sparkle emotes are in. Broader particles and scene presentation remain open.)*
- [ ] **Orange League:** water splashes and buoy feedback for Cissy; wind, ice and cold summit palette for Danny; typed battle introductions for Rudy; partnership staging for Luana; Dragonite reveal and trophy ceremony for Drake. *(Done: Cissy's surf pulse, Danny's cold haze, Drake's Dragonite roar and gold trophy light. Also each of Rudy's rounds opening in its type's color, hearts for Luana's partnership, and a sparkle for the trophy. Not yet: buoy feedback.)*
- [ ] **Pallet Invitational:** distinctive introductions, Tracey's sketch and a satisfying conclusion. *(Done: Pikachu's spark before Ash, gold light while Tracey sketches the winners.)*
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
- [ ] Optional: custom introduction/title screen after mandatory features fit. Any change to the existing title or music is an owner decision.

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

**Release gate:** Document emulator regressions, natural play, original hardware validation, save and trade compatibility, critical issue resolution, and fit on the agreed cartridge target.

---

# Version 2.1 — Living World & Cinematic Update

**Goal:** Deepen exploration, atmosphere and repeatable competition through
the final planned milestone. Use the following checklist to track inherited
proposals and implementation evidence. Before settling scope, measure
candidate features on the current build and bring significant choices to the
owner. Existing content and functionality remain in place.

## Phase 8 — Advanced Pokémon ecology

- [ ] Broaden ecology coverage. Eight profiles and 43 explicit species assignments ship today. Form-specific assignments and further coverage remain to be scoped.
- [ ] Refine the existing schooling, nocturnal, curiosity, territorial, aggressive, elusive and stationary behaviors. Measure timing, crowding and encounter pacing.
- [ ] Extend existing Sweet Honey and noise reactions where observation shows a useful difference. Check standing, walking, running, cycling and surfing.
- [ ] Reuse existing `!`, `?`, sleep and heart emotes. Scope ellipsis, musical note and broader use after checking sprite headroom.
- [ ] Preserve encounter tables, time/swarm/roamer rules, shiny odds, repel behavior and nonblocking movement.
- [ ] Test reachable tiles, boundaries, directional walls, ledges, ice, water, warps and NPC interactions; degrade gracefully with followers and crowded routes.

**Acceptance:** Meaningful observable behavior variety with no encounter distribution regressions, trapping or unacceptable frame-time increase.

## Phase 9 — Environmental presentation

- [ ] Stylized lighting: windows, caves, torches, shrines and palette-based light shafts.
- [ ] Extend environmental weather using the existing overworld rain, snow, lightning and other weather routines. Scope fog and intensity changes against readability and sprite use.
- [ ] Audit existing tile animation and scope extensions for water, flowers, machinery, flags and crystals.
- [ ] Reusable location title cards.
- [ ] Running dust, grass rustle, surf ripples, fishing splashes, item/shiny sparkles, honey cues and legendary cries.
- [ ] Audit existing effects before duplicating them; allocate tiles per screen and share assets with phase 4.

**Hardware limits:** 160×144 display, 40 OAM sprites total, 10 sprites per scanline, 16 KiB VRAM across two banks. Reserve capacity for the player, follower, NPCs and wild Pokémon. Prioritize gameplay readability over decorative effects.

**Acceptance:** Stable framerate, no persistent tile corruption or excessive sprite flicker, and correct state restoration after menus, maps and battles.

## Phase 10 — Recurring living world

- [ ] Add rotating stock if selected. The town-by-town specialty shops already exist with fixed stock.
- [ ] Traveling trainers and rotating opponents.
- [ ] Extend the current 14-sighting TV rotation and other time-dependent appearances where approved.
- [ ] Regional weekly events and optional daily/weekly challenges.
- [ ] Extend the current TV/radio sightings and cup spotlights, Field Book and Quest Map into a broader activity directory. Today’s Kimono type and multiple pending rewards already have guides.
- [ ] Derive schedules and stock from the software clock and deterministic seeds when possible; avoid unnecessary saved state.
- [ ] Preserve clock migration and wrap consistency with all 18 Kimono types and seven weekdays.
- [ ] Treat full seasons as an unapproved proposal. Establish a clock, art and map cost before any decision.

**Acceptance:** Recurring activities remain deterministic where required, work after save/reload, and provide useful reasons to revisit locations without forcing excessive waiting or grinding.

## Phase 11 — Tournament evolution

- [ ] **Rising Star:** rotating opponents, suitable early difficulty and explicitly documented eligibility.
- [ ] **Whirl:** Three fixed Water rosters ship today. Scope roster rotation and rain strategies.
- [x] **Kimono:** The desk names the next unmastered type, and the Album and trophy show mastery progress.
- [ ] **Kimono:** Scope a dedicated 18-type view and full-mastery celebration.
- [ ] **Dragon Masters:** varied Dragon teams with complementary support Pokémon.
- [x] **Rental:** The Look screen previews moves, held items, abilities and stats.
- [ ] **Rental:** Measure legal generated-team diversity and scope improvements.
- [x] **World Championship:** The solo bracket shows rounds, results and standings after elimination. Both brackets use deterministic weighted NPC outcomes.
- [ ] **World Championship:** Scope enhanced introductions and any linked visual bracket presentation.
- [ ] Generalize round, reward, selection and result helpers across cups. Preserve party restoration and bounded generation.
- [ ] Add opening ceremonies, versus cards, crowd/fanfare and trophy scenes using the cinematic library.
- [ ] Evaluate repeatable Cissy/Danny challenges and rotating Rudy opponents. Luana’s current singles rules remain the baseline.
- [ ] Evaluate linked Rising Star, Random and Unrestricted brackets after the current Championship is stable. Team rules, protocol compatibility and persistent generation are decisions to review with the owner.
- [ ] Add compact entries/wins/streaks and championship statistics, with per-type Kimono records only as budget permits.

**Acceptance:** Distinct tournament identities, legal and balanced teams, stable deterministic linked brackets, no duplicated rewards, measured runtime and storage costs.

## Phase 12 — Persistent multiplayer expansion

The proposed records compete for fragmented SRAM. At 136 B each, four extra Friend slots alone use 544 B before level metadata or recovery. The two largest gaps are 393 B and 392 B. Measure combinations and recovery before choosing any new save design.

| Feature | Provisional SRAM budget |
|---|---:|
| Four additional friend slots (six total) | 544 B at 136 B/slot |
| Championship recovery/history | 128–256 B |
| Trainer Card aggregate format stats | 50–200 B |
| Seasonal competitive history | 100–250 B |
| Regional cup statistics | 50–100 B |

- [ ] Expand Friend Battle cache, add favorites/protection and clear replacement/update notifications.
- [x] Friend Look shows moves, abilities, items and stats.
- [ ] Evaluate configurable difficulty separately from the existing preview.
- [ ] Extend Trainer Card aggregate stats and personal records without deleting the existing 65-opponent history.
- [ ] Preserve the distinction between real link results, offline practice and generated rentals.
- [ ] Add season archive and personal bests using the existing manually reset yearly records, if capacity permits.
- [ ] Maintain validity markers, checksums, safe writes and migration policy; measure fragmented capacity, not just totals.

**Acceptance:** Persistent features survive restarts and safe upgrades, do not compromise existing records, and remain within an explicit SRAM budget.

## Phase 13 — Advanced Adventure Album and Pokémon achievements

- [ ] Extend the current Leagues, Stories and Cups pages with Pallet Invitational, Legends, Link, Records and Exploration as appropriate.
- [x] The existing three Album pages support left/right and B exit. The trophy description includes the Kimono mastery count.
- [ ] Scope layout and tier refinements with the additional pages.
- [ ] Use existing flags/records and derived counters before allocating new saved bits.
- [x] The Cup Trophy counts a Kimono win as one cup, while the Album awards the Kimono star at 18/18.
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

- [ ] Finish auditing `meta_sim` coverage before changes to balance. The stats, damage, pipeline, accuracy, status and speed oracles have a fresh baseline. The whole-turn Baton Pass harness gap is tracked as L12.
- [ ] Support family, rental and legal competitive stat profiles; respect actual EV/DV and hyper-training rules.
- [ ] Increase simulation samples where useful, measure uncertainty, evaluate type matchups, team roles/synergy and switching.
- [ ] Calibrate tournament difficulty and deterministic NPC win probabilities using documented inputs.
- [ ] Regression-report damage, accuracy, status, speed, stats and competitive balance after engine changes.
- [ ] Incrementally improve switching, hazards, setup, recovery, team awareness and endgame decisions; profile on original hardware.
- [ ] Keep major AI overhaul separate from routine balancing and preserve link determinism.

**Acceptance:** Reproducible simulator results validated against the ROM; measurable AI improvements without excessive CPU time or regressions. Confirm with natural gameplay.

### 2.1 release gate

Repeat the relevant 2.0 regression and physical tests, especially scene restoration, ecology and clock interactions, all tournament formats, legacy saves and memory usage. Resolve any capacity or compatibility decision with the owner before changing the feature set or hardware target.

---

<details>
<summary>Historical 3.0 proposals, outside the active milestones</summary>

# Historical expanded Link Edition proposals

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

</details>

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

## Remaining work order

1. Resolve the outstanding linked prize recovery cases (L1) after agreeing
   how a restored adventure should interact with the cartridge record. Finish
   targeted link and Friend Battle regression cases, including trade directly
   after a Championship and deliberately refused moves.
2. Run lossless memory measurements and scene-level VRAM/OAM checks alongside
   reliability work. Use the existing cinematic library to scope the most
   visible unfinished 2.0 scenes.
3. Log natural progression, legacy save and original hardware validation while
   2.0 is stabilized.
4. Estimate 2.1 in small prototypes against the measured cartridge budget.
   Bring rules for new tournaments, persistence, legendary quest scope or a
   hardware change to the owner when they need a decision.

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
