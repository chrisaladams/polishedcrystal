; Return with the records' SRAM bank selected. Initialize from the old
; undated link totals once, before any new battle or adventure can change them.
OpenLinkCardRecords:
	; Always import the old opponent table before the first new battle or erase.
	call OpenLinkCardPlayers
	ld a, BANK(sLinkCardMarker)
	call GetSRAMBank
	ld hl, sLinkCardMarker
	ld a, [hli]
	cp 'L'
	jr nz, .initialize
	ld a, [hl]
	cp 'R'
	ret z
.initialize
	ld hl, sLinkCardLifetime
	ld bc, sLinkCardEnd - sLinkCardLifetime
	xor a
	rst ByteFill
	call LinkCardHasSave
	jr nz, .mark
	ld hl, sLinkBattleWins
	ld de, sLinkCardLifetime + 1
	ld b, 3
.loop
	ld a, [hli]
	ld [de], a
	inc de
	ld a, [hli]
	ld [de], a
	inc de
	inc de
	dec b
	jr nz, .loop
.mark
	ld hl, sLinkCardMarker
	ld a, 'L'
	ld [hli], a
	ld [hl], 'R'
	ret

LinkCardHasSave:
	; The title-screen erase shortcut can run before a save has been loaded.
	ld a, BANK(sCheckValue1)
	call GetSRAMBank
	ld a, [sCheckValue1]
	ld b, a
	ld a, [sCheckValue2]
	call LinkCardCheckHeader
	push af
	ld a, BANK(sLinkCardMarker)
	call GetSRAMBank
	pop af
	ret z
	assert BANK(sBackupCheckValue1) == BANK(sLinkCardMarker)
	ld a, [sBackupCheckValue1]
	ld b, a
	ld a, [sBackupCheckValue2]
LinkCardCheckHeader:
	cp SAVE_CHECK_VALUE_2
	ret nz
	ld a, b
	cp SAVE_CHECK_VALUE_1
	ret z
	cp SAVE_CHECK_VALUE_1_OLD
	ret

CountLinkCardResult:
	call OpenLinkCardRecords
	call CountLinkCardPlayer
	ld a, BANK(sLinkCardLifetime)
	call GetSRAMBank
	ld a, [wBattleResult]
	and $f
	cp LOSE
	ld bc, 0 ; WIN
	jr c, .count
	ld c, 3 ; LOSE
	jr z, .count
	ld c, 6 ; DRAW
.count
	ld hl, sLinkCardLifetime
	add hl, bc
	call .increment
	ld hl, sLinkCardYear
	add hl, bc
.increment
	; Saturate at $ffffff so even a full counter never rolls back to zero.
	ld a, [hli]
	and [hl]
	inc hl
	and [hl]
	inc a
	ret z
	inc [hl]
	ret nz
	dec hl
	inc [hl]
	ret nz
	dec hl
	inc [hl]
	ret

DrawLinkCardRecords:
	call OpenLinkCardRecords
	ld a, [wJumptableIndex]
	cp CARD_LINK_YEAR
	ld de, .Lifetime
	ld bc, sLinkCardLifetime
	jr nz, .print
	ld de, .Year
	ld bc, sLinkCardYear
.print
	push bc
	hlcoord 1, 9
	rst PlaceString
	hlcoord 2, 11
	ld de, .Labels
	rst PlaceString
	pop de
	hlcoord 10, 11
	lb bc, 3, 8
	call PrintNum
	inc de ; PrintNum returns DE at the final byte
	hlcoord 10, 12
	call PrintNum
	inc de
	hlcoord 10, 13
	call PrintNum
	call CloseSRAM
	hlcoord 2, 15
	ld de, .Players
	rst PlaceString
	hlcoord 1, 16
	ld a, [wJumptableIndex]
	cp CARD_LINK_YEAR
	ld de, .TurnPage
	jr nz, .footer
	ld de, .YearControls
.footer
	rst PlaceString
	ret

.Lifetime:     db "Link: Lifetime@"
.Year:         db "Link: Current Year@"
.Labels:       db "Wins<LNBRK>Losses<LNBRK>Draws@"
.Players:      db "▼ Player list@"
.TurnPage:     db "◀     This year ▶@"
.YearControls: db "◀  A: Reset year ▶@"

ConfirmResetLinkCardYear:
	hlcoord 1, 10
	lb bc, 7, 18
	call ClearBox
	hlcoord 2, 13
	ld de, .Prompt
	rst PlaceString
	call ApplyTilemapInVBlank
	call NoYesBox ; defaults to No, B cancels
	ret c
	call OpenLinkCardRecords
	call ResetLinkCardPlayerYears
	ld a, BANK(sLinkCardYear)
	call GetSRAMBank
	ld hl, sLinkCardYear
	ld bc, sLinkCardEnd - sLinkCardYear
	xor a
	rst ByteFill
	jmp CloseSRAM

.Prompt: db "Reset this year's<LNBRK>link record?@"

; Convert the five saved Cable Club opponents once. Unused SRAM can contain
; arbitrary bytes, so trust a legacy record only on a recognized adventure.
OpenLinkCardPlayers:
	ld a, BANK(sLinkCardPlayers)
	call GetSRAMBank
	ld hl, sLinkCardPlayerTag
	ld a, [hli]
	cp 'P'
	jr nz, .init
	ld a, [hl]
	cp '1'
	ret z
.init
	xor a
	ld [sLinkCardPlayerCount], a
	call LinkCardHasSave
	jr nz, .finish
	ld hl, sLinkBattleRecord
	ld b, NUM_LINK_BATTLE_RECORDS
.import
	push bc
	push hl
	ld de, wStringBuffer1
	ld bc, LINK_BATTLE_RECORD_LENGTH
	rst CopyBytes
	ld a, [wStringBuffer1 + 2]
	and a
	jr z, .next
	cp '@'
	jr z, .next
	cp $ff
	jr z, .next
	call LinkCardFindOrAdd
	jr c, .next
	ld d, h
	ld e, l
	ld hl, wStringBuffer1 + LINK_BATTLE_RECORD_LENGTH - 6
	ld bc, 6
	rst CopyBytes
.next
	ld a, BANK(sLinkBattleStats)
	call GetSRAMBank
	pop hl
	ld bc, LINK_BATTLE_RECORD_LENGTH
	add hl, bc
	pop bc
	dec b
	jr nz, .import
.finish
	ld a, BANK(sLinkCardPlayers)
	call GetSRAMBank
	ld hl, sLinkCardPlayerTag
	ld a, 'P'
	ld [hli], a
	ld [hl], '1'
	ret

; wStringBuffer1 starts with ID and seven name bytes. Ignore anything
; following the name terminator when matching trainers across different games.
LinkCardFindOrAdd:
	ld hl, wStringBuffer1 + 2
	ld b, PLAYER_NAME_LENGTH - 1
.normalize
	ld a, [hli]
	cp '@'
	jr z, .pad
	dec b
	jr nz, .normalize
	jr .lookup
.pad
	dec b
	jr z, .lookup
	ld [hli], a
	jr .pad
.lookup
	ld a, BANK(sLinkCardPlayers)
	call GetSRAMBank
	ld a, [sLinkCardPlayerCount]
	ld b, a
	ld hl, sLinkCardPlayers
.search
	ld a, b
	and a
	jr z, .add
	push bc
	push hl
	ld de, wStringBuffer1
	ld c, LINK_CARD_KEY_SIZE
	call StringCmp
	pop hl
	pop bc
	jr z, .found
	ld de, LINK_CARD_ROW_SIZE
	add hl, de
	dec b
	jr .search
.found
	ld de, LINK_CARD_KEY_SIZE
	add hl, de
	and a
	ret
.add
	ld a, [sLinkCardPlayerCount]
	cp LINK_CARD_MAX_PLAYERS
	ccf ; full: retain all existing players
	ret c
	push hl
	ld d, h
	ld e, l
	ld hl, wStringBuffer1
	ld bc, LINK_CARD_KEY_SIZE
	rst CopyBytes
	ld h, d
	ld l, e
	ld bc, 12
	xor a
	rst ByteFill
	ld hl, sLinkCardPlayerCount
	inc [hl] ; publish only after the entry is complete
	pop hl
	jr .found

CountLinkCardPlayer:
	ld hl, wOTPlayerID
	ld de, wStringBuffer1
	ld bc, 2
	rst CopyBytes
	ld hl, wOTPlayerName
	ld bc, PLAYER_NAME_LENGTH - 1
	rst CopyBytes
	call LinkCardFindOrAdd
	ret c
	ld a, [wBattleResult]
	and $f
	cp LOSE
	ld bc, 0
	jr c, .count
	ld c, 2
	jr z, .count
	ld c, 4
.count
	add hl, bc
	push hl
	call .increment
	pop hl
	ld bc, 6
	add hl, bc
.increment
	ld a, [hli]
	and [hl]
	inc a
	ret z ; $ffff
	inc [hl]
	ret nz
	dec hl
	inc [hl]
	ret

ResetLinkCardPlayerYears:
	ld a, BANK(sLinkCardPlayers)
	call GetSRAMBank
	ld a, [sLinkCardPlayerCount]
	and a
	ret z
	ld d, a
	ld hl, sLinkCardPlayers + LINK_CARD_KEY_SIZE + 6
.loop
	ld bc, 6
	xor a
	rst ByteFill
	ld bc, LINK_CARD_ROW_SIZE - 6
	add hl, bc
	dec d
	jr nz, .loop
	ret

BrowseLinkCardPlayers:
	xor a
	ld [wLinkCardPage], a
.redraw
	call DrawLinkCardPlayers
.input
	call DelayFrame
	call GetJoypad
	ldh a, [hJoyPressed]
	bit B_PAD_B, a
	jr nz, .back
	bit B_PAD_RIGHT, a
	jr z, .left
	ld a, [wLinkCardMore]
	and a
	jr z, .input
	ld hl, wLinkCardPage
	inc [hl]
	jr .redraw
.left
	bit B_PAD_LEFT, a
	jr z, .input
	ld hl, wLinkCardPage
	ld a, [hl]
	and a
	jr z, .input
	dec [hl]
	jr .redraw
.back
	; Restore the portrait, border and header overwritten by the table.
	call ClearTileMap
	farcall TrainerCard_PrintBorder
	farcall TrainerCard_PrintTopHalfOfCard
	ret

DrawLinkCardPlayers:
	call ClearTileMap
	hlcoord 1, 0
	ld a, [wLinkCardPeriod]
	and a
	ld de, .Lifetime
	jr z, .title
	ld de, .Year
.title
	rst PlaceString
	hlcoord 1, 2
	ld de, .Headings
	rst PlaceString
	ld a, BANK(sLinkCardPlayers)
	call GetSRAMBank
	xor a
	ld [wLinkCardMore], a
	ld a, [wLinkCardPage]
	add a
	add a
	ld d, a ; visible opponents to skip
	ld e, 0 ; visible rows on this page
	ld a, [sLinkCardPlayerCount]
	ld b, a
	ld hl, sLinkCardPlayers
.loop
	ld a, b
	and a
	jr z, .end
	ld a, [wLinkCardPeriod]
	and a
	jr z, .eligible
	; Use a temporary DE so the page skip and display index survive.
	push de
	ld de, LINK_CARD_KEY_SIZE + 6
	add hl, de
	xor a
rept 6
	or [hl]
	inc hl
endr
	ld de, -LINK_CARD_ROW_SIZE
	add hl, de ; ADD HL preserves Z
	pop de
	jr z, .next
.eligible
	ld a, d
	and a
	jr z, .visible
	dec d
	jr .next
.visible
	ld a, e
	cp LINK_CARD_ROWS_PER_PAGE
	jr z, .more
	push bc
	push de
	push hl
	call PrintLinkCardPlayer
	pop hl
	pop de
	pop bc
	inc e
.next
	push de
	ld de, LINK_CARD_ROW_SIZE
	add hl, de
	pop de
	dec b
	jr .loop
.more
	ld a, 1
	ld [wLinkCardMore], a
.end
	ld a, [sLinkCardPlayerCount]
	cp LINK_CARD_MAX_PLAYERS
	jr nz, .close
	push de
	hlcoord 10, 17
	ld de, .Full
	rst PlaceString
	pop de
.close
	call CloseSRAM
	ld a, e
	and a
	jr nz, .footer
	hlcoord 2, 6
	ld de, .Empty
	rst PlaceString
.footer
	hlcoord 1, 17
	ld de, .Back
	rst PlaceString
	ld a, [wLinkCardPage]
	and a
	jr z, .right
	hlcoord 1, 16
	ld [hl], '◀'
.right
	ld a, [wLinkCardMore]
	and a
	jr z, .done
	hlcoord 18, 16
	ld [hl], '▶'
.done
	jmp ApplyTilemapInVBlank

.Lifetime: db "Lifetime players@"
.Year:     db "This year's players@"
.Headings: db " Wins Losses Draws@"
.Empty:    db "No battles yet.@"
.Back:     db "B: Back@"
.Full:     db "List full@"

; HL = player entry, A = row on page. Two lines per player leave room
; for the seven-letter name, five-digit ID and every five-digit count.
PrintLinkCardPlayer:
	push hl
	ld hl, .Rows
	add a
	ld e, a
	ld d, 0
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	pop de
	push de
	push hl
	inc de
	inc de
	ld b, PLAYER_NAME_LENGTH - 1
.name
	ld a, [de]
	cp '@'
	jr z, .id
	ld [hli], a
	inc de
	dec b
	jr nz, .name
.id
	pop hl
	push hl
	ld bc, 10
	add hl, bc
	ld [hl], '<ID>'
	inc hl
	ld [hl], '№'
	inc hl
	pop bc
	pop de
	push bc
	lb bc, PRINTNUM_LEADINGZEROS | 2, 5
	call PrintNum
	ld hl, LINK_CARD_KEY_SIZE - 1
	add hl, de ; DE = entry + 1
	ld a, [wLinkCardPeriod]
	and a
	jr z, .scores
	ld de, 6
	add hl, de
.scores
	ld d, h
	ld e, l
	pop hl
	ld bc, SCREEN_WIDTH
	add hl, bc
	lb bc, 2, 5
	call PrintNum
	inc de
	inc hl
	call PrintNum
	inc de
	inc hl
	jmp PrintNum
.Rows
	dwcoord 1, 4
	dwcoord 1, 7
	dwcoord 1, 10
	dwcoord 1, 13
