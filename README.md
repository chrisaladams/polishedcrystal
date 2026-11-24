# Pokémon Polished Crystal: Link Edition

**Polished Crystal: Link Edition** is a competitive take on Pokémon Crystal, built for balanced L50 link battles. It rebalances the roster, tightens the link-battle rules, makes Cable Club connections forgiving, and sharpens the trainer AI, with its own Python balance-simulation toolkit (`meta_sim/`) to back each change with data.

It's built on [Rangi42's Polished Crystal](https://github.com/Rangi42/polishedcrystal), itself based on [the Pokémon Crystal disassembly](https://github.com/pret/pokecrystal). All credit for the base game—the engine, mechanics overhaul, new maps, Pokédex, and everything else—goes to that project and its contributors.

It's kept in sync with Polished Crystal: the latest merge brings in Rangi42's `master` as of November 14, 2026, including the cable car cutscene, the link party corruption fix, the Bad Dreams/Magic Guard fix, and their other battle and item fixes.

## What's different here

The [2.0 development roadmap](docs/link-edition-2.0-roadmap.md) tracks the
release phases, cartridge budgets and tests.

### Link battle balance

A pass at tightening up the meta for L50 link battles:

- **Stat compression** — buffed a bunch of weak/early-game mons, trimmed a handful of top-tier ceilings, so the power band is tighter across the roster. Most recently, Aerodactyl's Attack went from 105 to 95 and Charizard's from 101 to 93, reining in their Tough Claws physical hits. For the 1.0 release, the meta test (`meta_sim/metatest.py`) flagged a few builds that were clearly over or under an average teammate across two independent runs, so:
  - **Trimmed:** Beedrill (Atk 100→90, Spe 115→100), Gliscor (Atk 95→85, Def 120→110), Magnezone (Sp. Atk 130→120), Overqwil (Sp. Def 90→75), Annihilape (Atk 100→95).
  - **Buffed:** Clefable (Def 73→80, Sp. Atk 85→95), Wigglytuff (Def 55→65, Sp. Def 65→75), Hypno (Def 70→80, Sp. Atk 73→83).

  - **Then, with the family's real stats** (the meta test now gives every mon
    DV 8 and EV 64, as read from the family's saves) and every build's set
    re-optimised: **trimmed** Crobat (Spe 130→120), Glaceon (Sp. Atk
    130→120), Magnezone (Sp. Atk 110→100) and Vaporeon (Sp. Atk 110→100);
    **buffed** Farfetch'd (Atk 98→110, Spe 74→85), Cloyster (HP 50→60,
    Sp. Def 45→55) and Raticate (Atk 100→110). The strongest build now adds
    about 13 points of win rate over an average teammate (16 before), and the
    weakest (other than Unown) loses about 5 (9 before).

  These only apply to the normal build; `make faithful` keeps canon base stats.
- **Eviolite restricted** to genuine not-fully-evolved mons (closed a couple of edge-case loopholes). The restriction check used to wipe the attacking move's power, so every hit on an Eviolite holder did 1 damage; that's fixed.
- **Moody removed.**
- **Upstream battle bugs fixed:** Thunder never missed in harsh sunlight (it's 50% now), harsh sunlight didn't stop freezing (it let a freeze chance skip every check instead), and Low Kick gave 80 power to anything between 5 kg and 100 kg (it now follows the weight table: 40 power above 10 kg, 60 above 25 kg, 80 above 50 kg). In link battles, Sleep Talk picked its move with each Game Boy's own random numbers instead of the shared battle ones, so the two games could pick different moves and the battle split; it now uses the shared ones.
- **Evasion capped in link battles** — Double Team/Minimize/Bright Powder still help, but the target's evasion boost can't stack past +2 stages, so it can't be abused into an accuracy stall. Gated to real link play only, so singleplayer and the Battle Tower are untouched. (Trapping abilities — Shadow Tag, Arena Trap — and sleep are left as Polished Crystal ships them; Ghost-types, Shed Shell, and Run Away already give trapped mons an out.)
- **Link-battle healing/leveling** — mons get forced to L50 and topped off before a link battle, so games aren't decided by who happened to grind more.
- A few mart/item tweaks to go with the above.

### Easier Cable Club connections

Linking up used to need both players to be almost perfectly in sync. Now:

- The Cable Club desks open as soon as you have your first Pokémon, instead of after delivering the Mystery Egg to Professor Elm, so a fresh save can link right away.
- The receptionist waits about 26 seconds for your friend instead of about 8.
- If your friend isn't ready, or the link times out, you're asked whether to keep waiting instead of being kicked out, so neither player has to start over.
- The handshake after saving is more tolerant of one player saving slower than the other.

### Link battles that can't silently desync

In a link battle each Game Boy works out every turn itself; the two only swap
the players' choices, and nothing ever checked that they still agreed. One bad
byte on the cable, or two different builds, and the battle split without
either player knowing. Now:

- **Same-build check.** The battle desk compares the two ROMs and refuses to
  start a battle between different builds ("Your games are not the same
  build"), so everyone has to flash the same file.
- **Checked team swap.** Before the battle, both games fingerprint the parties
  and random numbers they sent and received and compare them. If anything
  arrived scrambled, both say "Link error! Trying again. Keep it on!" and redo
  the swap themselves (up to five times) instead of starting a battle that's
  already broken.
- **Confirmed moves.** Each turn's choice only counts once the same byte has
  arrived twice in a row, exchanges cycle through four sets of tags so a late
  byte can't be mistaken for another turn's, and nothing can overwrite a
  confirmed choice.
- **Bumped or unplugged cables.** Nothing in a turn's exchange gives up: if the
  cable comes out, both games wait, and the game driving the link says "Link
  cable out! Plug it back in." (after a long silence, either says "Still
  waiting… Check the cable."). Plug it back in and the battle carries on. Each
  exchange keeps answering the one before, so a game that missed the end of a
  turn can always catch up.
- **No garbage Pokémon.** A switch to a Pokémon the opponent doesn't have
  (which used to show a random picture with a broken HP bar) stops the battle.
- **Per-turn fingerprint.** Every turn the games also swap a fingerprint of
  the battle (HP, status, stat changes, the random number position). If the
  two ever disagree, both stop with "the battle went out of sync" and reset.
  The desk saves before every link battle and a link battle never changes your
  team, so nothing is lost: just start the battle again.

`utils/linktest/` plays link battles between two emulated Game Boys on a
virtual cable, with optional line noise, to test all of this.

### Link records on your Trainer Card

Open **Start → your name**, then press **Left** for **Lifetime**. Press
**Right** for **Current Year**. On either page, press **Down** for the player
list. Left and Right turn the pages. Each opponent appears once with their
name, Trainer ID, and your wins, losses and draws against them. A rematch
updates the same entry. The yearly list shows opponents battled since its
last reset.

The cartridge holds 65 distinct opponents. Once full, it keeps every name,
updates rematches, and counts every battle in the overall totals. Older saves
import their lifetime totals and up to five opponents retained by the original
Cable Club. Current Year starts at zero because older battles have no dates.

You choose when the year starts. Press **A** on Current Year and choose **Yes**
to reset its three counts. The prompt opens on **No**. Lifetime has no reset.
Both pages keep their totals if you start a new adventure on the same cartridge.

### Random Battle

At the battle desk, after "Would you like to battle?", choose **Normal** or
**Random teams** (both players must choose the same). With random teams each
player gets six random level 50 Pokémon, all different species, fully evolved
and non-legendary, with perfect DVs and a neutral nature, so a brand-new save
can battle a finished one on equal terms. Teams get a decent type spread: no
more than two members share a type, and no more than three are weak to the
same type (abilities like Levitate count). The sets (295 of them, for 155
species) come from the simulator's best-set optimiser, made friendly: no
Choice items, item-swapping moves or self-hurting orbs.
`utils/linktest/test_random_teams.py` builds hundreds of teams with the game's
own code and checks every one against these rules. Your own team isn't
touched; it's back after the battle. Regenerate the sets with
`python3 meta_sim/make_random_sets.py`.

A save made inside a room whose scripts moved in a newer build (the Pokémon
Center 2F link room, after this update) used to crash when you talked to
someone there; continuing a save now takes the room's scripts from the ROM.

**Both players need the same build.** This is the Christmas release, link version 2 (Link Edition 1.0 was version 1). A version 2 game won't battle a version 1 game, since the battle rules changed; everyone needs to flash the new build. Trading with a 1.0 game still works, because the party layout hasn't changed. Link Edition has its own link game ID, so it won't connect to stock Polished Crystal or to the pre-release Link Edition builds at all; that's deliberate, since mismatched battle rules or party layouts would desync.

### Specialty shops

Every town's Poké Mart keeps its basics and adds a specialty corner that
fits the town, so building teams means travelling: a type-boosting item for
every type (Violet: Sharp Beak and Silk Scarf, Azalea: Silver Powder and
Charcoal, Ecruteak: Spell Tag and Black Glasses, Olivine: Metal Coat and
Mystic Water, Cianwood: Black Belt, Mahogany: Never-Melt Ice, Blackthorn:
Dragon Fang, Pewter: Hard Stone, Viridian: Soft Sand, Vermilion: Magnet,
Celadon: Miracle Seed, Saffron: Twisted Spoon and Fairy Feather, Fuchsia:
Poison Barb), utility items along the way (Goldenrod: Muscle Band, Wise
Glasses, Shell Bell, Sitrus and Lum Berries; Cianwood: Punching Glove, Expert
Belt; Blackthorn: Scope Lens, Focus Sash; weather rocks and Light Clay in
Azalea, Mahogany, Pewter, Cerulean and Vermilion), and the strongest items at
the end: the Indigo Plateau sells Leftovers, Life Orb, the Choice items,
Assault Vest and Rocky Helmet. Celadon sells Bottle Caps and Lavender sells
Ability Capsules. Prices rise with power (type boosters ¥3,000, utility items
¥6,000, Focus Sash and similar ¥10,000, Leftovers, Life Orb and Choice items
¥20,000, Bottle Cap and Ability Capsule ¥30,000), so they're earned. The
Battle Tower and Battle Factory prize shops are unchanged.

### Quality of life

- Use **Save** from the Start menu before powering off. Bill's PC is available
  at Pokémon Centers.
- Magikarp has four patterns. Older patterns convert to the closest retained
  pattern when you continue or open a box. Shiny Magikarp keeps its shiny colors.

- **Your Pokémon follows you.** Your first healthy Pokémon walks behind you
  with its own walking sprite (front, back and side, each with a walking
  frame): it copies your steps (running, biking, ledges), never blocks you or
  anyone else, and never hides you from a trainer. It stays in its Poké Ball
  while you surf and in the battle and trade rooms, and changes when you
  change your lead. Turn it off under Options → Follower. The same sprites
  are the party menu, PC and Pokédex icons, so a Pokémon looks the same
  everywhere. Every Pokémon and form has one. (Rangi's own follower branch is unfinished; this
  is a smaller version built on the game's existing follow logic.)
- **Wild Pokémon you can see.** No more random battles in the grass: up to
  three wild Pokémon (four when the screen isn't busy) wander where you'd
  meet them (tall grass on routes, the floor in caves, the water while you
  surf), but only where you could walk to them and back from where you
  stand (around trees and corners, but not across ice, currents, ledges or
  warps, or past someone in the way), drawn with their walking sprites
  in their own colours. A shiny one shows its shiny colours. Walk into one, or
  face it and press A, to battle it. They're chosen exactly as random
  encounters are: the same tables and odds, time of day, swarms, roaming
  legendaries, lead abilities, music and Cleanse Tag, and the same 1 in 4,096
  shiny chance (3 with the Shiny Charm). Two are there when you arrive, and
  each step brings another, while there's room, with the map's usual
  encounter chance. A roaming legendary on your map comes just as often as
  it did: if there's no room for another, it takes the place of the wild
  Pokémon furthest from you. **Every TV has the Pokémon news**: each day a
  rare Pokémon (Eevee, Chansey, Scyther, Pinsir, Snorlax, Heracross,
  Larvitar, Pikachu, Electabuzz, Kangaskhan, Tauros, Smeargle, Skarmory or
  Phanpy, in turn) is spotted on one route, where a quarter of the wild
  Pokémon that come are it, one at a time, at that route's levels. It takes a
  slot the same way a roaming legendary does. One that wanders off screen is gone, making room for
  another. While a Repel works, the ones it would have kept away run from
  you, and run off if you walk into them. Some species react differently.
  Sentret flee from footsteps and notice you from farther away when you run
  or cycle. Eevee come closer if you stand still. Beedrill can start a battle,
  and Ursaring defend the area around their spawn. Chansey flee quickly when
  disturbed but will let you approach and wait beside them. Magikarp swim
  together, and nocturnal species are more active after dark. Sweet Honey
  draws compatible Pokémon to the spot where you used it for 12 steps.
  Fishing, Headbutt and Rock Smash work as before. Without the Silph Scope,
  the Pokémon Tower's ghosts still ambush you.
  They don't touch your save or any map's own people. To check them in the
  emulator: `python3 utils/wild_mons/test_wild_mons.py SAVE.sav` (every map
  with wild Pokémon, battles, Repel, sprites and colours, saving).

### In-game clock

A full day takes **90 minutes of play**, and a week takes **10½ hours**.
Daylight runs from 06:00 to 18:00 in-game. Morning starts at 06:00, day at
09:00, evening at 15:00, and night at 18:00. A manual save preserves the
world clock when you quit. Older saves resume from their last saved in-game
time.

The game uses an MBC3 cartridge with battery-backed save RAM. The clock runs
in software and pauses during link play. The Bug-Catching Contest still gives
you 20 minutes of play, and phone delays use gameplay time. Sightings and
weekday events follow the in-game day.

### Field Book

Choose **Start → Field Book → Next stop** for directions from New Bark Town
through Johto, Kanto and Mt. Silver. The book checks the badges you hold
and the quests you have completed. **Catch me up** recalls a milestone you
have reached, shows your current destination, then previews the next
unfinished step. It works when continuing an existing save. **Side quests**
offers leads for Kenya's mail, Moomoo Farm, Copycat's doll, and the Shamouti
beacons as they become available. The book on the table in Prof. Oak's lab
opens the same guide.

After Red, Molly's search at the Ruins of Alph leads into the disturbance
at Ilex Shrine. Oak's investigation takes you to the old Cinnabar Mansion
and then to Cerulean Cave. At Shamouti, the shrine keeper needs your help
relighting three island beacons. Visit them in any order and use the map
to see which still need attention.

The **Pokégear Map Card** and wall maps also show quest destinations. **★**
marks the Field Book's next stop and **!** marks other available leads in
the region. Press **Select** to browse the leads. **Up/Down** cycles through
them across Johto, Kanto and the Orange Islands, **A** reads the directions,
and **B** returns to the local map. Two goals in the same town share a pin
and have separate entries. The Guide Gent in Cherrygrove gives you the Map Card.

### After Red (the post-post game)

When you first beat Red on Mt. Silver, the Field Book opens its Orange League
and movie chapters, starting with Molly at the Ruins of Alph. Tracey's
sketches and letters point you to the next unfinished chapter. The book
recognizes earlier wins, including progress from before this update. Red's
MysticTicket keeps the season open when you begin alternating Red and Leaf
rematches.

The suggested route leads from Molly and her father at the Ruins of Alph
to Ilex Forest and Cerulean Cave, then to the four Orange Crew leaders,
Drake and the Whirl Cup. Tracey calls after Cerulean Cave, the Crew leaders
introduce the next challenger, Drake passes on Misty's invitation, and Misty
sends you to Ash when the Pallet finals are ready. These leads follow the
same progress as the Field Book. The movie events and the Cup can also be played in a different order after Red. Once Drake is beaten
and all four stories are complete, speak to Ash outside Oak's lab for the
Pallet Invitational. Drake and Ash use their existing teams in back-to-back
matches. You start healed and carry your team's condition into round two.
After a loss you can retry in Pallet. Win both rounds to see Tracey's
sketch on the lab wall. Ash then offers his friendly rematch again.

### The Orange League

From the anime's Orange Islands, on the islands Polished Crystal already has
(reached by the Seagallop Ferry from Vermilion City, in Kanto):
the four Orange Crew leaders, each with a badge, and Head Leader Drake, who
battles you once you have all four. Their teams start from the Pokémon they
used on the show, at post-game levels (70–79), with gym leader battle music.

| Leader | Where | Team | Badge |
|---|---|---|---|
| Cissy | Warm Beach, by the water | Kingdra, Starmie, Lapras, Golduck, Blastoise | Coral-Eye Badge |
| Danny | Rocky Beach, on the sandy path | Golem, Scyther, Electrode, Machamp, Nidoking | Sea Ruby Badge |
| Rudy | Beautiful Beach, where the ferry lands | Exeggutor, Starmie, Gyarados, Arcanine, Electivire | Spike Shell Badge |
| Luana | the house on Valencia Island | Kangaskhan, Persian, Ninetales, Marowak, Alakazam | Jade Star Badge |
| Drake | the house on Shamouti Island | Ditto, Steelix, Gengar, Venusaur, Electabuzz, Dragonite | Winner's Trophy and 3 Bottle Caps |

The season opens after Red, and all five offer rematches. The league uses
existing maps, sprites, music and spare save flags. `python3 utils/anime_events/test_orange_league.py SAVE.sav` checks it in
the emulator.

### Regional cups

Cups are free to enter, as often as you like, and losing costs nothing: no
blacking out, no money. Your Pokémon battle at the cup's level, healed, with
no items or experience in its battles, and come back exactly as they were
(healed) when it's over, win or lose.

- **Rising Star Cup**, in the Route 36 gate to the National Park, open from
  the start: choose three Pokémon (as at the Battle Tower: no two of a
  species or holding the same item) to battle at level 30 against Bug Catcher
  Ellis, Picnicker Ruth and Cooltrainer Rex. The first win gives Leftovers,
  each one after a Rare Candy.
- **Whirl Cup**, at Olivine Port after Red: below.
- **Kimono Cup**, in the Ecruteak Dance Theatre, open from the start: each
  day has a type, all 18 in turn (by the world clock's day). Choose three of
  that type to battle at level 50 against Kimono Girls Sayo, Zuki and Miki,
  whose teams of that type (three, three, then four) are drawn from the
  Random Battle sets. The first win with each type gives its item (Silk
  Scarf, Black Belt, ... Fairy Feather) and counts toward all 18; each win
  after a Big Pearl.
- **Dragon Masters Cup**, in Blackthorn's dragon house, once you hold the
  Rising Badge: your whole party enters (three to six, at least one of them
  a Dragon type) at level 50 against Dragon Tamers Erick and Aegon, then
  Clair. The first win gives a Dragon Scale, each one after a PP Up.

Everyone in a cup battles at its level, the cup's trainers too.
`python3 utils/anime_events/test_cups.py SAVE.sav` checks the Rising Star,
Kimono and Dragon Masters Cups.

### The Whirl Cup

From the anime: a Water-type tournament at Olivine Port, run by an official
who's there after you beat Red. Your whole party enters (eggs aside): three
to six Pokémon, all Water-type. At level 50, healed between rounds, you
battle three in a row: Swimmer Trinity (Seaking, Dewgong, Lanturn,
Corsola), Sailor Jasper (Tentacruel, Octillery, Quagsire, Kingler), then
Misty's Whirl Cup team (Psyduck, Corsola, Azumarill, Politoed, Gyarados,
Starmie), all at level 50 too. Losing a round just ends the run (no
blacking out), and as in every cup your party comes back as it was. Winning gives the Mystic Water the first time and a
Bottle Cap on repeat wins. If your bag is full on your first win, the
official keeps the Mystic Water for you and the win counts immediately.
`python3 utils/anime_events/test_whirl_cup.py SAVE.sav` checks it.

### Anime cameos

Once you've beaten both Red and the Orange League (Drake), five
characters from the anime show up, each ready for a battle any time you talk
to them, with teams from the show at levels 79–84:

| Who | Where | Team |
|---|---|---|
| Ash | Pallet Town, by Prof. Oak's lab | Bulbasaur, Pidgeot, Heracross, Snorlax, Charizard, Pikachu |
| Tracey | Prof. Oak's lab | Venonat, Marill, Scyther |
| Ritchie | outside Mt. Silver's Pokémon Center | Happy (Butterfree), Zippo (Charmeleon), Sparky (Pikachu) |
| Harrison | outside Mt. Silver's Pokémon Center | Hypno, Sneasel, Steelix, Houndoom |
| Casey | the National Park, by the fountain | Beedrill, Meganium, Electabuzz |

They reuse existing trainer pictures and sprites, and share one spare event
flag, so saves don't change. `python3 utils/anime_events/test_cameos.py
SAVE.sav` checks them in the emulator.

### The movies

Three events from the first movies, each a battle where the story happened:

- **Mewtwo Strikes Back**, Cerulean Cave (after Red): before you can battle
  Mewtwo, it speaks to you and sends out clones of your own team: the same Pokémon,
  levels, moves, items and stats, at full health even if yours are hurt. It
  has its own trainer picture (cut from its battle sprite) and its Stadium
  battle music. Then the usual Mewtwo battle. If you already caught or
  defeated Mewtwo, examine its former spot on the lowest floor to face a
  psychic echo of the clone challenge. A boy in Cerulean City points you
  there. The echo never gives another catch, and the clone story is recorded
  once you win, including across saves and rematches.
- **Spell of the Unown**, the Ruins of Alph Research Center (after Red): Molly, waiting for her papa, battles with the friends the Unown
  dreamed up for her and Entei (Unown, Ursaring, Donphan, Mantine, Ampharos,
  Entei, levels 64–70). Listen to Molly after the battle, then follow the
  knocking to the statue near the ladder in the inner chamber, where two of
  the Unown's illusions (Teddiursa and Phanpy, level 62, that no ball can
  catch) guard it until her father is free. Help her
  father home to unlock her friendly rematch. If your bag is full, Molly
  holds your Ability Patch and the rescue can still go ahead.
- **Celebi: Voice of the Forest**, Ilex Forest (after Red and the Celebi
  time travel): three forest Pokémon his black ball holds (Beedrill, Ariados,
  Noctowl, levels 64–66) guard the shrine until he's beaten; no ball can
  catch them, and each one you beat is freed. The Iron Mask Marauder of Team
  Rocket waits by the shrine with
  Sneasel, Scizor, Tyranitar and his Dark Ball Celebi (levels 70–76). Beat
  him once to drive him off for good and find a Big Nugget. If the Items
  pocket is full, make room and examine where he stood to collect it later;
  he stays defeated and the unclaimed reward survives saving. Once he's gone,
  the hurt Celebi heals at the shrine, and the traveler who kept calling from
  the other side steps out: Sammy, a boy from decades ago, who goes home with
  it. The Field Book then points to Pallet Town, where Prof. Oak reveals he
  was Sammy and gives you a Master Ball.

`python3 utils/anime_events/test_movie_events.py SAVE.sav` checks them in the
emulator.

### Checking the postgame

Set up an isolated emulator environment and run the checks from the project
root, using a compatible save with a healthy party:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r utils/anime_events/requirements.txt
.venv/bin/python utils/anime_events/run_checks.py /path/to/SAVE.sav --full --shots /tmp/postgame-shots
```

The runner checks the Johto, Kanto and optional quest pages against staged
progress, then follows the field book from Red through the Pallet finale.
It restarts the game mid-story and checks all three catch-up pages after
Continue. It also checks the Orange League, cameos, Whirl Cup and
movie events, and audits the 14 added character placements. It also executes
the ROM's spawn-path routine against walls, ledges, warps, water and objects.
With `--full`, it sweeps every wild encounter map; without it, it runs the
quicker encounter checks. Save data is loaded into memory, and the supplied
save file is not overwritten. Movie checks include continuing an in-memory
save after the echo and after leaving an unclaimed Marauder reward.

The placement audit assumes every HM is available. Battle victories are
forced to exercise scripts and rewards, so these checks do not assess
difficulty or replace a natural playthrough. The new characters still use
the existing portraits and overworld sprites listed above.

### Smarter trainer AI

These apply to every trainer battle, not just link play:

- Trainers weigh a move's accuracy, so they rank moves by expected damage (Aura Sphere over Focus Blast when it matters) and don't chase coin-flip KOs as eagerly as sure ones.
- Trainers stop switching into a mon that resists your attack but is about to faint.

## Building and testing

Build exactly as Polished Crystal does (see [INSTALL.md](INSTALL.md)); RGBDS 1.0.4 is required. On top of that:

- `make test` builds the ROM and runs a small test suite against the real assembled code under the PyBoy emulator, plus a static check for cross-bank calls. CI runs it on every push. It needs `pip install pyboy`.

## Upgrading old saves

If a new build says "Your save file does not match the game version of this ROM", run the save upgrader in `utils/save_upgrade/`. It converts saves from earlier builds, including the January 2026 family ROM. See [utils/save_upgrade/README.md](utils/save_upgrade/README.md).

## The `meta_sim/` balance tools

There's also a Python toolkit in `meta_sim/` for crunching the numbers on stat/move balance. It's not part of the game, just a helper for testing changes before they land:

- a 1v1 threat matrix and a 6v6 Monte Carlo battle sim with random, role-based, and synergy-drafted teams;
- "oracles" that run the ROM's real stat and damage routines under PyBoy, to confirm the sim's math matches the game.

See [meta_sim/README.md](meta_sim/README.md).

Everything else—features, install instructions, FAQ—still applies from Polished Crystal. See [FEATURES.md](FEATURES.md), [INSTALL.md](INSTALL.md), and [FAQ.md](FAQ.md).

## Credits

See [CREDITS.md](CREDITS.md). Original game design and the vast majority of this codebase: Rangi42 and the Polished Crystal contributors.
