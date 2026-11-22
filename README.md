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
- **Upstream battle bugs fixed:** Thunder never missed in harsh sunlight (it's 50% now), harsh sunlight didn't stop freezing (it let a freeze chance skip every check instead), and Low Kick gave 80 power to anything between 5 kg and 100 kg (it now follows the weight table: 40 power above 10 kg, 60 above 25 kg, 80 above 50 kg).
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

A save made inside a room whose scripts moved in a newer build (the Pokémon
Center 2F link room, after this update) used to crash when you talked to
someone there; continuing a save now takes the room's scripts from the ROM.

**Both players need the same build.** This is Link Edition 1.0, link version 1. Link Edition has its own link game ID, so it won't connect to stock Polished Crystal or to the pre-release Link Edition builds at all; that's deliberate, since mismatched battle rules or party layouts would desync. A later release that changes battles will raise the link version, and everyone will need to update together.

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
