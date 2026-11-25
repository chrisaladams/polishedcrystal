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
| `scene_end` | Fades back to the starting palettes and restarts the map's music if the scene changed it |

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
| Mewtwo Strikes Back | Cerulean Cave B1F | Silence, psychic pulses and purple light while Mewtwo speaks; cry and flash before the clones |
| The Power of One | Fire, Ice, Lightning Island roofs | Each beacon pulses in its guardian's color as it's tuned (red, blue, gold) |
| The Power of One | Shamouti shrine ruins | Blue light while Melody's song carries; a flash as Lugia answers |
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
| ROM: the library | 249 |
| ROM: the Mewtwo scene | 34 |
| ROM: the other campaigns' scenes | 291 |
| ROM: the sparkle emote (graphic and three table entries) | 57 |
| WRAM0: `wCinematicFlags` | 1 |
| WRAMX bank 5: `wCinematicSavedPals` | 128 |

Each use costs about 4 to 6 bytes of script.

## Not yet

- **Camera.** Gen 2's overworld scrolls with the player and has no camera to
  pan. Panning would need changes to the overworld's scrolling, which has a
  larger budget and more risk. Scenes move the player or other objects with
  `applymovement`, as the original game does.
- **More particles** (dust, water). The sparkle emote is in. Each new shape
  would cost about 50 to 64 bytes of graphics. A sparkle needs a character to
  appear over, so the beacons and Lugia keep their color pulses.
- **Reduced-flash or reduced-motion settings.** Flashes are capped at three
  short ones per command; a setting would need an options bit.
