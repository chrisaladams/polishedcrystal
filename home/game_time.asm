; Reset playtime and the elapsed-seconds counter used by short timers.
ResetGameTime::
	xor a
	ld [wGameTimeCap], a
	ld [wGameTimeHours], a
	ld [wGameTimeHours + 1], a
	ld [wGameTimeMinutes], a
	ld [wGameTimeSeconds], a
	ld [wGameTimeFrames], a
	ld [wClockFramePhase], a
	ld [wGameplaySeconds], a
	ld [wGameplaySeconds + 1], a
	ret

GameTimer::
	ldh a, [rWBK]
	push af
	ld a, 1
	ldh [rWBK], a

	call UpdateGameTimer

	pop af
	ldh [rWBK], a
	ret

UpdateGameTimer::
; Increment the game timer by one frame.
; The game timer is capped at 999:59:59.00.

; Don't update if game logic is paused.
	ld a, [wGameLogicPaused]
	and a
	ret nz

; Is the timer paused?
	ld a, [wGameTimerPaused]
	and a
	ret z

	; Distribute 59- and 60-frame seconds to follow the hardware refresh rate.
	ld a, [wClockFramePhase]
	add GAME_CLOCK_LONG_FRACTION
	ld b, a
	ld hl, wGameTimeFrames
	ld a, [hl]
	inc a
	ld [hl], a
	sbc 59
	ret c

	xor a
	ld [hl], a
	ld a, b
	ld [wClockFramePhase], a

	call TickSoftwareClock

	; Only the displayed playtime stops at 999:59:59.
	ld hl, wGameTimeCap
	bit 0, [hl]
	ret nz

; +1 second
	ld hl, wGameTimeSeconds
	ld a, [hl]
	inc a

	cp 60 ; seconds/minute
	jr nc, .minute

	ld [hl], a
	ret

.minute
	xor a
	ld [hl], a

; +1 minute
	ld hl, wGameTimeMinutes
	ld a, [hl]
	inc a

	cp 60 ; minutes/hour
	jr nc, .hour

	ld [hl], a
	ret

.hour
	xor a
	ld [hl], a

; +1 hour
	ld hl, wGameTimeHours
	ld a, [hli]
	ld l, [hl]
	ld h, a
	inc hl

; Cap the timer after 1000 hours.
	ld a, h
	cp HIGH(1000)
	jr c, .ok

	ld a, l
	cp LOW(1000)
	jr c, .ok

	ld hl, wGameTimeCap
	set 0, [hl]

	ld a, 59 ; 999:59:59.00
	ld [wGameTimeMinutes], a
	ld [wGameTimeSeconds], a
	ret

.ok
	ld a, h
	ld [wGameTimeHours], a
	ld a, l
	ld [wGameTimeHours + 1], a
	ret

TickSoftwareClock:
	; Linked battle timing is independent of each cartridge's world.
	ld a, [wLinkMode]
	and a
	ret nz
	ld hl, wGameplaySeconds
	inc [hl]
	jr nz, .world
	inc hl
	inc [hl]

.world
	ld hl, wRTCSeconds
	ld a, [hl]
	add WORLD_CLOCK_SPEED
	cp 60
	jr c, .write_seconds
	sub 60
	ld [hld], a
	inc [hl] ; minutes
	ld a, [hl]
	cp 60
	jr c, .short_timers
	xor a
	ld [hld], a
	inc [hl] ; hours
	ld a, [hl]
	cp MAX_HOUR
	jr c, .short_timers
	xor a
	ld [hld], a
	inc [hl] ; days
	ld a, [hl]
	cp WORLD_CLOCK_DAYS
	jr c, .short_timers
	ld [hl], 0
	jr .short_timers

.write_seconds
	ld [hl], a
.short_timers
	ld hl, wStatusFlags2
	bit STATUSFLAGS2_BUG_CONTEST_TIMER_F, [hl]
	ret z
	ld hl, wBugContestSecsRemaining
	ld a, [hl]
	and a
	jr z, .borrow_minute
	dec [hl]
	ret
.borrow_minute
	dec hl
	assert wBugContestSecsRemaining == wBugContestMinsRemaining + 1
	ld a, [hl]
	and a
	ret z
	dec [hl]
	inc hl
	ld [hl], 59
	ret
