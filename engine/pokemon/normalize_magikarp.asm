NormalizePartyMagikarp:
	ld hl, wPartyMon1Species
	ld a, [wPartyCount]
	and a
	ret z
	ld b, a
.loop
	push hl
	call NormalizeMagikarpForm
	pop hl
	ld de, PARTYMON_STRUCT_LENGTH
	add hl, de
	dec b
	jr nz, .loop
	ret

NormalizeMagikarpForm:
; HL = species byte of a decoded Pokémon. Preserve the form byte's other bits.
	ld a, [hl]
	cp MAGIKARP
	ret nz
	ld de, MON_FORM - MON_SPECIES
	add hl, de
	ld a, [hl]
	and EXTSPECIES_MASK
	ret nz
	ld a, [hl]
	and FORM_MASK
	cp 1 + NUM_MAGIKARP
	jr c, .lookup
	xor a
.lookup
	push hl
	push bc
	ld c, a
	ld b, 0
	ld hl, .Forms
	add hl, bc
	ld e, [hl]
	pop bc
	pop hl
	ld a, [hl]
	and ~FORM_MASK
	or e
	ld [hl], a
	ret

.Forms:
	db PLAIN_FORM ; legacy unset form
	db PLAIN_FORM ; old Plain
	db MAGIKARP_MASK1_FORM ; old Skelly
	db MAGIKARP_CALICO1_FORM ; old Calico1
	db MAGIKARP_CALICO1_FORM ; old Calico2
	db MAGIKARP_CALICO1_FORM ; old Calico3
	db MAGIKARP_ORCA_FORM ; old TwoTone
	db MAGIKARP_ORCA_FORM ; old Orca
	db MAGIKARP_CALICO1_FORM ; old Dapples
	db MAGIKARP_CALICO1_FORM ; old Tiger
	db MAGIKARP_ORCA_FORM ; old Zebra
	db MAGIKARP_ORCA_FORM ; old Stripe
	db PLAIN_FORM ; old Bubbles
	db MAGIKARP_CALICO1_FORM ; old Diamonds
	db MAGIKARP_CALICO1_FORM ; old Patches
	db MAGIKARP_MASK1_FORM ; old Forehead1
	db MAGIKARP_MASK1_FORM ; old Mask1
	db MAGIKARP_MASK1_FORM ; old Forehead2
	db MAGIKARP_MASK1_FORM ; old Mask2
	db PLAIN_FORM ; old Saucy
	db PLAIN_FORM ; old Raindrop
	assert @ - .Forms == NUM_MAGIKARP + 1
