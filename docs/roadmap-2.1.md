# Pokémon Polished Crystal: Link Edition — Updated development roadmap (final release 2.1)

The owner's consolidated roadmap (November 2026). It brings together the
original development plan, Claude's implementation, Codex's stabilization work
and proposed enhancements. Completed functionality is the foundation, not work
to repeat. Per-item implementation evidence stays in the
[master roadmap](link-edition-master-roadmap.md) and the
[issue ledger](issue-ledger.md).

**Development principles**

- Finish development through version 2.1.
- Preserve existing content and functionality.
- Pursue lossless optimization without automatically sacrificing features.
- Allow independent engineering judgment.
- Consult the owner before significant gameplay, storage, cartridge
  architecture or product decisions.
- Distinguish implementation, automated verification and physical hardware
  validation.

This is a work plan, not authorization to implement every optional feature or
compromise. Progress percentages, proposed quest designs, feature priorities
and the final validation phase are assessments and recommendations, not newly
approved requirements.

## Current baseline

Branch head when written: `d7fdddd9` (includes the line bracket, winners
advancing toward the centre). Implemented and to be maintained, tested and
refined rather than recreated: software world clock, followers, visible wild
Pokémon, eight behavior profiles, Field Book and quest map, four movie
campaigns, Orange League, Pallet Invitational, six regional cups, five
multiplayer formats, Friend Battles, linked World Championship, lifetime and
annual link records, bedroom trophies and Adventure Album, competitive
simulator. Cinematic effects engine: partially complete.

# Version 2.0 — Complete Edition

Objective: finish, polish and stabilize the existing adventure.

## Phase 1 — Engine reliability (in progress)

- [x] Reproducible build and testing baseline.
- [x] SRAM layout guards.
- [x] Quest Map memory overlap (L23).
- [x] Bound generated-team algorithms (L2).
- [x] Party summary out-of-bounds access (L22).
- [x] Cup party restoration (L6).
- [x] Standardized competitive battle settings (L20).
- [x] Resolve linked championship prize recovery edge cases (L1). *(New Game can no longer inherit the previous trainer's prize; a restored pre-prize backup against a closed bracket is an accepted, documented limit.)*
- [x] Complete Friend Battle record validation. *(`CheckFriendTeamFields` covers marker, checksum, rules, gender, count and each Pokémon. Forms are left unchecked by evaluation: the game reads an unknown form as the plain one, and `test_friend_battles.py` keeps a team with form 31 (no species has it) and plays Look, its summary screen and a battle to the end, the party back.)*
- [x] Evaluate stronger interrupted-write recovery (L3). *(Evaluated: a journal costs 143 B SRAM and about 100 B ROM to keep a friend team one battle restores; not done, by the owner's decision.)*
- [x] Test trading immediately after championship sessions. *(`linktest.py --trade --last-rules world,normal` and `--last-rules world`: both cartridges reach the Trade Center, with no Championship session and no rules refusal.)*
- [ ] Expand link interruption and recovery tests. *(Done so far: `test_world_plan.py`, the session plan from 27 crafted message pairs, injected out-of-range values included; trading after a Championship. Still open: disconnects at each commit boundary over the cable.)*
- [x] Correct the simulator Baton Pass test harness. *(`oracle_turn.py` now answers "who comes in?" with the first Pokémon that can battle and isn't out; 48/48 matchups agree.)*
- [ ] Audit remaining battle, save and progression defects.

Acceptance: no reproducible save corruption, party loss, unintended reward
duplication or unrecoverable tournament state in supported scenarios.

## Phase 2 — Engine optimization and memory (in progress)

- [x] ROM, SRAM, WRAM and HRAM reporting.
- [x] Reclaim unused save padding.
- [x] Deduplicate identical Nidorina walking graphics.
- [x] Evaluate Rangi's latest compression improvements. *(Merged with upstream through `6aac915e3` (51 commits, November 2026): the simpler LZP copy-offset encoding, the >255-byte `LZ_ALTERNATE` fix, and every LZP file recompressed by the build.)*
- [x] Evaluate upstream graphics recompression. *(Included in the same merge; the default build went from 8,988 B to 8,313 B free with all 51 commits, their new features included.)*
- [ ] Integrate relevant upstream engine optimizations. *(Upstream merged through `6aac915e3`: palette glow from streetlights, lanterns, neon and lit doors, the lit Olivine Lighthouse, colored status icons in the party menu, map refinements and map-stitch annotations. Keep merging as upstream moves.)*
- [ ] Audit duplicated tournament and link routines.
- [ ] Investigate more efficient text and graphics encoding.
- [ ] Improve ROM bank packing.
- [ ] Audit temporary WRAM allocation lifetimes.
- [ ] Audit VRAM and OAM usage per screen.
- [ ] Measure CPU and frame-time costs.
- [x] Establish the actual memory requirements for the remaining roadmap. *([`memory-requirements.md`](memory-requirements.md): about 34–66 KB of ROM for the remaining phases against 10,171 B free; options for the owner: prioritize within 2 MiB, more lossless savings (1–4 KB likely), or an MBC5 cartridge, which the software clock now makes possible.)*

If cartridge capacity becomes insufficient, present measured options before a
significant architectural decision. No existing content removal is authorized.
*(Decided: the measured needs exceeded 2 MiB, and the owner has 4 MiB carts, so
the game is now built for 4 MiB MBC5; see
[`memory-requirements.md`](memory-requirements.md).)*

## Phase 3 — Competitive rules and tournament foundation (mostly implemented)

- [x] Centralized competitive rules; five Cable Club formats; shared team
  eligibility checks; universal link synchronization protections.
- [x] Deterministic tournament outcomes with weighted NPC upsets.
- [x] Visual World Championship bracket; standings after elimination.
- [x] Detailed Rental Cup and Friend Battle team previews.
- [ ] Verify all eligibility and fallback edge cases.
- [ ] Calibrate NPC victory probabilities.
- [ ] Review rewards and tournament difficulty through natural gameplay.

## Phase 4 — Cinematic engine (in progress)

Implemented: scene begin/end lifecycle, palette tinting and fading, darkness
and color pulses, screen flashes and shake, global silhouettes, sparkle emotes,
music restoration, the Flash & Shake accessibility option.

Pending: individual character reveals, camera focus and panning, offscreen
character entrances, reusable particle effects, environmental transformations,
scene framing and title cards.

Investigate the existing overworld movement and scrolling systems before
designing camera functionality. Effects share graphics and cleanly restore
palettes, music, movement and map state.

## Phase 5 — Movie and anime campaign presentation (first pass implemented)

- **Mewtwo Strikes Back** — done: clone battle and psychic introduction,
  Cinnabar research logs, psychic lighting, silence and flashes. To do:
  individual clone appearances, laboratory and cloning chamber staging, a
  distinctive Mewtwo reveal, expanded psychic distortion.
- **The Power of One** — done: elemental beacon palette effects, Melody's song
  and Lawrence's confrontation. To do: escalating storm, legendary bird
  silhouettes and appearances, cinematic Lugia emergence, restoration of
  normal weather and daylight.
- **Spell of the Unown** — done: purple dream lighting, illusion encounters.
  To do: spreading crystal formations, floating Unown, more elaborate Entei
  illusion transitions, environmental restoration after the rescue.
- **Celebi: Voice of the Forest** — done: dark forest atmosphere, corrupted
  encounters, shrine pulses and green sparkles. To do: time distortion,
  enhanced corruption and healing, cinematic Celebi departure, expanded Sammy
  and Oak reveal.
- **Orange League and Pallet Invitational** — done: all four Crew challenges,
  elemental battle introductions, badge progress announcements, Drake's trophy
  effects. To do: Surf checkpoint visual feedback, mountain wind and snow,
  stronger character introductions, championship ceremony, expanded Tracey
  sketch and ending.

## Phase 6 — Character artwork and visual identity (substantial work remaining)

Appropriately authorized artwork in a consistent Generation II style.
Overworld sprites and trainer portraits needed for Ash, Tracey, Ritchie,
Harrison, Casey, Cissy, Danny, Rudy, Luana, Molly, the Iron Mask Marauder and
Lawrence III; Melody and Sammy (portraits where applicable); Drake and Mewtwo
to audit and refine. Candidates: cloning laboratory tiles, crystals,
corrupted forest, tournament decorations, achievement graphics. Audit existing
assets first. A custom introduction and title screen remain optional.

## Phase 7 — Version 2.0 validation (partially verified)

- [ ] Natural Johto and Kanto playthrough; all four movie campaigns; the Orange
  League in different badge orders; Pallet Invitational.
- [ ] All six cups and 18 Kimono types.
- [ ] Existing saves and migration.
- [ ] Every multiplayer format; physical link cable interruption and recovery.
- [ ] Cartridge save persistence; graphics and frame pacing on original GBC.
- [ ] Reproducible builds and release notes.

# Version 2.1 — Living World & Cinematic Update

Objective: a more immersive world, deeper replayability, a distinctive
identity beyond upstream Polished Crystal.

## Phase 8 — Advanced Pokémon ecology (partially implemented)

Done: the eight profiles, noise reactions, Sweet Honey, nocturnal behavior,
43 explicit species assignments. To do: broader species and form-specific
assignments, improved aquatic movement, more natural schooling and group
movement, territorial warnings before aggression, sleeping Pokémon, expanded
Honey interactions, behavioral emotes (alert !, curiosity ?, sleeping Z,
affection ♥, hesitation …, playful ♪), species-specific movement speeds,
improved follower interactions. Preserve encounter distributions, shiny odds,
roaming legendaries and existing encounter methods.

## Phase 9 — Environmental presentation (early)

Window lighting (palettes), streetlights (evaluate upstream), lanterns and
torches, cave lighting, shrine illumination, fog, storms, snow and wind, grass
rustling, running dust, surf ripples, fishing splashes, item sparkles (existing
sparkle system), location title cards, animated crystals. (Upstream's palette
glow for streetlights, lanterns, neon signs and lit doors, and the evening
Olivine Lighthouse, are merged; build on them.) Evaluate Rangi's
recent lighting and palette improvements before building equivalents.

## Phase 10 — Living world and recurring activities (partially implemented)

Done: software clock and weekdays, daily rare sightings, regional specialty
shops, daily Kimono rotation, TV and radio tournament announcements. To do:
rotating merchant inventories, traveling trainers, time-dependent NPCs,
expanded sightings, regional weekly events, daily and weekly challenges,
rotating rematches, a Field Book activity directory, upcoming event
announcements. Use the world clock; full seasons need a scope decision.

## Phase 11 — Tournament evolution (partially implemented)

Rising Star: rotating opponents, early-game balance. Whirl: diverse Water
teams, rain strategies. Kimono: upcoming types, mastery overview, completion
ceremony. Dragon Masters: varied Dragon teams with support Pokémon. Rental:
greater generated-team diversity. World Championship: enhanced introductions
and presentation. Orange League: repeatable challenges and rotating opponents,
subject to approval. Linked championships in more formats (Rising Star 30/3,
Random 50/6 generated, Unrestricted to be decided): proposed. Also opening
ceremonies, versus screens, opponent introductions, crowd effects and
fanfares, trophy ceremonies, personal tournament records, streaks and
statistics.

## Phase 12 — Persistent multiplayer expansion (partially implemented)

Implemented: lifetime and annual records, history for 65 opponents, two saved
Friend teams with detailed preview, deletion and automatic updates. Proposed:
expanded Friend capacity (sized by storage and owner preference), favorite or
protected friends, configurable offline AI difficulty, per-format statistics,
personal bests, historical records. Pending: improved update notifications,
improved interrupted-write recovery.

## Phase 13 — Adventure Album and Pokémon achievements (partially implemented)

Existing pages: Leagues, Stories, Cups. Proposed: Legendaries, Multiplayer,
Exploration, Records, Pokémon awards (ribbons such as Indigo League Champion,
Orange League Champion, Kimono Master, World Champion, Pallet Invitational
Champion), subject to whether Pokémon-specific data fits the storage and link
formats safely. Preserve all existing trophies and achievements.

## Phase 14 — Legendary Pokémon investigations (not started)

Short narrative adventures around existing legendary encounters, without
duplicate captures: Mew (Faraway Island), Ho-Oh (Burned and Tin Tower), Entei,
Raikou, Suicune (Eusine). Names and concepts are proposals; integrate with the
Field Book and respect completed captures.

## Phase 15 — Advanced battle AI and competitive simulation (foundation implemented)

Simulator: threat matrix, 6v6 Monte Carlo, set optimization and ROM oracles
done; to do: complete whole-turn oracle verification, team synergy, stat
profile comparisons, tournament difficulty and NPC bracket calibration.
Trainer AI: expected damage, accuracy and fatal-switch avoidance done; pending:
switching, hazards, setup timing, recovery, team awareness, weather, endgame;
optional difficulty profiles proposed. Evaluate CPU cost, behavior and
regression risk for every change.

## Phase 16 — Final optimization and release validation (pending)

Reconcile features with the approved roadmap; resolve critical defects; final
lossless optimization; cartridge capacity and compatibility; natural gameplay
and physical multiplayer testing; older saves; recurring activities and clock
rollover; all cinematic scenes, tournaments, achievements and records; artwork
provenance and credits; final patches, documentation and 2.1 release notes.

## Recommended work order

1. Stabilization: outstanding championship, save and multiplayer defects.
2. Upstream integration and optimization: Rangi's compression, lighting,
   graphics and engine improvements.
3. Artwork and cinematic presentation of the existing stories and characters.
4. Version 2.0 validation.
5. Living world expansion: ecology, environment, recurring activities.
6. Competition and collection expansion: tournaments, multiplayer,
   achievements, legendary investigations.
7. AI refinement and final validation.

Hoenn, double battles and Link Adventure are outside the active roadmap.
Cartridge architecture remains a separate engineering decision.
