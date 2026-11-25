; Link Edition: the linked World Championship. Two players register a shared
; bracket at a Cable Club battle desk (the Championship format): one draw,
; from a shared seed, with them in opposite halves (slots 0 and 4) and six of
; the World Championship's visiting trainers in the others. Each plays their
; quarterfinal and semifinal against those trainers on their own, at the
; Indigo Plateau, and each result is kept on the cartridge (sWorldLink). On
; linking up again they hear how each other did; if both qualified, the
; final is a link battle; if only one did, they play the other half's
; finalist at the Indigo Plateau.
;
; A session at the desk is two exchanges: what each side has (WorldLinkPut),
; then the plan each worked out from both, with the other's check echoed
; back. Only when both agree does either change anything, so a session cut
; short changes nothing, and running one twice changes nothing more.

; message bytes (WORLD_LINK_MESSAGE_LENGTH, the last a check)
	rsreset
DEF WLMSG_STATE       rb ; WLSTATE_*
DEF WLMSG_ID          rb 2
DEF WLMSG_SEED        rb 2
DEF WLMSG_HALF        rb
DEF WLMSG_MY_ID       rb 2
DEF WLMSG_PARTNER_ID  rb 2
DEF WLMSG_STATUS      rb
DEF WLMSG_NAME        rb PLAYER_NAME_LENGTH
DEF WLMSG_NEW_ID      rb 2 ; a new bracket's, should one be made
DEF WLMSG_NEW_SEED    rb 2
DEF WLMSG_CHECK EQU WORLD_LINK_MESSAGE_LENGTH - 1
	assert _RS <= WLMSG_CHECK
	const_def
	const WLSTATE_NONE   ; no bracket
	const WLSTATE_OPEN   ; in one
	const WLSTATE_CLOSED ; done with one (its record kept)
; (the plan message)
DEF WLMSG_PLAN EQU 0
DEF WLMSG_ECHO EQU 1

Special_WorldLinkSession::
; The Championship format's session, after PerformLinkChecks:
; hScriptVar = WORLDSESSION_*.
	ldh a, [rIF]
	push af
	ldh a, [rIE]
	push af
	farcall PrepareForLinkTransfers
	call .Session
	push af
	; as PerformLinkChecks ends: frames again, and the clock side waits
	; for the other to catch up
	xor a
	ldh [rIF], a
	ld a, IE_SERIAL | IE_VBLANK
	ldh [rIE], a
	ldh a, [hSerialConnectionStatus]
	cp USING_INTERNAL_CLOCK
	ld c, 66
	call z, DelayFrames
	ld hl, wWorldLinkTheirs + WLMSG_NAME
	ld de, wStringBuffer3
	ld bc, PLAYER_NAME_LENGTH
	rst CopyBytes
	ld a, '@'
	ld [de], a
	pop af
	ldh [hScriptVar], a
	pop af
	ldh [rIE], a
	pop af
	ldh [rIF], a
	ret

.Session:
	; 1. what each has (both exchanges always happen, so neither side waits
	; for the other in vain: a side that got garbage sends no plan)
	call WorldLinkPut
	call WorldLinkSwap
	sbc a
	ld [wWorldLinkPlan], a ; (-1 if the swap failed)
	ld hl, wWorldLinkMine
	ld de, wWorldLinkMineFirst
	ld bc, WORLD_LINK_MESSAGE_LENGTH * 2
	assert wWorldLinkTheirs == wWorldLinkMine + WORLD_LINK_MESSAGE_LENGTH
	assert wWorldLinkTheirsFirst == wWorldLinkMineFirst + WORLD_LINK_MESSAGE_LENGTH
	rst CopyBytes
	; 2. the plan each worked out, with the other's check echoed
	ld a, [wWorldLinkPlan]
	and a
	ld a, 0 ; (no plan, after a failed swap)
	jr nz, .planned
	call WorldLinkPlan
.planned
	ld [wWorldLinkPlan], a
	ld hl, wWorldLinkMine
	ld bc, WORLD_LINK_MESSAGE_LENGTH
	xor a
	rst ByteFill
	ld a, [wWorldLinkPlan]
	ld [wWorldLinkMine + WLMSG_PLAN], a
	ld a, [wWorldLinkTheirsFirst + WLMSG_CHECK]
	ld [wWorldLinkMine + WLMSG_ECHO], a
	call WorldLinkSeal
	call WorldLinkSwap
	ld a, WORLDSESSION_ERROR
	ret c
	; both worked out the same plan, and each got the other's message whole
	ld a, [wWorldLinkPlan]
	and a
	ld a, WORLDSESSION_ERROR
	ret z
	ld a, [wWorldLinkPlan]
	ld b, a
	ld a, [wWorldLinkTheirs + WLMSG_PLAN]
	cp b
	ld a, WORLDSESSION_ERROR
	ret nz
	ld a, [wWorldLinkMineFirst + WLMSG_CHECK]
	ld b, a
	ld a, [wWorldLinkTheirs + WLMSG_ECHO]
	cp b
	ld a, WORLDSESSION_ERROR
	ret nz
	; then do it
	ld hl, wWorldLinkMineFirst
	ld de, wWorldLinkMine
	ld bc, WORLD_LINK_MESSAGE_LENGTH * 2
	rst CopyBytes
	ld a, [wWorldLinkPlan]
	jmp WorldLinkCommit

WorldLinkPut:
; wWorldLinkMine = what this game has.
	ld hl, wWorldLinkMine
	ld bc, WORLD_LINK_MESSAGE_LENGTH
	xor a
	rst ByteFill
	call WorldLinkLoad ; carry if there's a bracket (wWorldLinkRecord)
	jr nc, .none
	ld a, [wWorldLinkRecord + WORLD_LINK_STATUS]
	rlca
	and 1
	inc a ; WLSTATE_OPEN or WLSTATE_CLOSED
	assert WLSTATE_CLOSED == WLSTATE_OPEN + 1 && WORLDLINK_CLOSED_F == 7
	ld [wWorldLinkMine + WLMSG_STATE], a
	ld hl, wWorldLinkRecord + WORLD_LINK_ID
	ld de, wWorldLinkMine + WLMSG_ID
	ld bc, 2 + 2 + 1
	assert WORLD_LINK_SEED == WORLD_LINK_ID + 2 && WORLD_LINK_HALF == WORLD_LINK_SEED + 2
	assert WLMSG_SEED == WLMSG_ID + 2 && WLMSG_HALF == WLMSG_SEED + 2
	rst CopyBytes
	ld a, [wWorldLinkRecord + WORLD_LINK_PARTNER_ID]
	ld [wWorldLinkMine + WLMSG_PARTNER_ID], a
	ld a, [wWorldLinkRecord + WORLD_LINK_PARTNER_ID + 1]
	ld [wWorldLinkMine + WLMSG_PARTNER_ID + 1], a
	ld a, [wWorldLinkRecord + WORLD_LINK_STATUS]
	and WORLDLINK_STATUS_MASK
	ld [wWorldLinkMine + WLMSG_STATUS], a
.none
	; a new bracket's ID and draw, in case this side's are used
	ld hl, wWorldLinkMine + WLMSG_NEW_ID
	ld b, 4
	assert WLMSG_NEW_SEED == WLMSG_NEW_ID + 2
.random
	call Random
	ld [hli], a
	dec b
	jr nz, .random
	ld a, [wPlayerID]
	ld [wWorldLinkMine + WLMSG_MY_ID], a
	ld a, [wPlayerID + 1]
	ld [wWorldLinkMine + WLMSG_MY_ID + 1], a
	ld hl, wPlayerName
	ld de, wWorldLinkMine + WLMSG_NAME
	ld bc, PLAYER_NAME_LENGTH
	rst CopyBytes
	; fallthrough
WorldLinkSeal:
; Set wWorldLinkMine's check.
	ld hl, wWorldLinkMine
	call WorldLinkCheck
	ld [wWorldLinkMine + WLMSG_CHECK], a
	ret

WorldLinkCheck:
; a = the check of the message at hl.
	ld b, WLMSG_CHECK
	ld a, WORLD_LINK_MAGIC_1
.loop
	add [hl]
	inc hl
	rlca
	dec b
	jr nz, .loop
	ret

WorldLinkSwap:
; Send wWorldLinkMine, receive wWorldLinkTheirs, as $1x nybbles after the
; preamble bytes. Carry if what came wasn't a whole, checked message.
	ld hl, wWorldLinkSend
	ld a, SERIAL_PREAMBLE_BYTE
	ld [hli], a
	ld a, SERIAL_POLISHED_PREAMBLE_BYTE
	ld [hli], a
	ld de, wWorldLinkMine
	ld b, WORLD_LINK_MESSAGE_LENGTH
.put
	ld a, [de]
	inc de
	swap a
	and $f
	or $10
	ld [hli], a
	dec de
	ld a, [de]
	inc de
	and $f
	or $10
	ld [hli], a
	dec b
	jr nz, .put
	ld hl, wWorldLinkReceive
	ld bc, WORLD_LINK_BUFFER_LENGTH
	xor a
	rst ByteFill
	ld hl, wWorldLinkSend
	ld de, wWorldLinkReceive
	ld bc, WORLD_LINK_BUFFER_LENGTH
	farcall Serial_ExchangeBytes
	; skip the preamble
	ld hl, wWorldLinkReceive
	ld b, SERIAL_POLISHED_MAX_PREAMBLE_LENGTH + 1
.skip
	ld a, [hli]
	cp SERIAL_POLISHED_PREAMBLE_BYTE
	jr z, .data
	dec b
	jr nz, .skip
	scf
	ret
.data
	ld de, wWorldLinkTheirs
	ld b, WORLD_LINK_MESSAGE_LENGTH
.get
	ld a, [hli]
	ld c, a
	and $f0
	cp $10
	jr nz, .bad
	ld a, [hli]
	push af
	and $f0
	cp $10
	jr nz, .bad_pop
	ld a, c
	swap a
	and $f0
	ld c, a
	pop af
	and $f
	or c
	ld [de], a
	inc de
	dec b
	jr nz, .get
	ld hl, wWorldLinkTheirs
	call WorldLinkCheck
	ld hl, wWorldLinkTheirs + WLMSG_CHECK
	cp [hl]
	ret z ; (no carry)
	scf
	ret
.bad_pop
	pop af
.bad
	scf
	ret

DEF WLPLAN_REGISTER   EQU 1 ; neither has one: a new bracket (the clock side's)
DEF WLPLAN_JOIN_THEIRS EQU 2 ; join the other's (with us as their partner)
DEF WLPLAN_JOIN_MINE  EQU 3 ; the other joins ours
DEF WLPLAN_SYNC       EQU 4 ; the same bracket
DEF WLPLAN_MISMATCH   EQU 5
; (each side works out the same one: JOIN_THEIRS on one is JOIN_MINE on the
; other, so the plan sent is made the same for both, as the clock side sees it)

WorldLinkPlan:
; a = the plan, as the internal-clock side would name it.
	call .Plan
	ld b, a
	ldh a, [hSerialConnectionStatus]
	cp USING_INTERNAL_CLOCK
	ld a, b
	ret z
	; the other side names the joins the other way round
	cp WLPLAN_JOIN_THEIRS
	jr nz, .not_theirs
	ld a, WLPLAN_JOIN_MINE
	ret
.not_theirs
	cp WLPLAN_JOIN_MINE
	ret nz
	ld a, WLPLAN_JOIN_THEIRS
	ret

.Plan:
	; anything out of range: no plan (so the two plans differ, and neither
	; side changes anything)
	ld hl, wWorldLinkTheirs
	call .Valid
	ld a, 0
	ret c
	ld a, [wWorldLinkMine + WLMSG_STATE]
	ld b, a
	ld a, [wWorldLinkTheirs + WLMSG_STATE]
	ld c, a
	ld a, b
	cp WLSTATE_OPEN
	jr z, .mine_open
	; neither in an open bracket (none, or closed): a new one
	ld a, c
	cp WLSTATE_OPEN
	ld a, WLPLAN_REGISTER
	ret nz
	; theirs open: the same bracket, mine closed?
	ld a, b
	cp WLSTATE_CLOSED
	jr nz, .theirs_partner
	call .SameBracket
	ld a, WLPLAN_SYNC
	ret z
.theirs_partner
	; else, am I their partner (a registration this side didn't keep)?
	ld hl, wWorldLinkTheirs + WLMSG_PARTNER_ID
	ld de, wWorldLinkMine + WLMSG_MY_ID
	call .SameID
	ld a, WLPLAN_JOIN_THEIRS
	ret z
	ld a, WLPLAN_MISMATCH
	ret

.mine_open
	ld a, c
	and a ; WLSTATE_NONE
	jr z, .my_partner
	call .SameBracket ; (theirs open or closed)
	ld a, WLPLAN_SYNC
	ret z
	ld a, c
	cp WLSTATE_OPEN
	ld a, WLPLAN_MISMATCH
	ret z ; both open, in different brackets
.my_partner
	; are they my partner (a registration that side didn't keep)?
	ld hl, wWorldLinkMine + WLMSG_PARTNER_ID
	ld de, wWorldLinkTheirs + WLMSG_MY_ID
	call .SameID
	ld a, WLPLAN_JOIN_MINE
	ret z
	ld a, WLPLAN_MISMATCH
	ret

.Valid:
; Carry if the message at hl has a value out of range.
	ld a, [hl] ; state
	cp WLSTATE_CLOSED + 1
	ccf
	ret c
	and a
	ret z
	ld de, WLMSG_HALF
	add hl, de
	ld a, [hl]
	cp 2
	ccf
	ret c
	ld de, WLMSG_STATUS - WLMSG_HALF
	add hl, de
	ld a, [hl]
	cp WORLDLINK_RUNNER_UP + 1
	ccf
	ret

.SameBracket:
; z if the two messages are the same bracket: its ID and draw, opposite
; halves, each the other's partner.
	ld hl, wWorldLinkMine + WLMSG_ID
	ld de, wWorldLinkTheirs + WLMSG_ID
	call .SameID
	ret nz
	ld hl, wWorldLinkMine + WLMSG_SEED
	ld de, wWorldLinkTheirs + WLMSG_SEED
	call .SameID
	ret nz
	ld a, [wWorldLinkMine + WLMSG_HALF]
	ld hl, wWorldLinkTheirs + WLMSG_HALF
	xor [hl]
	dec a
	ret nz
	ld hl, wWorldLinkMine + WLMSG_PARTNER_ID
	ld de, wWorldLinkTheirs + WLMSG_MY_ID
	call .SameID
	ret nz
	ld hl, wWorldLinkTheirs + WLMSG_PARTNER_ID
	ld de, wWorldLinkMine + WLMSG_MY_ID
	; fallthrough
.SameID:
; z if the two bytes at hl and de match.
	ld a, [de]
	cp [hl]
	ret nz
	inc hl
	inc de
	ld a, [de]
	cp [hl]
	ret

WorldLinkCommit:
; Do plan a (as the clock side names it): a = WORLDSESSION_*.
	ld b, a
	ldh a, [hSerialConnectionStatus]
	cp USING_INTERNAL_CLOCK
	ld a, b
	jr z, .named
	; back to this side's names
	cp WLPLAN_JOIN_THEIRS
	ld b, WLPLAN_JOIN_MINE
	jr z, .renamed
	cp WLPLAN_JOIN_MINE
	ld b, WLPLAN_JOIN_THEIRS
	jr z, .renamed
	ld b, a
.renamed
	ld a, b
.named
	cp WLPLAN_REGISTER
	jr z, .register
	cp WLPLAN_JOIN_THEIRS
	jr z, .join
	cp WLPLAN_JOIN_MINE
	jr z, .partner_joined
	cp WLPLAN_SYNC
	jr z, .sync
	ld a, WORLDSESSION_MISMATCH
	ret

.register
	; the clock side's ID and draw; the clock side takes the top half
	ldh a, [hSerialConnectionStatus]
	cp USING_INTERNAL_CLOCK
	ld hl, wWorldLinkMine + WLMSG_NEW_ID
	ld b, 0
	jr z, .new
	ld hl, wWorldLinkTheirs + WLMSG_NEW_ID
	ld b, 1
.new
	ld de, wWorldLinkRecord + WORLD_LINK_ID
	ld a, [hli]
	ld [de], a
	inc de
	ld a, [hli]
	ld [de], a
	inc de
	ld a, [hli]
	ld [de], a
	inc de
	ld a, [hli]
	ld [de], a
	inc de
	ld a, b
	ld [de], a ; half
	call .Partner
	ld a, WORLDSESSION_REGISTERED
	ret

.join
	; theirs, in the other half
	ld hl, wWorldLinkTheirs + WLMSG_ID
	ld de, wWorldLinkRecord + WORLD_LINK_ID
	ld bc, 2 + 2
	rst CopyBytes
	ld a, [wWorldLinkTheirs + WLMSG_HALF]
	xor 1
	ld [de], a
	call .Partner
	ld a, WORLDSESSION_REGISTERED
	ret

.partner_joined
	; ours stands; they've joined it, at the start
	call WorldLinkLoad
	ld a, WORLDLINK_QUARTERFINAL
	ld [wWorldLinkRecord + WORLD_LINK_PARTNER_STATUS], a
	call WorldLinkSave
	ld a, WORLDSESSION_REGISTERED
	ret

.Partner:
	ld hl, wWorldLinkTheirs + WLMSG_MY_ID
	ld de, wWorldLinkRecord + WORLD_LINK_PARTNER_ID
	ld bc, 2
	rst CopyBytes
	ld hl, wWorldLinkTheirs + WLMSG_NAME
	ld bc, PLAYER_NAME_LENGTH
	rst CopyBytes
	assert WORLD_LINK_PARTNER_NAME == WORLD_LINK_PARTNER_ID + 2
	ld a, WORLDLINK_QUARTERFINAL
	ld [wWorldLinkRecord + WORLD_LINK_STATUS], a
	ld a, WORLDLINK_UNKNOWN
	ld [wWorldLinkRecord + WORLD_LINK_PARTNER_STATUS], a
	jmp WorldLinkSave

.sync
	call WorldLinkLoad
	; done with it on this side: nothing changes here
	ld a, [wWorldLinkRecord + WORLD_LINK_STATUS]
	bit WORLDLINK_CLOSED_F, a
	ld a, WORLDSESSION_SYNCED
	ret nz
	; what they said of themselves (if they left it unfinished, as a forfeit
	; of their next match)
	ld a, [wWorldLinkTheirs + WLMSG_STATUS]
	ld b, a
	ld a, [wWorldLinkTheirs + WLMSG_STATE]
	cp WLSTATE_CLOSED
	jr nz, .their_status
	ld a, b
	cp WORLDLINK_SEMIFINAL
	ld b, WORLDLINK_OUT_QF
	jr c, .their_status
	cp WORLDLINK_FINAL + 1
	ld b, WORLDLINK_OUT_SF
	jr c, .their_status
	ld b, a ; finished: as it ended
.their_status
	ld a, b
	ld [wWorldLinkRecord + WORLD_LINK_PARTNER_STATUS], a
	ld hl, wWorldLinkRecord + WORLD_LINK_STATUS
	; a final cut short on this side: theirs says how it ended
	ld a, [hl]
	cp WORLDLINK_FINAL
	jr nz, .saved
	ld a, b
	cp WORLDLINK_CHAMPION
	ld c, WORLDLINK_RUNNER_UP
	jr z, .ended
	cp WORLDLINK_RUNNER_UP
	ld c, WORLDLINK_CHAMPION
	jr nz, .saved
.ended
	ld [hl], c
.saved
	call WorldLinkSave
	; both qualified: the final, now
	ld a, [wWorldLinkRecord + WORLD_LINK_STATUS]
	cp WORLDLINK_FINAL
	ld a, WORLDSESSION_SYNCED
	ret nz
	ld a, [wWorldLinkRecord + WORLD_LINK_PARTNER_STATUS]
	cp WORLDLINK_FINAL
	ld a, WORLDSESSION_SYNCED
	ret nz
	ld a, WORLDSESSION_FINAL
	ret

WorldLinkLoad::
; wWorldLinkRecord = sWorldLink; carry if it holds a bracket.
	ld a, BANK(sWorldLink)
	call GetSRAMBank
	ld hl, sWorldLink
	ld de, wWorldLinkRecord
	ld bc, WORLD_LINK_LENGTH
	rst CopyBytes
	call CloseSRAM
	ld hl, wWorldLinkRecord
	ld a, [hli]
	cp WORLD_LINK_MAGIC_1
	jr nz, .no
	ld a, [hli]
	cp WORLD_LINK_MAGIC_2
	jr nz, .no
	ld c, [hl]
	inc hl
	call WorldLinkRecordCheck
	cp c
	jr nz, .no
	scf
	ret
.no
	and a
	ret

WorldLinkRecordCheck:
; a = the check of the record from hl (its ID onwards).
	ld b, WORLD_LINK_LENGTH - WORLD_LINK_ID
	ld a, WORLD_LINK_MAGIC_2
.loop
	add [hl]
	inc hl
	rlca
	dec b
	jr nz, .loop
	ret

WorldLinkSave::
; sWorldLink = wWorldLinkRecord, marked and checked.
	ld hl, wWorldLinkRecord
	ld a, WORLD_LINK_MAGIC_1
	ld [hli], a
	ld a, WORLD_LINK_MAGIC_2
	ld [hli], a
	push hl
	inc hl
	call WorldLinkRecordCheck
	pop hl
	ld [hl], a
	ld a, BANK(sWorldLink)
	call GetSRAMBank
	ld hl, wWorldLinkRecord
	ld de, sWorldLink
	ld bc, WORLD_LINK_LENGTH
	rst CopyBytes
	jmp CloseSRAM

WorldLinkClose::
; This player is done with the bracket (it's over, or they leave it): the
; record stays, closed, as a receipt.
	call WorldLinkLoad
	ret nc
	ld hl, wWorldLinkRecord + WORLD_LINK_STATUS
	set WORLDLINK_CLOSED_F, [hl]
	jmp WorldLinkSave

WorldLinkClaim::
; The champion's prize has been given (or is held at the desk): this game's
; receipt names the bracket. The receipt is saved with the game, so the prize
; and the receipt are kept together, or both lost if the power goes before a
; save; a game with the receipt is never given the prize again.
	ld hl, wWorldLinkReceipt
	ld a, WORLD_LINK_RECEIPT_MARK
	ld [hli], a
	ld a, [wWorldLinkRecord + WORLD_LINK_ID]
	ld [hli], a
	ld a, [wWorldLinkRecord + WORLD_LINK_ID + 1]
	ld [hl], a
	ret

WorldLinkHasReceipt:
; z if this game's receipt names the bracket in wWorldLinkRecord.
	ld hl, wWorldLinkReceipt
	ld a, [hli]
	cp WORLD_LINK_RECEIPT_MARK
	ret nz
	ld a, [wWorldLinkRecord + WORLD_LINK_ID]
	cp [hl]
	ret nz
	inc hl
	ld a, [wWorldLinkRecord + WORLD_LINK_ID + 1]
	cp [hl]
	ret

WorldLinkCommitClaim::
; From SaveGameData, once the game is saved: a champion whose prize is in
; that save (its receipt) closes the bracket. (Tidying only: the receipt
; already stops a second prize, even if the power goes before this.)
	call WorldLinkLoad
	ret nc
	ld a, [wWorldLinkRecord + WORLD_LINK_STATUS]
	cp WORLDLINK_CHAMPION ; (and not closed: the closed bit is set in a closed record)
	ret nz
	call WorldLinkHasReceipt
	ret nz
	jr WorldLinkClose

WorldLinkFinalResult::
; After a link battle: if it was the linked final, keep how it went. (On
; the record in SRAM: the battle's work RAM may still be in use.)
	ld a, [wLinkBattleRules]
	cp LINK_RULE_WORLD
	ret nz
	ld a, [wBattleResult]
	and $f
	ld bc, WORLDLINK_CHAMPION << 8 | WORLDLINK_RUNNER_UP
	cp LOSE
	jr c, .result
	ret nz ; a draw: play it again
	ld bc, WORLDLINK_RUNNER_UP << 8 | WORLDLINK_CHAMPION
.result
	ld a, BANK(sWorldLink)
	call GetSRAMBank
	ld hl, sWorldLink
	ld a, [hli]
	cp WORLD_LINK_MAGIC_1
	jr nz, .done
	ld a, [hli]
	cp WORLD_LINK_MAGIC_2
	jr nz, .done
	push bc
	ld c, [hl]
	inc hl
	call WorldLinkRecordCheck
	cp c
	pop bc
	jr nz, .done
	ld a, [sWorldLink + WORLD_LINK_STATUS]
	cp WORLDLINK_FINAL
	jr nz, .done
	ld a, b
	ld [sWorldLink + WORLD_LINK_STATUS], a
	ld a, c
	ld [sWorldLink + WORLD_LINK_PARTNER_STATUS], a
	ld hl, sWorldLink + WORLD_LINK_ID
	call WorldLinkRecordCheck
	ld [sWorldLink + WORLD_LINK_CHECKSUM], a
.done
	jmp CloseSRAM

; The draw: from the seed, six of the seven visiting trainers (WorldCupTrainers
; indexes, plus one) in slots 1-3 and 5-7 of wWorldCupBracket; slots 0 and 4
; are the two players (0).

WorldLinkDraw::
	ld hl, wWorldLinkRecord + WORLD_LINK_SEED
	ld a, [hli]
	ld e, a
	ld d, [hl]
	; seven trainers, shuffled: wWorldLinkMine
	ld hl, wWorldLinkMine
	ld a, 1
.list
	ld [hli], a
	inc a
	cp WORLD_CUP_CONTESTANTS
	jr c, .list
	ld c, WORLD_CUP_CONTESTANTS - 2 ; i: 6 down to 1
.shuffle
	call .Next ; a = 0-255
	ld b, c
	inc b ; j in 0..i
.mod
	cp b
	jr c, .got
	sub b
	jr .mod
.got
	push de
	ld hl, wWorldLinkMine
	ld e, a
	ld d, 0
	add hl, de
	ld d, h
	ld e, l
	ld hl, wWorldLinkMine
	ld a, c
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, [de]
	ld b, [hl]
	ld [hl], a
	ld a, b
	ld [de], a
	pop de
	dec c
	jr nz, .shuffle
	; into the bracket around the players
	ld hl, wWorldLinkMine
	ld de, wWorldCupBracket
	xor a
	ld [de], a ; slot 0
	inc de
	ld b, 3
.top
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .top
	xor a
	ld [de], a ; slot 4
	inc de
	ld b, 3
.bottom
	ld a, [hli]
	ld [de], a
	inc de
	dec b
	jr nz, .bottom
	ret

.Next:
; de = de * 5 + 1 (mod 65536); a = its high byte.
	ld h, d
	ld l, e
	add hl, hl
	add hl, hl
	add hl, de
	inc hl
	ld d, h
	ld e, l
	ld a, h
	ret

WorldLinkStronger:
; a = the winner of the trainers in slots a and a+1 (a even: quarterfinal
; a / 2), as WorldCupWinner decides it from the bracket's seed. Keeps bc, de.
	push bc
	push de
	ld e, a
	srl e
	ld hl, wWorldCupBracket
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, [hli]
	ld b, a
	ld c, [hl]
	ld hl, wWorldLinkRecord + WORLD_LINK_SEED
	call WorldCupWinner
	pop de
	pop bc
	ret

WorldLinkOpponent::
; At the Indigo Plateau: hScriptVar = what's next (WORLDDESK_*), the
; opponent ready as loadtrainer would (WorldCupLoadOpponent's trainer), its
; name in wStringBuffer4, the partner's in wStringBuffer3.
	call WorldLinkLoad
	ld a, WORLDDESK_NONE
	jmp nc, .done
	ld a, [wWorldLinkRecord + WORLD_LINK_STATUS]
	bit WORLDLINK_CLOSED_F, a
	ld a, WORLDDESK_NONE
	jmp nz, .done
	ld hl, wWorldLinkRecord + WORLD_LINK_PARTNER_NAME
	ld de, wStringBuffer3
	ld bc, PLAYER_NAME_LENGTH
	rst CopyBytes
	ld a, '@'
	ld [de], a
	call WorldLinkDraw
	ld a, [wWorldLinkRecord + WORLD_LINK_HALF]
	add a
	add a
	ld e, a ; my slot
	ld a, [wWorldLinkRecord + WORLD_LINK_STATUS]
	cp WORLDLINK_QUARTERFINAL
	jr z, .quarterfinal
	cp WORLDLINK_SEMIFINAL
	jr z, .semifinal
	cp WORLDLINK_FINAL
	jr z, .final
	cp WORLDLINK_CHAMPION
	jr nz, .not_champion
	; (this game's receipt: the prize is already in it, or held at the desk)
	push de
	call WorldLinkHasReceipt
	pop de
	ld a, WORLDDESK_CLAIMED
	jmp z, .done
	ld a, WORLDDESK_CHAMPION
	jr .done
.not_champion
	ld a, [wWorldLinkRecord + WORLD_LINK_STATUS]
	cp WORLDLINK_RUNNER_UP
	ld a, WORLDDESK_RUNNER_UP
	jr z, .done
	; out: has the other finished too (as last heard)?
	ld a, [wWorldLinkRecord + WORLD_LINK_PARTNER_STATUS]
	cp WORLDLINK_UNKNOWN
	jr z, .still_playing
	cp WORLDLINK_OUT_QF
	ld a, WORLDDESK_OVER
	jr nc, .done
.still_playing
	ld a, WORLDDESK_OUT
	jr .done

.quarterfinal
	ld a, e
	inc a
	call WorldLinkSlot
	ld b, WORLDDESK_QUARTERFINAL
	jr .opponent
.semifinal
	ld a, e
	add 2
	call WorldLinkStronger
	ld b, WORLDDESK_SEMIFINAL
	jr .opponent
.final
	; the other half's finalist, once the partner's out
	ld a, [wWorldLinkRecord + WORLD_LINK_PARTNER_STATUS]
	cp WORLDLINK_OUT_QF
	jr z, .partner_out_qf
	cp WORLDLINK_OUT_SF
	ld a, WORLDDESK_WAIT
	jr nz, .done
	ld a, e
	xor 4
	add 2
	call WorldLinkStronger
	ld b, WORLDDESK_FINAL
	jr .opponent
.partner_out_qf
	ld a, e
	xor 4
	add 2
	call WorldLinkStronger
	ld c, a
	ld a, e
	xor 4
	inc a
	push bc
	call WorldLinkSlot
	pop bc
	ld b, a ; who beat the partner, against that quarterfinal's winner
	push de
	ld a, e
	xor 4
	rrca
	rrca
	add 4 ; that half's semifinal: 4 or 5
	ld e, a
	ld hl, wWorldLinkRecord + WORLD_LINK_SEED
	call WorldCupWinner
	pop de
	ld b, WORLDDESK_FINAL
.opponent
	push bc
	ld [wWorldCupBracket + 1], a ; (WorldCupLoadOpponent's slot)
	call WorldCupLoadOpponent
	ld a, [wWorldCupBracket + 1]
	ld de, wStringBuffer4
	call WorldCupCopyName
	pop bc
	ld a, b
.done
	ldh [hScriptVar], a
	ret

WorldLinkLastResult::
; Before the semifinal or the final (WorldLinkOpponent has just run): who the
; opponent beat to get here, in wStringBuffer5; hScriptVar = TRUE if that was
; an upset (the weaker trainer won).
	call WorldLinkDraw ; (WorldLinkOpponent wrote over slot 1)
	ld a, [wWorldLinkRecord + WORLD_LINK_HALF]
	add a
	add a
	ld e, a ; my slot
	ld a, [wWorldLinkRecord + WORLD_LINK_STATUS]
	cp WORLDLINK_SEMIFINAL
	jr z, .semifinal
	; the final: the other half's finalist beat the partner, or a trainer
	ld a, [wWorldLinkRecord + WORLD_LINK_PARTNER_STATUS]
	cp WORLDLINK_OUT_QF
	jr z, .trainers_semifinal
	ld hl, wStringBuffer3
	ld de, wStringBuffer5
	ld bc, STRING_BUFFER_LENGTH
	rst CopyBytes
	xor a
	ldh [hScriptVar], a
	ret

.trainers_semifinal
	ld a, e
	xor 4
	ld d, a ; that half's first slot
	add 2
	call WorldLinkStronger ; (keeps bc, de)
	ld c, a
	ld a, d
	inc a
	call WorldLinkSlot
	ld b, a
	ld a, d
	rrca
	rrca
	add 4 ; that half's semifinal
	ld e, a
	jr WorldCupAnnounce

.semifinal
	ld a, e
	add 2
	ld d, a
	call WorldLinkSlot
	ld b, a
	ld a, d
	inc a
	call WorldLinkSlot
	ld c, a
	srl d
	ld e, d ; that quarterfinal
	ld hl, wWorldLinkRecord + WORLD_LINK_SEED
	jr WorldCupAnnounceSeeded

WorldCupAnnounce:
	ld hl, wWorldLinkRecord + WORLD_LINK_SEED
WorldCupAnnounceSeeded:
; Trainers b and c's match e, with the seed at hl: the loser's name in
; wStringBuffer5; hScriptVar = TRUE for an upset.
	push bc
	call WorldCupWinner
	pop bc
	cp b
	jr nz, .b_lost
	ld b, c
.b_lost
	ld c, a ; the winner; b, the loser
	ld a, b
	push bc
	ld de, wStringBuffer5
	call WorldCupCopyName
	pop bc
	ld a, c
	cp b ; (the weaker won: an upset)
	ld a, FALSE
	jr nc, .done
	ld a, TRUE
.done
	ldh [hScriptVar], a
	ret

WorldLinkSlot:
; a = the trainer in slot a.
	ld hl, wWorldCupBracket
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, [hl]
	ret

WorldLinkResult::
; After a battle at the Indigo Plateau (hScriptVar: TRUE if lost): move on.
	call WorldLinkLoad
	ret nc
	ldh a, [hScriptVar]
	and a
	ld hl, wWorldLinkRecord + WORLD_LINK_STATUS
	ld a, [hl]
	jr nz, .lost
	cp WORLDLINK_FINAL
	ld b, WORLDLINK_CHAMPION
	jr z, .set
	inc a ; on to the next round
	ld b, a
	jr .set
.lost
	cp WORLDLINK_FINAL
	ld b, WORLDLINK_RUNNER_UP
	jr z, .set
	add WORLDLINK_OUT_QF - WORLDLINK_QUARTERFINAL
	ld b, a
.set
	ld [hl], b
	jmp WorldLinkSave
