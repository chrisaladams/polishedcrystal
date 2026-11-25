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
	; the draw kept for the bracket screen, and no results yet
	ldh a, [rWBK]
	push af
	ld hl, wWorldCupBracket
	ld de, wWorldCupDraw
	ld c, WORLD_CUP_CONTESTANTS
.keep
	ld a, [hli] ; (WRAM0)
	ld b, a
	ld a, BANK(wWorldCupDraw)
	ldh [rWBK], a
	ld a, b
	ld [de], a
	inc de
	dec c
	jr nz, .keep
	ld hl, wWorldCupResults
	ld bc, WORLD_CUP_CONTESTANTS
	xor a
	rst ByteFill
	pop af
	ldh [rWBK], a
	ret

WorldCupNoteResult:
; For the bracket screen: contestant a beat contestant c. Keeps af, bc.
	push af
	push bc
	ld b, a
	ldh a, [rWBK]
	push af
	ld a, BANK(wWorldCupResults)
	ldh [rWBK], a
	ld a, b
	call .Result
	inc [hl]
	ld a, c
	call .Result
	set WORLDCUP_OUT_F, [hl]
	pop af
	ldh [rWBK], a
	pop bc
	pop af
	ret

.Result:
	ld hl, wWorldCupResults
	add l
	ld l, a
	ret nc
	inc h
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

WorldCupNextResult::
; After you win a round (before WorldCupAdvance), the trainers' own matches in
; turn, from wWorldCupPairCursor (set it to 2 first): the winner's name in
; wStringBuffer4, the loser's in wStringBuffer5; hScriptVar = FALSE when
; there are no more, TRUE for a win, 2 for an upset.
	ld hl, wWorldCupPairCursor
	ld a, [wWorldCupRoundSize]
	cp [hl]
	jr z, .none
	jr c, .none
	ld a, [hl]
	inc [hl]
	inc [hl]
	push af ; the pair's first slot
	srl a
	dec a ; which of the trainers' pairs, from 0
	ld c, a
	ld a, [wWorldCupRoundSize]
	ld b, a
	ld a, WORLD_CUP_CONTESTANTS + 1
	sub b
	add c
	ld e, a ; its match (as WorldCupAdvance numbers them)
	pop af
	call WorldCupBracketSlot
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld hl, wWorldCupSeed
	call WorldCupAnnounceSeeded ; (c = the winner)
	ldh a, [hScriptVar]
	inc a
	ldh [hScriptVar], a
	ld a, c
	ld de, wStringBuffer4
	jr WorldCupCopyName

.none
	xor a
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
; After you win a round: the trainers' matches, and the next round's draw;
; hScriptVar = FALSE if that was the final.
	ld a, [wWorldCupBracket + 1]
	ld c, a
	xor a ; you
	call WorldCupNoteResult
	ld b, 1 ; (yours is decided)
	call WorldCupPlayRound
	ld a, FALSE
	jr z, .done
	inc a ; TRUE
.done
	ldh [hScriptVar], a
	ret

WorldCupPlayOut::
; After you lose: who beat you goes on, and the rest of the bracket is
; played out (decided as WorldCupWinner decides every trainers' match), so
; the bracket screen can show the champion.
	ld a, [wWorldCupBracket + 1]
	ld [wWorldCupBracket], a
	ld c, 0 ; you
	call WorldCupNoteResult
	ld b, 1
.round
	call WorldCupPlayRound
	ret z
	ld b, 0
	jr .round

WorldCupPlayRound:
; The round's matches from pair b on (each match numbered as WorldCupWinner
; expects: 0-3, 4-5, 6), the winners moved up to the next round's draw. z
; if that was the final.
	ld a, [wWorldCupRoundSize]
	ld c, a
	ld a, WORLD_CUP_CONTESTANTS
	sub c
	add b
	ld [wWorldCupMatch], a
	ld a, c
	srl a
	ld [wWorldCupRoundSize], a
	ld c, a
	xor a
	ld [wWorldCupPairCursor], a
	ld a, c
	sub b
	jr z, .played
	ld c, a ; pairs to play
	ld a, b
	add a
	ld hl, wWorldCupBracket
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, b
	ld de, wWorldCupBracket
	add e
	ld e, a
	adc d
	sub e
	ld d, a
	ld b, c
.match
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
	cp b
	jr nz, .b_lost
	ld b, c
.b_lost
	ld c, b ; the loser
	call WorldCupNoteResult
	pop hl
	pop de
	ld [de], a
	inc de
	pop bc
	dec b
	jr nz, .match
.played
	ld a, [wWorldCupRoundSize]
	dec a
	ret

WorldCupShowBracket::
; The bracket screen: everyone in the draw's order, a star for each round
; they've won and a cross where they went out, and the champion once there
; is one. (A copy of the bank-2 history in wStringBuffer5 to read from:
; the draw, then the results.)
	ldh a, [rWBK]
	push af
	ld hl, wWorldCupDraw
	ld de, wStringBuffer5
	ld c, 2 * WORLD_CUP_CONTESTANTS
.copy
	ld a, BANK(wWorldCupDraw)
	ldh [rWBK], a
	ld b, [hl]
	inc hl
	ld a, BANK(wStringBuffer5)
	ldh [rWBK], a
	ld a, b
	ld [de], a
	inc de
	dec c
	jr nz, .copy
	pop af
	ldh [rWBK], a

	call FadeToMenu_BackupSprites
	call LoadStandardFont
	call LoadFrame
	call ClearTileMap
	call ClearSprites
	hlcoord 0, 0
	lb bc, SCREEN_HEIGHT - 2, SCREEN_WIDTH - 2
	call Textbox
	hlcoord 1, 1
	ld de, .Title
	rst PlaceString
	hlcoord 11, 2
	ld de, .Rounds
	rst PlaceString
	ld c, 0
.row
	; rows 4-5, 7-8, 10-11, 13-14: the four first-round pairs
	push bc
	ld a, c
	srl a
	add c
	add 4
	hlcoord 2, 0
	ld bc, SCREEN_WIDTH
	call AddNTimes
	pop bc
	push bc
	push hl
	call .Who
	call .Name
	pop hl
	push hl
	rst PlaceString
	pop hl
	ld de, 9
	add hl, de ; their QF column
	pop bc
	push bc
	call .Who
	ld de, wStringBuffer5 + WORLD_CUP_CONTESTANTS
	add e
	ld e, a
	adc d
	sub e
	ld d, a
	ld a, [de]
	ld b, a
	and WORLDCUP_WINS_MASK
	jr z, .no_wins
	ld c, a
.star
	ld [hl], '★'
	inc hl
	inc hl
	inc hl
	dec c
	jr nz, .star
.no_wins
	bit WORLDCUP_OUT_F, b
	jr z, .next
	ld [hl], '×'
.next
	pop bc
	inc c
	ld a, c
	cp WORLD_CUP_CONTESTANTS
	jr c, .row

	; the champion: three wins
	ld hl, wStringBuffer5 + WORLD_CUP_CONTESTANTS
	ld c, 0
.find
	ld a, [hli]
	and WORLDCUP_WINS_MASK
	cp 3
	jr z, .champion
	inc c
	ld a, c
	cp WORLD_CUP_CONTESTANTS
	jr c, .find
	jr .shown
.champion
	ld a, c
	call .Name
	push de
	hlcoord 2, 16
	ld de, .Champion
	rst PlaceString
	pop de
	hlcoord 12, 16
	rst PlaceString
.shown
	hlcoord 0, 0, wAttrmap
	xor a
	ld bc, SCREEN_AREA
	rst ByteFill
	call ApplyAttrAndTilemapInVBlank
	ld a, CGB_PLAIN
	call GetCGBLayout
	call SetDefaultBGPAndOBP
	ld c, 8
	call DelayFrames
	call WaitPressAorB_BlinkCursor
	jmp ExitAllMenus

.Who:
; a = who's at draw position c. Keeps hl.
	push hl
	ld hl, wStringBuffer5
	ld b, 0
	add hl, bc
	ld a, [hl]
	pop hl
	ret

.Name:
; de = contestant a's name.
	and a
	ld de, wPlayerName
	ret z
	call WorldCupTrainer
	inc hl
	inc hl
	ld a, [hli]
	ld d, [hl]
	ld e, a
	ret

.Title:
	db "World Championship@"
.Rounds:
	db "QF SF F@"
.Champion:
	db "Champion:@"

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
