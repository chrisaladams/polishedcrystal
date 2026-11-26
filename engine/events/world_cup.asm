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

DEF BRACKET_TILES EQU $20 ; (vTiles2: ExitAllMenus reloads the tileset after)
; line kinds, as the left half draws them (the right half mirrors 2-4)
	const_def
	const BK_H    ; ─
	const BK_V    ; │
	const BK_TOP  ; ┐ (┌ on the right)
	const BK_BOT  ; ┘ (└)
	const BK_JOIN ; ├ (┤)
DEF BK_MIRROR EQU 3 ; ┌ └ ┤ follow ┐ ┘ ├
DEF BK_LIT EQU 8 ; the black set: someone went through here
DEF BK_X EQU 16 ; a cross: who went out here (17 on the right)
DEF BRACKET_HALF EQU 2 * WORLD_CUP_CONTESTANTS ; (in wStringBuffer5)
DEF BRACKET_NAME_LENGTH EQU 5

WorldCupShowBracket::
; The bracket: the draw's two halves at the sides, each match's winner
; carried toward the middle in black, a cross where each went out, and the
; champion below once there is one. (From a copy of the bank-2 history in
; wStringBuffer5: the draw, then the results; then the half being drawn.)
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
	call ClearTileMap
	call ClearSprites
	ld de, BracketLinesGFX
	ld hl, vTiles2 tile BRACKET_TILES
	lb bc, BANK(BracketLinesGFX), 18
	call Request2bpp
	hlcoord 1, 1
	ld de, .Title
	rst PlaceString
	xor a
	call .Half
	ld a, 1
	call .Half

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
	hlcoord 2, 15
	ld de, .Champion
	rst PlaceString
	pop de
	hlcoord 12, 15
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

.Half:
; Draw half a (0: the left, draw places 0-3; 1: the right, 4-7).
	ld [wStringBuffer5 + BRACKET_HALF], a
	; the four, each with its first line: black if they won their first
	; match, a cross if they lost it; and the corner to their match
	ld c, 0
.entrant
	push bc
	call .RowOf
	ld a, c
	call .Result ; d = the result, e = who
	push de
	push bc
	ld a, e
	call .ShortName
	pop bc
	push bc
	ld a, [wStringBuffer5 + BRACKET_HALF]
	and a
	ld c, 0
	jr z, .name_column
	ld c, SCREEN_WIDTH - BRACKET_NAME_LENGTH
.name_column
	call .Coord
	ld de, wStringBuffer4
	rst PlaceString
	pop bc
	pop de
	push de
	push bc
	ld a, d
	and WORLDCUP_WINS_MASK
	ld a, BK_H | BK_LIT
	jr nz, .first_line
	bit WORLDCUP_OUT_F, d
	ld a, BK_H
	jr z, .first_line
	ld a, BK_X
.first_line
	ld c, BRACKET_NAME_LENGTH + 1 ; (a space after the name)
	call .Cell
	pop bc
	pop de
	ld a, c
	and 1
	add BK_TOP ; (the top of a pair: ┐, the bottom: ┘)
	ld e, a
	ld a, d
	and WORLDCUP_WINS_MASK
	ld a, e
	jr z, .corner
	add BK_LIT
.corner
	ld c, BRACKET_NAME_LENGTH + 2
	call .Cell
	pop bc
	inc c
	ld a, c
	cp 4
	jr c, .entrant

	; the two first-round matches: the join, lit once decided, and the
	; winner's line on (a cross if they then lost their semifinal)
	ld c, 0
.pair
	push bc
	ld a, c
	add a
	push af
	call .Result
	pop af
	ld a, d
	and WORLDCUP_WINS_MASK
	jr nz, .pair_won
	ld a, c
	add a
	inc a
	call .Result
	ld a, d
	and WORLDCUP_WINS_MASK
	jr nz, .pair_won
	ld d, 0 ; (undecided)
.pair_won
	pop bc
	push bc
	ld a, c
	and a
	ld b, 5
	jr z, .pair_row
	ld b, 11
.pair_row
	push de
	ld a, d
	and a
	ld a, BK_JOIN
	jr z, .join
	add BK_LIT
.join
	ld c, BRACKET_NAME_LENGTH + 2
	call .Cell
	pop de
	ld e, 1
	call .OnLine
	ld c, BRACKET_NAME_LENGTH + 3
	call .Cell
	pop bc
	inc c
	ld a, c
	cp 2
	jr c, .pair

	; the semifinal: the side its winner came from lit, and its join, which
	; meets the other half's in the middle (a cross if they lost the final)
	ld c, 0
.semi
	push bc
	ld a, c
	call .Result
	pop bc
	ld a, d
	and WORLDCUP_WINS_MASK
	cp 2
	jr nc, .semi_won
	inc c
	ld a, c
	cp 4
	jr c, .semi
	ld d, 0
	ld c, 0
.semi_won
	; c < 2: from the top pair
	ld a, c
	cp 2
	ld a, 0
	jr nc, .from_bottom
	ld a, d
	and a
	jr z, .from_bottom ; (undecided: neither side)
	ld a, BK_LIT
.from_bottom
	ld e, a ; the top side's light
	ld a, d
	and a
	ld a, 0
	jr z, .got_sides
	ld a, BK_LIT
	xor e ; the bottom side's: the other
.got_sides
	push de
	push af
	ld c, BRACKET_NAME_LENGTH + 4
	ld b, 5
	ld a, BK_TOP
	add e
	call .Cell
	ld c, BRACKET_NAME_LENGTH + 4
	ld b, 6
	ld a, BK_V
	add e
	call .Cell
	ld c, BRACKET_NAME_LENGTH + 4
	ld b, 7
	ld a, BK_V
	add e
	call .Cell
	pop af
	push af
	ld c, BRACKET_NAME_LENGTH + 4
	ld b, 9
	add BK_V
	call .Cell
	pop af
	push af
	ld c, BRACKET_NAME_LENGTH + 4
	ld b, 10
	add BK_V
	call .Cell
	pop af
	ld c, BRACKET_NAME_LENGTH + 4
	ld b, 11
	add BK_BOT
	call .Cell
	pop de
	ld e, 2
	call .OnLine
	cp BK_X
	jr z, .semi_join
	and BK_LIT
	add BK_JOIN
.semi_join
	ld c, BRACKET_NAME_LENGTH + 4
	ld b, 8
	jr .Cell

.OnLine:
; a = the line after a match won by result d (0: undecided): black, or a
; cross if they went out in the next round (with e wins).
	ld a, d
	and a
	ld a, BK_H
	ret z
	bit WORLDCUP_OUT_F, d
	jr z, .on
	ld a, d
	and WORLDCUP_WINS_MASK
	cp e
	ld a, BK_X
	ret z
.on
	ld a, BK_H | BK_LIT
	ret

.Cell:
; Put line kind a (BK_*, maybe | BK_LIT, or BK_X) at row b, column c as the
; left half has it (the right half mirrors it).
	ld d, a
	ld a, [wStringBuffer5 + BRACKET_HALF]
	and a
	jr z, .place
	ld a, SCREEN_WIDTH - 1
	sub c
	ld c, a
	ld a, d
	cp BK_X
	jr z, .right_cross
	and BK_LIT - 1
	cp BK_TOP
	jr c, .place
	ld a, d
	add BK_MIRROR
	ld d, a
	jr .place
.right_cross
	inc d ; (the cross kept to the tile's left, away from the name)
.place
	call .Coord
	ld a, d
	add BRACKET_TILES
	ld [hl], a
	ret

.Coord:
; hl = the tilemap at row b, column c. Keeps bc, de.
	push bc
	ld a, b
	ld hl, wTilemap
	ld b, 0
	add hl, bc
	ld bc, SCREEN_WIDTH
	rst AddNTimes
	pop bc
	ret

.Result:
; d = the result of who's at place a of the half being drawn; e = who.
	ld e, a
	ld a, [wStringBuffer5 + BRACKET_HALF]
	add a
	add a
	add e
	ld hl, wStringBuffer5
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld e, [hl]
	ld hl, wStringBuffer5 + WORLD_CUP_CONTESTANTS
	ld a, e
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld d, [hl]
	ret

.ShortName:
; wStringBuffer4 = the first BRACKET_NAME_LENGTH letters of contestant a's
; name.
	call .Name
	ld hl, wStringBuffer4
	ld c, BRACKET_NAME_LENGTH
.letter
	ld a, [de]
	inc de
	cp '@'
	jr z, .end
	ld [hli], a
	dec c
	jr nz, .letter
.end
	ld [hl], '@'
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

.RowOf:
; b = the row of place c in a half.
	push hl
	ld hl, .Rows
	ld a, c
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld b, [hl]
	pop hl
	ret

.Rows:
	db 4, 6, 10, 12

.Title:
	db "World Championship@"
.Champion:
	db "Champion:@"

BracketLinesGFX:
INCBIN "gfx/world_cup/bracket_lines.2bpp"

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
