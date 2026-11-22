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
	ld hl, wLinkCheckSend
	ld de, wLinkCheckRecv
	ld bc, SERIAL_PREAMBLE_LENGTH + 2
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
