# Follower sprites

A following Pokémon with a sprite here walks with real frames: its party icon
facing down, its back view walking up, and its side view walking left
(mirrored for right). A Pokémon without one follows as its bouncing party
icon, so nothing breaks while the set is incomplete.

## Adding one

1. Draw a 16×32 picture, 4 shades (white, light, dark, black), like the
   party icons in `gfx/icons/`: the **back view** on top, the **side view
   facing left** below. Use the colours of the Pokémon's party icon; the
   follower is drawn with the icon's palette.
2. Save it as `gfx/followers/<species>.png`.
3. Add a section for it to `gfx/followers.asm` (copy Pikachu's).
4. Add a `follower_sprite` line to `data/pokemon/follower_sprites.asm`
   (leave out the form to match every form of the species).
5. Credit the artist in `CREDITS.md`.

Keep the back view **symmetric** where the Pokémon allows it (draw the left
half and mirror it): the compressor then stores almost only half of it,
which matters, because ROM space is the limit (below).

## Space budget (2 MB ROM)

Measured on the build in November 2026.

### What all sprites need (333 species and forms)

| Sprite style | Per species | All 333 |
|---|---|---|
| Full walking sprites (front, back, side, each with a walking frame), drawn as-is like NPCs | ~220 B | ~73 KB |
| Same, with front and back drawn symmetrically | ~145 B | ~48 KB |
| Back + side only, front from the party icon, drawn like Rangi's Pikachu | ~112 B | ~37 KB |
| **Back + side only, front from the party icon, symmetric back view** (the format used here) | **~60–70 B** | **~20–23 KB** |

The 174 fully evolved Pokémon alone need about 12 KB at ~70 B, or about
19.5 KB at ~112 B.

### What we have

About 11.9 KB of free ROM (measured from the build's map file, ROM banks
only; an earlier figure of "about 10 KB" wrongly counted spare RAM too, and
the true figure before the savings below was 3.2 KB). Each sprite is its
own section, so the linker places it in whatever gap fits.

### What we freed

| Source | Gain |
|---|---|
| Identical icons and minis shared | 684 B |
| Text repeated in map and phone scripts shared with `text_far` (100 copies) | 1.2 KB |
| The 6 songs only the music player played (Dewford Town RSE, Legendary Battle XY, four Prism battle themes); it still plays every song the game uses | 5.1 KB |
| Fonts stored compressed, unpacked when needed | 2.0 KB |
| Duplicate graphics shared (two back sprites, three mini masks) | 735 B |
| Random Battle sets: each type profile stored once | 653 B |
| More repeated text shared (10 map texts, 6 menu prompts) | 255 B |

### Replacing the minis and party icons

The game has two sets of small Pokémon pictures, 78 KB together: the
**party icons** in `gfx/icons/` (drawn only on the overworld: Pokémon
standing on maps, the Fly animation, and the follower) and the **minis** in
`gfx/minis/` (the party menu, PC, Pokédex list, trades and naming screen).
A full walking sprite per species could replace both: its front frames would
draw everything the icon and mini draw now, with a mask made from its
outline. Per species that frees about 220 B and costs about 145–220 B, so
space stops being the limit:

| Replace | Frees | All 333 walking sprites cost | Left over |
|---|---|---|---|
| Party icons only | ~31 KB | ~48 KB (symmetric) / ~73 KB (as-is) | short by ~4 KB / ~29 KB |
| Party icons and minis | ~78 KB | ~48 KB (symmetric) / ~73 KB (as-is) | ~42 KB / ~17 KB |

It works species by species, so a Pokémon without a walking sprite keeps
its mini and icon. Cosmetic forms (Unown letters, Magikarp patterns) can
share one walking sprite per species.

### What we could still cut

| Cut | Gain |
|---|---|
| Magikarp's 19 extra colour patterns (every Magikarp looks plain) | 17.1 KB |
| Front-sprite animations (Pokémon appear in battle and the Pokédex in a still pose) | 20.4 KB |
| Unown letters B–Z, ! and ? (every Unown looks like A) | 12.5 KB |
| Pokédex footprints (the small footprint box on each Pokédex page) | 5.2 KB |
| Six of the eight font choices in Options | ~3.9 KB |
| Pikachu's Fly and Chuchu forms | 2.4 KB |
| Game Boy Printer support | 2.0 KB |
| The second title-screen song (X/Y title, after the Hall of Fame) | 1.1 KB |

Not worth it or not possible: cries (15 KB, every Pokémon needs one), music
(145 KB, but songs are what the game plays everywhere), phone calls and
radio (mostly text that is already compressed), and a 4 MB ROM (MBC30, which
most flash carts don't support).

Not available: the graphics compressor (`tools/lzpcompress`) is already
optimal and already exploits mirrored and repeated data within each file,
and the game's text is already Huffman-compressed with an n-gram dictionary.
