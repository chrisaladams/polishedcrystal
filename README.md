# Pokémon Polished Crystal: Link Edition

**Polished Crystal: Link Edition** is a competitive take on Pokémon Crystal, built for balanced L50 link battles. It rebalances the roster, tightens the link-battle rules, makes Cable Club connections forgiving, and sharpens the trainer AI, with its own Python balance-simulation toolkit (`meta_sim/`) to back each change with data.

It's built on [Rangi42's Polished Crystal](https://github.com/Rangi42/polishedcrystal), itself based on [the Pokémon Crystal disassembly](https://github.com/pret/pokecrystal). All credit for the base game—the engine, mechanics overhaul, new maps, Pokédex, and everything else—goes to that project and its contributors.

It's kept in sync with Polished Crystal: the latest merge brings in Rangi42's `master` as of November 14, 2026, including the cable car cutscene, the link party corruption fix, the Bad Dreams/Magic Guard fix, and their other battle and item fixes.

## What's different here

### Link battle balance

A pass at tightening up the meta for L50 link battles:

- **Stat compression** — buffed a bunch of weak/early-game mons, trimmed a handful of top-tier ceilings, so the power band is tighter across the roster. Most recently, Aerodactyl's Attack went from 105 to 95 and Charizard's from 101 to 93, reining in their Tough Claws physical hits. For the 1.0 release, the meta test (`meta_sim/metatest.py`) flagged a few builds that were clearly over or under an average teammate across two independent runs, so:
  - **Trimmed:** Beedrill (Atk 100→90, Spe 115→100), Gliscor (Atk 95→85, Def 120→110), Magnezone (Sp. Atk 130→120), Overqwil (Sp. Def 90→75), Annihilape (Atk 100→95).
  - **Buffed:** Clefable (Def 73→80, Sp. Atk 85→95), Wigglytuff (Def 55→65, Sp. Def 65→75), Hypno (Def 70→80, Sp. Atk 73→83).

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

- **Autosave.** The game saves itself when you stop walking, wherever you
  could save normally (it takes a tenth of a second). Turn it off under
  Options → Autosave.
- **PC boxes from the start menu.** "Boxes" opens Bill's PC from anywhere you
  could save, so you can swap team members without a Pokémon Center. (When
  the menu is full, Exit makes room for it; B and Start still close the menu.)
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
  surf), drawn with their walking sprites
  in their own colours. A shiny one shows its shiny colours. Walk into one, or
  face it and press A, to battle it. They're chosen exactly as random
  encounters are: the same tables and odds, time of day, swarms, roaming
  legendaries, lead abilities, music and Cleanse Tag, and the same 1 in 4,096
  shiny chance (3 with the Shiny Charm). Two are there when you arrive, and
  each step brings another, while there's room, with the map's usual
  encounter chance. A roaming legendary on your map comes just as often as
  it did: if every slot is full, it takes the place of the wild Pokémon
  furthest from you. One that wanders off screen is gone, making room for
  another. While a Repel works, the ones it would have kept away run from
  you, and run off if you walk into them. The Bug-Catching Contest's bugs work
  the same way. Fishing, Headbutt, Rock Smash and Sweet Honey are unchanged,
  and without the Silph Scope the Pokémon Tower's ghosts still ambush you.
  They don't touch your save or any map's own people. To check them in the
  emulator: `python3 utils/wild_mons/test_wild_mons.py SAVE.sav` (every map
  with wild Pokémon, battles, Repel, sprites and colours, saving).

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
