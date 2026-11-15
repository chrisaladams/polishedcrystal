# Pokémon Polished Crystal: Link Edition

**Polished Crystal: Link Edition** is a competitive take on Pokémon Crystal, built for balanced L50 link battles. It rebalances the roster, tightens the link-battle rules, makes Cable Club connections forgiving, and sharpens the trainer AI, with its own Python balance-simulation toolkit (`meta_sim/`) to back each change with data.

It's built on [Rangi42's Polished Crystal](https://github.com/Rangi42/polishedcrystal), itself based on [the Pokémon Crystal disassembly](https://github.com/pret/pokecrystal). All credit for the base game—the engine, mechanics overhaul, new maps, Pokédex, and everything else—goes to that project and its contributors.

It's kept in sync with Polished Crystal: the latest merge brings in Rangi42's `master` as of November 14, 2026, including the cable car cutscene, the link party corruption fix, the Bad Dreams/Magic Guard fix, and their other battle and item fixes.

## What's different here

### Link battle balance

A pass at tightening up the meta for L50 link battles:

- **Stat compression** — buffed a bunch of weak/early-game mons, trimmed a handful of top-tier ceilings, so the power band is tighter across the roster. Most recently, Aerodactyl's Attack went from 105 to 95 and Charizard's from 101 to 93, reining in their Tough Claws physical hits. These only apply to the normal build; `make faithful` keeps canon base stats.
- **Eviolite restricted** to genuine not-fully-evolved mons (closed a couple of edge-case loopholes).
- **Moody removed.**
- **Evasion capped in link battles** — Double Team/Minimize/Bright Powder still help, but the target's evasion boost can't stack past +2 stages, so it can't be abused into an accuracy stall. Gated to real link play only, so singleplayer and the Battle Tower are untouched. (Trapping abilities — Shadow Tag, Arena Trap — and sleep are left as Polished Crystal ships them; Ghost-types, Shed Shell, and Run Away already give trapped mons an out.)
- **Link-battle healing/leveling** — mons get forced to L50 and topped off before a link battle, so games aren't decided by who happened to grind more.
- A few mart/item tweaks to go with the above.

### Easier Cable Club connections

Linking up used to need both players to be almost perfectly in sync. Now:

- The receptionist waits about 26 seconds for your friend instead of about 8.
- If your friend isn't ready, or the link times out, you're asked whether to keep waiting instead of being kicked out, so neither player has to start over.
- The handshake after saving is more tolerant of one player saving slower than the other.

**Both players need the same build.** The link version is 9, so it can't link with older Link Edition builds or with stock Polished Crystal. That's deliberate, since mismatched battle rules or party layouts would desync.

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
