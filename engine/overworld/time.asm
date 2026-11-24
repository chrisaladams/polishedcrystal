ClearDailyTimers:
	xor a
	ld [wLuckyNumberDayBuffer], a
	ld [wDailyResetTimer], a
	ret

InitCallReceiveDelay::
	xor a
	ld [wTimeCyclesSinceLastCall], a
	; fallthrough

NextCallReceiveDelay:
	ld a, [wTimeCyclesSinceLastCall]
	cp 3
	jr c, .lookup
	ld a, 3
.lookup
	add a
	ld e, a
	ld d, 0
	ld hl, .Delays
	add hl, de
	ld a, [hli]
	ld [wPhoneDelayRemaining], a
	ld a, [hl]
	ld [wPhoneDelayRemaining + 1], a
	call ReadGameplaySeconds
	ld hl, wPhoneDelayLastTick
	ld [hl], e
	inc hl
	ld [hl], d
	ret

.Delays:
	dw 20 * 60, 10 * 60, 5 * 60, 3 * 60

CheckReceiveCallTimer:
	call CheckReceiveCallDelay ; check timer
	ret nc
	ld hl, wTimeCyclesSinceLastCall
	ld a, [hl]
	cp 3
	jr nc, .ok
	inc [hl]

.ok
	call NextCallReceiveDelay ; restart timer
	scf
	ret

CheckDayDependentEventHL:
	inc hl
	call CalcDaysSince
	dec hl
	ld a, [hl]
	sub c
	jr c, .expired
	ld [hl], a
	ret nz
.expired
	ld [hl], 0
	scf
	ret

ReadGameplaySeconds:
; Read the 16-bit elapsed-seconds counter in DE, retrying across a carry.
	ld a, [wGameplaySeconds + 1]
	ld d, a
	ld a, [wGameplaySeconds]
	ld e, a
	ld a, [wGameplaySeconds + 1]
	cp d
	jr nz, ReadGameplaySeconds
	ret

CheckReceiveCallDelay:
	call ReadGameplaySeconds
	ld hl, wPhoneDelayLastTick
	ld a, e
	sub [hl]
	ld [hl], e
	inc hl
	ld c, a
	ld a, d
	sbc [hl]
	ld [hl], d
	ld b, a
	or c
	jr z, .pending

	; Lightning Rod still halves the playtime between calls.
	push bc
	call GetLeadAbility
	pop bc
	cp LIGHTNING_ROD
	jr nz, .subtract
	sla c
	rl b
	jr c, .expired
.subtract
	ld hl, wPhoneDelayRemaining
	ld a, [hl]
	sub c
	ld [hli], a
	ld c, a
	ld a, [hl]
	sbc b
	ld [hl], a
	jr c, .expired
	or c
	jr z, .expired
.pending
	and a
	ret
.expired
	scf
	ret

RestartDailyResetTimer:
	ld hl, wDailyResetTimer
	ld a, 1
	ld [hli], a
	push hl
	call UpdateTime
	pop hl
	jr CopyDayToHL

InitializeStartDay:
	call UpdateTime
	ld hl, wTimerEventStartDay
CopyDayToHL:
	ld a, [wCurDay]
	ld [hl], a
	ret

CheckDailyResetTimer::
	ld hl, wDailyResetTimer
	call CheckDayDependentEventHL
	ret nc

	xor a
	ld hl, wDailyFlags
	ld [hli], a ; wDailyFlags
	ld [hli], a ; wDailyFlags2
	ld [hli], a ; wDailyFlags3
	ld [hli], a ; wDailyFlags4
	ld [hli], a ; wWeeklyFlags
	ld [hli], a ; wWeeklyFlags2
	ld [hl], a ; wSwarmFlags
	ld [wLuckyNumberShowFlag], a
	ld hl, wFruitTreeFlags
rept (NUM_FRUIT_TREES + 7) / 8 - 1
	ld [hli], a
endr
	ld [hl], a
	ld hl, wDailyRematchFlags
rept 4 - 1
	ld [hli], a
endr
	ld [hl], a
	ld hl, wDailyPhoneItemFlags
rept 4 - 1
	ld [hli], a
endr
	ld [hl], a
	ld hl, wDailyPhoneTimeOfDayFlags
rept 4 - 1
	ld [hli], a
endr
	ld [hl], a

	call PickDailyTrainerHouseOpponent

	ld hl, wKenjiBreakTimer
	ld a, [hl]
	and a
	jr z, .RestartKenjiBreakCountdown
	dec [hl]
.RestartKenjiBreakCountdown:
	call z, Special_SampleKenjiBreakCountdown
	jr RestartDailyResetTimer

PickDailyTrainerHouseOpponent::
	ld a, NUM_TRAINER_HOUSE_OPPONENTS
	call RandomRange
	inc a
	ld [wDailyTrainerHouseOpponent], a
.got_opponent
	call .IsOpponentValid
	and a
	jr z, PickDailyTrainerHouseOpponent
	ret

.IsOpponentValid:
	cp OPP_EN
	jr nz, .not_en
	; must have caught all three legendary birds to battle En
	farjp SpecialBirdsCheck
.not_en
	cp OPP_MADOKA
	jr nz, .not_madoka
	; must have caught all three legendary beasts to battle Madoka
	farjp SpecialBeastsCheck
.not_madoka
	ld a, TRUE
	ret

Special_SampleKenjiBreakCountdown:
; Generate a random number between 3 and 6
	call Random
	and 3
	add 3
	ld [wKenjiBreakTimer], a
	ret

StartBugContestTimer:
	ld a, BUG_CONTEST_MINUTES
	ld [wBugContestMinsRemaining], a
	xor a
	ld [wBugContestSecsRemaining], a
	ret

CheckBugContestTimer::
	ld a, [wBugContestMinsRemaining]
	ld hl, wBugContestSecsRemaining
	or [hl]
	ret nz
	scf
	ret

CheckPokerusTick::
	ld hl, wTimerEventStartDay
	call CalcDaysSince
	ld a, c
	and a
	ret z ; no elapsed days
	ld b, c

	ld a, [wPartyCount]
	and a
	ret z ; don't waste time if we don't have any party members

; shift all partymon pokerus values to the left b times
; if this overflows the pokerus nybble, the infection no longer spreads
	ld c, a
	ld hl, wPartyMon1PokerusStatus
.loop
	ld a, [hl]
	and POKERUS_MASK
	jr z, .next
	assert POKERUS_CURED & %1000
	ld d, POKERUS_CURED ; no need to check if pokerus status = POKERUS_CURED, bit 3 is already set
	ld e, b
.inner_loop
	rlca
	cp POKERUS_MASK + 1
	jr nc, .cured
	dec e
	jr nz, .inner_loop
	ld d, a
.cured
	ld a, [hl]
	and ~POKERUS_MASK
	or d
	ld [hl], a
.next
	ld de, PARTYMON_STRUCT_LENGTH
	add hl, de
	dec c
	jr nz, .loop
	ret

CalcDaysSince:
; Update the old day at HL and return elapsed days in C.
	ld a, [wCurDay]
	ld c, a
	sub [hl]
	ld [hl], c
	jr nc, .same_cycle
	add WORLD_CLOCK_DAYS
.same_cycle
	ld c, a
	ret
