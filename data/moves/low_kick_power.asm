LowKickPowerByWeight:
	;    BP, weight (hectograms, as in data/pokemon/body_data.asm)
	; The last three used to read 50, 25, 10 (kilograms), which made any target
	; between 5 kg and 100 kg take 80 power.
	dbw 120, 2000 ; > 200 kg
	dbw 100, 1000 ; > 100 kg
	dbw  80, 500  ; > 50 kg
	dbw  60, 250  ; > 25 kg
	dbw  40, 100  ; > 10 kg
	dbw  20, 0
