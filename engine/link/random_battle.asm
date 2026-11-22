; Link Edition: Random Battle.
;
; With Random Battle rules (chosen at the Cable Club battle desk; both players
; must choose them), each game replaces its party with six random level 50
; Pokemon just before the link battle, from the sets in
; data/link/random_battle_sets.asm (different species, perfect DVs, neutral
; nature). The real party isn't touched in the save: after the battle the game
; reloads it from the save made at the desk, as it does after any link battle.

INCLUDE "data/link/random_battle_sets.asm"

LinkRandomBattle_MakeTeam::
	xor a
	ld [wPartyCount], a
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
	add hl, hl
	add hl, hl
	add hl, hl
	ld de, RandomBattleSets
	add hl, de
	; one of each species
	ld a, [hli]
	ld c, a
	ld a, [hld]
	ld b, a
	call .HaveSpecies
	jr z, .next

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

	ld a, [wPartyCount]
	cp PARTY_LENGTH
	jmp c, .next
	xor a
	ld [wCurPartyMon], a
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

