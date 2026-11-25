; The Cable Club formats' rules, in one place (docs/rules-matrix.md). The same
; checks run on the team you bring to the desk and on the team you receive.

LinkBattleRuleTable:
; normalized level (0: everyone's own), fewest, most, LINKRULE_* flags
	table_width 4
	db LINK_BATTLE_FORCED_LEVEL, 1, PARTY_LENGTH, LINKRULE_ONE_LEGEND ; Standard
	db LINK_BATTLE_FORCED_LEVEL, PARTY_LENGTH, PARTY_LENGTH, LINKRULE_NO_EGGS ; Random
	db 30, 3, 3, LINKRULE_NO_EGGS | LINKRULE_NO_UBERS | LINKRULE_CLAUSES ; Rising Star
	db 0, 1, PARTY_LENGTH, 0 ; Unrestricted
	db LINK_BATTLE_FORCED_LEVEL, PARTY_LENGTH, PARTY_LENGTH, LINKRULE_NO_EGGS ; Championship (engine/link/world_link.asm)
	assert_table_length NUM_LINK_BATTLE_RULES

LinkBattleGetRule:
	ld a, [wLinkBattleRules]
	ld hl, LinkBattleRuleTable
	ld bc, 4
	rst AddNTimes
	ret

LinkBattleRuleFlags:
; a = the rules' LINKRULE_* flags. Keeps bc, de and hl.
	push hl
	push bc
	call LinkBattleGetRule
	ld bc, 3
	add hl, bc
	ld a, [hl]
	pop bc
	pop hl
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

CheckFriendBattleTeam::
; Carry if the team chosen for a Friend Battle (wOTParty, from CupSelectTeam)
; breaks the Cable Club rules it's under (wLinkBattleRules, from FriendDeskArm).
	ld a, [wOTPartyCount]
	ld b, a
	ld c, 0
	ld hl, wOTPartyMons
	jr CheckLinkBattleParty

CheckReceivedLinkBattleParty::
	ld a, [wLinkBattleLevel]
	ld c, a
	ld a, [wOTPartyCount]
	ld b, a
	ld hl, wOTPartyMons
	; fallthrough

CheckLinkBattleParty:
; Party at hl, b members, c required level (zero: any).
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
	push hl
	push bc
	ld de, 0 ; d = legendaries, e = Pokemon who battle
.loop
	push hl
	push bc
	push de
	call CheckLinkBattleMon
	pop de
	pop bc
	pop hl
	jr c, .invalid_pop
	srl a ; carry: it battles; a: 1 if legendary
	jr nc, .egg
	inc e
.egg
	add d
	ld d, a
	push de
	ld de, PARTYMON_STRUCT_LENGTH
	add hl, de
	pop de
	dec b
	jr nz, .loop
	pop bc
	pop hl
	ld a, e
	and a
	jr z, .invalid ; (nobody to battle)
	call LinkBattleRuleFlags
	bit LINKRULE_ONE_LEGEND_F, a
	jr z, .legends_ok
	ld a, d
	cp 2
	jr nc, .invalid
.legends_ok
	call LinkBattleRuleFlags
	bit LINKRULE_CLAUSES_F, a
	jr nz, CheckLinkBattleClauses
	and a
	ret

.invalid_count
	pop hl
	scf
	ret

.invalid_pop
	pop bc
	pop hl
.invalid
	scf
	ret

CheckLinkBattleMon:
; Party struct at hl, c required level (zero: any). Carry rejects it; else
; a = 0 for an allowed Egg, %01 for one who battles, %11 for a legendary.
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
	ld c, b ; species
	ld b, [hl] ; form
	call LinkBattleRuleFlags
	bit LINKRULE_NO_UBERS_F, a
	jr z, .legendary
	push bc
	ld hl, UberMons
	call GetSpeciesAndFormIndexFromHL
	pop bc
	ret c
.legendary
	ld hl, LegendaryMons ; (UberMons follows it: they count too)
	call GetSpeciesAndFormIndexFromHL
	ld a, %01
	ret nc
	ld a, %11
	and a
	ret

.egg
	call LinkBattleRuleFlags
	bit LINKRULE_NO_EGGS_F, a
	jr nz, .invalid
	xor a
	ret

.invalid
	scf
	ret

CheckLinkBattleClauses:
; Party at hl, b members. Carry if two are the same species (any form) or hold
; the same item, as the Battle Tower's Species and Item Clauses.
	ld a, b
	cp 2
	ccf
	ret nc ; (fewer than two to compare)
	push hl
	push bc
	call .Fields
	ld a, c
	ldh [hProduct], a
	ld a, d
	ldh [hProduct + 1], a
	ld a, e
	ldh [hProduct + 2], a
	dec b
.others
	ld de, PARTYMON_STRUCT_LENGTH
	add hl, de
	call .Fields
	ldh a, [hProduct]
	cp c
	jr nz, .item
	ldh a, [hProduct + 1]
	cp d
	jr z, .broken
.item
	ld a, e
	and a
	jr z, .next ; (any number may hold nothing)
	ldh a, [hProduct + 2]
	cp e
	jr z, .broken
.next
	dec b
	jr nz, .others
	pop bc
	pop hl
	ld de, PARTYMON_STRUCT_LENGTH
	add hl, de
	dec b
	jr CheckLinkBattleClauses

.broken
	pop bc
	pop hl
	scf
	ret

.Fields:
; c = species, d = its extended species bits, e = item, of the party struct
; at hl. Keeps hl and b.
	push hl
	ld c, [hl]
	ld de, MON_ITEM
	add hl, de
	ld e, [hl]
	assert MON_FORM > MON_ITEM
	ld a, MON_FORM - MON_ITEM
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, [hl]
	and EXTSPECIES_MASK
	ld d, a
	pop hl
	ret
