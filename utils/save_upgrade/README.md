# Save upgrader

Upgrades a save from an older build of Polished Crystal: Link Edition so it loads on the current build.

You need it when the new ROM says **"Your save file does not match the game version of this ROM"**, or when a save from a development build would load with things in the wrong place. Polished Crystal's own patcher (`make bsp`) only covers official releases, so it can't help with builds in between.

## Quick start

Run from the repository root after building the current ROM with `make`:

```sh
# 1. Find out which build wrote the save
python3 utils/save_upgrade/upgrade_save.py identify path/to/game.sav

# 2. Upgrade it using that build's profile
python3 utils/save_upgrade/upgrade_save.py upgrade path/to/game.sav path/to/game_upgraded.sav \
    --from utils/save_upgrade/profiles/v10-2026-01-family-rom.json
```

Then rename the upgraded file to match the filename your emulator already uses for the old save, and choose **Continue**. Keep the original file as a backup. The tool never modifies its input.

`identify` lists every known profile that can read the save, along with the location and Fly towns each one reads from it. Builds that share a save layout will all read as valid, so pick the one whose Fly towns match how far the player actually got. For example, a save that has Ecruteak but not the Pokémon League is from a build whose numbering puts it that way.

## Known builds

| Profile | Build |
|---|---|
| `profiles/v10-2026-01-family-rom.json` | The January 2026 family ROM (`e9104ae`) |
| `profiles/v10-2026-11-pre-merge.json` | Balance builds up to the November 2026 upstream merge (`7cb835e`) |

To support another old build, snapshot it once and commit the profile:

```sh
python3 utils/save_upgrade/upgrade_save.py profile --rev <commit> \
    --name "description (save version N)" -o utils/save_upgrade/profiles/<name>.json
```

This builds that commit in a temporary git worktree, so it needs the same toolchain as a normal build.

## What it changes

For both the main and the backup copy of the save:

- **Saved fields** are matched by name. A field that moved is copied to its new place. A field that's new in the current build starts at zero, and the tool stops instead of overwriting non-zero old data unless you pass `--allow-reset`.
- **Map locations** are translated by map name: where you're standing, your last Pokémon Center, the Dig/Escape Rope point, the backup warp, the roaming legendaries, and the Yanma/Dunsparce swarms.
- **Fly destinations and event flags** are re-mapped by name, so renumbered flags keep their values.
- **The save version** is updated, and both checksums are recomputed.

The real-time-clock footer that emulators append to `.sav` files is left untouched.

## What it refuses

- Saves that fail their checksum under the chosen profile (wrong profile, or a corrupted file).
- Saves whose version doesn't match the profile (for example, a save that's already upgraded).
- Builds that number items, Pokémon or moves differently. Those IDs are stored in bags, parties and boxes, and this tool doesn't translate them.
- Builds where a saved block changed size or an SRAM area moved.

Party and box Pokémon keep the stats stored in the save. The game recalculates them on level up or when a Pokémon passes through the PC, which is how base-stat balance changes reach existing Pokémon.

## Renames

Fields and maps that were renamed without changing meaning are listed in `FIELD_RENAMES` and `MAP_RENAMES` at the top of `upgrade_save.py`. If an upgrade stops with "has no equivalent", add the rename there.


## If the area around the player looks wrong after upgrading

A save also keeps a snapshot of the blocks that were on screen. When a newer
build renumbers a tileset's blocks (the November 2026 upstream merge did for
the Johto tilesets), that snapshot draws the wrong tiles around the player on
Continue, for example rooftops on Route 41's sea. Rebuild it from the current
ROM's own map data (needs PyBoy):

```sh
python3 utils/save_upgrade/refresh_screen.py game_upgraded.sav game_fixed.sav
```

It only changes those 30 blocks and the checksums. Running it on a save that
doesn't need it leaves the file unchanged.
