; Link Edition: story scene effects (engine/events/cinematic.asm,
; macros/scripts/cinematic.asm)

; scene_tint colors (CinematicTintColors): each tint blends every color on
; screen halfway to its own, so two in a row go three quarters of the way
	const_def
	const TINT_DARK   ; toward black: night falling, a cave's depths
	const TINT_GREEN  ; Celebi, the forest's power
	const TINT_RED    ; danger, fire
	const TINT_BLUE   ; water, cold, the sea's guardians
	const TINT_PURPLE ; psychic power, Mewtwo, the Unown
	const TINT_GOLD   ; sunrise, Ho-Oh, a trophy
	const TINT_WHITE  ; mist, a dream, a memory
DEF NUM_TINTS EQU const_value

; wCinematicFlags
	const_def
	const CINEMATIC_ACTIVE_F ; between scene_begin and scene_end (no lightning)
