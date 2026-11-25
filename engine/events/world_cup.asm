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
	; the stronger seed (larger index in WorldCupTrainers) advances.
	ld a, [wWorldCupRoundSize]
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
	ld a, [hli]
	cp [hl]
	jr nc, .winner
	ld a, [hl]
.winner
	inc hl
	ld [de], a
	inc de
	dec b
	jr nz, .advance
	ld a, TRUE
	ldh [hScriptVar], a
	ret

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
