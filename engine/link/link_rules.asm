LinkBattleRuleTable:
; Normalized level, minimum party size, maximum party size.
	table_width 3
	db LINK_BATTLE_FORCED_LEVEL, 1, PARTY_LENGTH ; Standard
	db LINK_BATTLE_FORCED_LEVEL, PARTY_LENGTH, PARTY_LENGTH ; Random
	db 30, 3, 3 ; Rising Star
	db LINK_BATTLE_FORCED_LEVEL, 1, PARTY_LENGTH ; Unrestricted
	assert_table_length NUM_LINK_BATTLE_RULES

LinkBattleGetRule:
	ld a, [wLinkBattleRules]
	ld hl, LinkBattleRuleTable
	ld bc, 3
	rst AddNTimes
	ret

CheckLocalLinkBattleParty::
	; Use the selected rule for both the team we send and the live battle.
	call LinkBattleGetRule
	ld a, [hl]
	ld [wLinkBattleLevel], a
	ld a, [wLinkBattleRules]
	cp LINK_RULE_RANDOM
	jr z, .ready ; this format will generate a replacement party after saving
	ld a, [wPartyCount]
	ld b, a
	ld c, 0 ; levels are normalized after registration
	ld hl, wPartyMons
	call CheckLinkBattleParty
	ld a, FALSE
	jr c, .result
.ready
	ld a, TRUE
.result
	ldh [hScriptVar], a
	ret

CheckReceivedLinkBattleParty::
	ld a, [wLinkBattleLevel]
	ld c, a
	ld a, [wOTPartyCount]
	ld b, a
	ld hl, wOTPartyMons
	; fallthrough

CheckLinkBattleParty:
; Party at hl, b members, c required level (zero before normalization).
; Carry if the party doesn't satisfy the format.
	push hl
	push bc
	call LinkBattleGetRule
	pop bc
	inc hl
	ld a, b
	cp [hl]
	jr c, .invalid_count
	inc hl
	ld a, [hl]
	cp b
	jr c, .invalid_count
	pop hl
	ld e, 0
.loop
	push hl
	push bc
	push de
	call CheckLinkBattleMon
	pop de
	pop bc
	pop hl
	ret c
	add e
	ld e, a
	push de
	ld de, PARTYMON_STRUCT_LENGTH
	add hl, de
	pop de
	dec b
	jr nz, .loop
	ld a, e
	and a
	ret nz
	scf
	ret

.invalid_count
	pop hl
	scf
	ret

CheckLinkBattleMon:
; a is 1 for a participating Pokémon, 0 for an allowed Egg. Carry rejects it.
	ld b, [hl] ; species
	ld de, MON_IS_EGG
	add hl, de
	assert MON_IS_EGG == MON_FORM
	bit MON_IS_EGG_F, [hl]
	jr nz, .egg
	ld a, c
	and a
	jr z, .check_species
	push hl
	ld de, MON_LEVEL - MON_IS_EGG
	add hl, de
	cp [hl]
	pop hl
	jr nz, .invalid
.check_species
	ld a, [wLinkBattleRules]
	cp LINK_RULE_RISING_STAR
	jr nz, .valid
	ld c, b ; species
	ld b, [hl] ; form
	ld hl, UberMons
	call GetSpeciesAndFormIndexFromHL
	ret c
.valid
	ld a, 1
	and a
	ret

.egg
	ld a, [wLinkBattleRules]
	cp LINK_RULE_RISING_STAR
	jr z, .invalid
	cp LINK_RULE_RANDOM
	jr z, .invalid
	xor a
	ret
.invalid
	scf
	ret
