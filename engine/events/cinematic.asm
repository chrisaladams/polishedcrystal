; Link Edition: story scene effects, for map scripts through the macros in
; macros/scripts/cinematic.asm (docs/cinematics.md). The engine's own
; earthquake, showemote, cry, playsound, musicfadeout, applymovement and
; pause do the rest. Nothing here uses a random number, so scenes can't
; change battle or link results.

CinematicBegin::
; Keep the palettes to come back to. While a scene is on, weather lightning
; doesn't strike (Lightning checks wCinematicFlags). A scene_begin inside a
; scene changes nothing: the palettes kept are the first scene_begin's.
; (A script that ends with a scene still on ends it: Script_end; a new map
; drops it: RunMapSetupScript.)
	ld a, [wCinematicFlags]
	bit CINEMATIC_ACTIVE_F, a
	ret nz
	ld a, 1 << CINEMATIC_ACTIVE_F
	ld [wCinematicFlags], a
	ld hl, wBGPals1
	ld de, wCinematicSavedPals
	ld bc, 16 palettes
	jmp FarCopyColorWRAM

CinematicEndKeepMusic::
; As CinematicEnd, but the music is left as it is (a battle comes next).
	ld hl, wCinematicFlags
	bit CINEMATIC_ACTIVE_F, [hl]
	ret z
	ld [hl], 0
	jr CinematicEnd.palettes

CinematicEnd::
; Fade back to the palettes the scene began with, and restart the map's
; music if the scene changed it.
	ld hl, wCinematicFlags
	bit CINEMATIC_ACTIVE_F, [hl]
	ret z ; (no scene)
	ld [hl], 0
	ld a, [wMusicIDHi]
	and a
	jr nz, .music
	ld a, [wMapMusic]
	ld b, a
	ld a, [wMusicIDLo]
	cp b
	jr z, .palettes
.music
	call RestartMapMusic
.palettes
	ld c, 12
	jr CinematicFadeBack

CinematicRestoreNow::
; The scene's starting palettes back, quickly, the scene still on.
	ld c, 4
CinematicFadeBack:
; Fade to the saved palettes in c frames; sprites that appeared since get
; their own palettes again.
	push bc
	ld hl, wCinematicSavedPals
	ld de, wBGPals1
	ld bc, 16 palettes
	call FarCopyColorWRAM
	farcall ClearSavedObjPals
	farcall EnableDynPalUpdatesNoApply ; (into wOBPals1, for the fade)
	pop bc
	jmp FadePalettes

CinematicTint::
; Blend the screen's colors halfway toward TINT_* hScriptVar (the text box's
; palette aside, so text stays readable), fading there in 8 frames.
	call CinematicTintPals
	ld c, 8
	jmp FadePalettes

CinematicPulse::
; Tint toward TINT_* hScriptVar and back, three times.
	ld b, 3
.pulse
	push bc
	call CinematicTintPals
	ld c, 6
	call FadePalettes
	ld c, 6
	call CinematicFadeBack
	pop bc
	dec b
	jr nz, .pulse
	ret

CinematicFlash::
; hScriptVar white flashes (1 to 3).
	ldh a, [hScriptVar]
	and a
	ret z
	cp 4
	jr c, .count
	ld a, 3
.count
	ld b, a
.flash
	push bc
	call SetWhitePals
	farcall ApplyPals
	ld a, 1
	ldh [hCGBPalUpdate], a
	ld c, 3
	call DelayFrames
	ld c, 6
	call CinematicFadeBack
	pop bc
	dec b
	jr nz, .flash
	ret

CinematicTintPals:
; wBGPals1 (but the text box's) and wOBPals1 halfway toward TINT_* hScriptVar.
if DEF(MONOCHROME)
	ret ; (four shades: no colors to blend)
else
	ldh a, [hScriptVar]
	cp NUM_TINTS
	ret nc
	add a
	ld hl, CinematicTintColors
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, [hli]
	ld c, a
	ld b, [hl] ; the color to blend toward
	ldh a, [rWBK]
	push af
	ld a, BANK(wBGPals1)
	ldh [rWBK], a
	ld hl, wBGPals1
	ld d, 7 palettes / 2 ; (colors: the BG palettes but the text box's)
	call .Blend
	ld hl, wOBPals1
	ld d, 8 palettes / 2
	call .Blend
	pop af
	ldh [rWBK], a
	ret

.Blend:
; d colors at hl, each halfway to bc: per channel (x + t) / 2, worked out as
; (x & t) + ((x ^ t) & %0111101111011110) / 2, so no channel spills into the
; next. hProduct holds (x & t) and the count.
	ld a, d
	ldh [hProduct + 2], a
.color
	ld a, [hli]
	and c
	ldh [hProduct], a
	ld a, [hld]
	and b
	ldh [hProduct + 1], a
	ld a, [hli]
	xor c
	and LOW(%0111101111011110)
	ld e, a
	ld a, [hl]
	xor b
	and HIGH(%0111101111011110)
	srl a
	rr e
	ld d, a
	ldh a, [hProduct]
	add e
	ld e, a
	ldh a, [hProduct + 1]
	adc d
	ld [hld], a
	ld a, e
	ld [hli], a
	inc hl
	ldh a, [hProduct + 2]
	dec a
	ldh [hProduct + 2], a
	jr nz, .color
	ret

CinematicTintColors:
	table_width 2
	RGB  0,  0,  0 ; TINT_DARK
	RGB  4, 31,  6 ; TINT_GREEN
	RGB 31,  2,  2 ; TINT_RED
	RGB  2,  8, 31 ; TINT_BLUE
	RGB 20,  2, 31 ; TINT_PURPLE
	RGB 31, 24,  4 ; TINT_GOLD
	RGB 31, 31, 31 ; TINT_WHITE
	assert_table_length NUM_TINTS
endc
