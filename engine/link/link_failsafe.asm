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
	ld a, LINK_CHECK_OK
	jr .verdict

.bad_pop1
	pop bc
.bad
	ld a, LINK_CHECK_BAD
.verdict
	; tell each other the verdict: the battle only starts if both are happy
	ld [wLinkSetupFailed], a
	ld hl, wLinkCheckSend
	ld b, SERIAL_PREAMBLE_LENGTH
	ld c, a
	ld a, SERIAL_PREAMBLE_BYTE
.preamble2
	ld [hli], a
	dec b
	jr nz, .preamble2
	ld a, c
	ld [hli], a
	ld [hli], a
	call .PutSlack
	ld hl, wLinkCheckSend
	ld de, wLinkCheckRecv
	ld bc, LINK_VERDICT_LENGTH
	farcall Serial_ExchangeBytes
	xor a
	ldh [rIF], a
	ld a, IE_SERIAL | IE_VBLANK
	ldh [rIE], a

	ld de, wLinkCheckRecv
	call .SkipPreamble
	ld a, [de]
	cp LINK_CHECK_OK
	jr nz, .failed
	inc de
	ld a, [de]
	cp LINK_CHECK_OK
	jr nz, .failed
	ld a, [wLinkSetupFailed]
	cp LINK_CHECK_OK
	jr nz, .failed
	xor a
	ld [wLinkSetupFailed], a
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
	para "Please try again."
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
; Three fields go out in rotation, one byte per frame, each with its own tag:
; the action, then the fingerprint's high and low nybbles. Each exchange uses
; a different set of tags from the last (wLinkBattleExchangeTag alternates
; between SERIAL_BATTLE and SERIAL_BATTLE_ODD), so stale bytes are ignored. A
; field only counts once the same value arrives twice in a row, and can't be
; overwritten after that, so one bad bit on the cable can't change it.
;
; Returns the other game's action in [wOtherPlayerLinkAction], and sets
; [wLinkBattleDesynced] if the two games' battles no longer match.
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

.waiting
	call DelayFrame
	call .Transfer
	ld hl, wLinkExchangeReceived
	ld b, 3
.check
	ld a, [hli]
	inc a
	jr z, .waiting
	dec b
	jr nz, .check

	vc_hook Wireless_end_exchange
	; keep sending so the other game can confirm all three too
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
	call .Transfer
	pop bc
	dec b
	jr nz, .keep_sending

	vc_hook Wireless_start_send_zero_bytes
	vc_patch Wireless_net_delay_4
if DEF(VIRTUAL_CONSOLE)
	ld b, 26
else
	ld b, LINK_EXCHANGE_SEND_FRAMES / 2
endc
	vc_patch_end
.acknowledge
	call DelayFrame
	call LinkDataReceived
	dec b
	jr nz, .acknowledge

	ld a, [wLinkBattleExchangeTag]
	xor SERIAL_BATTLE ^ SERIAL_BATTLE_ODD
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

.Transfer:
; Send the next of our three fields, and take in whatever arrived.
	ld a, [wLinkExchangePhase]
	ld c, a
	inc a
	cp 3
	jr c, .phase_ok
	xor a
.phase_ok
	ld [wLinkExchangePhase], a
	; tag = this exchange's tag + field * $20
	ld a, c
	swap a
	add a
	ld b, a
	ld a, [wLinkBattleExchangeTag]
	add b
	ld b, a
	ld a, c
	and a
	ld a, [wLinkBattleSentAction]
	jr z, .send
	ld a, [wLinkBattleFingerprint]
	dec c
	jr nz, .low_nybble
	swap a
.low_nybble
	and $f
.send
	or b
	ldh [hSerialSend], a
	ldh a, [hSerialConnectionStatus]
	cp USING_INTERNAL_CLOCK
	jr nz, .receive
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
	ret c
	ld d, 0
	and a
	jr z, .got_field
	inc d
	cp $20
	jr z, .got_field
	inc d
	cp $40
	ret nz
.got_field
	xor a
	ldh [hSerialReceive], a
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
