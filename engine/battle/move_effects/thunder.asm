BattleCommand_thunderaccuracy:
	ld a, BATTLE_VARS_MOVE_TYPE
	call GetBattleVarAddr
	inc hl
	call GetSolarizedWeather
	call nz, GetWeatherAfterOpponentUmbrella
	cp WEATHER_RAIN
	jr z, .rain
	cp WEATHER_SUN
	ret nz
	; Move accuracy is a plain percentage here (see data/moves/moves.asm), not
	; the 0-255 scale the `percent` macro produces: "50 percent + 1" was 128,
	; which made Thunder never miss in sun.
	ld [hl], 50
	ret

.rain
	ld [hl], 100
	ret
