; Link Edition: regional cups (engine/events/cups.asm)

; cup ids (CupRules)
	const_def
	const CUP_RISING_STAR ; National Park: 3 at level 30
	const CUP_WHIRL       ; Olivine Port: 3-6 Water types at level 50
	const CUP_KIMONO      ; Ecruteak Dance Theatre: 3 of today's type at level 50
	const CUP_DRAGON      ; Blackthorn: 3-6 with a Dragon type at level 50
	const CUP_RENTAL      ; Goldenrod: three generated Pokémon at level 50
	const CUP_WORLD       ; Indigo Plateau: six at level 50
	const CUP_RUDY        ; one Pokémon of the round's type
	const CUP_LUANA       ; two Pokémon, singles rules
DEF NUM_CUPS EQU const_value
DEF NUM_BROADCAST_CUPS EQU CUP_WORLD + 1
DEF RENTAL_CUP_TEAM_SIZE EQU 3
DEF WORLD_CUP_CONTESTANTS EQU 8

; how a cup's team is chosen
	const_def
	const CUPPICK_THREE ; three, in the Battle Tower's party menu
	const CUPPICK_PARTY ; the whole party (eggs aside)
	const CUPPICK_GENERATED ; a new team from the rental sets
	const CUPPICK_SMALL ; choose one or two from the regular party menu

; what a cup asks of its team
	const_def
	const CUPRULE_ANY
	const CUPRULE_ALL_TYPE ; every one has the type
	const CUPRULE_HAS_TYPE ; at least one has the type

; CupRules and CupMakeTeam types besides the 18
DEF CUPTYPE_SCRIPTED EQU $fe ; use the type selected by the script (wCupFoeType)
DEF CUPTYPE_ANY   EQU $ff ; CupMakeTeam: any, with a decent spread

DEF NUM_KIMONO_TYPES EQU 18

; CupSelectTeam results (hScriptVar)
	const_def
	const CUPTEAM_OK
	const CUPTEAM_CANCEL ; backed out of choosing
	const CUPTEAM_SIZE   ; too few or too many
	const CUPTEAM_TYPE   ; doesn't meet the type rule
	const CUPTEAM_DUPLICATE ; chose the same party slot twice
	const CUPTEAM_EGG   ; chose an Egg

; wCupRecords: first wins (byte 0); Kimono Cup wins by type (bytes 1-3)
	const_def
	const CUPWON_RISING_STAR_F
	const CUPWON_DRAGON_F
	const CUPWON_RENTAL_F
	const CUPWON_WORLD_F
DEF CUP_RECORDS_LENGTH EQU 5
DEF CUP_KIMONO_PRIZE_OFFSET EQU 4 ; item owed for an earned type win
; (in the two bytes after them, once set up)
DEF CUP_RECORDS_MAGIC_1 EQU $4c
DEF CUP_RECORDS_MAGIC_2 EQU $45

; your party while you're in a cup (WRAMX bank 2)
DEF CUP_BACKUP_LENGTH EQU 1 + 7 + PARTY_LENGTH * (PARTYMON_STRUCT_LENGTH + PLAYER_NAME_LENGTH + 3 + MON_NAME_LENGTH)
