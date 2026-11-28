# Johto expansion: technical investigation (nothing implemented)

Measured from the build at the QA baseline (`qa-baseline-2.1-pre`, ROM sha1 `53dc05aa…`) and the repository. This corrects
and replaces the resource table in the earlier discovery document, which wrongly counted the reserved 4 MiB layout as free space.

## 1. ROM capacity: the real figures

| View | Used | Free | Notes |
|---|---:|---:|---|
| **2 MiB image** (ROM0 + ROMX banks 1 to 127) | 2,094,370 | **2,782 bytes** (0.13%) | ROM0 146 + ROMX 2,636 (largest gap 2,617). This is what "fits in 2 MiB" means today. |
| Linker layout (4 MiB, 255 ROMX banks) | 2,094,370 | 2,099,788 | The 128 empty banks (128 to 255) are **beyond** the 2 MiB image. They are reserved layout, not 2 MiB headroom. |

- The Makefile already builds for MBC5 and carries the comment "4 MiB carts … the ROM grows past 2 MiB once its banks fill", so the
  4 MiB layout was anticipated by the build. Whether to cross 2 MiB is still a **cartridge and compatibility decision for you**: it
  affects flash carts, repro carts, emulators and the original-hardware target.
- The earlier ROM reclamation audit measured 12,852 bytes free at an earlier commit. The Link Edition content since then has used
  almost all of it. Its remaining lossless candidates (jukebox-only tracks, optional fonts, cosmetic Pikachu forms, printer support,
  textbox frames, the post-Hall-of-Fame title tune) total **about 14 KiB**, and every one of them changes something a player sees
  or hears. Taking them all would give roughly **27 KiB** free.

**Consequence:** a Johto expansion of the size proposed (section 3 estimates 160 to 260 KB) cannot fit in 2 MiB, even with every
reclaim candidate taken. Three honest options:

| Option | What it means | Cost |
|---|---|---|
| A. 4 MiB ROM for the Link Edition | The image grows to 4 MiB; new data and code go in banks 128 and up | Compatibility decision; audit bank-number assumptions (below) |
| B. Stay at 2 MiB | About 27 KiB of new content at most | Only a thin slice of the proposal fits |
| C. Two builds | A 2 MiB "classic" and a 4 MiB "full" build | Doubles the build and test surface |

**Audit before crossing 2 MiB** (bank numbers of 128 and above): any code that uses bit 7 of a bank byte as a flag (battle script
flags use `1 << 7`; several scripts mask with `and $7f`) must be checked; `dba` stores banks in one byte, which is enough for 256
banks; the SameBoy and PyBoy test setup already handles larger ROMs.

Other regions: ROM0 (home bank) 146 bytes free, so new engine code must live in ROMX behind `farcall`; WRAM0 9 and HRAM 5 bytes free;
WRAMX has gaps of 1,809 bytes (bank 5) and 1,612 bytes (bank 2); SRAM 923 bytes free.

## 2. The event-flag problem

### Facts

| | |
|---|---|
| Capacity | 2,304 bits; the array's save size is locked by an assert in `constants/event_flags.asm` |
| Named flags | 2,288 |
| Free slots | **16** (`const_skip` placeholders) |
| Unreferenced flags | **0**: every named flag is used somewhere; earlier phases already recycled the dead ones |
| By kind | 760 trainer-beaten, 227 object-visibility, 178 item/gift received, 10 gave-item, 8 temporary until map reload, 1,105 story and other |
| Where it lives | WRAMX bank 1 (`wEventFlags`, 13 bytes free in that bank), saved in the main and backup save |
| Accessor | `FlagAction` in the home bank is generic: it works on any bit array whose address is passed in `hl` |

### Options

| Option | Advantages | Limitations | Migration risk |
|---|---|---|---|
| **1. Consolidate existing flags** | No new storage | No dead flags exist. Trainer, visibility and gift flags are each needed per object. Deriving visibility from other state would change how old saves read. Realistic yield: tens of flags. | High per flag (changes old-save meaning) |
| **2. Extension flag array** (a bit array in a new versioned SRAM record) | Generic: 128 bytes give 1,024 flags; reuses `FlagAction`, so no ROM0 cost | Needs a WRAMX home (bank 5 or 2), bank-aware access, new script access | Low: old saves read it as empty |
| **3. Adventure state counters** (one byte per adventure, as you proposed) | 64 bytes hold 64 adventures with 256 states each; monotone progress is how these stories work; branching is `if state >= n`; easy to migrate from old flags | Cannot represent parallel, independent milestones; needs sub-states or bits for those | Low |
| **4. Hybrid (2 + 3), recommended** | Counters for story arcs, bits for collectibles, visibility and one-offs: about 64 counters and 1,024 bits in 192 bytes. A story with 20 milestones costs 1 byte instead of 20 bits. | One new access layer; scripts use new macros | Low, if the record has its own marker, checksum and version |
| 5. More SRAM banks | Large | The cartridge has 32 KiB (4 banks); MBC5 could address more, but real carts and flash carts differ | Not recommended |

### Recommended design (for approval, not implemented)

- **Storage:** one record with a marker, a version byte, a checksum, 64 counter bytes and 128 flag bytes (about 196 bytes), placed
  in the SRAM padding that already exists inside the save copies: bank 1 `$ab84` (392 bytes) for the main save and bank 0 `$bd84`
  (393 bytes) for the backup. This follows the rules in `docs/sram-allocation.md` (own integrity check, interruption-safe write: clear
  the marker, write data and checksum, write the marker last).
- **Runtime:** a 196-byte mirror in a WRAMX bank with a gap (bank 5).
- **Access:** script macros built on `callasm` and ROMX routines: no new script command ids, no ROM0 growth. `FlagAction` serves the bit array.
- **Old saves:** the record is empty on an old save, so a one-time migration derives each counter from flags and badges that already exist
  (for example, a player with the Zephyr Badge starts the Alph arc at "available", a player who finished Alph's puzzles starts it
  further along). That is how a progressed save "experiences new content without restarting".
- **Capacity vs need:** the core proposal needs about 15 counters and 42 bits (about 20 bytes of the 196); the record is sized 64 counters and 1,024 bits to leave room for optional adventures and later work.

### Risks to settle before building

1. Upstream merges: a change that grows the save fails to link because the padding is used; that failure is the warning, then migrate.
2. The main and backup copies must stay consistent; the record is read from whichever copy the loader trusts.
3. `ErasePreviousSave` and the new-game path must clear the record (it belongs to one adventure).
4. A prototype with a power-cut test (as `test_save.power_cut_during_save` does) must pass before any content depends on it.

## 3. Cost model (calibrated on the current ROM)

Measured: 122 script sections average 3.2 KB (largest 9.9 KB; script and text together); 444 map layouts average 101 bytes; 229
overworld sprites average 205 bytes; earlier audit: a jukebox-only song is about 0.8 KB, a full map-music track 2 to 6 KB.

| Unit | ROM cost |
|---|---:|
| Cinematic scene (about 10 lines of text) | 0.6 to 1.2 KB |
| Story NPC with a few branches | 0.15 to 0.3 KB |
| Small new indoor map (layout, events, callbacks, text) | 0.8 to 1.5 KB |
| Large cave or outdoor map | 1.5 to 3 KB |
| Overworld sprite | about 0.2 KB |
| Music track (new) | 1.5 to 4 KB (reuse: 0) |
| Trainer team | 0.1 to 0.25 KB |
| Effect or puzzle code (ROMX) | 1 to 3 KB each |

## 4. What already exists to reuse (no ROM cost beyond a call)

- **Cinematic library** (`docs/cinematics.md`): tints, pulses, flashes, silhouettes, per-character shadows and reveals, characters
  entering, title cards, scene weather (rain, snow, thunderstorm, sandstorm, cherry blossoms), camera pans, spark, dust and drop
  particles, clone sprites.
- **Environment:** weather system, palette lighting, `showemote` set, earthquake, sparkles.
- **World:** the software clock and weekdays, visible wild Pokemon with eight behaviour profiles, followers (all 289 species),
  the Field Book and Quest Map, three roaming Pokemon with `RoamMaps` movement.
- **Assets:** 256 overworld sprites including Elm, Lyra, Eusine, Kurt, Proton, Petrel, Archer, Ariana, Sage, Scientist, Dragon Tamer,
  Dragonite, Celebi, Mew, big Ho-Oh, big Lugia, big Gyarados, big Lapras; 197 songs of which 6 are unused (Dewford Town, XY legendary
  battle, four Prism battles) and `MUSIC_LUGIAS_SONG_2000` and `MUSIC_SUMMONING_DANCE_HGSS` from The Power of One; 216 sound effects, 16 unused
  (grass rustle, wall open, twinkle, tingle, Suicune intro sounds, fanfares).
- **Characters already recurring:** Silver appears on 25 maps, Lyra on 24, Elm on 27, Eusine on 8, the Dragon Clan on 14.
  The expansion adds arcs, not new faces for their own sake.
