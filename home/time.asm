UpdateTime::
; Assumes rWBK == 1
	call FixTime
	farjp GetTimeOfDay

FixTime:
; Read a coherent clock snapshot if VBlank advances it during this read.
.snapshot
	ld hl, wRTCSeconds
	ld a, [hld]
	ld b, a
	ld a, [hld]
	ld d, a
	ld a, [hld]
	ld e, a
	ld c, [hl]
	ld a, [wRTCSeconds]
	cp b
	jr nz, .snapshot

	ldh [hSeconds], a
	ld a, d
	ldh [hMinutes], a
	ld a, e
	ldh [hHours], a
	ld a, c
	ld [wCurDay], a
	ret

SetTimeOfDay::
	xor a
	ld [wStringBuffer2], a
	ld [wStringBuffer2 + 3], a
	jr InitTime

SetDayOfWeek::
	call UpdateTime
	ldh a, [hHours]
	ld [wStringBuffer2 + 1], a
	ldh a, [hMinutes]
	ld [wStringBuffer2 + 2], a
	ldh a, [hSeconds]
	ld [wStringBuffer2 + 3], a
	; fallthrough

InitTime::
	farjp _InitTime

PanicResetClock::
	ld hl, wRTCDayHi
	ld bc, 5
	xor a
	rst ByteFill
	ret

GetValueByTimeOfDay::
; input: hl = 'db morn val, day val, eve val, nite val'
; output: a = value corresponding to current hour
	assert 0 < MORN_HOUR && MORN_HOUR < DAY_HOUR && DAY_HOUR < EVE_HOUR && EVE_HOUR < NITE_HOUR
	ldh a, [hHours]
	cp MORN_HOUR
	jr nc, .not_early
	ld a, NITE_HOUR
.not_early
	cp DAY_HOUR
	jr c, .ok
	inc hl
	cp EVE_HOUR
	jr c, .ok
	inc hl
	cp NITE_HOUR
	jr c, .ok
	inc hl
.ok
	ld a, [hl]
	ret
