; StartMenu.Items indexes
	const_def
	const STARTMENUITEM_POKEDEX  ; 0
	const STARTMENUITEM_POKEMON  ; 1
	const STARTMENUITEM_PACK     ; 2
	const STARTMENUITEM_STATUS   ; 3
	const STARTMENUITEM_SAVE     ; 4
	const STARTMENUITEM_OPTION   ; 5
	const STARTMENUITEM_EXIT     ; 6
	const STARTMENUITEM_POKEGEAR ; 7
	const STARTMENUITEM_QUIT     ; 8
	const STARTMENUITEM_FIELD_BOOK

DEF FIELD_BOOK_MENU_LEFT EQU 7

StartMenu::

	call ClearWindowData
	call BackupSprites

	ld de, SFX_MENU
	call PlaySFX

	farcall ReanchorBGMap_NoOAMUpdate

	ld hl, wStatusFlags2
	bit STATUSFLAGS2_BUG_CONTEST_TIMER_F, [hl]
	ld hl, .ContestMenuDataHeader
	jr nz, .GotMenuData
	ld a, [wLinkMode]
	and a
	ld hl, .MenuDataHeader
	jr nz, .GotMenuData
	ld hl, .FieldBookMenuHeader
.GotMenuData:

	call LoadMenuHeader
	call .SetUpMenuItems
	call ClearSpritesUnderStartMenu
	ld a, [wBattleMenuCursorBuffer]
	ld [wMenuCursorBuffer], a
	call .DrawMenuBox
	call .DrawBugContestStatusBox
	call SafeUpdateSprites
	call BGMapAnchorTopLeft
	farcall LoadFonts_NoOAMUpdate
	call .DrawBugContestStatus
	call UpdateTimePals
	jr .Select

.Reopen:
	call RestoreSprites
	farcall LoadWeatherPal
	call .SetUpMenuItems
	call ClearSpritesUnderStartMenu
	call UpdateSprites
	call UpdateTimePals
	ld a, [wBattleMenuCursorBuffer]
	ld [wMenuCursorBuffer], a

.Select:
	call .GetInput
	jr c, .Exit
	ld a, [wMenuCursorBuffer]
	ld [wBattleMenuCursorBuffer], a
	call PlayClickSFX
	call PlaceHollowCursor
	call .OpenMenu

; Menu items have different return functions.
; For example, saving exits the menu.
	call StackJumpTable

.MenuReturns:
	dw .Reopen
	dw .Exit
	dw .ExitMenuCallFuncCloseText
	dw .ExitMenuRunScriptCloseText
	dw .ExitMenuRunScript
	dw .ReturnEnd
	dw .ReturnRedraw

.Exit:
	ldh a, [hOAMUpdate]
	push af
	ld a, 1
	ldh [hOAMUpdate], a
	call LoadFrame
	call RestoreSprites
	pop af
	ldh [hOAMUpdate], a
.ReturnEnd:
	call ExitMenu
.ReturnEnd2:
	call CloseText
	farcall RefreshFollower ; Link Edition: the lead or the option may have changed
	jmp UpdateTimePals

.GetInput:
; Return carry on exit, and no-carry on selection.
	xor a
	assert NO_BG_MAP_TRANSFER == 0
	ldh [hBGMapMode], a
	call .SetUpMenu
	ld a, $ff
	ld [wMenuSelection], a
.loop
	call ReadMenuJoypad
	ld a, [wMenuJoypad]
	cp PAD_B
	jr z, .b
	cp PAD_A
	jr nz, .loop
.a
	call PlayClickSFX
	and a
	ret
.b
	scf
	ret

.ExitMenuRunScript:
	call ExitMenu
	ld a, HMENURETURN_SCRIPT
	ldh [hMenuReturn], a
	ret

.ExitMenuRunScriptCloseText:
	call ExitMenu
	ld a, HMENURETURN_SCRIPT
	ldh [hMenuReturn], a
	jr .ReturnEnd2

.ExitMenuCallFuncCloseText:
	call ExitMenu
	ld hl, wQueuedScriptBank
	call FarPointerCall
	jr .ReturnEnd2

.ReturnRedraw:
	farcall ClearSavedObjPals
	farcall DisableDynPalUpdates
	call ClearBGPalettes
	call ExitMenu
	call ReloadTilesetAndPalettes
	call .DrawMenuBox
	call .DrawBugContestStatus
	call UpdateSprites
	call FinishExitMenu
	jmp .Reopen

; The book adds a ninth action to a fully unlocked menu. Use one tile
; per row in that layout so the cursor and every action fit on screen.
.DrawMenuBox:
	ld a, [wMenuBorderLeftCoord]
	cp FIELD_BOOK_MENU_LEFT
	jmp nz, DrawVariableLengthMenuBox
	call CopyMenuData2
	call GetMenuIndexSet
	ld a, [wMenuDataItems]
	inc a ; one row per item, then the bottom border
	ld [wMenuBorderBottomCoord], a
	jmp MenuBox

.SetUpMenu:
	ld a, [wMenuBorderLeftCoord]
	cp FIELD_BOOK_MENU_LEFT
	jmp nz, SetUpMenu
	call .DrawMenuBox
	hlcoord FIELD_BOOK_MENU_LEFT + 2, 1
	ld de, wMenuItemsList + 1
.row
	ld a, [de]
	cp -1
	jr z, .cursor
	ld [wMenuSelection], a
	push de
	push hl
	ld d, h
	ld e, l
	call .MenuString
	pop hl
	ld bc, SCREEN_WIDTH
	add hl, bc
	pop de
	inc de
	jr .row
.cursor
	call SafeUpdateSprites
	call ApplyTilemap
	call InitMenuCursorAndButtonPermissions
	ld hl, w2DMenuCursorInitY
	dec [hl] ; the first row sits just inside the top border
	ln a, 1, 0
	ld [w2DMenuCursorOffsets], a
	ld hl, w2DMenuFlags1
	set 7, [hl]
	ret

.FieldBookMenuHeader:
	db MENU_BACKUP_TILES
	menu_coords FIELD_BOOK_MENU_LEFT, 0, 19, 11
	dw .MenuData
	db 1

.MenuDataHeader:
	db MENU_BACKUP_TILES
	menu_coords 10, 0, 19, 17
	dw .MenuData
	db 1 ; default selection

.ContestMenuDataHeader:
	db MENU_BACKUP_TILES
	menu_coords 10, 2, 19, 17
	dw .MenuData
	db 1 ; default selection

.MenuData:
	db %10101000 ; x padding, wrap around, start can close
	dn 0, 0 ; rows, columns
	dw wMenuItemsList
	dw .MenuString
	dw .Items

.Items:
	dw StartMenu_Pokedex,  .PokedexString
	dw StartMenu_Pokemon,  .PartyString
	dw StartMenu_Pack,     .PackString
	dw StartMenu_Status,   .StatusString
	dw StartMenu_Save,     .SaveString
	dw StartMenu_Option,   .OptionString
	dw StartMenu_Exit,     .ExitString
	dw StartMenu_Pokegear, .PokegearString
	dw StartMenu_Quit,     .QuitString
	dw StartMenu_FieldBook, .FieldBookString

.PokedexString:  db "#dex@"
.PartyString:    db "#mon@"
.PackString:     db "Bag@"
.StatusString:   db "<PLAYER>@"
.SaveString:     db "Save@"
.OptionString:   db "Options@"
.ExitString:     db "Exit@"
.PokegearString: db "<PO><KE>gear@"
.QuitString:     db "Quit@"
.FieldBookString: db "Field Book@"

.OpenMenu:
	ld a, [wMenuSelection]
	call .GetMenuItemPointer
	jmp IndirectHL

.MenuString:
	push de
	ld a, [wMenuSelection]
	call .GetMenuItemPointer
	inc hl
	inc hl
	ld a, [hli]
	ld d, [hl]
	ld e, a
	pop hl
	rst PlaceString
	ret

.GetMenuItemPointer:
	ld e, a
	ld d, 0
	ld hl, wMenuDataPointerTableAddr
	ld a, [hli]
	ld h, [hl]
	ld l, a
rept 4
	add hl, de
endr
	ret

.SetUpMenuItems:
	xor a
	ld [wWhichIndexSet], a
	call .FillMenuList

	ld hl, wStatusFlags
	bit 0, [hl]
	jr z, .no_pokedex
	xor a ; STARTMENUITEM_POKEDEX
	call .AppendMenuList
.no_pokedex

	ld a, [wPartyCount]
	and a
	jr z, .no_pokemon
	ld a, STARTMENUITEM_POKEMON
	call .AppendMenuList
.no_pokemon

	ld a, [wLinkMode]
	and a
	jr nz, .no_pack
	ld hl, wStatusFlags2
	bit STATUSFLAGS2_BUG_CONTEST_TIMER_F, [hl]
	jr nz, .no_pack
	ld a, STARTMENUITEM_PACK
	call .AppendMenuList
.no_pack

	ld hl, wPokegearFlags
	bit POKEGEAR_OBTAINED_F, [hl]
	jr z, .no_pokegear
	ld a, STARTMENUITEM_POKEGEAR
	call .AppendMenuList
.no_pokegear

	ld a, [wMenuBorderLeftCoord]
	cp FIELD_BOOK_MENU_LEFT
	jr nz, .no_book
	ld a, STARTMENUITEM_FIELD_BOOK
	call .AppendMenuList
.no_book
	ld a, STARTMENUITEM_STATUS
	call .AppendMenuList

	call SavingAllowed
	ld a, STARTMENUITEM_QUIT ; for bug catching contest
	jr c, .write
	ld a, STARTMENUITEM_SAVE
	jr nz, .no_save
.write
	call .AppendMenuList
.no_save

	ld a, STARTMENUITEM_OPTION
	call .AppendMenuList
	; Exit only if there's room (B and Start close the menu too)
	ld a, c
	cp 8
	jr nc, .no_exit
	ld a, STARTMENUITEM_EXIT
	call .AppendMenuList
.no_exit
	ld a, c
	ld [wMenuItemsList], a
	ret

.FillMenuList:
	xor a
	ld hl, wMenuItemsList
	ld [hli], a
	ld a, -1
	ld bc, wMenuItemsListEnd - (wMenuItemsList + 1)
	rst ByteFill
	ld de, wMenuItemsList + 1
	ld c, 0
	ret

.AppendMenuList:
	ld [de], a
	inc de
	inc c
	ret

.DrawBugContestStatusBox:
	ld hl, wStatusFlags2
	bit STATUSFLAGS2_BUG_CONTEST_TIMER_F, [hl]
	ret z
	farjp StartMenu_DrawBugContestStatusBox

.DrawBugContestStatus:
	ld hl, wStatusFlags2
	bit STATUSFLAGS2_BUG_CONTEST_TIMER_F, [hl]
	ret z
	farjp StartMenu_PrintBugContestStatus

SavingAllowed:
; Checks if we are allowed to save. Returns z if we can. Also returns carry
; if we're in the Bug Catching Contest, because in that case we want a different
; menu option instead.
	ld a, [wLinkMode]
	and a
	ret nz
	ld a, [wStatusFlags2]
	bit STATUSFLAGS2_BUG_CONTEST_TIMER_F, a
	scf
	ret nz
	xor a
	ret

StartMenu_FieldBook:
	ld a, BANK(ReadFieldBook)
	ld hl, ReadFieldBook
	call FarQueueScript
	ld a, 3 ; close the Start menu and run the book's map script
	ret

StartMenu_Exit:
	ld a, 1
	ret

StartMenu_Quit:
	ld hl, .EndTheContestText
	call StartMenuYesNo
	jr c, .DontEndContest
	ld a, BANK(BugCatchingContestReturnToGateScript)
	ld hl, BugCatchingContestReturnToGateScript
	call FarQueueScript
	ld a, 4
	ret

.DontEndContest:
	xor a
	ret

.EndTheContestText:
	text_farend _StartMenuContestEndText
StartMenu_Save:
	call ClearSprites
	call BufferScreen
	farcall SaveMenu
	jr nc, .saved
	xor a
	ret

.saved
	ld a, 1
	ret

StartMenu_Option:
	call FadeToMenu
	farcall OptionsMenu
	ld a, 6
	ret

StartMenu_Status:
	call FadeToMenu
	farcall TrainerCard
	call CloseSubmenu
	xor a
	ret

StartMenu_Pokedex:
	ld a, [wPartyCount]
	and a
	jr z, .empty
	call FadeToMenu
	farcall Pokedex
	call CloseSubmenu
.empty
	xor a
	ret

StartMenu_Pokegear:
	call FadeToMenu
	farcall InitPokegearPalettes
	farcall PokeGear
	ld a, [wDefaultSpawnpoint]
	and a
	jr nz, _ExitStartMenuAndDoScript
	call CloseSubmenu
	call ApplyTilemapInVBlank
	call SetDefaultBGPAndOBP
	call DelayFrame
	xor a
	ret

StartMenu_Pack:
	call FadeToMenu
	call Pack
	ld a, [wPackUsedItem]
	and a
	jr nz, _ExitStartMenuAndDoScript
	call CloseSubmenu
	xor a
	ret

_ExitStartMenuAndDoScript:
	call ExitAllMenus
	ld a, 4
	ret

StartMenu_Pokemon:
	ld a, [wPartyCount]
	and a
	jr z, .return
	call FadeToMenu
.choosemenu
	xor a ; PARTYMENUACTION_CHOOSE_POKEMON
	ld [wPartyMenuActionText], a
	call ClearBGPalettes
.menu
	farcall LoadPartyMenuGFX
	farcall InitPartyMenuWithCancel
	farcall InitPartyMenuGFX
.menunoreload
	ld a, PAD_A | PAD_B | PAD_SELECT
	ld [wMenuJoypadFilter], a
	farcall WritePartyMenuTilemap
	farcall PlacePartyMenuText
	call ApplyTilemapInVBlank
	call SetDefaultBGPAndOBP ; load regular palettes?
	call DelayFrame
	farcall PartyMenuSelect
	jr c, .return ; if cancelled or pressed B
	ldh a, [hJoyLast]
	and PAD_SELECT
	jr z, .not_switch
	call SwitchPartyMons
	jr .after_action
.not_switch
	call PokemonActionSubmenu
.after_action
	push af
	call SFXDelay2
	pop af
	and a ; 0?
	jr z, .choosemenu
	dec a ; 1?
	jr z, .menunoreload
	dec a ; 2?
	jr z, .quit
	dec a ; 3?
	jr z, .menu
.return
	call CloseSubmenu
	xor a
	ret

.quit
	ld a, b
	push af
	call ExitAllMenus
	pop af
	ret

ClearSpritesUnderStartMenu:
	ld b, 10 * TILE_WIDTH
	ld a, [wMenuBorderLeftCoord]
	cp FIELD_BOOK_MENU_LEFT
	ld a, $ff ; the original layout covers the full height
	jr nz, .bounds
	ld b, FIELD_BOOK_MENU_LEFT * TILE_WIDTH
	ld a, [wMenuItemsList]
	add 2 ; top and bottom borders
	add a
	add a
	add a
	add 16 ; OAM Y coordinates start 16 pixels above the visible screen
.bounds
	ld h, a
	ld de, wShadowOAMSprite00XCoord
	ld c, OAM_COUNT
.loop
	; Hide sprites underneath the chosen menu.
	ld a, [de]
	cp b
	jr nc, .clear_sprite
; fallthrough
.next
	ld a, e
	add OBJ_SIZE
	ld e, a
	dec c
	jr nz, .loop
	ldh a, [hOAMUpdate]
	push af
	ld a, TRUE
	ldh [hOAMUpdate], a
	call DelayFrame
	pop af
	ldh [hOAMUpdate], a
	ret

.clear_sprite
	dec e
	ld a, [de]
	cp h
	jr nc, .keep
	ld a, OAM_YCOORD_HIDDEN
	ld [de], a
.keep
	inc e
	jr .next
