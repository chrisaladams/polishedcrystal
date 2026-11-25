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

MACRO scene_restore
; The map's own palettes back at once, the scene still on.
	callasm CinematicRestoreNow
ENDM
