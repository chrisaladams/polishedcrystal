_DeleteSaveData:
	farcall BlankScreen
	ld a, CGB_PLAIN
	call GetCGBLayout
	call LoadStandardFont
	call LoadFrame
	call BlackOutScreen
	ld e, MUSIC_MAIN_MENU
	call PlayMusic
	ld hl, .Text_ClearAllSaveData
	call PrintText
	ld hl, NoYesMenuDataHeader
	call CopyMenuHeader
	call VerticalMenu
	ret c
	ld a, [wMenuCursorY]
	dec a
	ret z

	; Initialize even if this is the first time an older cartridge is opened.
	farcall OpenLinkCardRecords
	ld hl, STARTOF(SRAM)
	ld bc, sLinkCardMarker - STARTOF(SRAM)
	xor a
	rst ByteFill
	ld hl, sLinkCardEnd
	ld bc, STARTOF(SRAM) + SIZEOF(SRAM) - sLinkCardEnd
	xor a
	rst ByteFill
	call CloseSRAM
	ld a, 2
	call .EmptyBank
	ld a, 3
	call .EmptyBank
	ld a, BANK(sLinkCardPlayers) ; wipe the access counter last, just before Init
	call GetSRAMBank
	ld hl, STARTOF(SRAM)
	ld bc, sLinkCardPlayerTag - STARTOF(SRAM)
	xor a
	rst ByteFill
	ld hl, sLinkCardPlayersEnd
	ld bc, STARTOF(SRAM) + SIZEOF(SRAM) - sLinkCardPlayersEnd
	xor a
	rst ByteFill
	jmp CloseSRAM

.EmptyBank:
	call GetSRAMBank
	ld hl, STARTOF(SRAM)
	ld bc, SIZEOF(SRAM)
	xor a
	rst ByteFill
	jmp CloseSRAM

.Text_ClearAllSaveData:
	; Clear all save data?
	text_farend _ClearAllSaveDataText
