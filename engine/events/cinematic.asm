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
; Tint toward TINT_* hScriptVar and back, three times (not with Flash &
; Shake off).
	call CinematicCalm
	ret nz
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

CinematicPan::
; The camera, which follows the player: hScriptVar = direction (DOWN, UP,
; LEFT, RIGHT) << 4 | steps (1-15), bit 7 for the way back. Going out, the
; player is hidden and the follower put away (it would follow the steps);
; the script waits while the view moves (scene_pan_back ends with
; CinematicPanEnd).
	ldh a, [hScriptVar]
	bit 7, a
	jr nz, .move
	push af
	ld hl, wPlayerStruct + OBJECT_FLAGS1
	set INVISIBLE_F, [hl]
	set NOCLIP_TILES_F, [hl] ; (the view goes over walls and people)
	set NOCLIP_OBJS_F, [hl]
	farcall RemoveFollower
	pop af
.move
	ld b, a
	and $0f
	ld c, a ; steps
	ld a, b
	swap a
	and %11 ; direction
	swap a ; * 16, a table each
	add 15
	sub c ; the last c steps of its table
	ld e, a
	ld d, 0
	ld hl, CinematicPanSteps
	add hl, de
	push hl
	ld c, PLAYER ; (FreezeAllOtherObjects keeps object c moving)
	farcall FreezeAllOtherObjects
	pop hl
	ld c, PLAYER
	ld b, BANK(CinematicPanSteps)
	call GetMovementData
	ret c
	ld a, SCRIPT_WAIT_MOVEMENT
	ld [wScriptMode], a
	ld hl, wScriptFlags
	res SCRIPT_RUNNING, [hl]
	ret

CinematicPanEnd::
; After the way back: the player seen again, the follower under them.
	ld hl, wPlayerStruct + OBJECT_FLAGS1
	res INVISIBLE_F, [hl]
	res NOCLIP_TILES_F, [hl]
	res NOCLIP_OBJS_F, [hl]
	farjp SpawnFollower

CinematicPanSteps:
; fifteen slow steps each way, in direction order (a pan takes the last n)
	assert DOWN == 0 && UP == 1 && LEFT == 2 && RIGHT == 3
for _, 15
	slow_step_down
endr
	step_end
for _, 15
	slow_step_up
endr
	step_end
for _, 15
	slow_step_left
endr
	step_end
for _, 15
	slow_step_right
endr
	step_end

CinematicFlash::
; hScriptVar white flashes (1 to 3), not with Flash & Shake off.
	call CinematicCalm
	ret nz
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

CinematicCalm:
; nz if the player turned Flash & Shake off.
	ld a, [wOptions3]
	and 1 << CALM_SCREEN_F
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
