; Link Edition: Random Battle.
;
; With Random Battle rules (chosen at the Cable Club battle desk; both players
; must choose them), each game replaces its party with six random level 50
; Pokemon just before the link battle, from the sets in
; data/link/random_battle_sets.asm (different species, perfect DVs, neutral
; nature), with a decent type spread: no more than RANDOM_MAX_SAME_TYPE of
; them share a type, and no more than RANDOM_MAX_SAME_WEAK are weak to the
; same type. The real party isn't touched in the save: after the battle the
; game reloads it from the save made at the desk, as after any link battle.

INCLUDE "data/link/random_battle_sets.asm"

LinkRandomBattle_MakeTeam::
	xor a
	ld [wRandomStartOvers], a
	ld [wRandomSeqIndex], a
	ld [wRandomSeqIndex + 1], a
.start_over
	xor a
	ld [wPartyCount], a
	ld [wRandomTries], a
	ld hl, wRandomTypeCounts
	ld bc, NUM_RANDOM_TYPES * 2
	rst ByteFill
.next
	ld a, [wRandomStartOvers]
	cp RANDOM_MAX_START_OVERS
	jr c, .random_pick
	; past the limit: the next set in order (RandomNextInOrder), the type
	; spread checked on the first pass only; out of sets, the team is as full
	; as it can be (a short team is refused at the other desk, not hung on)
	call RandomNextInOrder
	jr c, .out_of_sets
	ld a, b
	and a
	jr z, .picked ; (first pass: the usual checks)
	; the second pass: one of each species, whatever the spread
	push hl
	ld a, [hli]
	ld c, a
	ld b, [hl]
	pop hl
	call .HaveSpecies
	jr z, .next
	jr .add_set
.out_of_sets
	xor a
	ld [wCurPartyMon], a
	ret

.random_pick
	; pick a set: 10 random bits, tried again until below the number of sets
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
	; hl = RandomBattleSets + index * RANDOM_SET_LENGTH (9)
	ld d, h
	ld e, l
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, de
	ld de, RandomBattleSets
	add hl, de
.picked
	; one of each species, and a decent type spread
	ld a, [hli]
	ld c, a
	ld a, [hld]
	ld b, a
	call .HaveSpecies
	jmp z, .reject
	call .TypeSpreadOK
	jr c, .reject
	call .CountTypes
.add_set
	ld a, [hli] ; species and form again (the checks used b and c)
	ld c, a
	ld a, [hld]
	ld b, a

	; add it to the party, as the game adds any Pokemon
	push hl
	ld a, c
	ld [wCurPartySpecies], a
	ld a, b
	ld [wCurForm], a
	ld a, LINK_BATTLE_FORCED_LEVEL
	ld [wCurPartyLevel], a
	xor a ; PARTYMON
	ld [wMonType], a
	farcall TryAddMonToParty
	ld a, [wPartyCount]
	dec a
	ld [wCurPartyMon], a
	ld hl, wPartyMon1
	call GetPartyLocation
	ld d, h
	ld e, l
	pop hl

	; then give it the set: moves, item, ability
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
	; PP for the new moves
	push de
	ld hl, MON_PP
	add hl, de
	push hl
	ld hl, MON_MOVES
	add hl, de
	pop de
	farcall FillPP
	pop de
	; stats for the new DVs (UpdatePkmnStats keeps HP full)
	farcall UpdatePkmnStats

	xor a
	ld [wRandomTries], a
	ld a, [wPartyCount]
	cp PARTY_LENGTH
	jmp c, .next
	xor a
	ld [wCurPartyMon], a
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

.TypeSpreadOK:
; Carry if adding the set at hl would put too many of a type on the team, or
; too many members weak to the same type.
	push hl
	call .GetProfile
	ld a, [hli] ; first type
	ld b, a
	call .TypeFull
	jr c, .spread_done
	ld a, [hli] ; second type (the same again for a single type)
	cp b
	call nz, .TypeFull
	jr c, .spread_done
	; weaknesses: 24 flag bits, one per type
	ld de, wRandomWeakCounts
	ld c, NUM_RANDOM_TYPES
.weak_byte
	ld a, [hli]
	ld b, 8
.weak_bit
	srl a
	jr nc, .not_weak
	push af
	ld a, [de]
	cp RANDOM_MAX_SAME_WEAK
	jr nc, .too_weak
	pop af
.not_weak
	inc de
	dec c
	jr z, .spread_ok
	dec b
	jr nz, .weak_bit
	jr .weak_byte
.too_weak
	pop af
	scf
	jr .spread_done
.spread_ok
	and a
.spread_done
	pop hl
	ret

.GetProfile:
; hl = the type profile of the set at hl.
	ld de, RANDOM_SET_PROFILE
	add hl, de
	ld l, [hl]
	ld h, 0
	ld d, h
	ld e, l
	add hl, hl
	add hl, hl
	add hl, de
	assert RANDOM_PROFILE_LENGTH == 5
	ld de, RandomBattleProfiles
	add hl, de
	ret

.TypeFull:
; Carry if type a is already on RANDOM_MAX_SAME_TYPE team members.
	push hl
	ld hl, wRandomTypeCounts
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, [hl]
	cp RANDOM_MAX_SAME_TYPE
	ccf
	pop hl
	ret

.CountTypes:
; Add the set at hl's types and weaknesses to the team counts.
	push hl
	call .GetProfile
	ld a, [hli]
	ld b, a
	call .CountType
	ld a, [hli]
	cp b
	call nz, .CountType
	ld de, wRandomWeakCounts
	ld c, NUM_RANDOM_TYPES
.count_byte
	ld a, [hli]
	ld b, 8
.count_bit
	srl a
	jr nc, .count_next
	push af
	ld a, [de]
	inc a
	ld [de], a
	pop af
.count_next
	inc de
	dec c
	jr z, .counted
	dec b
	jr nz, .count_bit
	jr .count_byte
.counted
	pop hl
	ret

.CountType:
	push hl
	ld hl, wRandomTypeCounts
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	inc [hl]
	pop hl
	ret

.HaveSpecies:
; Return z if the party already has species c (extspecies flag in b).
	ld a, [wPartyCount]
	and a
	jr z, .none
	push hl
	push de
	ld e, a
	ld hl, wPartyMon1Species
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

RandomNextInOrder::
; The next Random Battle set in order, for a team past RANDOM_MAX_START_OVERS
; (LinkRandomBattle_MakeTeam, CupMakeTeam): hl = the set, b = 0 on the first
; pass through them, 1 on the second; carry once both passes are done.
	ld hl, wRandomSeqIndex
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld de, -2 * NUM_RANDOM_BATTLE_SETS
	push hl
	add hl, de ; (carry if the index is 2 * NUM_RANDOM_BATTLE_SETS or more)
	pop hl
	ret c ; (both passes done)
	; the index for next time
	push hl
	inc hl
	ld a, l
	ld [wRandomSeqIndex], a
	ld a, h
	ld [wRandomSeqIndex + 1], a
	pop hl
	; which pass, and the set within it
	ld b, 0
	ld de, -NUM_RANDOM_BATTLE_SETS
	push hl
	add hl, de
	pop de ; (de = the index)
	jr nc, .first
	inc b ; the second pass: hl = index - NUM_RANDOM_BATTLE_SETS
	jr .got
.first
	ld h, d
	ld l, e
.got
	; hl = RandomBattleSets + hl * RANDOM_SET_LENGTH (9)
	ld d, h
	ld e, l
	add hl, hl
	add hl, hl
	add hl, hl
	add hl, de
	ld de, RandomBattleSets
	add hl, de
	and a
	ret

