WorldCupDraw::
	ld hl, wWorldCupBracket
	xor a
.seed
	ld [hli], a
	inc a
	cp WORLD_CUP_CONTESTANTS
	jr c, .seed
	ld [wWorldCupRoundSize], a
	; Shuffle the seven visiting trainers, leaving the player in slot zero.
	ld b, WORLD_CUP_CONTESTANTS - 1
.shuffle
	ld a, b
	call RandomRange
	inc a
	call WorldCupBracketSlot
	ld d, h
	ld e, l
	ld a, b
	call WorldCupBracketSlot
	ld a, [de]
	ld c, [hl]
	ld [hl], a
	ld a, c
	ld [de], a
	dec b
	jr nz, .shuffle
	call Random
	ld [wWorldCupSeed], a
	call Random
	ld [wWorldCupSeed + 1], a
	xor a
	ld [wWorldCupPairCursor], a
	ret

WorldCupNextPair::
	ld hl, wWorldCupPairCursor
	ld a, [wWorldCupRoundSize]
	cp [hl]
	ld a, FALSE
	ldh [hScriptVar], a
	ret z
	ld a, [hl]
	inc [hl]
	inc [hl]
	call WorldCupBracketSlot
	ld a, [hli]
	push hl
	ld de, wStringBuffer3
	call WorldCupCopyName
	pop hl
	ld a, [hl]
	ld de, wStringBuffer4
	call WorldCupCopyName
	ld a, TRUE
	ldh [hScriptVar], a
	ret

WorldCupCopyName:
	and a
	ld hl, wPlayerName
	jr z, CopyCupDisplayName
	call WorldCupTrainer
	inc hl
	inc hl
	ld a, [hli]
	ld h, [hl]
	ld l, a
CopyCupDisplayName:
	ld a, [hli]
	ld [de], a
	inc de
	cp '@'
	jr nz, CopyCupDisplayName
	ret

WorldCupLoadOpponent::
	ld a, [wWorldCupBracket + 1]
	call WorldCupTrainer
	; Set up the same trainer battle fields as loadtrainer.
	ld a, (1 << 7) | 1
	ld [wBattleScriptFlags], a
	ld a, [hli]
	ld [wOtherTrainerClass], a
	ld a, [hl]
	ld [wOtherTrainerID], a
	xor a ; TRAINERPAL_NONE
	ld [wTrainerPal], a
	ret

WorldCupAdvance::
	; The player's win leaves seed zero in slot zero. For other matches,
	; WorldCupWinner decides, from the draw's seed and the match.
	ld a, [wWorldCupRoundSize]
	ld c, a
	ld a, WORLD_CUP_CONTESTANTS
	sub c
	inc a
	ld [wWorldCupMatch], a ; this round's first trainers' match: 1 (of 0-3), then 5 (of 4-5)
	ld a, c
	srl a
	ld [wWorldCupRoundSize], a
	ld b, a
	xor a
	ld [wWorldCupPairCursor], a
	inc a
	cp b
	ld a, FALSE
	ldh [hScriptVar], a
	ret z
	dec b
	ld hl, wWorldCupBracket + 2
	ld de, wWorldCupBracket + 1
.advance
	push bc
	push de
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld c, a
	push hl
	ld a, [wWorldCupMatch]
	ld e, a
	inc a
	ld [wWorldCupMatch], a
	ld hl, wWorldCupSeed
	call WorldCupWinner
	pop hl
	pop de
	ld [de], a
	inc de
	pop bc
	dec b
	jr nz, .advance
	ld a, TRUE
	ldh [hScriptVar], a
	ret

WorldCupWinner::
; a = the winner of trainers b and c (WorldCupTrainers indexes, plus one) in
; match e of the bracket with the seed at hl. Matches are numbered 0-3 for
; the quarterfinals (slot / 2), 4 and 5 for the semifinals, 6 the final. The
; stronger (the larger index) wins with 50% plus 10% for each place between
; them, at most 90% (docs/rules-matrix.md); the seed and the match alone
; decide, so every cartridge and every visit agree, and nothing else's
; random numbers are used (utils/world_cup/bracket.py does the same).
	ld a, [hli]
	ld h, [hl]
	ld l, a
	or h
	jr nz, .seeded
	inc l ; (the state can't be zero)
.seeded
	inc e
.roll
	; xorshift (7, 9, 8): the state steps once more for each later match
	ld a, h
	rra
	ld a, l
	rra
	xor h
	ld h, a
	ld a, l
	rra
	ld a, h
	rra
	xor l
	ld l, a
	xor h
	ld h, a
	dec e
	jr nz, .roll
	; b = the stronger, c = the other
	ld a, b
	cp c
	jr nc, .ordered
	ld b, c
	ld c, a
.ordered
	ld a, b
	sub c
	cp 4
	jr c, .odds
	ld a, 4
.odds
	ld e, a
	ld d, 0
	push hl
	ld hl, .Odds
	add hl, de
	ld e, [hl]
	pop hl
	ld a, h ; the roll, 0-255
	cp e
	ld a, b
	ret c
	ld a, c
	ret

.Odds:
; out of 256, the stronger's chance for each place between them (none: even)
	db 128, 154, 179, 205, 230

WorldCupBracketSlot:
	ld hl, wWorldCupBracket
	add a, l
	ld l, a
	ret nc
	inc h
	ret

WorldCupTrainer:
	dec a
	add a
	add a
	ld hl, WorldCupTrainers
	add a, l
	ld l, a
	ret nc
	inc h
	ret

MACRO world_cup_trainer
	db \1, \2
	dw .\3
ENDM

WorldCupTrainers:
	table_width 4
	world_cup_trainer ASH_T, 1, Ash
	world_cup_trainer DRAKE_T, 1, Drake
	world_cup_trainer LEAF, 1, Green
	world_cup_trainer BLUE, 2, Blue
	world_cup_trainer CHAMPION, LANCE, Lance
	world_cup_trainer CYNTHIA, 2, Cynthia
	world_cup_trainer RED, 1, Red
	assert_table_length WORLD_CUP_CONTESTANTS - 1
.Ash:     db "Ash@"
.Drake:   db "Drake@"
.Green:   db "Green@"
.Blue:    db "Blue@"
.Lance:   db "Lance@"
.Cynthia: db "Cynthia@"
.Red:     db "Red@"
