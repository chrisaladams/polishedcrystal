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
- **Individual reveals** (one sprite in silhouette, L15): ready to build with
  the first scene that stages separate figures.
