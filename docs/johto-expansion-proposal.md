# The Awakening of Johto: expansion proposal (draft for discussion and approval)

Nothing here is implemented. It answers the owner's brief: an expanded Pokemon Crystal campaign in which the legendary Pokemon
shape Johto's ecosystem, mythology and events, organized by badge progression, with cost estimates. The resource figures come
from [`johto-technical-investigation.md`](johto-technical-investigation.md); read its section 1 first: **inside the 2 MiB
image only 2,782 bytes are free**, so this proposal assumes a decision on a 4 MiB build (section 9).

Legend: **[EXISTING]** is in the game today and stays; **[EXTENDS]** adds to something that exists; **[NEW]** is new.

## 1. The premise

Johto is waking. Something older than the League is stirring, and the signs are visible long before anyone says what they mean:

| Force | Presence | The land shows it by |
|---|---|---|
| Entei, the land | heat, flight, burnt ground | scorched grass, frightened wild Pokemon, footprints, warm stone |
| Raikou, the sky | storms, static, lightning | thunderstorms out of season, agitated Electric Pokemon, struck trees |
| Suicune, the waters | purity and change | clouded then clearing water, Pokemon that gather at shores, Eusine's trail |
| Ho-Oh, renewal | rainbows, rebirth | rainbow light at certain hours, feathers, the towers' history |
| Lugia, the sea | depth and currents | strange currents, sailors' tales, a shape under the boat |
| Celebi, time and the forest | memory | the forest remembers; glimpses of Johto's past |

**What is waking it** (the spine, to be agreed): the Unown at the Ruins of Alph hold a record of an old covenant that keeps these
forces in balance, and it is wearing thin. Team Rocket did not cause it, but its radio signal and its forced-evolution experiments
are the spark that makes the imbalance visible and dangerous. The player, with Elm's research, Eusine's pursuit, Silver's
rivalry, Lyra's friendship and the Dragon Clan's old duty, must renew the covenant. The finale is **the Rite of Renewal** at the
Tin Tower before the Elite Four: the player does not simply catch legends; the player is the one who sets things right.

Tone: faithful to Crystal's mystery (towers, bells, a lighthouse, ancient ruins), with the scale and spectacle of the movies
and the anime's sense of travel and wonder. Generation II look throughout.

## 2. Where the early and mid game is thin (from the source)

Structural survey of scripted content (scene scripts, trainers, trigger tiles) per area. Only the figures below were confirmed in
the survey; a full per-area table should be regenerated from the maps before this section is used to size work.

| Area | Finding |
|---|---|
| Ilex Forest | 2 maps, 1 trainer, 2 scenes: the thinnest area |
| Azalea and Slowpoke Well | 0 scene scripts |
| Cherrygrove and Routes 30 to 31 | 1 scene script |
| Blackthorn and the Dragon Clan | 1 scene script, 1 trigger tile |
| Goldenrod (48 maps) | large, mostly shops |
| Mahogany and Lake of Rage | about 50 trigger tiles: already dense |
| Olivine and the sea | moderate |

The thinnest stretches for story (not for trainers) are **Cherrygrove and Routes 30 to 31**, **Azalea and Slowpoke Well**,
**Ilex Forest** (two maps), the **Ruins of Alph's** narrative triggers, and **Blackthorn and the Dragon Clan**. Goldenrod is large
but mostly shops. Mahogany already has plenty of triggers (the Rocket base). Meanwhile 37 maps change only after the Elite Four.
These counts say where scripted story is sparse; where it feels sparse in play is your call.

Characters who already recur (on how many maps): Silver 25, Lyra 24, Elm 27, Eusine 8, the Dragon Clan 14. The proposal gives them
**arcs**, not new walk-ons.

## 3. Overview by badge

| Stage | Arc | Adventure | New playtime (core) |
|---|---|---|---:|
| Before Badge 1 | Prologue: the first sign | The Rainbow Feather begins; Elm's research | 0.5 h |
| Badges 1 to 2 | Signs in stone | Secrets of Alph, part 1 | 1.5 h |
| Badges 2 to 3 | The forest remembers | Echoes of the Forest; Rocket in Slowpoke Well deepened | 1.5 h |
| Badges 3 to 4 | The legends wake | Ecruteak legends; the beasts stir (The Three Beasts, part 1) | 1.5 h |
| Badges 4 to 5 | The restless sea | Beneath the Whirl Islands, part 1 | 1.5 h |
| Badges 5 to 6 | Following the beasts | The Three Beasts, parts 2 to 3; Alph part 2 | 2.5 h |
| Badges 6 to 7 | The Rocket conspiracy | Forced evolution and ecological disruption | 2 h |
| Badges 7 to 8 | The Dragon legacy | Rite of Scales; culmination of the mysteries | 2 h |
| Before the Elite Four | The Rite of Renewal | Finale | 1.5 h |
| Postgame | Conclusions | Existing movie campaigns gain earlier setups | (existing) |

Estimated added playtime: **about 14 hours of core story** (range 10 to 16) and **6 to 8 hours of optional adventures**. These are
estimates from content volume, not measurements.

## 4. The arcs in detail

For each stage: new story and adventures, characters, locations, legendary appearances, environment, cinematics, mechanics, world
consequences, connections, and cost.

### Prologue: before Badge 1 (New Bark, Route 29, Cherrygrove, Violet)

- **Story [NEW/EXTENDS]:** at first light, as the player leaves New Bark, a rainbow light crosses the sky and a shape too large for
  a bird passes over: **Ho-Oh, seen by the player and by Elm.** Wild Pokemon on Route 29 act oddly. Elm, who already sends the player
  to Mr. Pokemon, now asks for something more: to keep a **field journal** of strange occurrences. That gives the player a reason to
  keep looking beyond the badges.
- **Adventure: The Rainbow Feather [NEW], stage 1.** On Route 29, after the sighting, the player finds a single feather. It reacts: in
  certain light and weather it shimmers. The Sprout Tower sages (Violet) read it. It becomes a recurring thread (section 5).
- **Characters:** Prof. Elm [EXTENDS: the field journal, a **Research Wall** in his lab that fills in as discoveries are made];
  Lyra [EXISTING] as the friendly companion who notices things; the Sprout Tower elder [EXISTING] [EXTENDS: omens].
- **Locations:** Elm's Lab [EXISTING], Route 29 [EXISTING], Sprout Tower [EXISTING]. No new maps required in this stage.
- **Legendary:** Ho-Oh (sighting only).
- **Environment [NEW]:** a **rainbow effect** (a palette and tile overlay used for a sunshower and rainbow arc) and "frightened"
  behaviour for visible wild Pokemon on Route 29 (they flee when the player approaches).
- **Cinematics [NEW]:** the dawn sighting (title card, rainbow, Ho-Oh silhouette crossing, Elm's reaction).
- **Mechanics [NEW]:** the **Field Notes** page in the Field Book (it exists as a menu; a new page listing omens and discoveries).
- **Consequences:** Elm's Lab changes after the sighting (notes on the wall, a map with pins).
- **Connects to:** Elm's lab and Lyra [EXISTING]; seeds Spell of the Unown and The Power of One for the postgame.
- **Cost:** ROM about 7 KB (scenes, text, one effect); state: 1 counter.

### Badges 1 to 2: Secrets of Alph (Union Cave, Route 32 to 33, Alph)

- **Story [EXTENDS]:** the Ruins of Alph [EXISTING] become the first great investigation. Researchers have a camp; **Unown words
  appear elsewhere in Johto** (carved on a Sprout Tower pillar, scratched on a Ruins wall, on a lake rock). Each chamber the player
  opens teaches a **verse** of the covenant. Verse 1 is learned from the Ruins' own puzzle; later verses are earned elsewhere and
  point to other adventures (a verse that names the sea opens a door in the Whirl Islands).
- **Adventure: Secrets of Alph [NEW]:** part 1 here (verses 1 to 3: the Ruins, the Union Cave inscription, the Sprout Tower pillar),
  part 2 after Badge 5 (verses 4 to 6), final verse at the Rite.
- **Characters:** Prof. Hale and Molly [EXISTING in Spell of the Unown]: introduced **early** as researchers (so the postgame
  campaign pays off a relationship the player already has); the Alph researchers [EXISTING].
- **Locations [NEW]:** an **Alph research annex** (2 small maps) and an **Unown archive** (1 map) opened by verse 3; the existing
  chambers [EXISTING] gain a second state (lit after a verse is understood).
- **Legendary:** the Unown as a collective presence; the existing Ho-Oh chamber [EXISTING] becomes a foreshadow.
- **Environment [NEW]:** Unown "echoes" (floating glyphs, a hum) on Alph's maps by time of day; the radio's Alph frequency
  [EXISTING] acquires a verse broadcast at night.
- **Cinematics [NEW]:** the first verse (chamber lights and glyphs rise, the screen tints, the Unown cry), the archive opening.
- **Mechanics [NEW]:** a **verse puzzle**: arrange Unown letters in a menu to complete a word from clues gathered across Johto
  (an expansion of the existing sliding puzzles, not a replacement).
- **Consequences:** the researchers' camp grows with each verse; Union Cave gains a hidden route; Elm's Research Wall adds the verses.
- **Connects to:** Spell of the Unown (Entei's illusion, Molly) [EXISTING, postgame], the Field Notes.
- **Cost:** ROM about 18 KB (scenes, three maps, the puzzle code about 3 KB, glyph effect art); sprites 2 (a researcher, glyph); state: 1 counter and 6 bits.

### Badges 2 to 3: Echoes of the Forest (Azalea, Ilex Forest, Goldenrod); Rocket thread begins

- **Story [EXTENDS]:** Ilex Forest has only two maps and one trainer. It becomes the second great mystery: **the forest remembers**.
  Early disturbances (animals gathering at the shrine, a path that was not there yesterday) lead to **time-slip glimpses**: at the
  shrine, with the right progress, the player sees short scenes of Johto's past (the sages and the first bell, the awakening of the
  three beasts, the founding of the Dragon Clan). Each glimpse delivers lore and has a consequence in the present.
- **Adventure: Echoes of the Forest [NEW]:** three glimpses across the game (here, after the beasts wake, at the Rite).
- **Characters:** Kurt [EXISTING] (the GS Ball and the shrine's guardians [EXTENDS]); the Ilex charcoal man [EXISTING]; Lyra [EXISTING]
  (she is at Ilex already) as the witness; a forest keeper [NEW].
- **Locations [NEW]:** a **shrine grove** (1 map, the heart of the forest) and the **keeper's hut** (1 map); Ilex Forest [EXISTING] gains
  state-dependent paths.
- **Legendary:** Celebi (glimpses, never a battle here); the existing capture path via the GS Ball [EXISTING] stays untouched.
- **Environment [NEW]:** a past/present palette change at the shrine; glowing motes; forest animals gather or flee with the state.
- **Cinematics [NEW]:** the time-slip (tint, sparkle, the shrine's past with silhouettes of the sages).
- **Mechanics [NEW]:** none beyond the glimpse system; it is a state check at the shrine.
- **Rocket thread [EXTENDS]:** Slowpoke Well [EXISTING] now shows the Rockets testing a **signal** on the Slowpoke that make wild Pokemon
  uneasy; Silver [EXISTING] is there.
- **Consequences:** the forest's paths and a glade stay open; Azalea's Slowpoke return when the well is cleared.
- **Connects to:** Celebi: Voice of the Forest [EXISTING, postgame], which gains an earlier setup.
- **Cost:** ROM about 14 KB; sprites 2; a short new tune (about 2 KB) or reuse; state: 1 counter and 4 bits.

### Badges 3 to 4: Ecruteak legends; the beasts stir (Ecruteak, Routes 36 to 39, Burned and Tin Tower)

- **Story [EXTENDS]:** the Burned Tower reveal [EXISTING] becomes a hinge. The Kimono Girls and Morty [EXISTING] tell the legend of the
  three beasts and Ho-Oh; the **Sage Archive** [NEW] holds the records. After the reveal the beasts **awaken**: the omen chains begin.
- **Adventure: The Three Beasts, part 1 [NEW]:** each beast gets an omen chain on the routes:
  - **Entei:** scorched grass tiles on Routes 36 to 37, wild Pokemon fleeing the heat, warm footprints.
  - **Raikou:** thunderstorms over Routes 38 to 39, Electric Pokemon agitated, a struck tree with a hidden item.
  - **Suicune:** the existing Eusine thread [EXISTING] extended; water clouds then clears at the shores.
- **Characters:** Eusine [EXISTING, EXTENDS: his notebook becomes a Field Notes page]; Morty and the Kimono Girls [EXISTING]; the sage archivist [NEW].
- **Locations [NEW]:** the **Sage Archive** (1 map); omen tiles on existing routes.
- **Legendary:** scripted **sightings** of Entei, Raikou and Suicune (silhouettes crossing at dusk or in a storm) tied to the roaming
  Pokemon's current map (section 6); Ho-Oh in the tower's legend [EXISTING].
- **Environment [NEW]:** scorched-grass tile variants; storm weather overrides on set routes (the weather system already supports
  thunderstorms); water palette states.
- **Cinematics [NEW]:** a silhouette crossing for each beast; the Archive's reveal.
- **Mechanics [NEW]:** the **omen layer**: a map callback reads the arc's counter and swaps weather, palette and visible-Pokemon
  behaviour; no per-tile flags needed.
- **Consequences:** routes show lasting scars; towns react (Ecruteak's people talk of the beasts).
- **Connects to:** the existing roamers (preserved), Eusine, the Burned and Tin Tower [EXISTING].
- **Cost:** ROM about 22 KB (omen layer code about 3 KB, art for scorched and storm states, scenes); sprites 3; state: 3 counters and 6 bits.

### Badges 4 to 5: Beneath the Whirl Islands (Olivine, Routes 40 to 41, Cianwood, Whirl Islands)

- **Story [EXTENDS]:** the sea is restless. Sailors at Olivine tell of a shadow under the boats; the **lighthouse** [EXISTING] (Jasmine and
  Amphy) becomes more than a waystop: its beacon lamp must be aligned to answer a signal from the Whirl Islands. In Cianwood a storm
  tests the town.
- **Adventure: Beneath the Whirl Islands [NEW]:** part 1 here (currents, the beacon, the first deep chamber).
- **Characters:** Jasmine and Amphy [EXISTING] (a larger role); Cianwood's Chuck [EXISTING] (the storm); sailors [EXISTING]; Lyra [EXISTING] (she is in Cianwood).
- **Locations [NEW]:** the **beacon room** at the lighthouse (1 map), a **Cianwood lookout** (1 map), the Whirl Islands' **deep chamber**
  (3 maps: tunnel, antechamber, the sealed hall).
- **Legendary:** Lugia (a shape beneath the boat while surfing, the song on the wind: *Lugia's Song* [EXISTING track]); the capture and The Power of One [EXISTING] unchanged.
- **Environment [NEW]:** current states on the sea routes (a swirl pattern that changes with the arc and the time), calm and storm water
  palettes; whirlpool positions change at set states.
- **Cinematics [NEW]:** the shadow under the boat; the beacon aligning; the chamber's first opening (earthquake and light).
- **Mechanics [NEW]:** the **beacon puzzle** (rotate mirrors, a short logic puzzle) and the sea-current states.
- **Consequences:** a safe shortcut across the sea opens; Olivine's harbour lights up at night.
- **Connects to:** The Power of One [EXISTING, postgame]; Alph verse 4 names the sea.
- **Cost:** ROM about 24 KB (puzzle code about 2.5 KB, three maps, scenes); sprites 3; music reuse (Lighthouse, Lugia's Song); state: 1 counter and 6 bits.

### Badges 5 to 6: following the beasts (Routes 42 to 44, Mt. Mortar, Alph part 2)

- **Story [NEW]:** with the omens understood, the beasts can be followed. Each chase is a short adventure:
  - **Raikou's storm chase** on Route 42 to Mt. Mortar: following a storm front, using the lightning to open a sealed way.
  - **Entei's fire path** to a lava-warm cave behind Mt. Mortar's waterfall.
  - **Suicune's waters** at Lake of Rage and Cianwood, with Eusine at his most driven.
- **Adventure: The Three Beasts, parts 2 to 3 [NEW]:** each ends in a **meeting**: a guaranteed, scripted encounter place. The roaming
  Pokemon [EXISTING] stay random until the chase is solved; after that, the player can meet each beast at its place once (a battle with
  a capture chance, decided by the rules in section 6).
- **Characters:** Eusine [EXISTING]; Silver [EXISTING] (a tense meeting at Mt. Mortar); Lyra [EXISTING] (Route 42); the Mt. Mortar hermit [EXISTING Karate King nearby] [EXTENDS].
- **Locations [NEW]:** the **storm hollow** (1 map), the **warm cave** (2 maps), the **waterfall pool** (1 map).
- **Environment [NEW]:** lightning strikes that open paths, heat shimmer, water clarity states.
- **Cinematics [NEW]:** each beast's meeting (a cry, a long look, a sprint away or a battle).
- **Alph part 2 [NEW]:** verses 4 to 6, the archive's second hall, the first sign that the covenant is failing.
- **Consequences:** the beasts leave marks in their places; the roamers continue to roam but now show up in scripted sightings more often.
- **Connects to:** Spell of the Unown (Entei), the Rocket arc (their signal affects the beasts).
- **Cost:** ROM about 36 KB (4 to 5 maps, three meeting scenes, Alph part 2); sprites 4; state: 3 counters and 8 bits.

### Badges 6 to 7: the Rocket conspiracy (Mahogany, Routes 43 to 44, Lake of Rage, Ice Path)

- **Story [EXTENDS]:** the Lake of Rage's forced-evolution scheme [EXISTING] becomes the centre of a larger plan. The Rockets' **radio signal**
  [EXISTING at Goldenrod] is being aimed to *call* the beasts; forced-evolution experiments are altering wild Pokemon (Magikarp
  swarms, evolved species where they should not be). Archer, Ariana, Proton and Petrel [EXISTING sprites] each get a scene with a
  distinct personality.
- **Adventure: The Rocket Conspiracy [EXTENDS/NEW]:** a mid-sized dungeon, **Rocket Research Station** [NEW] near the Lake of Rage, and
  clean-up consequences across Routes 43 and 44.
- **Characters:** Archer, Ariana, Proton, Petrel [EXISTING]; Silver [EXISTING] (his reasons matter here; section 7); a Rocket scientist [NEW].
- **Locations [NEW]:** the **Research Station** (3 maps), a **signal tower** on Route 43 (1 map).
- **Legendary:** the beasts disturbed (they appear agitated near the station).
- **Environment [NEW]:** ecological disruption: grass with no wild Pokemon, Pokemon that flee, Gyarados in odd places; reversed after the clean-up.
- **Cinematics [NEW]:** the signal firing; the station's alarm.
- **Mechanics [NEW]:** **radio tuning**: use the Pokegear radio to find the Rocket signal and calm disturbed Pokemon (a short mini-game on the existing radio).
- **Consequences:** areas recover; the Research Station becomes an optional dungeon with a record.
- **Connects to:** Mewtwo Strikes Back [EXISTING postgame] (forced evolution technology foreshadows the clone project), the Rocket base [EXISTING].
- **Cost:** ROM about 30 KB (4 maps, a dungeon with trainers, the tuning code about 2 KB); sprites 3; music reuse (Rocket Overture, Hideout); state: 2 counters and 6 bits.

### Badges 7 to 8: the Dragon legacy (Blackthorn, Dragon's Den, Route 45 to 46)

- **Story [EXTENDS]:** the Dragon Clan [EXISTING] is a keeper of the covenant. Clair [EXISTING] is wrestling with her family's duty. The elders
  set the **Rite of Scales**: a three-part trial in the Den. Lance [EXISTING] appears as a mentor with a stake in Rocket's plans.
- **Adventure: The Dragon Legacy [NEW]:** the Rite of Scales; the elders' lore; the clan's role in the final Rite.
- **Characters:** Clair [EXISTING] (a fuller arc), the Dragon Clan elders [EXISTING], Lance [EXISTING]; Silver [EXISTING] (the Den is where he is).
- **Locations [NEW]:** the **Elders' Hall** (2 maps), the **trial chambers** (3 maps); Dragon's Den [EXISTING] and the shrine [EXISTING] gain states.
- **Legendary:** the Dragon Clan's guardianship of the covenant; Dragonite [EXISTING sprite] in the trial.
- **Environment [NEW]:** ritual lighting (torches, scale-shaped glow), the trial's puzzles.
- **Cinematics [NEW]:** the Rite of Scales; Clair's choice.
- **Mechanics [NEW]:** the trial: a strength, a patience and a courage challenge (boulder, a timed path and a choice).
- **Consequences:** the clan opens the shrine to the player; Blackthorn's streets show the clan.
- **Connects to:** Lance and the Elite Four [EXISTING]; Alph's final verse.
- **Cost:** ROM about 28 KB (5 maps, trials, elders' text); sprites 3; music reuse (Dragon's Den) plus one short new tune; state: 2 counters and 6 bits.

### Before the Elite Four: the Rite of Renewal (Tin Tower)

- **Story [NEW]:** with the verses read, the Rockets stopped and the clan's trial passed, the player climbs the Tin Tower. Companions
  join in turn (Eusine, Elm by radio, Silver by choice, Lyra, Jasmine and Morty at their posts). The three beasts gather; **Ho-Oh descends**;
  Lugia answers from the sea and Celebi from the forest. The covenant is renewed.
- **Characters:** all of them. **Legendary:** all six.
- **Cinematics [NEW]:** the climb and the gathering, the longest scene in the expansion (about 8 minutes).
- **Mechanics:** a final puzzle that uses what the player learned (a verse, a beacon pattern, a signal); no new system.
- **Consequences:** the omens end; the weather and the routes heal; legendary encounter opportunities (section 6) open.
- **Cost:** ROM about 20 KB; sprites 2; a new or reused climax tune (reuse Summoning Dance or Ho-Oh Battle); state: 1 counter.

## 5. The recurring threads

| Thread | Where it runs | Role |
|---|---|---|
| **The Rainbow Feather** [NEW] | Route 29, Violet, Ecruteak, Tin Tower | A keepsake that shimmers near omen sites and shows hidden rainbow-lit details in the right weather and hour; not a fetch quest, a tool of discovery |
| **Secrets of Alph** [NEW] | Alph, Union Cave, Sprout Tower, Whirl Islands | Six verses, each a discovery |
| **Echoes of the Forest** [NEW] | Ilex | Three time-slip glimpses |
| **The Three Beasts** [NEW] | Routes 36 to 44 | Omens, sightings, chases, meetings |
| **Beneath the Whirl Islands** [NEW] | Olivine, Cianwood, Whirl Islands | Sea disturbances and Lugia |
| **The Dragon Legacy** [NEW] | Blackthorn | The Rite of Scales |
| **The Rocket Conspiracy** [EXTENDS] | Azalea to Mahogany | Radio signal and forced evolution |
| **Eusine's Journey** [EXTENDS] | Routes 36, Burned Tower, Cianwood, Tin Tower, the Whirl Islands | Recurring research and the final companion |

## 6. Legendary presence and encounter rules (for your decision)

- **Preserved:** the three random roamers keep roaming; every existing capture method and location is unchanged; the four movie campaigns
  and their rewards are unchanged.
- **New presence:** omens (state-driven environment), scripted **sightings** triggered when a roamer's map matches the player's map
  and the time or weather fits (no battle, once per stage), **chases** and **meetings** at fixed places after a chase is solved.
- **Encounter opportunities:** each beast's meeting offers a battle with a capture chance **only if the player has not already caught it**
  (respect completed captures and avoid duplicates). Ho-Oh, Lugia and Celebi captures stay where they are; the Rite adds cinematic
  appearances, not new captures.
- **Not yet decided:** whether a beast that was caught is still shown in its scripted places (recommended: yes, as an apparition).

## 7. Characters

| Character | Today | In this proposal |
|---|---|---|
| Prof. Elm | 27 maps | Field research network, Research Wall, radio broadcast at the Rite |
| Silver (rival) | 25 maps | A development arc: curt at Slowpoke Well, tested at Mt. Mortar, a reason for his path in the Dragon's Den, a choice before the Rite (stands with the player or stays away) |
| Lyra | 24 maps | Witness and friend at Alph, Ilex, Cianwood and Route 42; a short companion scene at the Rite |
| Eusine | 8 maps | Notebook, Whirl Islands, the final companion |
| Clair, Lance, the Dragon Clan | 14 maps | The Rite of Scales; Lance as a mentor |
| Team Rocket executives | existing sprites | One scene each with a distinct motive; Archer leads the signal plan |
| New | none | A forest keeper, a sage archivist, a Rocket scientist (reusing existing sprites where possible) |

## 8. Cost estimates

All figures are estimates from the calibration in the technical investigation. ROM is scripts, text, maps and engine code together.

| Stage | New maps | ROM (KB) | New sprites | New music | State (counters, bits) |
|---|---:|---:|---:|---:|---|
| Prologue | 0 | 7 | 1 | 0 | 1, 0 |
| Alph part 1 | 3 | 18 | 2 | 0 | 1, 6 |
| Ilex | 2 | 14 | 2 | 0 to 1 | 1, 4 |
| Ecruteak and the beasts | 1 | 22 | 3 | 0 | 3, 6 |
| Sea | 5 | 24 | 3 | 0 | 1, 6 |
| Beasts, parts 2 to 3 and Alph part 2 | 5 | 36 | 4 | 0 to 1 | 3, 8 |
| Rocket | 4 | 30 | 3 | 0 | 2, 6 |
| Dragon | 5 | 28 | 3 | 1 | 2, 6 |
| Rite | 0 | 20 | 2 | 0 to 1 | 1, 0 |
| Shared systems (Field Notes, omen layer, rainbow and glyph effects, verse and beacon puzzles, radio tuning, state layer) | 0 | 14 | 0 | 0 | 0 |
| **Total** | **about 25** | **about 213 (range 160 to 260)** | **about 23** | **0 to 4 tunes** | **about 15 counters, 42 bits** |

- **ROM:** about 213 KB, or about 10% of today's ROM. It does not fit in 2 MiB (2.8 KB free, about 27 KB with every reclaim).
- **Flags:** the whole proposal needs about 15 counters and 42 bits, about 20 bytes of the 196-byte hybrid record. It does not fit
  in the 16 existing event flags.
- **WRAM and SRAM:** the state record's mirror is about 196 bytes in a WRAMX gap; the saved record uses existing SRAM padding.
- **Sprites:** about 23 new overworld sprites at about 0.2 KB each is under 5 KB; reuse of Elm, Lyra, Eusine, Kurt, Sage, Scientist,
  Rocket executives, Dragon Tamer, Dragonite, big Lugia, big Ho-Oh and Celebi covers most of the cast.
- **OAM:** set pieces with the player, two or three characters, a legend and effects stay under 40 sprites; the Cinnabar Lab
  finding (ledger L36) means each set piece must be checked for the 13-object limit.
- **Music:** nearly everything reuses existing tracks (Burned Tower, Tin Tower, Lighthouse, Dragon's Den, Rocket Overture,
  Lugia's Song, Summoning Dance, Ho-Oh Battle, Ruins of Alph interior and radio); new tunes are optional.

## 9. Decisions needed

1. **Cartridge size.** Approve a 4 MiB build (A), keep 2 MiB and take a slice (B), or ship two builds (C). Everything beyond about 27 KB depends on this.
2. **State storage.** Approve the hybrid record (counters plus a bit array, in the save padding, versioned, with a migration from old flags),
   after a prototype with a power-cut test.
3. **Scope.** Full proposal, or a staged release starting with the Prologue, Alph part 1 and Ilex as a pilot slice.
4. **Legendary encounter rules** (section 6), especially duplicates and the beast meetings.
5. **Silver's arc** (his choice at the Rite) and how much of Clair's and Lance's family story you want.
6. **Assets:** new music (optional), and whether new overworld art is drawn by you or generated in Generation II style for your approval.
7. **Order of work:** a pilot slice first (Prologue and Alph part 1, including the state layer) to prove the storage design before the
   rest is written.

## 10. Risks

- Save compatibility and the migration: mitigated by the versioned record, the one-time derivation from existing flags and the power-cut test.
- ROM size and cartridge compatibility (decision 1).
- Scope: this is large; staging by badge keeps the game playable and buildable.
- Sprite and OAM pressure in set pieces (ledger L36).
- Interactions with the existing postgame campaigns: new setup lines must read the new state without changing their progression or rewards.
- Merge cost with upstream: new engine hooks stay small and in ROMX.
