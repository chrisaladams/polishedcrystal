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
.start_over
	xor a
	ld [wPartyCount], a
	ld [wRandomTries], a
	ld hl, wRandomTypeCounts
	ld bc, NUM_RANDOM_TYPES * 2
	rst ByteFill
.next
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
	; one of each species, and a decent type spread
	ld a, [hli]
	ld c, a
	ld a, [hld]
	ld b, a
	call .HaveSpecies
	jmp z, .reject
	call .TypeSpreadOK
	jmp c, .reject
	call .CountTypes
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
	; if nothing fits after many tries, start the team over
	ld hl, wRandomTries
	inc [hl]
	ld a, [hl]
	cp RANDOM_MAX_TRIES
	jmp c, .next
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

