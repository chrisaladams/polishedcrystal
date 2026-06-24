# Pokémon Polished Crystal (balance fork)

This is a fork of [Rangi42's Polished Crystal](https://github.com/Rangi42/polishedcrystal), a custom Pokémon game built on [the Pokémon Crystal disassembly](https://github.com/pret/pokecrystal). All credit for the base game—the engine, mechanics overhaul, new maps, Pokédex, and everything else—goes to that project. This fork starts from their work and layers on a set of competitive balance tweaks for link play.

## What's different here

A pass at tightening up the meta for L50 link battles, nothing more:

- **Stat compression** — buffed a bunch of weak/early-game mons, trimmed a handful of top-tier ceilings, so the power band is tighter across the roster.
- **Trapping fixed** — Gengar lost Shadow Tag, Dugtrio/Diglett lost Arena Trap. Trapping someone with no way to switch isn't really a fun interaction. Wobbuffet/Wynaut keep it since it's their whole gimmick.
- **Eviolite restricted** to genuine not-fully-evolved mons (closed a couple of edge-case loopholes).
- **Moody removed.**
- **Sleep and evasion clauses** for link battles — can't stack a second mon to sleep at once, and Double Team/Minimize no longer raise miss rate. Both gated to real link play only, so singleplayer and the Battle Tower are untouched.
- **Link-battle healing/leveling** — mons get forced to L50 and topped off before a link battle, so games aren't decided by who happened to grind more.
- A few mart/item tweaks to go with the above.

There's also a small Python tool in `meta_sim/` for crunching the numbers on stat/move balance—not part of the game, just a helper for testing changes before they land.

Everything else—features, install instructions, FAQ—still applies from upstream. See [FEATURES.md](FEATURES.md), [INSTALL.md](INSTALL.md), and [FAQ.md](FAQ.md).

## Credits

See [CREDITS.md](CREDITS.md). Original game design and the vast majority of this codebase: Rangi42 and the Polished Crystal contributors.
