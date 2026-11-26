; Link Edition: story scene effects, for map scripts (engine/events/cinematic.asm).
; With the engine's own earthquake, showemote, cry, playsound, musicfadeout,
; applymovement and pause, a scene is written like this:
;
;	scene_begin
;	musicfadeout MUSIC_NONE, 16
;	scene_tint TINT_DARK
;	scene_silhouette
;	cry MEWTWO
;	scene_flash 2
;	scene_end            ; palettes and the map's music back as they were

MACRO scene_begin
; Keep the palettes to come back to; no weather lightning until scene_end.
	callasm CinematicBegin
ENDM

MACRO scene_end
; Fade back to the palettes the scene began with, and restart the map's music
; if the scene changed it.
	callasm CinematicEnd
ENDM

MACRO scene_end_keep_music
; As scene_end, but leave the music as the scene left it: for a scene that
; leads straight into a battle, whose music takes over.
	callasm CinematicEndKeepMusic
ENDM

MACRO scene_tint
; Blend everything on screen halfway toward TINT_* \1.
	setval \1
	callasm CinematicTint
ENDM

MACRO scene_pulse
; Tint toward TINT_* \1 and back, three times.
	setval \1
	callasm CinematicPulse
ENDM

MACRO scene_flash
; \1 white flashes (1-3; each is a few frames).
	setval \1
	callasm CinematicFlash
ENDM

MACRO scene_silhouette
; Every sprite black, for a reveal (scene_end or scene_restore undoes it).
	callasm SetBlackObjectPals
ENDM

MACRO scene_shadow
; Object \1 (PLAYER or a map object) as a black shadow, the others as they
; are; scene_unshadow or scene_end gives its colors back.
	setval \1
	callasm CinematicShadow
ENDM

MACRO scene_unshadow
; Object \1's own colors back: a reveal.
	setval \1
	callasm CinematicUnshadow
ENDM

MACRO scene_enter
; Object \1 comes on from past the screen's edge toward \2 (DOWN, UP, LEFT,
; RIGHT), in line with the player, and walks up beside them (appear, too).
	assert (\1) < 32 && (\2) < 4, "scene_enter OBJECT, DIRECTION"
	setval (\2) << 5 | (\1)
	callasm CinematicEnter
ENDM

MACRO scene_title
; A title card: the screen fades to black, the line at \1 (in this bank, up
; to 18 characters) shows centered in white for about two seconds (A or B
; sooner), and the map comes back.
	callasm CinematicTitle
	dw \1
ENDM

MACRO scene_weather
; The scene's weather (OW_WEATHER_RAIN, _SNOW, _THUNDERSTORM, _SANDSTORM,
; _CHERRY_BLOSSOMS, or _NONE for a clear sky) until scene_end.
	setval \1
	callasm CinematicWeather
ENDM

MACRO scene_restore
; The map's own palettes back at once, the scene still on.
	callasm CinematicRestoreNow
ENDM

MACRO scene_pan
; The camera moves \2 steps (1-15) toward \1 (DOWN, UP, LEFT, RIGHT), the
; player hidden, the follower put away; the script waits until it's there.
; End with scene_pan_back, given the same \1 and \2.
	assert 1 <= (\2) && (\2) <= 15, "scene_pan takes 1-15 steps"
	setval (\1) << 4 | (\2)
	callasm CinematicPan
ENDM

MACRO scene_pan_back
; The camera back to the player (\1 and \2 as scene_pan had them), who is
; shown again, the follower under them.
	assert 1 <= (\2) && (\2) <= 15, "scene_pan_back takes 1-15 steps"
	setval ((\1) ^ 1) << 4 | (\2) | $80
	callasm CinematicPan
	callasm CinematicPanEnd
ENDM
