# Pokémon Polished Crystal: Link Edition 2.0

Link Edition is a competitive, family-link take on Rangi42's
[Polished Crystal](https://github.com/Rangi42/polishedcrystal) 3.2.3, itself
built on the [pret/pokecrystal](https://github.com/pret/pokecrystal)
disassembly. Version 2.0 is the Complete Edition: the adventure, the
post-game stories, the Orange League, six regional cups and five Cable Club
formats, finished and stabilized.

The full description of each feature is in the [README](../../README.md).
What's still to be tested on real cartridges and cables is in the
[hardware checklist](hardware-checklist.md), and the evidence behind this
release is in the [release checklist](checklist.md).

## What's in 2.0

**Link play**
- Five Cable Club battle formats: Standard (level 50, up to six, one
  legendary), Random teams (six generated Pokémon), Rising Star (three at
  level 30), Unrestricted, and the linked World Championship. Trading as
  before.
- Link battles can't silently desync: an error-checked turn exchange and a
  per-turn battle fingerprint stop a split battle; a bumped or unplugged
  cable is recovered or ended cleanly, with your party restored.
- Both players need the same build, and the desk tells you when the link
  didn't go through and offers to try again.
- Trainer Card records: lifetime and yearly results against up to 65
  different friends.
- Friend Battles: the Cable Club's third desk keeps the last team of two
  friends you've battled, to battle again offline.
- The linked World Championship: two players share one bracket, play their
  rounds at the Indigo Plateau, and sync results over the cable; the final is
  a link battle.

**Battles and balance**
- A rebalanced roster for level-50 link battles (Default build; Faithful
  keeps canon stats), Eviolite restricted, Moody removed, evasion capped at
  +2 in link play, smarter trainer AI, and fixes to several upstream battle
  bugs.
- Competitive settings are fixed for everyone (natures, abilities, the
  physical/special split, Modern EVs), so every family save can link.

**The world**
- Your lead Pokémon follows you (Options → Follower).
- Wild Pokémon you can see, with eight behavior profiles, instead of random
  encounters; the same tables, odds and shiny chance.
- A software world clock (a day is 90 minutes of play), so no clock battery
  is needed.
- The Field Book and Quest Map: where to go next, for the main story and
  every post-game chapter.

**After Red**
- Four movie stories: Spell of the Unown (Molly at the Ruins of Alph), Celebi:
  Voice of the Forest (Ilex Forest and the Iron Mask Marauder), Mewtwo Strikes
  Back (Cinnabar and Cerulean Cave) and The Power of One (Shamouti Island),
  staged with title cards, camera pans, weather, lighting and music.
- The Orange League: Cissy's Surf course, Danny's ridge climb, Rudy's three
  rounds, Luana's two-on-two singles, then Drake.
- The Pallet Invitational and anime cameos (Ash, Ritchie, Harrison, Tracey,
  Casey).
- Six regional cups (Rising Star, Whirl, Kimono with a daily type, Dragon
  Masters, Rental, and the World Championship at the Indigo Plateau).
- Bedroom trophies and the Adventure Album.

**New in this release's finishing pass**
- Dedicated overworld sprites for Molly, the Iron Mask Marauder, Ash's
  Pikachu, Melody, Drake, the Orange Crew and Sammy; new trainer portraits for
  the Orange Crew; cloning tanks, Unown crystals and a corrupted Ilex Forest.
- Real dialogue for upstream placeholders on the Orange Islands (Prof. Ivy's
  assistants, Darach and Caitlin, the Sightseers Cy & Vi).
- Faithful build: generated typed teams (Kimono Cup, Dragon Masters, Rental)
  now follow the Faithful build's types.

## Compatibility

- **Console:** Game Boy Color, or a Game Boy Advance/SP in its Game Boy Color
  mode.
- **Cartridge:** MBC5 with battery-backed save RAM (32 KiB), 2 MiB or larger.
  The ROM is 2 MiB; it also runs on 4 MiB MBC5 and MBC30 carts. No real-time
  clock is needed.
- **Emulators:** any accurate Game Boy Color emulator with MBC5 support
  (for example mGBA, SameBoy, Gambatte, BGB, Emulicious). The test suites use
  PyBoy.
- **Link cable:** a Game Boy Color link cable. Both players need the same
  release build (Default with Default, Faithful with Faithful).
- **Saves:** saves from Link Edition builds with save version 11 (every
  family save) load directly. Older builds' saves (save version 10, such as
  the January 2026 family ROM) need the save upgrader once:
  [`utils/save_upgrade/README.md`](../../utils/save_upgrade/README.md).
  Saves from upstream Polished Crystal 3.x are not compatible.

## Installing

Download the files for your build from the release: the `.gbc` ROM, or the
`.bps` patch. Check them against `CHECKSUMS.txt`.

- **Flash cartridge or emulator:** load the `.gbc`. On a flash cart that asks,
  choose MBC5 with 32 KiB battery save.
- **From the patch:** get the official Polished Crystal 3.2.3 ROM from
  [its release page](https://github.com/Rangi42/polishedcrystal/releases/tag/v3.2.3)
  (`polishedcrystal-3.2.3.gbc` for Default, `polishedcrystal-faithful-3.2.3.gbc`
  for Faithful), then apply the matching `.bps` with
  [Floating IPS](https://github.com/Alcaro/Flips) or
  [ROM Patcher JS](https://www.marcrobledo.com/RomPatcher.js/). The patch
  checks that the source ROM is the right one, and the result's checksums
  must match `CHECKSUMS.txt`.
- **Building it yourself:** see [INSTALL.md](../../INSTALL.md) (RGBDS 1.0.x),
  then `make` (Default) or `make faithful`. `utils/release/build_release.py`
  makes the release files.
- **Keeping your save:** keep the emulator's or cartridge's `.sav`; rename it
  to match the new ROM's file name if your emulator uses the name.

## Known limitations

- **Not yet tested on real hardware.** Everything is verified in emulation;
  the [hardware checklist](hardware-checklist.md) lists what remains.
- A restored pre-prize backup paired with a cartridge whose Championship
  bracket is already closed loses access to that prize (an accepted limit;
  issue ledger L1).
- A power cut while a Friend team is being rewritten loses that friend's
  previous team until you battle them again (no journal, by decision; L3).
- In tall grass, bringing out a new visible wild Pokémon can take about two
  frames, roughly once every six steps (L27).
- Faithful and Default builds can't link with each other, by design.
