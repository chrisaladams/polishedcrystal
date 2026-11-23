# Follower sprites

Each `<name>.png` here is a Pokémon's walking sprite: six 16×16 frames in a
16×96 picture, 4 shades (white is transparent), in this order:

1. facing down
2. facing down, walking
3. facing up
4. facing up, walking
5. facing left (mirrored for right)
6. facing left, walking

The following Pokémon walks with all six. The first two also replace the
Pokémon's mini and party icon: the party menu, PC, Pokédex, trades and
Pokémon standing on maps draw them, and a mask for the PC and trade screens
is worked out from the picture. These Pokémon are drawn in the colours of
their overworld icon (`data/pokemon/overworld_icon_pals.asm`), so they look
the same everywhere.

A Pokémon without a walking sprite keeps its mini and icon (`gfx/minis/`,
`gfx/icons/`) and follows as its bouncing party icon.

## Adding sprites

1. Put standard 16×96 overworld sprite sheets (pokecrystal order: down, up,
   left, then the walking frames) in a folder, named after the Pokémon.
2. `python3 utils/followers/import_sheets.py FOLDER` converts the ones whose
   names match a mini into `gfx/followers/` in the order above (`--map
   name=file` for a name that doesn't match).
3. `python3 utils/followers/make_tables.py` hooks them up: their sections in
   `gfx/followers.asm`, and `walking_mon` entries in
   `data/pokemon/mini_icon_pointers.asm` in place of their minis and icons.
4. Credit the artist in `CREDITS.md` and below.

## Credits

The 277 Gen 1–2 and Unown sprites come from
[gcox32/pokecrystal](https://github.com/gcox32/pokecrystal) (`gfx/following/`),
a pokecrystal following-Pokémon hack: the follower port by vulcandth, the
Unown sprites by FrenchOrange and LJSTAR, and the art from the follower set of
ShockSlayer's Pokémon Crystal Clear. Surfing Pikachu and Armored Mewtwo are
the game's own overworld sprites.

21 regional forms shaped like their regular form (Alolan Rattata, Raticate,
Sandshrew, Vulpix, Ninetales, Diglett, Dugtrio, Meowth, Persian, Geodude and
Graveler; Galarian Slowpoke, Articuno and Moltres; Hisuian Arcanine, Qwilfish
and Sneasel; Paldean Wooper and Tauros; Bloodmoon Ursaluna) use its sprite in
their own colours (`SHARE` in `make_tables.py`).

43 more (most Gen 4 evolutions, Sylveon, Cursola, Sirfetch'd, Mr. Rime,
Kleavor, Ursaluna and 13 regional forms) come from SheerSt's
[PokéWilds](https://github.com/SheerSt/pokewilds) (`pokemon/pokemon/*/overworld.png`),
the same art style in colour, converted by `import_sheets.py`. Its README
credits Megaman-Omega for most of its overworld sprites, and Sadfish (Alolan
Raichu, Mantyke), Internet_Goblin (Ambipom), betsybugaboo (Azurill, Alolan
Marowak), LuxBeacon (Happiny, Munchlax), Invader (Honchkrow), SkwovetSquire
(Mime Jr.) and Shaqtothefuture (Alolan Grimer and Muk, Galarian Farfetch'd,
Sirfetch'd) among others.

## Space

About 33.8 KB of the 2 MB ROM is free (two whole empty banks, 126 and 127,
plus gaps). Count free space with the banks the map file doesn't list: an
entirely empty bank doesn't appear in it, which once made the free space look
16 KB smaller than it was. Sharing and compressing data (below) freed 5.8 KB,
and replacing a mini and icon (about 220 bytes together) with a walking
sprite (about 230 bytes) costs almost nothing; forms that share their regular
form's sprite free their mini and icon entirely.

| Freed | Gain |
|---|---|
| Identical icons and minis shared | 684 B |
| Text repeated in map and phone scripts shared with `text_far` (100 copies) | 1.2 KB |
| Fonts stored compressed, unpacked when needed | 2.0 KB |
| Duplicate graphics shared (two back sprites, three mini masks) | 735 B |
| Random Battle sets: each type profile stored once | 653 B |
| More repeated text shared (10 map texts, 6 menu prompts) | 255 B |

### What we could still cut

| Cut | Gain |
|---|---|
| Magikarp's 19 extra colour patterns (every Magikarp looks plain) | 17.1 KB |
| Front-sprite animations (Pokémon appear in battle and the Pokédex in a still pose) | 20.4 KB |
| Unown letters B–Z, ! and ? in battle (every Unown looks like A there) | 9.6 KB |
| Pokédex footprints (the small footprint box on each Pokédex page) | 5.2 KB |
| Six of the eight font choices in Options | ~3.9 KB |
| The 6 songs only the music player plays (cut once, then put back) | 5.1 KB |
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
