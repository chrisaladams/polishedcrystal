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
	call CinematicOff
	jr CinematicEnd.palettes

CinematicEnd::
; Fade back to the palettes the scene began with, and restart the map's
; music if the scene changed it.
	ld hl, wCinematicFlags
	bit CINEMATIC_ACTIVE_F, [hl]
	ret z ; (no scene)
	call CinematicOff
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

CinematicOff:
; The scene flag off ([hl]); the map's own weather back if the scene changed
; it, and every shadow's colors.
	ld a, [hl]
	ld [hl], 0
	and CINEMATIC_WEATHER_MASK
	jr z, .weather_done
	farcall SetCurrentWeather
.weather_done
	jmp CinematicUnshadowAll

CinematicWeather::
; The scene's weather: OW_WEATHER_* hScriptVar (OW_WEATHER_NONE for a clear
; sky) until scene_end, which brings back the map's own. Only in a scene.
	ld hl, wCinematicFlags
	bit CINEMATIC_ACTIVE_F, [hl]
	ret z
	ldh a, [hScriptVar]
	cp NUM_OW_WEATHERS
	ret nc
	inc a
	assert CINEMATIC_WEATHER_SHIFT == 1
	add a
	ld b, a
	ld a, [hl]
	and ~CINEMATIC_WEATHER_MASK
	or b
	ld [hl], a
	farjp SetCurrentWeather

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
	farcall LoadWeatherPalNoApply ; (its slot as the weather now is)
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

CinematicShadow::
; Object hScriptVar (PLAYER, or a map object) as a black shadow, for a
; reveal; scene_unshadow or scene_end gives its colors back. Only in a scene,
; so a shadow can't outlast one. (Flashes, pulses and tints keep it.)
	ld a, [wCinematicFlags]
	bit CINEMATIC_ACTIVE_F, a
	ret z
	call CinematicObjectPal
	ret c
	ld a, [hl]
	cp OBJECT_PAL_SHADOW
	ret z ; (already)
	ld [hl], OBJECT_PAL_SHADOW
	ld b, a
	call CinematicShadowSlot
	ldh a, [rWBK]
	push af
	ld a, BANK(wCinematicShadowPals)
	ldh [rWBK], a
	ld a, b
	ld [de], a
	pop af
	ldh [rWBK], a
	farjp EnableDynPalUpdates

CinematicUnshadow::
; Object hScriptVar's own colors back.
	call CinematicObjectPal
	ret c
	ld a, [hl]
	cp OBJECT_PAL_SHADOW
	ret nz
	call CinematicShadowSlot
	call CinematicUnshadowAll.restore
	farjp EnableDynPalUpdates

CinematicObjectPal:
; hl = OBJECT_PAL_INDEX of object hScriptVar's struct; carry if it isn't out.
	ldh a, [hScriptVar]
	call CheckObjectVisibility
	ret c
	ld hl, OBJECT_PAL_INDEX
	add hl, bc
	and a
	ret

CinematicShadowSlot:
; de = its kept palette index (wCinematicShadowPals, by object struct).
	ldh a, [hObjectStructIndexBuffer]
	add LOW(wCinematicShadowPals)
	ld e, a
	adc HIGH(wCinematicShadowPals)
	sub e
	ld d, a
	ret

CinematicUnshadowAll:
; Every shadow's own palette index back (the scene's end recomputes sprite
; palettes after).
	ld hl, wObjectStructs + OBJECT_PAL_INDEX
	ld de, wCinematicShadowPals
	ld c, NUM_OBJECT_STRUCTS
.loop
	ld a, [hl]
	cp OBJECT_PAL_SHADOW
	call z, .restore
	push bc
	ld bc, OBJECT_LENGTH
	add hl, bc
	pop bc
	inc de
	dec c
	jr nz, .loop
	ret

.restore
; [hl] = [de], de in the shadow table's WRAM bank
	ldh a, [rWBK]
	push af
	ld a, BANK(wCinematicShadowPals)
	ldh [rWBK], a
	ld a, [de]
	ld b, a
	pop af
	ldh [rWBK], a
	ld [hl], b
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

CinematicEnter::
; A character comes on: object hScriptVar & %11111 appears just past the
; screen's edge toward hScriptVar >> 5 (DOWN, UP, LEFT, RIGHT), in line with
; the player, and walks up to stand next to them; the script waits. (The
; engine keeps objects a step past the screen, so it's drawn from its first
; step.)
	ldh a, [hScriptVar]
	and %11111
	ld b, a
	ldh a, [hScriptVar]
	swap a
	rrca
	and %11
	ld c, a
	push bc
	ld e, a
	ld d, 0
	ld hl, .offsets
	add hl, de
	add hl, de
	ld a, [wXCoord]
	add [hl]
	ld d, a
	inc hl
	ld a, [wYCoord]
	add [hl]
	ld e, a
	farcall CopyDECoordsToMapObject ; (b = the object)
	pop bc
	push bc
	ld a, b
	call _CopyObjectStruct
	ldh a, [hMapObjectIndexBuffer] ; its event flag reset, as appear does
	call GetMapObject
	ld hl, MAPOBJECT_EVENT_FLAG
	add hl, bc
	ld a, [hli]
	ld d, [hl]
	ld e, a
	and d
	inc a
	ld b, RESET_FLAG
	call nz, EventFlagAction
	pop bc
	ld e, c
	ld d, 0
	ld hl, .walks
	add hl, de
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	push hl
	ld c, b
	push bc
	farcall FreezeAllOtherObjects ; (c = the object)
	pop bc
	pop hl
	ld b, BANK(@)
	call GetMovementData
	ret c
	ld a, SCRIPT_WAIT_MOVEMENT
	ld [wScriptMode], a
	ld hl, wScriptFlags
	res SCRIPT_RUNNING, [hl]
	ret

.offsets
; x, y from the player's tile (map object coordinates are 4 more): the
; player is drawn 4 tiles from the left, top and bottom, 5 from the right
	db 4,      4 + 5 ; below
	db 4,      4 - 5 ; above
	db 4 - 5,  4     ; left
	db 4 + 6,  4     ; right

.walks
	dw .up4, .down4, .right4, .left5
.up4
	step_up
	step_up
	step_up
	step_up
	step_end
.down4
	step_down
	step_down
	step_down
	step_down
	step_end
.right4
	step_right
	step_right
	step_right
	step_right
	step_end
.left5
	step_left
	step_left
	step_left
	step_left
	step_left
	step_end

CinematicTitle::
; A title card. The script's next word points to one line of text in the
; script's bank (up to SCREEN_WIDTH - 2 characters, "@"-terminated): the map
; fades to black, the line shows centered in white on black for about two
; seconds (A or B sooner), and the map comes back as it was.
	call GetScriptWord ; (hl, and the script goes on after the word)
	push hl
	; (FadeToMenu, but to black: a white flash would come first)
	xor a
	assert NO_BG_MAP_TRANSFER == 0
	ldh [hBGMapMode], a
	call LoadStandardMenuHeader
	ld c, 10
	call FadeToBlack
	call ClearSprites
	call DisableSpriteUpdates
	call BackupSprites
	call LoadStandardFont
	call ClearTileMap
	pop de
	; centered: (SCREEN_WIDTH - length) / 2
	push de
	ld h, d
	ld l, e
	ld c, 0
.length
	ldh a, [hScriptBank]
	call GetFarByte
	cp '@'
	jr z, .measured
	inc hl
	inc c
	jr .length
.measured
	ld a, SCREEN_WIDTH
	sub c
	jr nc, .fits
	xor a
.fits
	srl a
	ld e, a
	ld d, 0
	hlcoord 0, SCREEN_HEIGHT / 2 - 1
	add hl, de
	pop de
	ldh a, [hScriptBank]
	call FarString
	hlcoord 0, 0, wAttrmap
	xor a
	ld bc, SCREEN_AREA
	rst ByteFill
	call ApplyAttrAndTilemapInVBlank
	; BG palette 0 (every tile's): black ground, white letters
	ldh a, [rWBK]
	push af
	ld a, BANK(wBGPals1)
	ldh [rWBK], a
	ld hl, wBGPals1
if !DEF(MONOCHROME)
	ld de, palred 0 + palgreen 0 + palblue 0
	ld bc, palred 31 + palgreen 31 + palblue 31
else
	ld de, PAL_MONOCHROME_BLACK
	ld bc, PAL_MONOCHROME_WHITE
endc
	ld a, e
	ld [hli], a
	ld a, d
	ld [hli], a
	ld a, e
	ld [hli], a
	ld a, d
	ld [hli], a
	ld a, e
	ld [hli], a
	ld a, d
	ld [hli], a
	ld a, c
	ld [hli], a
	ld [hl], b
	pop af
	ldh [rWBK], a
	ld c, 12
	call FadePalettes
	ld c, 120
.hold
	call DelayFrame
	call GetJoypad
	ldh a, [hJoyPressed]
	and PAD_A | PAD_B
	jr nz, .done
	dec c
	jr nz, .hold
.done
	jmp ExitAllMenus

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
