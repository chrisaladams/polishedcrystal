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

This review covers `fbbc45025`. The branch has the software world clock,
followers, visible wild Pokémon with eight behavior profiles, Field Book and
Quest Map, four movie campaigns, Orange League, Pallet Invitational, six
regional cups and five multiplayer formats. It also has Friend Battles,
linked World Championship, lifetime and annual link records, bedroom trophies
and Adventure Album, and the competitive simulator. The cinematic toolkit
has weather, camera movements, individual reveals and title cards available
for further scene work. See the [build and memory baseline](memory-baseline.md).

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
- [x] Expand virtual cable interruption and recovery tests. `test_world_plan.py` covers 27 crafted message pairs, including out-of-range values. `test_world_link.py` checks interruption before either exchange begins and recovery from one persisted registration or final result. `test_world_cuts.py` covers 12 registration and six result cuts across packet and commit boundaries, each followed by a clean session. Every session returned to the desk, and clean reconnects converged on one bracket with results intact. A cut at byte 110 persisted the result on one side and the next session reconciled it.
- [ ] Verify interruption during SRAM writes and recovery on original hardware.
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
- [x] Audit duplicated tournament and link routines. *(20 short repeats; the largest, link-message nybble coding in three link paths, is left alone: tens of bytes against protocol risk, with 2 MiB free. [`phase2-audits.md`](phase2-audits.md).)*
- [ ] Investigate more efficient text and graphics encoding.
- [ ] Improve ROM bank packing. *(Not needed for space since the move to 4 MiB; left for build tidiness.)*
- [ ] Audit temporary WRAM allocation lifetimes.
- [ ] Audit VRAM and OAM usage per screen.
- [ ] Measure CPU and frame-time costs. *(Overworld measured: visible wild Pokémon cost 3–5% lag frames in grass; their per-step choice now comes after the chance roll (odds unchanged); a spawn's reachability window is the remaining two-frame hitch. Battles, menus and link screens not yet measured. [`phase2-audits.md`](phase2-audits.md).)*
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
- [x] Verify all eligibility and fallback edge cases. *(Link formats: `test_link_rules.py`, every row of the rules matrix on your team, a received team and a Friend Battle. Offline cups: `test_cups.py`, `test_whirl_cup.py`, `test_orange_league.py`, and `test_cup_eligibility.py` for the whole-party cups' edges: too few, Eggs left out of the count and the staged team, a wrong type among enough, a dual type counting, a Dragon among others, six exactly, Friend Battle rules. Fallbacks: `test_team_generation.py`, each team generator forced past its restart limit.)*
- [ ] Calibrate NPC victory probabilities. *(Measured over all 65,536 seeds, unchanged from [`rules-matrix.md`](rules-matrix.md): the strongest visiting trainer reaches 58% of finals and wins 42%, the weakest 7% and 1%; 26% of trainer-vs-trainer matches are upsets. The odds (60/70/80/90% by places between them) are kept; changing them is the owner's call.)*
- [ ] Review rewards and tournament difficulty through natural gameplay.

## Phase 4 — Cinematic engine (in progress)

Implemented: scene begin/end lifecycle, palette tinting and fading, darkness
and color pulses, screen flashes and shake, global silhouettes, sparkle emotes,
music restoration, the Flash & Shake accessibility option. Then:

- camera focus and panning: `scene_pan` / `scene_pan_back`, the original
  endings' technique (the camera follows a hidden player), the follower put
  away during the pan;
- individual character reveals: `scene_shadow` / `scene_unshadow`, one figure
  black in a palette slot of its own while the rest keep their colors;
- offscreen character entrances: `scene_enter`, from past any edge of the
  screen, wherever the player stands;
- title cards: `scene_title`, a centered line, white on black, between fades;
- environmental transformations: `scene_weather`, a scene's own weather (rain,
  snow, storm, sand, blossoms or a clear sky) until its end; map blocks change
  with the engine's `changeblock` and `refreshmap`.

See [`cinematics.md`](cinematics.md).

Particle effects: done as emotes, `EMOTE_DUST` and `EMOTE_DROPS` beside the
sparkles. Scene framing (letterbox bars): evaluated and set aside, since the
overworld's text boxes are drawn on the window, the only layer a bar could
use (see [`cinematics.md`](cinematics.md)); title cards frame scenes instead.

Investigate the existing overworld movement and scrolling systems before
designing camera functionality. Effects share graphics and cleanly restore
palettes, music, movement and map state.

## Phase 5 — Movie and anime campaign presentation (first pass implemented)

- **Mewtwo Strikes Back** — done: clone battle and psychic introduction,
  Cinnabar research logs, psychic lighting, silence and flashes; individual
  clone appearances (copies of your own team rising as shadows) and Mewtwo's
  reveal (a shadow until its cry); a title card at the Cinnabar flight log,
  and the lab shaking with falling dust at Mewtwo's answer. Second pass: in
  the cave the camera rises over the pool as the copies form, and the silence
  breaks with the Stadium Mewtwo theme at its reveal, carried into the
  battle; at the flight log the music falls silent and a vision of the
  armored clone flickers as a shadow in the lab. Evidence:
  `test_movie_events.py`, `test_story.py`;
  [`phase5-screens/mewtwo-clones.png`](phase5-screens/mewtwo-clones.png),
  [`phase5-screens/mewtwo-flight-log.png`](phase5-screens/mewtwo-flight-log.png).
  Third pass: after Red, Mansion B1F has the cloning tanks the log tells of,
  two along the wall and one shattered from the inside ("SPECIMEN M2"),
  each with its own text. Evidence:
  [`phase5-screens/mansion-clone-tanks.png`](phase5-screens/mansion-clone-tanks.png).
- **The Power of One** — done: elemental beacon palette effects, Melody's song
  and Lawrence's confrontation; a title card; the escalating storm, the three
  legendary birds as silhouettes in the lightning, Lugia's emergence (a
  shadow, then revealed) and the storm clearing to daylight. Second pass: the
  camera rises into the storm to find the guardians one by one, each in its
  own lightning flash, under the Summoning Dance; it comes back down for
  Melody's song (Lugia's Song) and rises again for the full-size Lugia
  sprite. Evidence: `test_campaigns.py`;
  [`phase5-screens/power-of-one-restoration.png`](phase5-screens/power-of-one-restoration.png).
- **Spell of the Unown** — done: purple dream lighting, illusion encounters;
  a title card; floating Unown and the Entei illusion's transitions (a
  dream's shadow, its colors as it roars, breaking into letters around you).
  Second pass: the Unown's radio signal as the scene's music; crystal
  formations spreading out from the statue one by one (each with a glass
  chime and a sparkle), staying through the illusion and shattering in a
  flash when Hale is free, the chamber itself again and its own music back.
  Evidence: `test_campaigns.py` (Alph staging);
  [`phase5-screens/unown-statue.png`](phase5-screens/unown-statue.png).
  Third pass: the crystals are drawn crystal clusters (`SPRITE_SCENE_PROPS`)
  instead of rock icons. Evidence:
  [`phase5-screens/alph-crystals.png`](phase5-screens/alph-crystals.png).
- **Celebi: Voice of the Forest** — done: dark forest atmosphere, corrupted
  encounters, shrine pulses and green sparkles; a title card; corruption and
  healing (Celebi a shadow until the shrine heals it, the forest blooming),
  time distortion (a white haze as Sammy arrives) and Celebi's departure (it
  rises before it takes him home); Oak's reveal as a memory (white haze, a
  Celebi's cry, a green sparkle over him). Second pass: the corruption as the
  forest turning dark and sickly purple around Celebi's shadow under the
  Eterna Forest theme; the healing under the White Treehollow theme; the
  farewell under the Celestial Tower theme, Sammy gone in a flash and the
  camera following Celebi up through the trees. Evidence:
  `test_movie_events.py`;
  [`phase5-screens/celebi-corruption-healing.png`](phase5-screens/celebi-corruption-healing.png),
  [`phase5-screens/celebi-departure.png`](phase5-screens/celebi-departure.png).
  Third pass: the corrupted forest. While the Marauder holds Ilex Forest
  (after Red and the time travel, until he's beaten) its trees are dark
  violet through every visit, battle and menu (a special map palette,
  `IlexForestSpecialCase`); at the shrine the green pulse fades into the
  forest's own colors (`scene_reload_map`), and it stays healed. Sammy has
  his own sprite. Evidence: `test_movie_events.py`;
  [`phase5-screens/ilex-corruption.png`](phase5-screens/ilex-corruption.png)
  (corrupted on arrival, the Dark Ball's hurt, the pulse, healed, Sammy).
- **Orange League and Pallet Invitational** — done: all four Crew challenges,
  elemental battle introductions, badge progress announcements, Drake's trophy
  effects, wind and snow on Danny's first summit visit, and a splash and chime
  at each accepted Surf checkpoint; title cards for the Orange League final
  and the Invitational; Drake's Dragonite and Ash's Pikachu coming out for
  their finals; the championship ceremony; a closing card. Second pass: each
  Crew leader's first challenge opens with a title card (ORANGE CREW: CISSY,
  DANNY, RUDY, LUANA); Drake's Dragonite is the full Dragonite sprite; the
  ceremony plays the Hall of Fame theme. Third pass: Cissy, Danny, Rudy and
  Luana have their own sprites. Evidence: `test_orange_league.py`;
  [`phase5-screens/orange-league-cards.png`](phase5-screens/orange-league-cards.png),
  [`phase5-screens/orange-league-final.png`](phase5-screens/orange-league-final.png).
  Pallet second pass: after the Invitational's card the camera pans across
  Pallet Town and back (Pallet's theme); at the end Tracey (the artist
  sprite of his Oak's Lab cameo) runs in from offscreen to sketch the
  winners under the post-credits theme. Evidence: `test_story.py`,
  `test_cameos.py`;
  [`phase5-screens/pallet-establishing-pan.png`](phase5-screens/pallet-establishing-pan.png),
  [`phase5-screens/pallet-ending.png`](phase5-screens/pallet-ending.png).

## Phase 6 — Character artwork and visual identity (substantial work remaining)

Appropriately authorized artwork in a consistent Generation II style.
Overworld sprites and trainer portraits needed for Ash, Tracey, Ritchie,
Harrison, Casey, Cissy, Danny, Rudy, Luana, Molly, the Iron Mask Marauder and
Lawrence III; Melody and Sammy (portraits where applicable); Drake and Mewtwo
to audit and refine. Candidates: cloning laboratory tiles, crystals,
corrupted forest, tournament decorations, achievement graphics. Audit existing
assets first. A custom introduction and title screen remain optional.

*(Started with Phase 5: Molly Hale (`SPRITE_MOLLY`, from the Gen 2 lass, a pale
headband and a bow) and the Iron-Masked Marauder (`SPRITE_IRON_MASK`, from the
Gen 2 burglar, an iron mask and helmet), each six frames at 16×16 in the
game's four shades, used by the Research Center's Molly and the Ilex Forest
Marauder. No published Gen 2-style sprites of these characters with reuse
terms were found, so the rest follow the same approach. Ash's Pikachu is
Pokémon Yellow's walking sprite (`SPRITE_PIKACHU`, from the pret/pokeyellow
disassembly, its middle shades swapped for Crystal's palettes), replacing
the icon in the Pallet final ([`phase5-screens/pikachu-sprite.png`](phase5-screens/pikachu-sprite.png));
Yellow's Jessie, James and Officer Jenny are already in Polished Crystal.
Melody (`SPRITE_MELODY`, the beauty's long hair with a bow, in brown) and
Drake (`SPRITE_DRAKE`, the veteran with a plain cap, in blue) followed
([`phase5-screens/melody-and-drake-sprites.png`](phase5-screens/melody-and-drake-sprites.png)). Evidence:
[`phase5-screens/molly-and-marauder-sprites.png`](phase5-screens/molly-and-marauder-sprites.png),
[`phase5-screens/molly-sprite-frames.png`](phase5-screens/molly-sprite-frames.png).
The Orange Crew and Sammy followed, each a Gen 2 head on a Gen 2 body, in
the character's colors: Cissy (the beach girl's ponytail on the cooltrainer,
blue), Danny (the skier's headband on the sailor, brown), Rudy (Falkner's
swept hair on the cooltrainer, red), Luana (Lorelei's long hair on the
lady, purple) and Sammy (Bill's hair on the schoolboy, green)
([`phase5-screens/crew-and-sammy-sprites.png`](phase5-screens/crew-and-sammy-sprites.png)).
Environment pieces, drawn for this: a cloning tank, an Unown crystal
cluster and a thorn bramble, the three facings of one `SPRITE_SCENE_PROPS`
(the overworld sprite list is full up to the Pokémon sprite range). Ilex
Forest has no free object slot for brambles, so its corruption is a palette
instead; the bramble frame is unused for now.)*

## Phase 7 — Version 2.0 validation (partially verified)

Default and Faithful build on the current MBC5 target. Emulator coverage
includes old-save and backup recovery, the World bracket, and smoke tests
in the four other Cable Club formats.

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

The simulator has a threat matrix, 6v6 Monte Carlo, set optimization and ROM
oracles, including the recorded 48-matchup whole-turn verification. Team
synergy, stat profile comparisons, tournament difficulty and NPC bracket
calibration remain open.
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
