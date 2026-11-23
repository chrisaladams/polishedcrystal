WhirlCupCheckParty::
; Link Edition: the Whirl Cup (maps/OlivinePort.asm) is for Water-type
; Pokemon. hScriptVar = TRUE if every Pokemon in the party (eggs aside) is
; Water-type.
	ld a, [wPartyCount]
	and a
	jr z, .no
	ld b, a
	ld hl, wPartyMon1
.loop
	push bc
	push hl
	ld bc, MON_IS_EGG
	add hl, bc
	bit MON_IS_EGG_F, [hl]
	jr nz, .next
	assert MON_FORM == MON_IS_EGG
	ld a, [hl]
	and SPECIESFORM_MASK
	ld [wCurForm], a
	pop hl
	push hl
	ld a, [hl] ; MON_SPECIES
	ld [wCurSpecies], a
	call GetBaseData
	ld a, [wBaseType1]
	cp WATER
	jr z, .next
	ld a, [wBaseType2]
	cp WATER
	jr nz, .not_water
.next
	pop hl
	ld bc, PARTYMON_STRUCT_LENGTH
	add hl, bc
	pop bc
	dec b
	jr nz, .loop
	ld a, TRUE
	ldh [hScriptVar], a
	ret

.not_water
	pop hl
	pop bc
.no
	xor a
	ldh [hScriptVar], a
	ret
