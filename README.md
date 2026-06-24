# Pokémon Polished Crystal (balance fork)

This is a fork of [Rangi42's Polished Crystal](https://github.com/Rangi42/polishedcrystal), a custom Pokémon game built on [the Pokémon Crystal disassembly](https://github.com/pret/pokecrystal). All credit for the base game—the engine, mechanics overhaul, new maps, Pokédex, and everything else—goes to that project. This fork starts from their work and layers on a set of competitive balance tweaks for link play.

## What's different here

A pass at tightening up the meta for L50 link battles, nothing more:

- **Stat compression** — buffed a bunch of weak/early-game mons, trimmed a handful of top-tier ceilings, so the power band is tighter across the roster.
- **Eviolite restricted** to genuine not-fully-evolved mons (closed a couple of edge-case loopholes).
- **Moody removed.**
- **Evasion capped in link battles** — Double Team/Minimize/Bright Powder still help, but the target's evasion boost can't stack past +2 stages, so it can't be abused into an accuracy stall. Gated to real link play only, so singleplayer and the Battle Tower are untouched. (Trapping abilities — Shadow Tag, Arena Trap — and sleep are left as upstream ships them; Ghost-types, Shed Shell, and Run Away already give trapped mons an out.)
- **Link-battle healing/leveling** — mons get forced to L50 and topped off before a link battle, so games aren't decided by who happened to grind more.
- A few mart/item tweaks to go with the above.

There's also a small Python tool in `meta_sim/` for crunching the numbers on stat/move balance—not part of the game, just a helper for testing changes before they land.

Everything else—features, install instructions, FAQ—still applies from upstream. See [FEATURES.md](FEATURES.md), [INSTALL.md](INSTALL.md), and [FAQ.md](FAQ.md).

## Credits

See [CREDITS.md](CREDITS.md). Original game design and the vast majority of this codebase: Rangi42 and the Polished Crystal contributors.
