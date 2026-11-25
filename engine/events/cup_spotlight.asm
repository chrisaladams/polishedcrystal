GetCupSpotlight::
	; Rotate with the world clock. Skip cups whose story gates are closed.
	assert WORLD_CLOCK_DAYS % NUM_CUPS == 0
	ld a, [wRTCDayLo]
.day
	sub NUM_CUPS
	jr nc, .day
	add NUM_CUPS
	ld c, a
.check
	ld a, c
	cp CUP_WORLD
	jr z, .post_red
	cp CUP_WHIRL
	jr z, .post_red
	cp CUP_DRAGON
	ret nz
	flagcheck wJohtoBadges, (ENGINE_RISINGBADGE - ENGINE_BADGES)
	jr .gate
.post_red
	eventflagcheck EVENT_GOT_MYSTICTICKET_FROM_RED
.gate
	ld a, c
	ret nz
	inc c
	cp NUM_CUPS - 1
	jr nz, .check
	ld a, CUP_RISING_STAR
	ret

BufferTodaysCupSpotlight::
	call GetCupSpotlight
BufferCupSpotlight::
	add a
	add a
	ld e, a
	ld d, 0
	ld hl, CupSpotlightNames
	add hl, de
	ld a, [hli]
	ld b, [hl]
	inc hl
	push hl
	ld l, a
	ld h, b
	ld de, wStringBuffer3
	call CopyCupDisplayName
	pop hl
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld de, wStringBuffer4
	jmp CopyCupDisplayName

CupSpotlightNames:
	table_width 4
	dw .Rising, .Park
	dw .Whirl, .Olivine
	dw .Kimono, .Ecruteak
	dw .Dragon, .Blackthorn
	dw .Rental, .Goldenrod
	dw .World, .Indigo
	assert_table_length NUM_CUPS
.Rising:     db "Rising Star Cup@"
.Park:       db "National Park Gate@"
.Whirl:      db "Whirl Cup@"
.Olivine:    db "Olivine Port@"
.Kimono:     db "Kimono Cup@"
.Ecruteak:   db "Dance Theatre@"
.Dragon:     db "Dragon Masters Cup@"
.Blackthorn: db "Blackthorn City@"
.Rental:     db "Rental Cup@"
.Goldenrod:  db "Goldenrod Store 6F@"
.World:      db "World Championship@"
.Indigo:     db "Indigo Plateau@"
