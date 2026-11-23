INCLUDE "data/pokemon/overworld_icon_pals.asm"

LoadOverworldMonIcon:
	; c = species
	ld a, [wCurIconSpecies]
	ld c, a
	; b = form
	ld a, [wCurIconForm]
	ld b, a
	; bc = extended index
	call GetCosmeticSpeciesAndFormIndex
	; hl = pointer table
	ld hl, MiniIconPointers
rept 7
	add hl, bc
endr
	; b = gfx bank
	ld a, [hli]
	ld b, a
	; skip mini and mask pointers
rept 4
	inc hl
endr
	; de = icon pointer
	ld a, [hli]
	ld d, [hl]
	ld e, a
	; c = tile count
	ld c, 8
	ret

LoadMini:
	; c = species
	ld a, [wCurIconSpecies]
	ld c, a
	; b = form
	ld a, [wCurIconForm]
	ld b, a
	; fallthrough
LoadMiniForSpeciesAndForm:
	; bc = extended index
	call GetCosmeticSpeciesAndFormIndex
	; hl = pointer table
	ld hl, MiniIconPointers
rept 7
	add hl, bc
endr
	; b = gfx bank
	ld a, [hli]
	ld b, a
	; de = mini pointer
	ld a, [hli]
	ld d, [hl]
	ld e, a
	; c = tile count
	ld c, 8
	ret

SetTradeMiniIconColor:
	push hl
	push de
	push bc
	push af

	ld a, [wTempIconSpecies]
	ld [wCurPartySpecies], a
	ld c, a
	ld a, [wCurIconForm]
	ld b, a
	call GetMiniColorsInBCDE
	ldh a, [rWBK]
	push af
	ld a, BANK(wOBPals1)
	ldh [rWBK], a
	ld hl, wOBPals1 palette 1 + 5
	ld a, d
	ld [hld], a
	ld a, e
	ld [hld], a
	ld a, b
	ld [hld], a
	ld [hl], c
	farcall ApplyOBPals
	pop af
	ldh [rWBK], a
	ld a, TRUE
	ldh [hCGBPalUpdate], a
	ld a, 1 ; OBJ 1
	; fallthrough
_SetMonColor:
	ld hl, wShadowOAMSprite00Attributes
_ShiftedSetMonColor:
	ld c, MINI_OAM_COUNT
	ld de, OBJ_SIZE
.loop
	ld [hl], a
	add hl, de
	dec c
	jr nz, .loop
	jmp PopAFBCDEHL

_GetFlyMonColor:
	ld a, MON_SPECIES
	call GetPartyParamLocationAndValue
	ld [wCurPartySpecies], a
	ld a, MON_SHINY
	call GetPartyParamLocationAndValue
	jmp GetMonIconPalette

SetFlyMonColor:
	push hl
	push de
	push bc
	push af
	call _GetFlyMonColor
	; Decode PAL_MON_*_* value into dark/light palette indices
	call DecodeMonIconPal
	ld de, wOBPals1 + 3 palettes
	ld hl, wPalFlags
	push hl
	set USE_DAYTIME_PAL_F, [hl]
	farcall CopySpritePalHandler
	pop hl
	res USE_DAYTIME_PAL_F, [hl]
	ld a, 3 ; OBJ 3
	jr _SetMonColor

SetOWFlyMonColor:
	push hl
	push de
	push bc
	push af
	call _GetFlyMonColor
	; Decode PAL_MON_*_* value into dark/light palette indices
	call DecodeMonIconPal
	; a = dark color index (wNeededPalIndex already set)
	ld b, a
	push bc
	ld b, 0
	ld a, [wUsedObjectPals]
	inc a
	jr z, .unset_bit_found
	dec a
	ld b, -1
.bit_check_loop
	inc b
	rrca
	jr c, .bit_check_loop
.unset_bit_found
	ld a, b
	pop bc
	ld c, a
	ld a, b
	ld b, 0
	ld hl, wLoadedObjPal0
	add hl, bc
	ld [hl], a
	push bc
	ld a, c
	ld bc, 1 palettes
	ld hl, wOBPals1
	rst AddNTimes
	ld d, h
	ld e, l
	farcall CopySpritePalHandler
	pop bc
	ldh a, [hUsedOAMIndex]
	cp (OAM_COUNT - NUM_FLYFROM_ANIM_OAMS - 1) * OBJ_SIZE
	; if we didn't have enough OAM slots, we need to use the last NUM_FLYFROM_ANIM_OAMS slots
	ld a, (OAM_COUNT - NUM_FLYFROM_ANIM_OAMS) * OBJ_SIZE
	jr nc, .got_oam_addr
	ldh a, [hUsedOAMIndex]
	; a = (OAM_COUNT - NUM_FLYFROM_ANIM_OAMS) * OBJ_SIZE + 1
	cpl
	add (OAM_COUNT - NUM_FLYFROM_ANIM_OAMS) * OBJ_SIZE + 1
.got_oam_addr
	ld hl, wShadowOAM + OAMA_FLAGS
	add l
	ld l, a
	ld a, c
	jmp _ShiftedSetMonColor

SetPartyMenuMonMiniColors:
	push hl
	push de
	push bc
	push af

	ld a, [wPartyCount]
	sub c
	ld [wCurPartyMon], a

	ld a, MON_ITEM
	call GetPartyParamLocationAndValue
	ld [wCurIconMonHasItemOrMail], a

	ld de, MON_IS_EGG - MON_ITEM
	add hl, de
	bit MON_IS_EGG_F, [hl]
	ld a, EGG
	jr nz, .got_species
	ld de, MON_SPECIES - MON_IS_EGG
	add hl, de
	ld a, [hl]
.got_species
	ld [wCurPartySpecies], a

	; hl = wShadowOAMSprite00Attributes + [wCurPartyMon] * MINI_OAM_COUNT * OAMA_FLAGS
	ld hl, wShadowOAMSprite00Attributes
	ld a, [wCurPartyMon]
	add a ; * 2
	add a ; * 4
	ld e, a
	add a ; * 8
	add a ; * 16
	add e ; + a * 4
	ld d, 0
	ld e, a
	add hl, de

	; mon minis use palette [wCurPartyMon]+2
	ld a, [wCurPartyMon]
	inc a
	inc a
	ld de, OBJ_SIZE
	ld [hl], a
	push hl
rept MINI_OAM_COUNT - 1
	add hl, de
	ld [hl], a
endr
	pop hl

	; item and mail icons use palette 0
	ld a, [wCurIconMonHasItemOrMail]
	and a
	jr z, .done
	xor a
	ld [hl], a
.done
	jmp PopAFBCDEHL

GetOverworldMonIconPalette::
	ld a, [wCurIcon]
	ld hl, wCurIconShiny
	call _GetMonIconPalette
	dec a ; remove +1 encoding so OBJECT_PAL_INDEX gets the raw nybble pair
	ret

GetMonIconPalette:
	ld a, [wCurPartySpecies]
	; fallthrough
_GetMonIconPalette:
	; c = species
	ld c, a
	; b = form
	inc hl ; Form is in the byte after Shiny
	ld a, [hld]
	and SPECIESFORM_MASK
	ld b, a

	; check shininess at hl
	ld a, [hl]
	and SHINY_MASK
	push af

	; bc = index
	call GetCosmeticSpeciesAndFormIndex
	; bc *= 2 for 2-byte table
	sla c
	rl b
	ld hl, OverworldMonIconColors
	add hl, bc

	pop af
	jr z, .not_shiny
	inc hl
.not_shiny
	ld a, [hl]
	ret

; Decode a PAL_MON_*_* value into wNeededPalIndex and wNeededMonPalLight.
; Input: a = PAL_MON_*_* value
; Output: a = dark color (PAL_OW_*), wNeededPalIndex = dark, wNeededMonPalLight = light (or NO_PAL_LOADED if same)
DecodeMonIconPal:
	dec a ; remove +1 encoding offset
	ld c, a
	and $f
	ld [wNeededPalIndex], a ; low nybble = dark color
	ld b, a ; save dark color
	ld a, c
	swap a
	and $f ; high nybble = light color
	cp b
	jr nz, .two_colors
	; Same nybbles: single-color palette
	ld a, NO_PAL_LOADED
; fallthrough
.two_colors
	ld [wNeededMonPalLight], a
.return_dark
	ld a, b
	ret

LoadPartyMenuMonMini:
	call SetPartyMenuMonMiniColors
	push hl
	push de
	push bc

	call InitPartyMenuMini
	call .SpawnItemSprite
	call SetPartyMonMiniAnimSpeed

	jmp PopBCDEHL

.SpawnItemSprite:
	ldh a, [hObjectStructIndexBuffer]
	ld hl, wPartyMon1Item
	call GetPartyLocation
	ld a, [hl]
	and a
	ret z
	ld d, a
	call ItemIsMail_a
	ld a, SPRITE_ANIM_FRAMESET_PARTY_MON_WITH_MAIL
	jr c, .got_frameset
	ld a, d
	cp FIRST_BERRY
	jr c, .not_berry
	cp FIRST_BERRY + NUM_BERRIES
	ld a, SPRITE_ANIM_FRAMESET_PARTY_MON_WITH_BERRY
	jr c, .got_frameset
.not_berry
	push bc
	ld hl, ItemAttributes + ITEMATTR_EFFECT
	ld c, d
	ld b, 0
	ld a, ITEMATTR_STRUCT_LENGTH
	rst AddNTimes
	ld a, BANK(ItemAttributes)
	call GetFarByte
	pop bc
	and a
	ld a, SPRITE_ANIM_FRAMESET_PARTY_MON_WITH_INERT_ITEM
	jr z, .got_frameset
	assert SPRITE_ANIM_FRAMESET_PARTY_MON_WITH_INERT_ITEM - 1 == SPRITE_ANIM_FRAMESET_PARTY_MON_WITH_ITEM
	dec a
.got_frameset
	ld hl, SPRITEANIMSTRUCT_FRAMESET_ID
	add hl, bc
	ld [hl], a
	ret

LoadNamingScreenMonMini:
	push hl
	push de
	push bc

	ld a, [wMonType]
	cp TEMPMON
	jr nz, .party_mon
	ld hl, wTempMonForm
	ld a, [hl]
	jr .got_mon
.party_mon
	ld a, MON_FORM ; aka MON_IS_EGG
	call GetPartyParamLocationAndValue
.got_mon
	depixel 4, 4, 4, 0
	jr _LoadMonMini

LoadMoveMenuMonMini:
	push hl
	push de
	push bc

	ld hl, wTempMonForm
	ld a, [hl]

	depixel 3, 4, 2, 4
	; fallthrough
_LoadMonMini:
	push de
	and SPECIESFORM_MASK
	ld [wCurIconForm], a
	bit MON_IS_EGG_F, [hl]
	ld a, [wTempIconSpecies]
	jr z, .got_species
	ld a, EGG
.got_species
	ld [wTempIconSpecies], a
	ld [wCurIcon], a
	ld [wCurPartySpecies], a

	; for move menu, mon minis use palette 1
	ld de, wOBPals1 palette 1 + 2

	ld a, [wMonType]
	cp TEMPMON
	jr z, .use_temp
	; not temp -> use party palette
	farcall LoadPartyMonPalette
	jr .palette_done
.use_temp
	farcall LoadTempMonPalette

.palette_done
	; a walking sprite uses its overworld colors
	ld a, [wCurPartySpecies]
	ld c, a
	ld a, [wCurIconForm]
	ld b, a
	ld a, [wMonType]
	cp TEMPMON
	ld a, [wTempMonShiny]
	jr z, .got_shiny
	ld a, MON_SHINY
	call GetPartyParamLocationAndValue
.got_shiny
	ld de, wOBPals1 palette 1 + 2
	call SetWalkingMiniPal
	ld a, 1
	ld hl, wShadowOAMSprite00Attributes
	ld de, OBJ_SIZE
rept MINI_OAM_COUNT - 1
	ld [hl], a
	add hl, de
endr
	ld [hl], a

	xor a
	call GetMiniGFX

	pop de
	ld a, SPRITE_ANIM_INDEX_PARTY_MON
	call _InitSpriteAnimStruct
	ld hl, SPRITEANIMSTRUCT_ANIM_SEQ_ID
	add hl, bc
	ld [hl], SPRITE_ANIM_SEQ_NULL

	jmp PopBCDEHL

InitPartyMenuMini:
	ld a, [wCurIconTile]
	push af
	ldh a, [hObjectStructIndexBuffer]
	assert wPartyMon1IsEgg == wPartyMon1Form
	ld hl, wPartyMon1IsEgg
	call GetPartyLocation
	ld a, [hl]
	bit MON_IS_EGG_F, a
	jr nz, .egg
	and SPECIESFORM_MASK
	ld [wCurIconForm], a
	ld de, MON_SPECIES - MON_FORM
	add hl, de
	ld a, [hl]
	jr .got_icon
.egg
	xor a
	ld [wCurIconForm], a
	dec a ; ld a, EGG
.got_icon
	ld [wCurIcon], a
	call GetMemMiniGFX
	ldh a, [hObjectStructIndexBuffer]
; y coord
	swap a ; a *= 16, assuming a < 16 since [hObjectStructIndexBuffer] < NUM_OBJECT_STRUCTS EQU 13
	add $1c
	ld d, a
; x coord
	ld e, $10
; type is partymon icon
	ld a, SPRITE_ANIM_INDEX_PARTY_MON
	call _InitSpriteAnimStruct
	pop af
	ld hl, SPRITEANIMSTRUCT_TILE_ID
	add hl, bc
	ld [hl], a
	ret

SetPartyMonMiniAnimSpeed:
	push bc
	call .getspeed
	pop bc
	ld hl, SPRITEANIMSTRUCT_DURATIONOFFSET
	add hl, bc
	ld [hl], a
	rlca
	rlca
	ld hl, SPRITEANIMSTRUCT_VAR2
	add hl, bc
	ld [hl], a
	ret

.getspeed
	ldh a, [hObjectStructIndexBuffer]
	ld hl, wPartyMon1IsEgg
	call GetPartyLocation
	bit MON_IS_EGG_F, [hl]
	jr nz, .egg
	ldh a, [hObjectStructIndexBuffer]
	ld hl, wPartyMon1HP
	call GetPartyLocation
	call GetHPPal
.gotindex
	ld e, d
	ld d, 0
	ld hl, .speeds
	add hl, de
	ld a, [hl]
	ret

.egg
	ldh a, [hObjectStructIndexBuffer]
	ld hl, wPartyMon1Happiness
	call GetPartyLocation
	ld a, [hl]
; same happiness thresholds as EggSummaryScreen
	ld d, 0
	cp $6
	jr c, .gotindex
	inc d ; 1
	cp $b
	jr c, .gotindex
	inc d ; 2
	jr .gotindex

.speeds
	db $00, $40, $80

GetFollowerWalkingSprite::
; Set wFollowerHasSprite, and wFollowerSpriteBank and wFollowerSpriteAddr to
; the walking sprite of the Pokemon in wCurIconSpecies and wCurIconForm.
; A walking_mon entry has a mask pointer of 0 and its icon is the sprite.
	call LoadOverworldMonIcon ; b:de = icon, hl = its pointer's high byte
	ld a, b
	ld [wFollowerSpriteBank], a
	ld a, e
	ld [wFollowerSpriteAddr], a
	ld a, d
	ld [wFollowerSpriteAddr + 1], a
	dec hl
	dec hl
	ld a, [hld]
	or [hl]
	ld a, FALSE
	jr nz, .done
	inc a
.done
	ld [wFollowerHasSprite], a
	ret

IsWalkingMon:
; Return z if species c, form b has a walking sprite (a walking_mon entry,
; with a mask pointer of 0). Clobbers a and hl.
	push bc
	call GetCosmeticSpeciesAndFormIndex
	ld hl, MiniIconPointers + 3
rept 7
	add hl, bc
endr
	pop bc
	ld a, [hli]
	or [hl]
	ret

GetMiniColorsInBCDE::
; Like GetMonPalInBCDE: bcde = the two colors for species c, form b's mini
; (a = shininess). A walking sprite is drawn for its overworld icon colors (the
; main colors of its light and dark overworld palettes, by day); other minis
; use the battle palette.
	push hl
	push af
	call IsWalkingMon
	jr z, .walking
	pop af
	pop hl
	farjp GetMonPalInBCDE

.walking
	pop af
	and SHINY_MASK
	push af
	push bc
	call GetCosmeticSpeciesAndFormIndex
	sla c
	rl b
	ld hl, OverworldMonIconColors
	add hl, bc
	pop bc
	pop af
	jr z, .normal
	inc hl
.normal
	ld a, [hl]
	dec a ; remove the +1 encoding: high nybble light, low nybble dark
	push af
	and $f
	ld c, 2
	call .GetOWPalColor
	pop af
	push de ; dark color
	ld b, a
	swap a
	and $f
	ld c, a ; light palette
	ld a, b
	and $f
	cp c
	ld a, c
	ld c, 2
	jr nz, .two_palettes
	dec c ; one palette: its colors 1 and 2
.two_palettes
	call .GetOWPalColor
	ld b, d
	ld c, e
	pop de
	pop hl
	ret

.GetOWPalColor:
; de = color c of overworld palette a, by day.
	push hl
	cp NUM_OW_TIME_OF_DAY_PALS
	jr c, .time_of_day
	sub NUM_OW_TIME_OF_DAY_PALS
	ld hl, SingleObjectPals
	jr .got_table
.time_of_day
	add DAY * NUM_OW_TIME_OF_DAY_PALS
	ld hl, MapObjectPals
.got_table
	push bc
	ld b, 0
	sla c
	add hl, bc
	ld c, a
rept 1 palettes
	add hl, bc
endr
	pop bc
	assert BANK(MapObjectPals) == BANK(SingleObjectPals)
	ld a, BANK(MapObjectPals)
	call GetFarWord
	ld d, h
	ld e, l
	pop hl
	ret

SetWalkingMiniPal:
; If species c, form b (a = shininess) has a walking sprite, write its mini
; colors to colors 1 and 2 at de (in wOBPals1's WRAM bank).
	push af
	call IsWalkingMon
	jr z, .walking
	pop af
	ret

.walking
	pop af
	push de
	call GetMiniColorsInBCDE
	pop hl
	ld a, BANK(wOBPals1)
	call StackCallInWRAMBankA
	ld a, c
	ld [hli], a
	ld a, b
	ld [hli], a
	ld a, e
	ld [hli], a
	ld [hl], d
	ret

SetPartyWalkingMiniPals::
; After InitPartyMenuOBPals: party members with walking sprites get their
; overworld colors.
	ld a, [wPartyCount]
	and a
	ret z
	ld hl, wPartyMon1
	ld de, wOBPals1 palette 2 + 2
.loop
	push af
	push de
	push hl
	; b = form
	ld bc, MON_FORM
	add hl, bc
	ld a, [hl]
	and SPECIESFORM_MASK
	ld b, a
	; c = species, or EGG
	assert MON_IS_EGG == MON_FORM
	bit MON_IS_EGG_F, [hl]
	pop hl
	ld c, EGG
	jr nz, .got_species
	assert MON_SPECIES == 0
	ld c, [hl]
.got_species
	; a = shininess
	push hl
	push bc
	ld bc, MON_SHINY
	add hl, bc
	ld a, [hl]
	pop bc
	call SetWalkingMiniPal
	pop hl
	ld bc, PARTYMON_STRUCT_LENGTH
	add hl, bc
	pop de
	push hl
	ld hl, 1 palettes
	add hl, de
	ld d, h
	ld e, l
	pop hl
	pop af
	dec a
	jr nz, .loop
	ret

MakeMiniMaskInWRA6:
	call RunFunctionInWRA6
MakeMiniMask:
; Turn c 2bpp tiles at wDecompressScratch into 1bpp masks in place: each row
; is solid from its leftmost to its rightmost drawn pixel. For walking
; sprites, which have no mask of their own.
	ld hl, wDecompressScratch
	ld d, h
	ld e, l
	ld a, c
	add a
	add a
	add a
	ld b, a ; rows
.row
	ld a, [hli]
	or [hl]
	inc hl
	ld [de], a ; the drawn pixels
	; a = every pixel right of the leftmost one
	ld c, a
	srl a
	or c
	ld c, a
	srl a
	srl a
	or c
	ld c, a
	swap a
	and $0f
	or c
	push af
	; a = every pixel left of the rightmost one
	ld a, [de]
	ld c, a
	add a
	or c
	ld c, a
	add a
	add a
	or c
	ld c, a
	swap a
	and $f0
	or c
	ld c, a
	pop af
	and c
	ld [de], a
	inc de
	dec b
	jr nz, .row
	ret

FlyFunction_GetMonIcon:
; Fly is in the overworld so it uses overworld icons
	push de
	ld a, MON_FORM
	call GetPartyParamLocationAndValue
	and SPECIESFORM_MASK
	ld [wCurIconForm], a
	ld de, MON_SPECIES - MON_FORM
	add hl, de
	ld a, [hl]
	ld [wTempIconSpecies], a
	ld [wCurIcon], a
	pop de
	ld a, e
; Load icon graphics into VRAM starting from tile a
	ld l, a ; no-optimize hl|bc|de = a * 16 (rept)
	ld h, 0
rept 4
	add hl, hl
endr
	ld de, vTiles0
	add hl, de
	push hl
	push hl
	call LoadOverworldMonIcon
	ld h, d
	ld l, e
	pop de
	ld c, 8
	call DecompressRequest2bpp
	pop hl
	ret

LoadTradeAnimationMonMiniAndMask:
	call SetTradeMiniIconColor
	ld a, [wTempIconSpecies]
	ld [wCurIcon], a
	ld a, [wCurIconSpecies]
	ld c, a
	ld a, [wCurIconForm]
	ld b, a
	call GetCosmeticSpeciesAndFormIndex

	ldh a, [rWBK]
	push af
	ld a, BANK(wDecompressScratch)
	ldh [rWBK], a

	ld hl, MiniIconPointers
rept 7
	add hl, bc
endr
	ld a, [hli]
	ld b, a
	ld de, vTiles0 tile $62
	ld a, [hli]
	push hl
	push bc
	ld h, [hl]
	ld l, a
	ld c, 8
	call DecompressRequest2bpp
	pop bc
	pop hl
	inc hl
	ld a, [hli]
	ld h, [hl]
	ld l, a
	or h
	jr nz, .decompress_mask
	; a walking sprite: make the mask from the frames still in the scratch
	ld c, 8
	call MakeMiniMask
	jr .got_mask
.decompress_mask
	call FarDecompressInB
.got_mask
	ld hl, vTiles0 tile $6a
	ld de, wDecompressScratch
	lb bc, BANK(wDecompressScratch), 8
	call Request1bpp

	pop af
	ldh [rWBK], a
	ret

GetMemMiniGFX:
	ld a, [wCurIconTile]
	; fallthrough
GetMiniGFX:
	call GetMini_a
	ld de, 8 tiles
	add hl, de
	ld de, HeldItemIcons
	lb bc, BANK(HeldItemIcons), NUM_HELD_ITEM_TYPES
	call Request2bpp
	ld a, [wCurIconTile]
	add 8 + NUM_HELD_ITEM_TYPES
	ld [wCurIconTile], a
	ret

GetMini_a:
; Load mini graphics into VRAM starting from tile a
	ld l, a ; no-optimize hl|bc|de = a * 16 (rept)
	ld h, 0
rept 4
	add hl, hl
endr
	ld de, vTiles0
	add hl, de
	push hl
	push hl
	call LoadMini
	ld h, d
	ld l, e
	pop de
	ld c, 8
	call DecompressRequest2bpp
	pop hl
	ret

GetStorageMini_a:
; Load frame 1 mini graphics into VRAM starting from tile a
	ld l, a ; no-optimize hl|bc|de = a * 16 (rept)
	ld h, 0
rept 4
	add hl, hl
endr
	ld de, vTiles0
	add hl, de
	; fallthrough
GetStorageMini:
	push hl
	push hl
	call LoadMini
	ld h, d
	ld l, e
	pop de
	push de
	ld c, 4
	push bc
	call FarDecompressWRA6InB
	pop bc
	pop hl
	ld de, wDecompressScratch
	farcall BillsPC_SafeRequest2bppInWRA6
	pop hl
	ret

GetStorageMask:
	push hl
	ld bc, 4 tiles
	add hl, bc
	push hl
	; c = species
	ld a, [wCurIconSpecies]
	ld c, a
	; b = form
	ld a, [wCurIconForm]
	ld b, a
	; bc = extended index
	call GetCosmeticSpeciesAndFormIndex
	; hl = pointer table
	ld hl, MiniIconPointers
rept 7
	add hl, bc
endr
	; b = gfx bank
	ld a, [hli]
	ld b, a
	; de = mini pointer
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	; hl = mask pointer
	ld a, [hli]
	ld h, [hl]
	ld l, a
	or h
	jr nz, .got_mask
	; a walking sprite: make the mask from its first frame
	ld h, d
	ld l, e
	call FarDecompressWRA6InB
	ld c, 4
	call MakeMiniMaskInWRA6
	jr .masked
.got_mask
	call FarDecompressWRA6InB
.masked
	pop hl
	ld c, 4
	ld de, wDecompressScratch
	farcall BillsPC_SafeRequest1bppInWRA6
	pop hl
	ret

FreezeMonIcons:
	ld hl, wSpriteAnimationStructs
	ld e, PARTY_LENGTH
	ld a, [wMenuCursorY]
	ld d, a
.loop
	ld a, [hl]
	and a
	jr z, .next
	cp d
	ld a, SPRITE_ANIM_SEQ_PARTY_MON_SWITCH
	jr z, .ok
	xor a ; SPRITE_ANIM_SEQ_NULL
.ok
	push hl
	ld c, l
	ld b, h
	ld hl, SPRITEANIMSTRUCT_ANIM_SEQ_ID
	add hl, bc
	ld [hl], a
	pop hl

.next
	ld bc, SPRITEANIMSTRUCT_LENGTH
	add hl, bc
	dec e
	jr nz, .loop
	ret

UnfreezeMonIcons:
	ld hl, wSpriteAnimationStructs
	ld e, PARTY_LENGTH
.loop
	ld a, [hl]
	and a
	jr z, .next
	push hl
	ld c, l
	ld b, h
	ld hl, SPRITEANIMSTRUCT_ANIM_SEQ_ID
	add hl, bc
	ld [hl], SPRITE_ANIM_SEQ_PARTY_MON
	pop hl
.next
	ld bc, SPRITEANIMSTRUCT_LENGTH
	add hl, bc
	dec e
	jr nz, .loop
	ret

HoldSwitchmonIcon:
	ld hl, wSpriteAnimationStructs
	ld e, PARTY_LENGTH
	ld a, [wSwitchMon]
	ld d, a
.loop
	ld a, [hl]
	and a
	jr z, .next
	cp d
	ld a, SPRITE_ANIM_SEQ_PARTY_MON_SELECTED
	jr nz, .join_back
	assert SPRITE_ANIM_SEQ_PARTY_MON_SELECTED - 1 == SPRITE_ANIM_SEQ_PARTY_MON_SWITCH
	dec a
.join_back
	push hl
	ld c, l
	ld b, h
	ld hl, SPRITEANIMSTRUCT_ANIM_SEQ_ID
	add hl, bc
	ld [hl], a
	pop hl
.next
	ld bc, SPRITEANIMSTRUCT_LENGTH
	add hl, bc
	dec e
	jr nz, .loop
	ret

HeldItemIcons:
	table_width TILE_SIZE
INCBIN "gfx/stats/held_items.2bpp"
	assert_table_length NUM_HELD_ITEM_TYPES
