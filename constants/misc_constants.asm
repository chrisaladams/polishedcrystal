; Boolean checks
DEF FALSE EQU 0
DEF TRUE  EQU 1

; FlagAction arguments (see home/flag.asm)
	const_def
	const RESET_FLAG
	const SET_FLAG
	const CHECK_FLAG

; input
DEF NO_INPUT EQU %00000000

; save file corruption check values
DEF SAVE_CHECK_VALUE_1     EQU 97
DEF SAVE_CHECK_VALUE_2     EQU 127
DEF SAVE_CHECK_VALUE_1_OLD EQU 99 ; check digit before save version 7

; save file version
DEF SAVE_VERSION EQU 11

; time of day boundaries
DEF MORN_HOUR EQU  6 ; 06:00-09:00
DEF DAY_HOUR  EQU  9 ; 09:00-15:00
DEF EVE_HOUR  EQU 15 ; 15:00-18:00
DEF NITE_HOUR EQU 18 ; 18:00-06:00
DEF MAX_HOUR  EQU 24 ; 12 AM - 12 AM (24 hours)

DEF BUENA_START_HOUR EQU 17

; The GBC refreshes at about 59.7275 Hz. 186/256 of seconds use 60 frames.
DEF GAME_CLOCK_LONG_FRACTION EQU 186
DEF WORLD_CLOCK_SPEED EQU 16 ; in-game seconds per gameplay second
DEF WORLD_CLOCK_DAYS EQU 18 * 7 ; keep both weekdays and the Kimono rotation in order
DEF SOFTWARE_CLOCK_MARKER EQU $434c
DEF CLOCK_RESET_PENDING EQU $a5

; significant money values
DEF START_MONEY EQU 3000
DEF MOM_MONEY   EQU 2300
DEF MAX_MONEY   EQU 9999999
DEF MAX_COINS   EQU 50000

; link record
DEF MAX_LINK_RECORD EQU 9999

; day-care
DEF MAX_DAY_CARE_EXP EQU $500000

; hall of fame
DEF HOF_MASTER_COUNT EQU 200

; Kirk ID
DEF KIRK_SHUCKIE_ID EQU 00518

; initial best Magikarp length (in mm)
DEF BEST_MAGIKARP_LENGTH EQU 1066

; SGB command MLT_REQ can be used to detect SGB hardware
DEF JOYP_SGB_MLT_REQ EQU %00000011

; crash error codes
	const_def
	const ERR_RST_0
	const ERR_RST_38
	const ERR_DIV_ZERO
	const ERR_EGG_SPECIES
	const ERR_EXECUTING_RAM
	const ERR_STACK_OVERFLOW
	const ERR_STACK_UNDERFLOW
	const ERR_BT_STATE
	const ERR_CHECKSUM_MISMATCH
	const ERR_PC_BOX_OLD
	const ERR_PC_BOX_ZERO
	const ERR_PC_BOX_COLLISION
	const ERR_WINDOW_OVERFLOW
	const ERR_WINDOW_UNDERFLOW
	const ERR_SRAM_MISMATCH
	const ERR_PEBKAC
DEF NUM_ERR_CODES EQU const_value
