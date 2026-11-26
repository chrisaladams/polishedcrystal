# Story scenes (Phase 4)

A small effects library for map scripts: `engine/events/cinematic.asm`, with
its script macros in `macros/scripts/cinematic.asm`. It adds only what the
engine lacked, a scene's begin and end with clean restoration, and palette
effects. It works alongside the engine's own commands: `earthquake` (screen
shake), `showemote` (`!`, `?`, happy, sad, heart, bolt, sleep), `cry`,
`playsound`, `musicfadeout` (fades and silence), `applymovement` and `pause`.

## Commands

| Macro | What it does |
|---|---|
| `scene_begin` | Keeps the palettes to come back to; no weather lightning until `scene_end` |
| `scene_tint TINT_*` | Fades every color halfway to the tint in 8 frames. The text box's palette is left alone, so text stays readable. Two tints compound: two `TINT_DARK` go three quarters to black |
| `scene_pulse TINT_*` | Tints and comes back, three times |
| `scene_flash n` | `n` white flashes (1–3), each back to the scene's palettes |
| `scene_silhouette` | Every sprite black (`SetBlackObjectPals`) |
| `scene_shadow OBJ` | One character (`PLAYER` or a map object) a black shadow, everyone else as they are. Only inside a scene; tints, pulses, flashes and `scene_restore` keep it |
| `scene_unshadow OBJ` | That character's own colors back: the reveal (`scene_end` gives every shadow its colors back too) |
| `scene_enter OBJ, DIR` | A character comes on: it appears just past the screen's edge toward `DIR` (`DOWN`, `UP`, `LEFT`, `RIGHT`), in line with the player, and walks up to stand beside them (4 steps, 5 from the right); the script waits. It also does what `appear` does |
| `scene_title .Line` | A title card: the screen fades to black, the line (one line in the script's bank, up to 18 characters, `@`-terminated) shows centered in white for about two seconds (A or B sooner), and the map comes back |
| `scene_weather OW_WEATHER_*` | The scene's weather (`RAIN`, `SNOW`, `THUNDERSTORM`, `SANDSTORM`, `CHERRY_BLOSSOMS`, or `NONE` for a clear sky) until `scene_end`, which brings back the map's own. Only inside a scene; no lightning flashes during one |
| `scene_restore` | Back to the scene's starting palettes quickly, the scene still on |
| `scene_pan DIR, n` | The camera moves `n` steps (1–15) toward `DOWN`, `UP`, `LEFT` or `RIGHT`: the player is hidden and walked there (the view follows the player), through walls and people, the follower put away; the script waits until it's there |
| `scene_pan_back DIR, n` | Back the same way (give it the same `DIR` and `n`): the player shown again on their tile, walls and people solid again, the follower back under them |
| `scene_end` | Fades back to the starting palettes and restarts the map's music if the scene changed it |
| `scene_end_keep_music` | The same, but leaves the music as the scene left it, for a scene that leads straight into a battle |

**Flash & Shake** (Options, Link Edition): with it off, `scene_flash` and
`scene_pulse` do nothing, weather lightning is only its thunder, and
`earthquake` doesn't shake the screen (its pause still happens). Tints, fades
and silhouettes are steady changes and stay. Battle animations have their own
option (Battle Effects). The setting is `CALM_SCREEN_F` in `wOptions3`.

Tints: `TINT_DARK`, `TINT_GREEN`, `TINT_RED`, `TINT_BLUE`, `TINT_PURPLE`,
`TINT_GOLD`, `TINT_WHITE`.

Sparkles are emotes, so `showemote` draws them over a character:
`EMOTE_SPARKLE` (gold), `EMOTE_SPARKLE_GREEN` and `EMOTE_SPARKLE_PURPLE`.
They share one 16×16 graphic (`gfx/emotes/sparkle.png`, a four-point star
with two glints and no speech bubble), each with its own emote palette.

An example, the first scene to use it (the Mewtwo clones, `maps/CeruleanCaveB1F.asm`):

```
	scene_begin
	musicfadeout MUSIC_NONE, 8
	pause 20
	scene_pulse TINT_PURPLE
	scene_tint TINT_PURPLE
	showtext .ClonesText
	cry MEWTWO
	scene_flash 1
	scene_end
```

## Scenes using it

| Campaign | Where | Scene |
|---|---|---|
| Mewtwo Strikes Back | Pokémon Mansion B1F | The lab's lights flicker and dim while you read the flight log; a distant cry and a psychic pulse answer |
| Mewtwo Strikes Back | Cerulean Cave B1F | Silence, psychic pulses and purple light while Mewtwo speaks; at "Look.", a rumble and every sprite a black shadow, rising from the pool; cry and flash, the silence lasting into the clone battle |
| The Power of One | Fire, Ice, Lightning Island roofs | Each beacon pulses in its guardian's color as it's tuned (red, blue, gold) |
| The Power of One | Shamouti shrine ruins | A storm gathers while Lawrence speaks: darkness, thunder and a flash, his theme playing on into the battle. Later, blue light while Melody's song carries, and a flash as Lugia answers |
| Spell of the Unown | Ruins of Alph Research Center | Before Molly's first battle, the Unown's power gathers around her: purple light, a purple sparkle, a rumble |
| Spell of the Unown | Ruins of Alph inner chamber | The Entei illusion in a dream's purple light, a purple sparkle as it breaks into letters |
| Voice of the Forest | Ilex Forest | The forest darkens around the Marauder. After he's beaten: a flash as he vanishes, the forest dim with Celebi's hurt glow, green pulses from the shrine until the daylight returns, a green sparkle as it heals, another and two flashes as it takes Sammy home |
| Orange League | Warm Beach, Rocky Beach, Beautiful Beach, Valencia, Shamouti house | A blue surf pulse for Cissy; a cold white haze for Danny; each of Rudy's rounds opens in its type's color (green, red, blue); hearts over Luana and you, partners; Dragonite's roar, a rumble and a flash for Drake; gold light and a sparkle for the trophy |
| Pallet Invitational | Pallet Town | Pikachu's spark before Ash's battle; gold light and a sparkle while Tracey sketches the winners |

The Voice of the Forest scenes used to call `BlindingFlash` for their flashes.
That routine is the Flash field move: it marks the map as lit by Flash.
They use `scene_flash` now. Upstream's own Cinnabar Lab scene still calls it.

## How it restores

`scene_begin` copies all 16 target palettes (`wBGPals1`, `wOBPals1`) to
`wCinematicSavedPals`, 128 bytes in WRAM bank 5. The effects change those
target palettes and fade the screen to them (`FadePalettes`). `scene_end`
copies the saved palettes back, so the map's palettes return exactly,
whatever its time of day or special palettes. Sprite palettes are then
recomputed for any sprite that appeared during the scene, and the screen fades
to them. The map's music restarts only if a different song is playing. Weather
lightning checks the scene flag (`wCinematicFlags`), so it can't strike mid-scene.

Nothing in the library draws a random number, so a scene can't change a battle
or a link session. A blend is `(x & t) + ((x ^ t) & %0111101111011110) / 2`
for each color, so no channel spills into the next. In the monochrome build,
tints and pulses do nothing (it has four shades, not colors), and flashes
still work.

`utils/anime_events/test_cinematic.py` checks each tint's exact colors,
compounding, the text palette left alone, the return after flashes and
pulses, exact restoration at `scene_end`, the music rule, lightning during
and after a scene, and that no random number is drawn.

## Cost

| | Bytes |
|---|---:|
| ROM: the library | 255 |
| ROM: the sparkle emote (graphic and three table entries) | 57 |
| ROM: every scene's script, all campaigns | 429 |
| WRAM0: `wCinematicFlags` | 1 |
| WRAMX bank 5: `wCinematicSavedPals` | 128 |

Each use costs about 4 to 6 bytes of script.

## Shadows

`scene_silhouette` blacks out every sprite at once (it overwrites the shown
sprite palettes). `scene_shadow` is for one figure: it marks the object's
palette index `OBJECT_PAL_SHADOW` (`$ff`, never a real index or Pokémon
nybble pair, which use nybbles 0–13), and the dynamic sprite palettes give any
object so marked the black `PAL_OW_SILHOUETTE`, in a slot of its own, so
people who shared its palette keep their colors. Its own index is kept in
`wCinematicShadowPals` (13 bytes, WRAM bank 5, by object struct), and
`scene_unshadow` and `scene_end` put it back. A shadow is in the object's
palette index, so it lasts through tints, pulses and flashes; an object that
leaves the screen and comes back loses it. About 120 bytes and one palette.

## Entrances

The player is drawn 4 tiles from the screen's left, top and bottom edges and
5 from its right, and the engine keeps objects one step past the screen, so a
character placed one tile past an edge is drawn from its first step in.
`scene_enter` places the object there with the player's coordinates (scenes
often start from a coordinate event, wherever the player crossed it), resets
its event flag as `appear` does, and walks it in with `applymovement`'s own
routine. The side it comes from has to be inside the map: in a room smaller
than the screen, bring it from a side with space, or place it with
`moveobject`, `appear` and `applymovement` as the original scenes do. About
110 bytes.

## Title cards

`scene_title` leaves the map the way menus do (the tilemap and sprites kept,
`ExitAllMenus` to come back), but fades to black instead of white. The card
is the standard font on a blank screen, every tile in BG palette 0, set to a
black ground and white letters, and faded in. The pointer is the word after
the `callasm`; `GetScriptWord` reads it, so the script goes on after it. The
map's palettes are rebuilt on the way back, so put a card before a scene's
tints, or `scene_begin` after it. About 150 bytes.

```
	scene_title .Title
	scene_begin
	...
.Title:
	db "THE POWER OF ONE@"
```

## Weather

The scene's weather is kept in `wCinematicFlags` (bits 1–3, the weather plus
one, so a clear sky can be asked for too). `SetCurrentWeather` asks the story
weather first (`ShamoutiStoryStorm`), and that now looks at a scene's weather
before the beacons' storm; `scene_weather` calls it, and the engine moves
between weathers as it always does (a short change-over unless rain and storm
swap). `scene_end` clears the flags and calls it again for the map's own
weather. Every return to the kept palettes (`scene_restore`, pulses, flashes,
the end) reloads the weather's sprite palette as the weather now is, since
the kept copy is from before it changed: that also fixes the Shamouti shrine,
whose storm starts mid-scene. About 70 bytes.

Other changes to the scene's surroundings use the engine's own commands:
`changeblock` and `refreshmap` change map blocks (a door, crystals, rubble),
and `appear` and `disappear` show and hide objects.

## The camera

Gen 2's overworld always scrolls with the player, so `scene_pan` moves the
camera the way the original game's endings do (Navel Rock's pan up): the
player is hidden and walked along, through walls and people (the no-clip
flags), and the view follows. `scene_pan_back` walks back and shows the player
on their own tile. The follower would replay those steps, so it's put away for
the pan and put back under the player after. Keep a pan inside the map: the
view can show the border blocks, but a walk off the map's edge is not tested.
Fifteen steps each way at most (`CinematicPanSteps`). About 140 bytes.
`test_cinematic.py` runs one as a real script.

## Not yet

- **More particles** (dust, water). The sparkle emote is in. Each new shape
  would cost about 50 to 64 bytes of graphics. A sparkle needs a character to
  appear over, so the beacons and Lugia keep their color pulses.
