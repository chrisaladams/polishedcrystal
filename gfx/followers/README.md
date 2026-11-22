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

About 10.0 KB free (after the savings marked done below), almost all in a
few large gaps, so it packs well: about 160 sprites at 60 B, 120 at 80 B,
or 85 at 112 B. Each sprite is its own section, so the linker places it in
whatever gap fits.

### What we can still make

| Source | Gain | Status |
|---|---|---|
| Identical icons and minis shared | 684 B | done |
| Drop the 6 songs only the music player played (Dewford Town RSE, Legendary Battle XY, four Prism battle themes); it still plays every song the game uses | 5.1 KB | done |
| Share text repeated in map and phone scripts (100 extra copies now point at one copy with `text_far`) | 1.2 KB | done |
| Compress the fonts | ~2.5 KB | possible; a few routines read letters straight from ROM |
| Share the remaining duplicate graphics (two back sprites, three form masks) | ~0.7 KB | needs moving them into shared sections |
| Share the remaining repeated text (in item/move descriptions and common texts, which are printed differently, so it needs another approach) | ~0.5 KB | possible |
| Store less in our Random Battle set table (work out types and weaknesses when the game needs them) | ~1.5 KB | possible |
| Drop the Pokédex footprints (the small footprint box on each Pokédex page) | 5.2 KB | needs the go-ahead |
| Drop Game Boy Printer support | 2.0 KB | needs the go-ahead |
| Drop the front-sprite animations (Pokémon would appear in battle and the Pokédex in a still pose) | 20.4 KB | needs the go-ahead; could be kept for some Pokémon |

The lossless items together: about 15 KB free, enough for every fully
evolved Pokémon (12 KB) in this style. With the footprints, printer and
jukebox songs too: about 27 KB, enough for all 333 at ~70 B. With the
front-sprite animations as well: about 47 KB, enough for all 333 in Rangi's
style (37 KB). Full walking sprites for everything (48–73 KB) don't fit in
2 MB.

### Replacing the party icons

The party icons in `gfx/icons/` (31.7 KB) are only drawn on the overworld:
Pokémon standing on maps, the Fly animation, and the follower. The party
menu, PC, trades and naming screen draw the separate minis in `gfx/minis/`.
So a full walking sprite could replace each icon, its front frames then
drawing those overworld Pokémon too, and it only costs what it adds over
the icon:

| Replacing every icon with | All 333 | Extra over today |
|---|---|---|
| Full walking sprites, symmetric front and back | ~48 KB | ~16 KB |
| Full walking sprites, drawn as-is | ~73 KB | ~41 KB |


Not worth it or not possible: cries (15 KB, every Pokémon needs one), music
(145 KB, but songs are what the game plays everywhere), phone calls and
radio (mostly text that is already compressed), and a 4 MB ROM (MBC30, which
most flash carts don't support).

Not available: the graphics compressor (`tools/lzpcompress`) is already
optimal and already exploits mirrored and repeated data within each file,
and the game's text is already Huffman-compressed with an n-gram dictionary.
