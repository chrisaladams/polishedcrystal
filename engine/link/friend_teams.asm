; Link Edition: Friend Battles. After a link battle with your own teams (any
; format but Random, whose teams are generated), your friend's team is kept
; on the cartridge (sFriendTeam1 and sFriendTeam2, keyed by their name and
; ID as on the Trainer Card), and updated each time you battle them again.
; The Cable Club's third receptionist lets you battle a kept team offline,
; under the rules it was kept with, look it over, or remove it; removing a
; team leaves your link records alone. Nothing new is exchanged over the
; cable: the team is the one the battle already received.

GetFriendTeam:
; hl = friend team a's record (SRAM bank 0).
	ld hl, sFriendTeam1
	and a
	ret z
	ld hl, sFriendTeam2
	ret

CheckFriendTeam:
; Carry if friend team a holds a team (SRAM open): marked, checked, and every
; field one the game can use. Anything else counts as an empty slot.
	call GetFriendTeam
	push hl
	ld a, [hli]
	cp FRIEND_TEAM_MAGIC_1
	jr nz, .no
	ld a, [hli]
	cp FRIEND_TEAM_MAGIC_2
	jr nz, .no
	ld c, [hl]
	inc hl
	call FriendTeamSum
	cp c
	jr nz, .no
	pop hl
	jr CheckFriendTeamFields
.no
	pop hl
	and a
	ret

CheckFriendTeamFields:
; Carry if the record at hl has usable values: kept rules (not Random), a
; player gender, one to six Pokemon (three for Rising Star), and for each a
; species, no egg, an item, moves (the first one set) and a nature.
	push hl
	ld de, FRIEND_TEAM_RULE
	add hl, de
	ld a, [hli]
	cp NUM_LINK_BATTLE_RULES
	jr nc, .bad
	cp LINK_RULE_RANDOM
	jr z, .bad
	ld b, a
	assert FRIEND_TEAM_GENDER == FRIEND_TEAM_RULE + 1
	ld a, [hl]
	cp NUM_PLAYER_GENDERS
	jr nc, .bad
	pop hl
	push hl
	ld de, FRIEND_TEAM_COUNT
	add hl, de
	ld a, [hli]
	and a
	jr z, .bad
	cp PARTY_LENGTH + 1
	jr nc, .bad
	ld c, a
	ld a, b
	cp LINK_RULE_RISING_STAR
	jr nz, .mon
	ld a, c
	cp 3
	jr nz, .bad
.mon
	call .Mon
	jr c, .bad
	dec c
	jr nz, .mon
	pop hl
	scf
	ret
.bad
	pop hl
	and a
	ret

.Mon:
; Carry if the packed Pokemon at hl isn't usable; else hl = the next.
	assert HIGH(NUM_SPECIES) == 1 && NUM_ITEMS < $ff && NUM_ATTACKS <= $ff
	push hl
	ld a, [hli] ; species: 1-$fe ($00 and $ff aren't species)
	ld b, a
	and a
	jr z, .mon_bad
	inc a
	jr z, .mon_bad
	ld a, [hli] ; form
	assert FRIENDMON_FORM == FRIENDMON_SPECIES + 1
	bit MON_IS_EGG_F, a
	jr nz, .mon_bad
	and EXTSPECIES_MASK
	jr z, .species_ok
	ld a, b ; (an extended species: up to NUM_SPECIES)
	cp LOW(NUM_SPECIES) + 1
	jr nc, .mon_bad
.species_ok
	ld a, [hli] ; item
	assert FRIENDMON_ITEM == FRIENDMON_FORM + 1
	cp NUM_ITEMS + 1
	jr nc, .mon_bad
	ld a, [hli] ; moves: the first one set
	assert FRIENDMON_MOVES == FRIENDMON_ITEM + 1
	and a
	jr z, .mon_bad
if NUM_ATTACKS < $ff ; (with $ff moves, every byte is one, or none)
	cp NUM_ATTACKS + 1
	jr nc, .mon_bad
	ld b, NUM_MOVES - 1
.moves
	ld a, [hli]
	cp NUM_ATTACKS + 1
	jr nc, .mon_bad
	dec b
	jr nz, .moves
else
	inc hl
	inc hl
	inc hl
endc
	assert FRIENDMON_PERSONALITY == FRIENDMON_MOVES + NUM_MOVES + 1 + 3
	inc hl ; PP Ups
	inc hl ; DVs
	inc hl
	inc hl
	ld a, [hl] ; personality: a nature
	and NATURE_MASK
	cp NUM_NATURES
	jr nc, .mon_bad
	pop hl
	ld de, FRIENDMON_LENGTH
	add hl, de
	and a
	ret
.mon_bad
	pop hl
	scf
	ret

FriendTeamSum:
; a = the checksum of the record from hl (its rule onwards).
	assert FRIEND_TEAM_CHECKSUM + 1 == FRIEND_TEAM_RULE
	ld de, FRIEND_TEAM_LENGTH - FRIEND_TEAM_RULE
	ld b, FRIEND_TEAM_MAGIC_1
.loop
	ld a, [hli]
	add b
	ld b, a
	dec de
	ld a, d
	or e
	jr nz, .loop
	ld a, b
	ret

FriendTeamIsOpponent:
; Carry if friend team a is the link opponent's (wOTPlayerID, wOTPlayerName).
	push af
	call CheckFriendTeam
	pop bc
	ret nc
	ld a, b
	call GetFriendTeam
	ld de, FRIEND_TEAM_ID
	add hl, de
	ld de, wOTPlayerID
	ld c, 2 + PLAYER_NAME_LENGTH
	assert FRIEND_TEAM_NAME == FRIEND_TEAM_ID + 2
.compare
	ld a, [de]
	cp [hl]
	jr nz, .different
	inc hl
	inc de
	dec c
	jr z, .same
	ld a, c
	cp PLAYER_NAME_LENGTH
	jr nz, .compare
	ld de, wOTPlayerName
	jr .compare
.same
	scf
	ret
.different
	and a
	ret

KeepFriendTeam::
; After a link battle: keep the opponent's team, in the slot already theirs,
; else an empty one (if both hold other friends' teams, it isn't kept).
	ld a, [wLinkBattleRules]
	cp LINK_RULE_RANDOM
	ret z
	ld a, BANK(sFriendTeam1)
	call GetSRAMBank
	xor a
	call FriendTeamIsOpponent
	ld a, 0
	jr c, .keep
	inc a
	call FriendTeamIsOpponent
	ld a, 1
	jr c, .keep
	xor a
	call CheckFriendTeam
	ld a, 0
	jr nc, .keep
	inc a
	call CheckFriendTeam
	ld a, 1
	jmp c, CloseSRAM
.keep
	; The marker goes first and comes back last: if the power goes while the
	; record is being written, the slot reads as empty (that friend's team is
	; lost), never as a team with the wrong data.
	call GetFriendTeam
	push hl
	xor a
	ld [hli], a
	ld [hli], a
	inc hl ; checksum, below
	ld a, [wLinkBattleRules]
	ld [hli], a
	ld a, [wLinkOtherPlayerGender]
	ld [hli], a
	ld a, [wOTPlayerID]
	ld [hli], a
	ld a, [wOTPlayerID + 1]
	ld [hli], a
	ld d, h
	ld e, l
	ld hl, wOTPlayerName
	ld bc, PLAYER_NAME_LENGTH
	rst CopyBytes
	ld h, d
	ld l, e
	push hl ; the count, below
	inc hl
	ld b, 0 ; kept
	ld c, 0 ; party index
.mon
	ld a, [wOTPartyCount]
	cp c
	jr z, .kept
	push bc
	push hl
	ld a, c
	ld hl, wOTPartyMon1
	call GetPartyLocation
	ld d, h
	ld e, l
	pop hl
	ld a, MON_IS_EGG
	call .Field
	bit MON_IS_EGG_F, a
	jr nz, .skip
	call PackFriendMon
	pop bc
	inc b
	jr .next
.skip
	pop bc
.next
	inc c
	jr .mon
.kept
	pop hl
	ld [hl], b ; count
	pop hl
	push hl
	ld de, FRIEND_TEAM_RULE
	add hl, de
	call FriendTeamSum
	pop hl
	push hl
	inc hl
	inc hl
	ld [hl], a ; checksum
	pop hl
	inc hl
	ld [hl], FRIEND_TEAM_MAGIC_2
	dec hl
	ld [hl], FRIEND_TEAM_MAGIC_1 ; (last: the record is whole)
	jmp CloseSRAM

.Field:
; a = field a of the party struct at de.
	push hl
	ld h, d
	ld l, e
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, [hl]
	pop hl
	ret

PackFriendMon:
; Pack the party struct at de (OT party member c) into hl; hl = after it.
	ld a, c
	push af
	ld a, MON_SPECIES
	call .Copy1
	ld a, MON_FORM
	call .Copy1
	ld a, MON_ITEM
	call .Copy1
	ld a, MON_MOVES
	ld b, NUM_MOVES
	call .CopyN
	; the PP Ups, two bits a move (the first move's highest)
	push hl
	ld hl, MON_PP
	add hl, de
	lb bc, NUM_MOVES, 0
.ppups
	ld a, [hli]
	and PP_UP_MASK
	srl c
	srl c
	or c
	ld c, a
	dec b
	jr nz, .ppups
	pop hl
	ld [hl], c
	inc hl
	ld a, MON_DVS
	ld b, 3
	call .CopyN
	ld a, MON_PERSONALITY
	call .Copy1
	ld a, MON_EVS
	ld b, NUM_STATS
	call .CopyN
	ld a, MON_HAPPINESS
	call .Copy1
	; hyper training (in the first of the OT's three extra bytes, with two
	; bits that aren't)
	pop af
	push hl
	ld hl, wOTPartyMonOTs + PLAYER_NAME_LENGTH
	ld bc, PLAYER_NAME_LENGTH + 3
	rst AddNTimes
	ld a, [hl]
	and HYPER_TRAINING_MASK
	pop hl
	ld [hli], a
	ret

.Copy1:
	ld b, 1
.CopyN:
	push de
	add e
	ld e, a
	adc d
	sub e
	ld d, a
.copy
	ld a, [de]
	ld [hli], a
	inc de
	dec b
	jr nz, .copy
	pop de
	ret

LoadFriendTeam::
; The trainer party for a Friend Battle: friend team wFriendBattleSlot - 1,
; at the level CupBegin set (wCupLevel), as the battle received it.
	ld a, BANK(sFriendTeam1)
	call GetSRAMBank
	ld a, [wFriendBattleSlot]
	dec a
	call GetFriendTeam
	ld de, FRIEND_TEAM_NAME
	add hl, de
	ld de, wOTPlayerName
	ld bc, PLAYER_NAME_LENGTH
	rst CopyBytes
	ld a, '@'
	ld [de], a
	ld a, [hli] ; count
	ld b, a
	xor a
	ld [wOTPartyCount], a
	ld a, OTPARTYMON
	ld [wMonType], a
.mon
	push bc
	push hl
	call UnpackFriendMon
	pop hl
	ld bc, FRIENDMON_LENGTH
	add hl, bc
	pop bc
	dec b
	jr nz, .mon
	jmp CloseSRAM

UnpackFriendMon:
; Add the packed Pokemon at hl to wOTParty.
	ld a, [wOTPartyCount]
	ld [wCurPartyMon], a
	inc a
	ld [wOTPartyCount], a
	push hl
	ld a, [wCurPartyMon]
	ld hl, wOTPartyMon1
	call GetPartyLocation
	ld d, h
	ld e, l
	pop hl
	; species, form, item, moves
	ld a, [hli]
	ld [de], a ; MON_SPECIES
	ld [wCurSpecies], a
	ld [wNamedObjectIndex], a
	ld a, [hli]
	ld c, a ; form
	ld a, MON_FORM
	call .Put
	ld a, c
	and SPECIESFORM_MASK
	ld [wCurForm], a
	ld [wNamedObjectIndex + 1], a
	ld a, [hli]
	ld c, a
	ld a, MON_ITEM
	call .Put
	push de
	ld a, e
	add MON_MOVES
	ld e, a
	adc d
	sub e
	ld d, a
	ld bc, NUM_MOVES
	rst CopyBytes
	pop de
	; PP Ups, then full PP (_RestoreAllPP keeps them)
	ld a, [hli]
	push hl
	ld hl, MON_PP
	add hl, de
	ld b, NUM_MOVES
.ppups
	ld c, a
	and PP_UP_MASK
	ld [hli], a
	ld a, c
	add a
	add a
	dec b
	jr nz, .ppups
	pop hl
	; DVs, personality, EVs, happiness
	ld a, MON_DVS
	ld b, 3
	call .PutN
	ld a, MON_PERSONALITY
	ld b, 1
	call .PutN
	ld a, MON_EVS
	ld b, NUM_STATS
	call .PutN
	ld a, MON_HAPPINESS
	ld b, 1
	call .PutN
	ld a, [hl] ; hyper training (only those bits: GetHyperTraining's)
	and HYPER_TRAINING_MASK
	push af
	; the ID, level and no status
	ld a, [wOTPlayerID]
	ld c, a
	ld a, MON_ID
	call .Put
	ld a, [wOTPlayerID + 1]
	ld c, a
	ld a, MON_ID + 1
	call .Put
	ld a, [wCupLevel]
	and a
	jr nz, .level
	ld a, LINK_BATTLE_FORCED_LEVEL
.level
	ld [wCurPartyLevel], a
	ld c, a
	ld a, MON_LEVEL
	call .Put
	; its name, and its trainer's
	push de
	call GetPokemonName
	ld a, [wCurPartyMon]
	ld hl, wOTPartyMonNicknames
	call SkipNames
	ld d, h
	ld e, l
	ld hl, wStringBuffer1
	ld bc, MON_NAME_LENGTH
	rst CopyBytes
	ld a, [wCurPartyMon]
	ld hl, wOTPartyMonOTs
	ld bc, PLAYER_NAME_LENGTH + 3
	rst AddNTimes
	ld d, h
	ld e, l
	ld hl, wOTPlayerName
	ld bc, PLAYER_NAME_LENGTH
	rst CopyBytes
	pop hl ; the struct
	pop af ; hyper training
	ld [de], a ; (the OT's first extra byte follows its name)
	ld d, h
	ld e, l
	; full PP
	push de
	push af
	ld hl, MON_PP
	add hl, de
	push hl
	ld hl, MON_MOVES
	add hl, de
	pop de
	farcall _RestoreAllPP
	pop af
	pop de
	; stats, at full HP
	inc a
	ld b, a
	push de
	push bc
	call GetBaseData
	pop bc
	pop de
	push de
	ld hl, MON_MAXHP
	add hl, de
	push hl
	ld hl, MON_EVS - 1
	add hl, de
	pop de
	push de
	farcall CalcPkmnStats
	pop hl
	ld a, [hli]
	ld b, a
	ld c, [hl]
	pop de
	ld hl, MON_HP
	add hl, de
	ld a, b
	ld [hli], a
	ld [hl], c
	ret

.Put:
; Field a of the struct at de = c.
	push hl
	ld h, d
	ld l, e
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld [hl], c
	pop hl
	ret

.PutN:
; Copy b bytes from hl to field a of the struct at de; hl = after them.
	push de
	add e
	ld e, a
	adc d
	sub e
	ld d, a
.put
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .put
	pop de
	ret

FriendDeskFirst::
; wFriendTeamSlot = the first friend team kept, its trainer named in
; wStringBuffer3; hScriptVar = FALSE if there are none.
	xor a
	ld [wFriendTeamSlot], a
	call FriendDeskFind
	ret c
	ld a, 1
	ld [wFriendTeamSlot], a
	jr FriendDeskFind

FriendDeskNext::
; The other friend team, if there is one.
	ld a, [wFriendTeamSlot]
	push af
	xor 1
	ld [wFriendTeamSlot], a
	call FriendDeskFind
	pop bc
	ret c
	ld a, b
	ld [wFriendTeamSlot], a
	; fallthrough
FriendDeskFind:
; Carry and hScriptVar = TRUE if wFriendTeamSlot holds a team; name it.
	ld a, BANK(sFriendTeam1)
	call GetSRAMBank
	ld a, [wFriendTeamSlot]
	call CheckFriendTeam
	ld a, FALSE
	jr nc, .done
	ld a, [wFriendTeamSlot]
	call GetFriendTeam
	ld de, FRIEND_TEAM_NAME
	add hl, de
	ld de, wStringBuffer3
	ld bc, PLAYER_NAME_LENGTH
	rst CopyBytes
	ld a, '@'
	ld [de], a
	ld a, TRUE
	scf
.done
	ldh [hScriptVar], a
	jmp CloseSRAM

FriendDeskRemove::
	ld a, BANK(sFriendTeam1)
	call GetSRAMBank
	ld a, [wFriendTeamSlot]
	call GetFriendTeam
	xor a
	ld [hli], a
	ld [hl], a
	jmp CloseSRAM

FriendDeskArm::
; Ready a Friend Battle against wFriendTeamSlot: hScriptVar = its rule's cup
; for CupSelectTeam (wCupId), and the trainer, as loadtrainer would.
	ld a, BANK(sFriendTeam1)
	call GetSRAMBank
	ld a, [wFriendTeamSlot]
	call GetFriendTeam
	ld de, FRIEND_TEAM_RULE
	add hl, de
	ld a, [hli]
	cp LINK_RULE_RISING_STAR
	ld b, CUP_FRIEND_RISING_STAR
	jr z, .cup
	ld b, CUP_FRIEND
.cup
	ld a, b
	ld [wCupId], a
	ld a, [hli] ; gender
	assert FRIEND_TEAM_GENDER == FRIEND_TEAM_RULE + 1
	assert PLAYER_MALE + 1 == CAL
	inc a
	ld [wOtherTrainerClass], a
	ld a, [hli]
	ld [wOTPlayerID], a
	ld a, [hli]
	ld [wOTPlayerID + 1], a
	assert FRIEND_TEAM_NAME == FRIEND_TEAM_ID + 2
	ld de, wOTPlayerName
	ld bc, PLAYER_NAME_LENGTH
	rst CopyBytes
	ld a, '@'
	ld [de], a
	call CloseSRAM
	ld a, 1
	ld [wOtherTrainerID], a
	ld a, (1 << 7) | 1
	ld [wBattleScriptFlags], a
	xor a ; TRAINERPAL_NONE
	ld [wTrainerPal], a
	ld a, [wFriendTeamSlot]
	inc a
	ld [wFriendBattleSlot], a
	ret

FriendDeskDone::
; After the battle (leaves hScriptVar, the battle's result, alone).
	xor a
	ld [wFriendBattleSlot], a
	ret

Special_FriendTeamPreview::
	call FadeToMenu_BackupSprites
	call .Show
	jmp ExitAllMenus

.Show:
	call ClearTileMap
	call ClearSprites
	call LoadStandardFont
	call LoadFrame
	hlcoord 0, 0
	lb bc, SCREEN_HEIGHT - 2, SCREEN_WIDTH - 2
	call Textbox
	ld a, BANK(sFriendTeam1)
	call GetSRAMBank
	ld a, [wFriendTeamSlot]
	call GetFriendTeam
	push hl
	ld de, FRIEND_TEAM_NAME
	add hl, de
	ld de, wStringBuffer3
	ld bc, PLAYER_NAME_LENGTH
	rst CopyBytes
	ld a, '@'
	ld [de], a
	pop hl
	push hl
	ld de, FRIEND_TEAM_RULE
	add hl, de
	ld a, [hl]
	ld hl, .Rules
	add a
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, [hli]
	ld e, a
	ld d, [hl]
	hlcoord 2, 3
	rst PlaceString
	ld de, wStringBuffer3
	hlcoord 2, 1
	rst PlaceString
	ld de, .Team
	ld h, b
	ld l, c
	rst PlaceString
	pop hl
	ld de, FRIEND_TEAM_COUNT
	add hl, de
	ld a, [hli]
	ld b, a
	decoord 3, 5
.mon
	push bc
	push de
	ld a, [hli]
	ld [wNamedObjectIndex], a
	ld a, [hld]
	ld [wNamedObjectIndex + 1], a
	ld bc, FRIENDMON_LENGTH
	add hl, bc
	pop de
	push hl
	push de
	call GetPokemonName
	pop hl
	push hl
	ld de, wStringBuffer1
	rst PlaceString
	pop hl
	ld bc, SCREEN_WIDTH * 2
	add hl, bc
	ld d, h
	ld e, l
	pop hl
	pop bc
	dec b
	jr nz, .mon
	call CloseSRAM
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
	jmp WaitPressAorB_BlinkCursor

.Team:
	db "'s team@"
.Rules:
	table_width 2
	dw .Standard, .Random, .RisingStar, .Unrestricted, .World
	assert_table_length NUM_LINK_BATTLE_RULES
.Standard:     db "Standard, Lv.50@"
.Random:       db "Random, Lv.50@"
.RisingStar:   db "Rising Star, Lv.30@"
.Unrestricted: db "Unrestricted, Lv.50@"
.World:        db "Championship, Lv.50@"
