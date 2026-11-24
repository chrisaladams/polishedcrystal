GetTimeOfDay::
	ld hl, .TimesOfDay
	call GetValueByTimeOfDay
	ld [wTimeOfDay], a
	ret

.TimesOfDay:
	db MORN, DAY, EVE, NITE

StageGameClockForSave:
	call UpdateTime
	ld hl, wRTC
	ld a, [wCurDay]
	ld [hli], a
	ldh a, [hHours]
	ld [hli], a
	ldh a, [hMinutes]
	ld [hli], a
	ldh a, [hSeconds]
	ld [hli], a
MarkSoftwareClock:
	ld hl, wSoftwareClockMarker
	ld a, LOW(SOFTWARE_CLOCK_MARKER)
	ld [hli], a
	ld [hl], HIGH(SOFTWARE_CLOCK_MARKER)
	ret

RestoreGameClock:
; Old saves kept the displayed clock even when their cartridge's RTC kept
; running. Resume from that snapshot on the first Continue in this build.
	ld hl, wSoftwareClockMarker
	ld a, [hli]
	cp LOW(SOFTWARE_CLOCK_MARKER)
	jr nz, .legacy
	ld a, [hl]
	cp HIGH(SOFTWARE_CLOCK_MARKER)
	ret z
.legacy
	xor a
	ld [wClockFramePhase], a
	ld [wGameplaySeconds], a
	ld [wGameplaySeconds + 1], a
	ld hl, wRTC
	call SetGameClock
	call MarkSoftwareClock
	farjp NextCallReceiveDelay

_InitTime::
	ld hl, wStringBuffer2
	; fallthrough
SetGameClock:
; HL points to a day, hour, minute, second tuple.
	ld a, [wGameLogicPaused]
	push af
	ld a, TRUE
	ld [wGameLogicPaused], a
	ld a, [hli]
	cp WORLD_CLOCK_DAYS
	jr c, .day
	sub WORLD_CLOCK_DAYS
.day
	ld [wRTCDayLo], a
	ld a, [hli]
	cp MAX_HOUR
	jr c, .hour
	ld a, MORN_HOUR
.hour
	ld [wRTCHours], a
	ld a, [hli]
	cp 60
	jr c, .minutes
	xor a
.minutes
	ld [wRTCMinutes], a
	ld a, [hl]
	cp 60
	jr c, .seconds
	xor a
.seconds
	ld [wRTCSeconds], a
	xor a
	ld [wRTCDayHi], a
	pop af
	ld [wGameLogicPaused], a
	ret

CheckClockResetRequest:
	ld a, BANK(sRTCStatusFlags)
	call GetSRAMBank
	ld a, [sRTCStatusFlags]
	cp CLOCK_RESET_PENDING
	jmp CloseSRAM

ClearClockResetRequest:
	ld a, BANK(sRTCStatusFlags)
	call GetSRAMBank
	xor a
	ld [sRTCStatusFlags], a
	jmp CloseSRAM
