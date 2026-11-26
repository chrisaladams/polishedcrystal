; Link Edition: generated teams for the regional cups (engine/events/cups.asm),
; from the Random Battle sets (data/link/random_battle_sets.asm, in this
; section). This leaves the Random Battle link format's own code as it is.

CupMakeTeam::
; Fill wOTParty with b level 50 Pokemon from the Random Battle sets, all
; different species, as LinkRandomBattle_MakeTeam makes them (perfect DVs,
; neutral nature). With c = a type, every one has it; with c = CUPTYPE_ANY,
; they have a decent type spread, as in a Random Battle.
	ld a, b
	ld [wCupMakeCount], a
	ld a, c
	ld [wCupFoeType], a
	xor a
	ld [wRandomStartOvers], a
	ld [wRandomSeqIndex], a
	ld [wRandomSeqIndex + 1], a
	; a type with fewer species in the sets than asked for (Dragon in the
	; faithful build has three): the team is every one of them, taken in
	; order at once (random picks would hunt for them for seconds, and the
	; relaxed pass would add one that isn't of the type)
	ld a, [wCupFoeType]
	cp CUPTYPE_ANY
	jr z, .start_over
	call .CountOfType
	and a
	jr z, .start_over ; (none at all: as before)
	ld hl, wCupMakeCount
	cp [hl]
	jr nc, .start_over
	ld [hl], a
	ld a, RANDOM_MAX_START_OVERS
	ld [wRandomStartOvers], a
.start_over
	xor a
	ld [wOTPartyCount], a
	ld [wRandomTries], a
	ld hl, wRandomTypeCounts
	ld bc, NUM_RANDOM_TYPES * 2
	rst ByteFill
.next
	ld a, [wRandomStartOvers]
	cp RANDOM_MAX_START_OVERS
	jr c, .random_pick
	; past the limit: the next set in order (RandomNextInOrder), the type
	; rules kept on the first pass only; out of sets, the team is as full as
	; it can be (with today's sets every type fills six: test_team_generation)
	call RandomNextInOrder
	ret c
	ld a, b
	and a
	jr z, .picked
	push hl
	ld a, [hli]
	ld c, a
	ld b, [hl]
	pop hl
	call .HaveSpecies
	jr z, .next
	jr .add

.random_pick
	; a set: 10 random bits, tried again until below the number of sets
	call Random
	and %11
	ld h, a
	call Random
	ld l, a
	ld de, -NUM_RANDOM_BATTLE_SETS
	push hl
	add hl, de
	pop hl
	jr c, .next
	ld d, h
	ld e, l
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, de
	assert RANDOM_SET_LENGTH == 9
	ld de, RandomBattleSets
	add hl, de
.picked
	; one of each species
	ld a, [hli]
	ld c, a
	ld a, [hld]
	ld b, a
	call .HaveSpecies
	jmp z, .reject
	ld a, [wCupFoeType]
	cp CUPTYPE_ANY
	jr z, .any_type
	; of the type
	push hl
	call LinkRandomBattle_MakeTeam.GetProfile
	ld a, [wCupFoeType]
	cp [hl]
	inc hl
	jr z, .has_type
	cp [hl]
.has_type
	pop hl
	jmp nz, .reject
	jr .add

.any_type
	call LinkRandomBattle_MakeTeam.TypeSpreadOK
	jmp c, .reject
	call LinkRandomBattle_MakeTeam.CountTypes
.add
	push hl
	ld a, [hli]
	ld [wCurPartySpecies], a
	ld a, [hl]
	ld [wCurForm], a
	ld a, [wCupLevel]
	and a
	jr nz, .level
	ld a, LINK_BATTLE_FORCED_LEVEL
.level
	ld [wCurPartyLevel], a
	ld a, OTPARTYMON
	ld [wMonType], a
	; Generate fresh stats with zero EVs. Trainer defaults would otherwise
	; give rentals the last opponent's EVs and gender.
	ld a, [wBattleMode]
	push af
	ld a, [wBattleType]
	push af
	ld a, WILD_BATTLE
	ld [wBattleMode], a
	ld a, BATTLETYPE_NORMAL
	ld [wBattleType], a
	farcall TryAddMonToParty
	pop af
	ld [wBattleType], a
	pop af
	ld [wBattleMode], a
	ld a, [wOTPartyCount]
	dec a
	ld hl, wOTPartyMon1
	call GetPartyLocation
	ld d, h
	ld e, l
	pop hl

	; the set: moves, item, ability
	inc hl
	inc hl
	push de
	push hl
	ld hl, MON_MOVES
	add hl, de
	ld d, h
	ld e, l
	pop hl
	ld bc, NUM_MOVES
	rst CopyBytes
	pop de
	ld a, [hli]
	push hl
	ld hl, MON_ITEM
	add hl, de
	ld [hl], a
	pop hl
	ld b, [hl] ; ability slot
	ld hl, MON_PERSONALITY
	add hl, de
	ld a, [hl]
	and SHINY_MASK ; keep shininess; neutral nature (HARDY is 0)
	or b
	ld [hl], a
	; perfect DVs
	ld hl, MON_DVS
	add hl, de
	ld a, $ff
	ld [hli], a
	ld [hli], a
	ld [hl], a
	; PP for the moves
	push de
	ld hl, MON_PP
	add hl, de
	push hl
	ld hl, MON_MOVES
	add hl, de
	pop de
	farcall FillPP
	pop de
	; stats for the DVs (the base data is still this species'), at full HP
	push de
	ld hl, MON_MAXHP
	add hl, de
	push hl
	ld hl, MON_EVS - 1
	add hl, de
	pop de
	ld b, TRUE
	push de
	farcall CalcPkmnStats
	pop hl ; max HP
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop de
	ld hl, MON_HP
	add hl, de
	ld a, b
	ld [hli], a
	ld [hl], c

	xor a
	ld [wRandomTries], a
	ld a, [wCupMakeCount]
	ld b, a
	ld a, [wOTPartyCount]
	cp b
	jmp c, .next
	ret

.reject
	; in order, just the next one; else if nothing fits after many tries,
	; start the team over (and count it)
	ld a, [wRandomStartOvers]
	cp RANDOM_MAX_START_OVERS
	jmp nc, .next
	ld hl, wRandomTries
	inc [hl]
	ld a, [hl]
	cp RANDOM_MAX_TRIES
	jmp c, .next
	ld hl, wRandomStartOvers
	inc [hl]
	jmp .start_over

.CountOfType:
; a = how many different species (and forms) in the sets have type
; [wCupFoeType]. A species' sets are next to each other, and its sets all
; have its types, so a set counts when it isn't the species before.
	ld hl, RandomBattleSets
	ld bc, NUM_RANDOM_BATTLE_SETS
	xor a
	ld [wRandomTries], a ; (the count, here: .start_over clears it)
	ld de, $ffff ; the set before: species, form
.count_loop
	push bc
	ld a, [hli]
	cp d
	ld d, a
	ld a, [hld]
	jr nz, .new_species
	cp e
	jr z, .count_next ; (another set of the same one)
.new_species
	ld e, a
	push hl
	push de
	call LinkRandomBattle_MakeTeam.GetProfile
	ld a, [wCupFoeType]
	cp [hl]
	inc hl
	jr z, .is_type
	cp [hl]
.is_type
	pop de
	pop hl
	jr nz, .count_next
	ld a, [wRandomTries]
	inc a
	ld [wRandomTries], a
.count_next
	ld bc, RANDOM_SET_LENGTH
	add hl, bc
	pop bc
	dec bc
	ld a, b
	or c
	jr nz, .count_loop
	ld a, [wRandomTries]
	ret

.HaveSpecies:
; Return z if wOTParty already has species c (extspecies flag in b).
	ld a, [wOTPartyCount]
	and a
	jr z, .none
	push hl
	push de
	ld e, a
	ld hl, wOTPartyMon1Species
.loop
	ld a, [hl]
	cp c
	jr nz, .different
	push hl
	ld a, l
	add MON_FORM - MON_SPECIES
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, [hl]
	pop hl
	xor b
	and EXTSPECIES_MASK
	jr z, .found
.different
	ld a, l
	add PARTYMON_STRUCT_LENGTH
	ld l, a
	adc h
	sub l
	ld h, a
	dec e
	jr nz, .loop
	pop de
	pop hl
.none
	or 1
	ret
.found
	pop de
	pop hl
	ret ; z
