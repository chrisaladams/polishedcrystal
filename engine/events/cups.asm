; Link Edition: regional cups. A cup's script calls these with callasm:
; CupSelectTeam (with wCupId set), then CupBegin, its battles (losable, at
; the cup's level), CupHealTeam between them, CupEnd, and CupWin for a win.
; Your party is kept aside in WRAMX bank 2 meanwhile and comes back exactly
; as it was (then healed); the battles give no experience and allow no
; items (wCupLevel).

CupRules:
; level, fewest, most, how they're chosen, rule, type
	db 30, 3, 3, CUPPICK_THREE, CUPRULE_ANY,      0     ; CUP_RISING_STAR
	db 50, 3, 6, CUPPICK_PARTY, CUPRULE_ALL_TYPE, WATER ; CUP_WHIRL
	db 50, 3, 3, CUPPICK_THREE, CUPRULE_ALL_TYPE, CUPTYPE_SCRIPTED ; CUP_KIMONO
	db 50, 3, 6, CUPPICK_PARTY, CUPRULE_HAS_TYPE, DRAGON ; CUP_DRAGON
	db 50, RENTAL_CUP_TEAM_SIZE, RENTAL_CUP_TEAM_SIZE, CUPPICK_GENERATED, CUPRULE_ANY, 0 ; CUP_RENTAL
	db 50, PARTY_LENGTH, PARTY_LENGTH, CUPPICK_PARTY, CUPRULE_ANY, 0 ; CUP_WORLD
	db 50, 1, 1, CUPPICK_SMALL, CUPRULE_ALL_TYPE, CUPTYPE_SCRIPTED ; CUP_RUDY
	db 50, 2, 2, CUPPICK_SMALL, CUPRULE_ANY, 0 ; CUP_LUANA
	db LINK_BATTLE_FORCED_LEVEL, 1, PARTY_LENGTH, CUPPICK_PARTY, CUPRULE_ANY, 0 ; CUP_FRIEND
	db 30, 3, 3, CUPPICK_THREE, CUPRULE_ANY, 0 ; CUP_FRIEND_RISING_STAR
	db CUP_OWN_LEVELS, 1, PARTY_LENGTH, CUPPICK_PARTY, CUPRULE_ANY, 0 ; CUP_FRIEND_UNRESTRICTED
.End:
	rsreset
DEF CUPRULE_LEVEL rb
DEF CUPRULE_FEWEST rb
DEF CUPRULE_MOST rb
DEF CUPRULE_PICK rb
DEF CUPRULE_RULE rb
DEF CUPRULE_TYPE rb
DEF CUP_RULES_LENGTH EQU _RS
	assert CupRules.End - CupRules == NUM_CUPS * CUP_RULES_LENGTH

CupRecordMasks:
; the wCupRecords bit for each cup's first win (0: kept elsewhere)
	db 1 << CUPWON_RISING_STAR_F ; CUP_RISING_STAR
	db 0                         ; CUP_WHIRL (EVENT_WON_WHIRL_CUP)
	db 0                         ; CUP_KIMONO (a bit for each type)
	db 1 << CUPWON_DRAGON_F      ; CUP_DRAGON
	db 1 << CUPWON_RENTAL_F      ; CUP_RENTAL
	db 1 << CUPWON_WORLD_F       ; CUP_WORLD
	db 0                         ; CUP_RUDY (Orange Crew badge)
	db 0                         ; CUP_LUANA (Orange Crew badge)
	db 0 ; CUP_FRIEND
	db 0 ; CUP_FRIEND_RISING_STAR
	db 0 ; CUP_FRIEND_UNRESTRICTED
.End:
	assert CupRecordMasks.End - CupRecordMasks == NUM_CUPS

GetCupRules:
; hl = cup wCupId's CupRules entry + c. Keeps de.
	ld a, [wCupId]
	ld b, 0
	ld hl, CupRules
	add hl, bc
	ld bc, CUP_RULES_LENGTH
	rst AddNTimes
	ret

CupSelectTeam::
; Choose the team for cup wCupId and check it against the rules: hScriptVar
; = CUPTEAM_*. The team is left in wOTParty, in order, for CupBegin.
	ld c, CUPRULE_PICK
	call GetCupRules
	ld a, [hl]
	cp CUPPICK_GENERATED
	jmp z, .rentals
	cp CUPPICK_SMALL
	jmp z, .small_team
	cp CUPPICK_THREE
	jr nz, .whole_party
	; three, in the Battle Tower's party menu (no eggs or banned Pokemon,
	; nor two of a species or two holding the same item)
	xor a
	ld [wBT_PartySelectCounter], a
	farcall BT_PartySelect
	ld a, CUPTEAM_CANCEL
	jr c, .done
	jr .stage

.whole_party
	; every Pokemon but eggs, in party order
	xor a
	ld [wBT_PartySelectCounter], a
	ld a, [wPartyCount]
	and a
	jr z, .stage
	ld b, a
	ld c, 0
	ld hl, wPartyMon1IsEgg
.party_loop
	bit MON_IS_EGG_F, [hl]
	jr nz, .egg
	push hl
	ld a, [wBT_PartySelectCounter]
	ld e, a
	ld d, 0
	ld hl, wBT_PartySelections
	add hl, de
	ld [hl], c
	inc a
	ld [wBT_PartySelectCounter], a
	pop hl
.egg
	push bc
	ld bc, PARTYMON_STRUCT_LENGTH
	add hl, bc
	pop bc
	inc c
	dec b
	jr nz, .party_loop

.stage
	call CupStageTeam
	; how many
	ld c, CUPRULE_FEWEST
	call GetCupRules
	ld a, [wOTPartyCount]
	cp [hl]
	ld a, CUPTEAM_SIZE
	jr c, .done
	inc hl
	assert CUPRULE_MOST == CUPRULE_FEWEST + 1
	ld a, [hl]
	ld b, a
	ld a, [wOTPartyCount]
	dec a
	cp b
	ld a, CUPTEAM_SIZE
	jr nc, .done
	; and of what type
	ld c, CUPRULE_RULE
	call GetCupRules
	ld a, [hli]
	assert CUPRULE_TYPE == CUPRULE_RULE + 1
	and a
	assert CUPRULE_ANY == 0
	jr z, .ok
	push af
	ld a, [hl]
	cp CUPTYPE_SCRIPTED
	jr nz, .got_type
	ld a, [wCupFoeType]
.got_type
	ld d, a
	call CupCountType ; e = how many have it
	pop af
	cp CUPRULE_HAS_TYPE
	jr z, .has_type
	; every one
	ld a, [wOTPartyCount]
	cp e
	ld a, CUPTEAM_TYPE
	jr nz, .done
	jr .ok

.has_type
	ld a, e
	and a
	ld a, CUPTEAM_TYPE
	jr z, .done
.ok
	call CupFriendRules
	jr c, .done
	ld a, CUPTEAM_OK
.done
	ldh [hScriptVar], a
	ret

.rentals
	lb bc, RENTAL_CUP_TEAM_SIZE, CUPTYPE_ANY
	farcall CupMakeTeam
	ld a, CUPTEAM_OK
	jr .done

.small_team
	xor a
	ld [wBT_PartySelectCounter], a
.pick
	farcall SelectMonFromParty
	ld a, CUPTEAM_CANCEL
	jr c, .done
	ld a, MON_IS_EGG
	call GetPartyParamLocationAndValue
	bit MON_IS_EGG_F, a
	ld a, CUPTEAM_EGG
	jr nz, .done
	ld hl, wBT_PartySelections
	ld a, [wBT_PartySelectCounter]
	and a
	ld a, [wCurPartyMon]
	jr z, .store_pick
	cp [hl]
	ld a, CUPTEAM_DUPLICATE
	jr z, .done
	ld a, [wCurPartyMon]
	inc hl
.store_pick
	ld [hl], a
	ld hl, wBT_PartySelectCounter
	inc [hl]
	ld c, CUPRULE_MOST
	call GetCupRules
	ld a, [wBT_PartySelectCounter]
	cp [hl]
	jr nc, .picked
	ld hl, .PartnerText
	call PrintText
	jr .pick
.picked
	jmp .stage

.PartnerText:
	text "Now choose your"
	line "second #mon."
	prompt

CupStageTeam:
; Copy the chosen Pokemon (wBT_PartySelections) to wOTParty, in order.
	ld a, [wBT_PartySelectCounter]
	ld [wOTPartyCount], a
	and a
	ret z
	ld c, 0
.loop
	ld hl, wBT_PartySelections
	ld b, 0
	add hl, bc
	ld b, [hl] ; which of yours
	ld hl, wPartyMons
	ld de, wOTPartyMons
	ld a, PARTYMON_STRUCT_LENGTH
	call .Entry
	ld hl, wPartyMonNicknames
	ld de, wOTPartyMonNicknames
	ld a, MON_NAME_LENGTH
	call .Entry
	ld hl, wPartyMonOTs
	ld de, wOTPartyMonOTs
	ld a, NAME_LENGTH
	call .Entry
	inc c
	ld a, [wBT_PartySelectCounter]
	cp c
	jr nz, .loop
	ret

.Entry:
; Copy entry b of table hl to entry c of table de, a bytes each. Keeps bc.
	push bc
	push de
	push af
	ld e, a
	ld d, 0
	ld a, b
	call .Times
	pop af
	pop de
	push hl
	push af
	ld h, d
	ld l, e
	ld e, a
	ld d, 0
	ld a, c
	call .Times
	ld d, h
	ld e, l
	pop af
	pop hl
	ld c, a
	ld b, 0
	rst CopyBytes
	pop bc
	ret

.Times:
; hl += a * de
	and a
	ret z
.times
	add hl, de
	dec a
	jr nz, .times
	ret

CupCountType:
; e = how many Pokemon in wOTParty have type d.
	ld e, 0
	ld a, [wOTPartyCount]
	and a
	ret z
	ld b, a
	ld hl, wOTPartyMon1
.loop
	push bc
	push de
	push hl
	ld bc, MON_FORM
	add hl, bc
	ld a, [hl]
	and SPECIESFORM_MASK
	ld [wCurForm], a
	pop hl
	push hl
	ld a, [hl] ; MON_SPECIES
	ld [wCurSpecies], a
	call GetBaseData
	pop hl
	pop de
	ld a, [wBaseType1]
	cp d
	jr z, .has
	ld a, [wBaseType2]
	cp d
	jr nz, .next
.has
	inc e
.next
	ld bc, PARTYMON_STRUCT_LENGTH
	add hl, bc
	pop bc
	dec b
	jr nz, .loop
	ret

CupFriendRules:
; For a Friend Battle, the Cable Club's own checks under the kept team's rules:
; carry and a = CUPTEAM_RULES if your team breaks them.
	assert CUP_FRIEND_RISING_STAR > CUP_FRIEND && CUP_FRIEND_UNRESTRICTED > CUP_FRIEND
	assert NUM_CUPS == CUP_FRIEND_UNRESTRICTED + 1
	ld a, [wCupId]
	cp CUP_FRIEND
	ccf
	ret nc
	farcall CheckFriendBattleTeam
	ld a, CUPTEAM_RULES
	ret

CupBegin::
; Keep your party aside, and bring out the team from CupSelectTeam at the
; cup's level, healed.
	call CupBackupParty
	assert wPartyMonNicknamesEnd - wPartyCount == CUP_BACKUP_LENGTH
	ld hl, wOTPartyCount
	ld de, wPartyCount
	ld bc, CUP_BACKUP_LENGTH
	rst CopyBytes
	ld c, CUPRULE_LEVEL
	call GetCupRules
	ld a, [hl]
	ld [wCupLevel], a
	cp CUP_OWN_LEVELS
	jr z, .own_levels
	farcall BT_SetLevel
.own_levels
	farjp HealParty

CupHealTeam::
	farjp HealParty

CupEnd::
; Your party back as it was, healed.
	call CupRestoreParty
	xor a
	ld [wCupLevel], a
	farjp HealParty

CupWin::
; Record a win in cup wCupId (for the Kimono Cup, with type wCupFoeType):
; hScriptVar = TRUE if it's the first.
	call CupCheckRecords
	ld a, [wCupId]
	cp CUP_KIMONO
	jr nz, .not_kimono
	call GetKimonoRecordBit
	jr .record
.not_kimono
	ld e, a
	ld d, 0
	ld hl, CupRecordMasks
	add hl, de
	ld a, [hl]
	ld hl, wCupRecords
.record
	ld b, a
	ld a, [hl]
	ld c, a
	or b
	ld [hl], a
	ld a, c
	and b
	ld a, TRUE
	jr z, .first
	xor a ; FALSE
.first
	ldh [hScriptVar], a
	ret

CupCheckRecords::
; Older saves may have an old party species list where wCupRecords are:
; clear them the first time.
	call ValidCupRecords
	ret z
	ld hl, wCupRecords
	ld bc, CUP_RECORDS_LENGTH
	xor a
	rst ByteFill
	ld a, CUP_RECORDS_MAGIC_1
	ld [wCupRecordsMagic], a
	ld a, CUP_RECORDS_MAGIC_2
	ld [wCupRecordsMagic + 1], a
	ret

GetCupFirstWinFlags::
; The quest map reads the records without changing an older save.
	call ValidCupRecords
	ld a, 0
	ret nz
	ld a, [wCupRecords]
	ret

ValidCupRecords:
	ld a, [wCupRecordsMagic]
	cp CUP_RECORDS_MAGIC_1
	ret nz
	ld a, [wCupRecordsMagic + 1]
	cp CUP_RECORDS_MAGIC_2
	ret

CupBackupParty:
; wPartyCount... (WRAMX bank 1) to wCupPartyBackup (bank 2).
	ldh a, [rWBK]
	push af
	ld hl, wPartyCount
	ld de, wCupPartyBackup
	ld bc, CUP_BACKUP_LENGTH
.loop
	ld a, BANK(wPartyCount)
	ldh [rWBK], a
	ld a, [hli]
	push af
	ld a, BANK(wCupPartyBackup)
	ldh [rWBK], a
	pop af
	ld [de], a
	inc de
	dec bc
	ld a, b
	or c
	jr nz, .loop
	pop af
	ldh [rWBK], a
	ret

CupRestoreParty:
; wCupPartyBackup (WRAMX bank 2) back to wPartyCount... (bank 1).
	ldh a, [rWBK]
	push af
	ld hl, wCupPartyBackup
	ld de, wPartyCount
	ld bc, CUP_BACKUP_LENGTH
.loop
	ld a, BANK(wCupPartyBackup)
	ldh [rWBK], a
	ld a, [hli]
	push af
	ld a, BANK(wPartyCount)
	ldh [rWBK], a
	pop af
	ld [de], a
	inc de
	dec bc
	ld a, b
	or c
	jr nz, .loop
	pop af
	ldh [rWBK], a
	ret

; The Kimono Cup's type of the day: all 18 in turn, one a day by the world
; clock's day count, which wraps at a multiple of both 18 and seven.
KimonoCupTypes:
	assert WORLD_CLOCK_DAYS % NUM_KIMONO_TYPES == 0
	table_width 1
	db NORMAL, FIRE, WATER, GRASS, ELECTRIC, ICE, FIGHTING, POISON, GROUND
	db FLYING, PSYCHIC, BUG, ROCK, GHOST, DRAGON, DARK, STEEL, FAIRY
	assert_table_length NUM_KIMONO_TYPES

KimonoCupToday::
; Today's type: in wCupFoeType (for the team rule, the Kimono Girls' teams
; and the prize, even if the day turns meanwhile) and named in
; wStringBuffer3.
	ld a, [wRTCDayLo]
.mod
	sub NUM_KIMONO_TYPES
	jr nc, .mod
	add NUM_KIMONO_TYPES
	ld e, a
	ld d, 0
	ld hl, KimonoCupTypes
	add hl, de
	ld a, [hl]
	ld [wCupFoeType], a
	ld [wNamedObjectIndex], a
	farcall GetTypeName
	ld hl, wStringBuffer1
	ld de, wStringBuffer3
	ld bc, MOVE_NAME_LENGTH
	rst CopyBytes
	ret

KimonoCupPendingPrize::
	call CupCheckRecords
	ld a, [wCupRecords + CUP_KIMONO_PRIZE_OFFSET]
	ldh [hScriptVar], a
	ret

KimonoCupQueuePrize::
	ld a, [wCupFoeType]
	assert SILK_SCARF + FAIRY == FAIRYFEATHER
	add SILK_SCARF
	ld [wCupRecords + CUP_KIMONO_PRIZE_OFFSET], a
	ldh [hScriptVar], a
	ret

KimonoCupClearPrize::
	xor a
	ld [wCupRecords + CUP_KIMONO_PRIZE_OFFSET], a
	ret

GetKimonoRecordBit:
; hl = the wCupRecords byte, a = the bit, for a Kimono Cup win with type
; wCupFoeType.
	ld a, [wCupFoeType]
	ld c, a
	srl a
	srl a
	srl a
	ld e, a
	ld d, 0
	ld hl, wCupRecords + 1
	add hl, de
	ld a, c
	and 7
	ld c, a
	ld a, 1
	inc c
.shift
	dec c
	ret z
	add a
	jr .shift

KimonoCupTypesWon::
; hScriptVar = how many types have won the Kimono Cup.
	ld hl, wCupRecords + 1
	ld c, 3
	ld b, 0
.byte
	ld a, [hli]
.bit
	and a
	jr z, .next
	srl a
	jr nc, .bit
	inc b
	jr .bit
.next
	dec c
	jr nz, .byte
	ld a, b
	ldh [hScriptVar], a
	ret
