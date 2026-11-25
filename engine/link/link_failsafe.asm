; Link Edition: link battle safeguards.
;
; Before a link battle the two games swap their parties and the random number
; seed with no error checking, so one bad byte on the cable could give one game
; a different opposing team (or seed) without either player knowing. Here each
; game fingerprints what it sent and what it received, the games swap those
; fingerprints, and the battle only starts if both agree; otherwise both games
; show an error and leave the battle, so the players can simply try again.

LinkFailsafe_HashSentParty::
; Fingerprint our party as it is about to be sent (call right after
; Link_PrepPartyData_Gen2, before the data is patched for transfer).
; The send buffer holds the preamble, our name, the party count, our
; trainer ID and then the party structs.
	ld a, [wLinkData + SERIAL_PREAMBLE_LENGTH + NAME_LENGTH]
	ld hl, wLinkData + SERIAL_PREAMBLE_LENGTH + NAME_LENGTH + 1 + 2
	call LinkFailsafe_HashParty
	ld a, d
	ld [wLinkSentPartyHash], a
	ld a, e
	ld [wLinkSentPartyHash + 1], a
	ret

LinkFailsafe_HashParty:
; a = party count, hl = party structs.
; Returns de = fingerprint of the count and the first count structs.
	ld de, 0
	cp PARTY_LENGTH + 1
	jr c, .count_ok
	ld a, PARTY_LENGTH
.count_ok
	ld b, a
	add e
	ld e, a
	add d
	ld d, a
	ld a, b
	ld bc, 0
	and a
	ret z
.size
	push hl
	ld hl, PARTYMON_STRUCT_LENGTH
	add hl, bc
	ld b, h
	ld c, l
	pop hl
	dec a
	jr nz, .size
	; fallthrough

LinkFailsafe_Hash:
; Add bc bytes at hl to the fingerprint de (Fletcher-16, modulo 256).
	ld a, b
	or c
	ret z
	ld a, [hli]
	add e
	ld e, a
	add d
	ld d, a
	dec bc
	jr LinkFailsafe_Hash

LinkFailsafe_VerifySetup::
; Call once the opponent's party and the random numbers are in place.
; Sets [wLinkSetupFailed] to 0 if both games received the same battle.
	; Check party rules before the serial exchange. The two parties can have
	; different sizes, so this work must finish before the link synchronizes.
	call CheckReceivedLinkBattleParty
	ld a, LINK_CHECK_OK
	jr nc, .save_verdict
	ld a, LINK_CHECK_BAD
.save_verdict
	ld [wLinkSetupFailed], a
	; our fingerprints: sent party, received party, random numbers
	ld a, [wOTPartyCount]
	ld hl, wOTPartyMons
	call LinkFailsafe_HashParty
	push de
	ld de, 0
	ld hl, wLinkBattleRNs
	ld bc, SERIAL_RNS_LENGTH
	call LinkFailsafe_Hash

	ld hl, wLinkCheckSend
	ld a, SERIAL_PREAMBLE_BYTE
	ld b, SERIAL_PREAMBLE_LENGTH
.preamble
	ld [hli], a
	dec b
	jr nz, .preamble
	ld a, [wLinkSentPartyHash]
	call .PutNybbles
	ld a, [wLinkSentPartyHash + 1]
	call .PutNybbles
	pop bc ; received party fingerprint
	ld a, b
	call .PutNybbles
	ld a, c
	call .PutNybbles
	ld a, d
	call .PutNybbles
	ld a, e
	call .PutNybbles
	; keep our values to compare with what the other game sends back
	push de
	push bc
	call .PutSlack

	farcall PrepareForLinkTransfers
	ld hl, wLinkCheckSend
	ld de, wLinkCheckRecv
	ld bc, LINK_CHECK_LENGTH
	farcall Serial_ExchangeBytes

	; compare: their "sent" must be our "received" and vice versa, and the
	; random numbers must match
	ld de, wLinkCheckRecv
	call .SkipPreamble
	pop bc ; our received party fingerprint
	call .ReadNybbles ; their sent party
	jr c, .bad_pop1
	cp b
	jr nz, .bad_pop1
	call .ReadNybbles
	jr c, .bad_pop1
	cp c
	jr nz, .bad_pop1
	call .ReadNybbles ; their received party
	jr c, .bad_pop1
	ld hl, wLinkSentPartyHash
	cp [hl]
	jr nz, .bad_pop1
	call .ReadNybbles
	jr c, .bad_pop1
	inc hl
	cp [hl]
	jr nz, .bad_pop1
	pop bc ; our random number fingerprint
	call .ReadNybbles
	jr c, .bad
	cp b
	jr nz, .bad
	call .ReadNybbles
	jr c, .bad
	cp c
	jr nz, .bad
	ld a, [wLinkSetupFailed]
	jr .verdict

.bad_pop1
	pop bc
.bad
	ld a, LINK_CHECK_BAD
.verdict
	; tell each other the verdict: the battle only starts if both are happy
	ld [wLinkSetupFailed], a
	ld hl, wLinkVerdictSend
	ld b, SERIAL_PREAMBLE_LENGTH
	ld c, a
	ld a, SERIAL_PREAMBLE_BYTE
.preamble2
	ld [hli], a
	dec b
	jr nz, .preamble2
	ld a, c
	ld b, LINK_VERDICT_COPIES
.verdict_copies
	ld [hli], a
	dec b
	jr nz, .verdict_copies
	call .PutSlack
	ld hl, wLinkVerdictSend
	ld de, wLinkVerdictRecv
	ld bc, LINK_VERDICT_LENGTH
	farcall Serial_ExchangeBytes
	xor a
	ldh [rIF], a
	ld a, IE_SERIAL | IE_VBLANK
	ldh [rIE], a

	; the other game is happy if most of its verdict copies say so (one bad
	; byte mustn't make the two games decide differently)
	ld de, wLinkVerdictRecv
	call .SkipPreamble
	ld b, LINK_VERDICT_COPIES
	ld c, 0
.count_ok
	ld a, [de]
	inc de
	cp LINK_CHECK_OK
	jr nz, .not_ok
	inc c
.not_ok
	dec b
	jr nz, .count_ok
	ld a, c
	cp LINK_VERDICT_COPIES - 1
	jr c, .failed
	ld a, [wLinkSetupFailed]
	cp LINK_CHECK_OK
	jr nz, .failed
	xor a
	ld [wLinkSetupFailed], a
	ld [wLinkSetupTries], a
	ret

.failed
	ld a, 1
	ld [wLinkSetupFailed], a
	ret

.PutNybbles:
; Store a at hl as two bytes, $10 | high nybble and $10 | low nybble, so no
; data byte can look like a serial control byte.
	push af
	swap a
	and $f
	or $10
	ld [hli], a
	pop af
	and $f
	or $10
	ld [hli], a
	ret

.PutSlack:
; Pad the send buffer at hl with zeros.
	xor a
	ld b, LINK_CHECK_SLACK
.slack
	ld [hli], a
	dec b
	jr nz, .slack
	ret

.ReadNybbles:
; Read two nybble bytes at de into a; carry if they aren't nybble bytes.
	ld a, [de]
	inc de
	push bc
	ld b, a
	and $f0
	cp $10
	jr nz, .not_nybbles
	ld a, [de]
	inc de
	ld c, a
	and $f0
	cp $10
	jr nz, .not_nybbles
	ld a, b
	swap a
	and $f0
	ld b, a
	ld a, c
	and $f
	or b
	pop bc
	and a
	ret
.not_nybbles
	pop bc
	scf
	ret

.SkipPreamble:
	ld a, [de]
	cp SERIAL_PREAMBLE_BYTE
	ret nz
	inc de
	jr .SkipPreamble

LinkFailsafe_SetupFailed::
; The check failed: try the swap again (both games decide the same, from the
; same verdicts), up to LINK_SETUP_TRIES times. Sets [wLinkSetupFailed] to 0
; to try again, or leaves it nonzero (after telling the players) to give up.
	ld hl, wLinkSetupTries
	inc [hl]
	ld a, [hl]
	cp LINK_SETUP_TRIES
	jr nc, .give_up
	hlcoord 0, 12
	lb bc, 4, 18
	farcall LinkTextbox
	ld hl, .RetryText
	bccoord 1, 14
	call PlaceWholeStringInBoxAtOnce
	ld c, 60
	call DelayFrames
	xor a
	ld [wLinkSetupFailed], a
	ret

.give_up
	xor a
	ld [hl], a
	call LinkFailsafe_ShowSetupError
	ld a, 1
	ld [wLinkSetupFailed], a
	ret

.RetryText:
	text "Link error! Trying"
	line "again. Keep it on!"
	done

LinkFailsafe_ShowSetupError::
; Tell the players the battle data didn't arrive intact.
	hlcoord 0, 12
	lb bc, 4, 18
	farcall LinkTextbox
	ld hl, .Text
	bccoord 1, 14
	call PlaceWholeStringInBoxAtOnce
	ld c, 180
	jmp DelayFrames

.Text:
	text "Link error: the"
	line "battle data didn't"
	cont "arrive intact."
	para "Check the cable"
	line "and try again."
	done

LinkFailsafe_BattleFingerprint:
; Returns a = a fingerprint of the battle state that both games share: both
; active Pokemon's HP, status and stat changes, both parties' HP and the
; position in the shared random numbers. The clock side's half comes first,
; so both games add the same bytes in the same order.
	ld de, 0
	ldh a, [hSerialConnectionStatus]
	cp USING_INTERNAL_CLOCK
	jr nz, .enemy_first
	call .Player
	call .Enemy
	jr .done
.enemy_first
	call .Enemy
	call .Player
.done
	ld hl, wLinkBattleRNCount
	ld bc, 1
	call LinkFailsafe_Hash
	ld a, d
	xor e
	ret

.Player:
	ld hl, wBattleMonHP
	ld bc, 2
	call LinkFailsafe_Hash
	ld hl, wBattleMonStatus
	ld bc, 1
	call LinkFailsafe_Hash
	ld hl, wPlayerStatLevels
	ld bc, NUM_LEVEL_STATS
	call LinkFailsafe_Hash
	ld a, [wPartyCount]
	ld hl, wPartyMon1HP
	jr .PartyHP

.Enemy:
	ld hl, wEnemyMonHP
	ld bc, 2
	call LinkFailsafe_Hash
	ld hl, wEnemyMonStatus
	ld bc, 1
	call LinkFailsafe_Hash
	ld hl, wEnemyStatLevels
	ld bc, NUM_LEVEL_STATS
	call LinkFailsafe_Hash
	ld a, [wOTPartyCount]
	ld hl, wOTPartyMon1HP
	; fallthrough

.PartyHP:
; Add the 2-byte HP of each of the first a party structs at hl.
	cp PARTY_LENGTH + 1
	jr c, .hp_count_ok
	ld a, PARTY_LENGTH
.hp_count_ok
	and a
	ret z
.hp_loop
	push af
	push hl
	ld bc, 2
	call LinkFailsafe_Hash
	pop hl
	ld bc, PARTYMON_STRUCT_LENGTH
	add hl, bc
	pop af
	dec a
	jr nz, .hp_loop
	ret

LinkFailsafe_ExchangeAction::
; Swap this turn's action with the other game, along with a fingerprint of
; the battle state. [wLinkBattleSentAction] is our action (0-15).
;
; Three fields go out, one byte per frame, each with its own tag: the action,
; then the fingerprint's high and low nybbles. Exchanges cycle through four
; sets of tags (wLinkBattleExchangeTag is the set's first tag: $10, $40, $70
; or $a0, see NextLinkExchangeTag), so bytes from another exchange, even the
; one before last, are never taken for this one. A field
; only counts once the same value arrives twice in a row, and can't be
; overwritten after that, so one bad bit on the cable can't change it.
;
; Nothing here gives up or times out: if the cable is bumped or pulled out,
; both games keep waiting (and say so) until it's back. And the fields of the
; previous exchange go out in the rotation too, so if the other game missed
; the end of the last exchange (say the cable came out just then), it can
; still finish it from what we send now; neither game can be left waiting.
;
; Returns the other game's action in [wOtherPlayerLinkAction], and sets
; [wLinkBattleDesynced] if the two games' battles no longer match.
	ld a, [wLinkBattleSentAction]
	ld [wLinkCurSent], a
	call LinkFailsafe_BattleFingerprint
	ld [wLinkBattleFingerprint], a
	ld a, $ff
	ld hl, wLinkExchangeCandidates
	ld [hli], a
	ld [hli], a
	ld [hli], a
	ld hl, wLinkExchangeReceived
	ld [hli], a
	ld [hli], a
	ld [hli], a
	xor a
	ld [wLinkExchangePhase], a
	ld [wLinkQuietFrames], a
	ld [wLinkQuietFrames + 1], a
	ld [wLinkDeadFrames], a
	ld [wLinkLostShown], a

.waiting
	call DelayFrame
	call LinkFailsafe_Transfer
	call LinkFailsafe_Watch
	ld hl, wLinkExchangeReceived
	ld b, 3
.check
	ld a, [hli]
	inc a
	jr z, .waiting
	dec b
	jr nz, .check

	ld a, [wLinkLostShown]
	and a
	call nz, LinkFailsafe_ShowWaiting

	vc_hook Wireless_end_exchange
	; keep sending for a moment so the other game can confirm all three too
	; (if it can't yet, the next exchange keeps answering this one)
	vc_patch Wireless_net_delay_3
if DEF(VIRTUAL_CONSOLE)
	ld b, LINK_EXCHANGE_SEND_FRAMES_VC
else
	ld b, LINK_EXCHANGE_SEND_FRAMES
endc
	vc_patch_end
.keep_sending
	push bc
	call DelayFrame
	call LinkFailsafe_Transfer
	pop bc
	dec b
	jr nz, .keep_sending
	vc_hook Wireless_start_send_zero_bytes
	vc_patch Wireless_net_delay_4
if DEF(VIRTUAL_CONSOLE)
	ld b, 26
else
	ld b, 1
endc
	vc_patch_end

	; this exchange becomes the previous one
	ld a, [wLinkCurSent]
	ld [wLinkPrevSent], a
	ld a, [wLinkBattleFingerprint]
	ld [wLinkPrevFingerprint], a
	ld a, [wLinkBattleExchangeTag]
	call NextLinkExchangeTag
	ld [wLinkBattleExchangeTag], a

	ld hl, wLinkExchangeReceived
	ld a, [hli]
	ld [wOtherPlayerLinkAction], a
	ld a, [hli]
	swap a
	or [hl]
	ld hl, wLinkBattleFingerprint
	xor [hl]
	ld [wLinkBattleDesynced], a ; nonzero if the fingerprints differ
	ret

LinkFailsafe_FinishLinkBattle::
; Call when a link battle ends: keep answering the last exchange for a few
; seconds, in case the other game missed its end and is still waiting on it.
	ld a, [wLinkBattleExchangeTag]
	call PrevLinkExchangeTag
	ld [wLinkBattleExchangeTag], a
	ld a, [wLinkPrevSent]
	ld [wLinkCurSent], a
	ld a, [wLinkPrevFingerprint]
	ld [wLinkBattleFingerprint], a
	ld b, LINK_FINISH_FRAMES
.loop
	push bc
	call DelayFrame
	call LinkFailsafe_Transfer
	pop bc
	dec b
	jr nz, .loop
	ret

LinkFailsafe_Transfer:
; Send the next field in the rotation (this exchange's three, then the last
; exchange's three) and take in whatever arrived.
	ld a, [wLinkExchangePhase]
	ld c, a
	inc a
	cp 6
	jr c, .phase_ok
	xor a
.phase_ok
	ld [wLinkExchangePhase], a
	ld a, [wLinkBattleExchangeTag]
	ld e, a
	ld hl, wLinkCurSent
	ld a, c
	sub 3
	jr c, .got_set
	ld c, a
	ld a, e
	call PrevLinkExchangeTag
	ld e, a
	ld hl, wLinkPrevSent
.got_set
	; tag = set's first tag + field * $10
	ld a, c
	swap a
	add e
	ld b, a
	ld a, c
	and a
	ld a, [hli] ; action
	jr z, .send
	ld a, [hl] ; fingerprint
	dec c
	jr nz, .low_nybble
	swap a
.low_nybble
	and $f
.send
	and $f
	or b
	ldh [hSerialSend], a
	ldh a, [hSerialConnectionStatus]
	cp USING_INTERNAL_CLOCK
	jr nz, .receive
	; the clock side can tell a pulled cable: it reads $ff
	ldh a, [hSerialReceive]
	inc a
	ld hl, wLinkDeadFrames
	jr nz, .line_alive
	ld a, [hl]
	inc a
	jr z, .start
	ld [hl], a
	jr .start
.line_alive
	ld [hl], 0
.start
	ld a, $1
	ldh [rSC], a
	ld a, SC_START | SC_INTERNAL
	ldh [rSC], a

.receive
	ldh a, [hSerialReceive]
	ld c, a
	and $f0
	ld b, a
	ld a, [wLinkBattleExchangeTag]
	ld e, a
	ld a, b
	sub e
	jr c, .not_ours
	ld d, 0
	and a
	jr z, .got_field
	inc d
	cp $10
	jr z, .got_field
	inc d
	cp $20
	jr nz, .not_ours
.got_field
	ld a, $ff ; reads as a dead line until the next byte arrives
	ldh [hSerialReceive], a
	xor a
	ld [wLinkQuietFrames], a
	ld [wLinkQuietFrames + 1], a
	ld [wLinkDeadFrames], a
	ld a, c
	and $f
	ld c, a
	; already confirmed: never overwritten
	ld hl, wLinkExchangeReceived
	ld a, l
	add d
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, [hl]
	inc a
	ret nz
	push hl
	ld hl, wLinkExchangeCandidates
	ld a, l
	add d
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, [hl]
	ld [hl], c
	pop hl
	cp c
	ret nz
	ld [hl], c
	ret

.not_ours
	ld hl, wLinkQuietFrames
	inc [hl]
	ret nz
	inc hl
	inc [hl]
	ret nz
	dec [hl] ; stay at the top
	ret

NextLinkExchangeTag:
; a = the next exchange's first tag after a: $10, $40, $70, $a0, $10...
	add LINK_TAG_SET_STEP
	cp LINK_FIRST_TAG + 4 * LINK_TAG_SET_STEP
	ret c
	ld a, LINK_FIRST_TAG
	ret

PrevLinkExchangeTag:
; a = the previous exchange's first tag before a.
	cp LINK_FIRST_TAG + 1
	jr nc, .ok
	ld a, LINK_FIRST_TAG + 4 * LINK_TAG_SET_STEP
.ok
	sub LINK_TAG_SET_STEP
	ret

LinkFailsafe_Watch:
; Tell the players when the link has gone quiet, and help it recover.
	ld a, [wLinkQuietFrames]
	and LINK_REARM_FRAMES - 1
	jr nz, .no_rearm
	ld a, [wLinkQuietFrames]
	ld b, a
	ld a, [wLinkQuietFrames + 1]
	or b
	jr z, .no_rearm
	; a bumped cable can leave the external-clock side counting bits out of
	; step with the clock side; restarting its transfer lines them up again
	ldh a, [hSerialConnectionStatus]
	cp USING_EXTERNAL_CLOCK
	jr nz, .no_rearm
	xor a
	ldh [rSC], a
	ld a, SC_START | SC_EXTERNAL
	ldh [rSC], a
.no_rearm
	ld a, [wLinkLostShown]
	cp 2
	jr nz, .not_cable_out
	; "cable out" is showing: once the line is alive again, say "Waiting…!"
	ld a, [wLinkDeadFrames]
	and a
	ret nz
	jr LinkFailsafe_ShowWaiting
.not_cable_out
	; the clock side reading a dead line for a second: the cable is out
	ld a, [wLinkDeadFrames]
	cp LINK_DEAD_FRAMES
	jr nc, .cable_out
	ld a, [wLinkLostShown]
	and a
	ret nz
	; anyone hearing nothing for a long while: maybe the cable
	ld a, [wLinkQuietFrames + 1]
	cp HIGH(LINK_QUIET_FRAMES)
	ret c
	ld a, 1
	ld [wLinkLostShown], a
	ld de, .StillWaiting
	jr LinkFailsafe_ShowBox

.cable_out
	ld a, 2
	ld [wLinkLostShown], a
	ld de, .CableOut
	jr LinkFailsafe_ShowBox

.StillWaiting:
	db   "Still waiting…"
	next "Check the cable.@"

.CableOut:
	db   "Link cable out!"
	next "Plug it back in.@"

LinkFailsafe_ShowWaiting:
	xor a
	ld [wLinkLostShown], a
	ld de, LinkFailsafe_WaitingText
	; fallthrough
LinkFailsafe_ShowBox:
; Show the two lines at de in a box where "Waiting…!" is.
	push de
	hlcoord 1, 9
	lb bc, 3, 16
	call Textbox
	pop de
	hlcoord 2, 10
	rst PlaceString
	ret

LinkFailsafe_WaitingText:
	db "Waiting…!@"

LinkFailsafe_CheckEnemySwitch::
; [wEnemySwitchTarget] (1-6) came from the other game's choice. It must be a
; Pokemon the opponent actually has that can still battle. If it isn't, the
; two games disagree about the battle: stop it now, instead of sending out an
; empty party slot (a garbage Pokemon with a random picture and HP bar).
; Returns a = [wEnemySwitchTarget] if it's fine.
	ld a, [wEnemySwitchTarget]
	and a
	jr z, .bad
	ld b, a
	ld a, [wOTPartyCount]
	cp b
	jr c, .bad
	ld a, b
	dec a
	ld hl, wOTPartyMon1HP
	ld bc, PARTYMON_STRUCT_LENGTH
	rst AddNTimes
	ld a, [hli]
	or [hl]
	jr z, .bad
	ld a, [wEnemySwitchTarget]
	ret

.bad
	ld hl, LinkBattleOutOfSyncText
	call StdBattleTextbox
	jmp SoftReset
