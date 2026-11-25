; wLinkMode
	const_def 2
	const LINK_TRADECENTER ; 2
	const LINK_COLOSSEUM   ; 3
	const LINK_ROOM_DUMMY  ; 4 (prevents linking with Polished Crystal before commit 35d5fafd, PR #708)

; hSerialReceive high nybbles
DEF SERIAL_TRADECENTER EQU $70
DEF SERIAL_BATTLE      EQU $80

DEF ESTABLISH_CONNECTION_WITH_INTERNAL_CLOCK EQU $01
DEF ESTABLISH_CONNECTION_WITH_EXTERNAL_CLOCK EQU $02

; hSerialConnectionStatus
DEF USING_EXTERNAL_CLOCK       EQU $01
DEF USING_INTERNAL_CLOCK       EQU $02
DEF CONNECTION_NOT_ESTABLISHED EQU $ff

; Similar to SERIAL_PREAMBLE_BYTE, signals the start of Polished-only link data.
DEF SERIAL_POLISHED_PREAMBLE_BYTE     EQU $fb
; length of a patch list (less than any of the signal bytes)
DEF SERIAL_PATCH_LIST_LENGTH          EQU $fc
; signals the start of an array of bytes transferred over the link cable
DEF SERIAL_PREAMBLE_BYTE              EQU $fd
; this byte is used when there is no data to send
DEF SERIAL_NO_DATA_BYTE               EQU $fe
; signals the end of one part of a patch list (there are two parts) for player/enemy party data
DEF SERIAL_PATCH_LIST_PART_TERMINATOR EQU $ff
; used to replace SERIAL_NO_DATA_BYTE
DEF SERIAL_PATCH_REPLACEMENT_BYTE     EQU $ff

; This is equal to (1 to 3 SERIAL_PREAMBLE_BYTEs) + 1 SERIAL_POLISHED_PREAMBLE_BYTE
DEF SERIAL_POLISHED_MAX_PREAMBLE_LENGTH EQU 4
; size of the Polished link check buffers (preamble, options, ROM checksum, rules)
DEF LINK_MISC_BUFFER_LENGTH EQU 12

DEF SERIAL_PREAMBLE_LENGTH    EQU 6
DEF SERIAL_RN_PREAMBLE_LENGTH EQU 7
DEF SERIAL_RNS_LENGTH         EQU 10

; Link Edition: the check both games make before a link battle starts
; (engine/link/link_failsafe.asm): three 2-byte fingerprints, sent as nybbles
; plus room for extra preamble bytes: while waiting to sync, each game keeps
; resending its first preamble byte, so more of them can arrive
DEF LINK_CHECK_SLACK  EQU 8
DEF LINK_CHECK_LENGTH EQU SERIAL_PREAMBLE_LENGTH + 3 * 2 * 2 + LINK_CHECK_SLACK
DEF LINK_VERDICT_COPIES EQU 4
DEF LINK_VERDICT_LENGTH EQU SERIAL_PREAMBLE_LENGTH + LINK_VERDICT_COPIES + LINK_CHECK_SLACK
; how many times the team swap is tried before giving up
DEF LINK_SETUP_TRIES EQU 5

; Random Battle (engine/link/random_battle.asm)
DEF RANDOM_SET_LENGTH     EQU 9  ; bytes per set in data/link/random_battle_sets.asm
DEF RANDOM_SET_PROFILE    EQU 8  ; offset of a set's type profile index
DEF RANDOM_PROFILE_LENGTH EQU 5  ; two types, then 3 weakness bytes
DEF NUM_RANDOM_TYPES      EQU 18 ; types counted for the type spread
DEF RANDOM_MAX_SAME_TYPE  EQU 2  ; at most this many team members share a type
DEF RANDOM_MAX_SAME_WEAK  EQU 3  ; at most this many are weak to the same type
DEF RANDOM_MAX_TRIES      EQU 200 ; rejected picks in a row before starting over
DEF LINK_CHECK_OK     EQU $1a
DEF LINK_CHECK_BAD    EQU $15
; frames to keep sending a confirmed action exchange, so the other game can
; confirm all three fields too (LinkFailsafe_ExchangeAction)
DEF LINK_EXCHANGE_SEND_FRAMES EQU 18
; link battle action exchanges cycle through four sets of three tags (high
; nybbles $1-$c), so a byte from the exchange before last is never mistaken
; for one from the next
DEF LINK_FIRST_TAG    EQU $10
DEF LINK_TAG_SET_STEP EQU $30
; how long a finished link battle keeps answering its last exchange
DEF LINK_FINISH_FRAMES EQU 180
; the clock side reading a dead line this many frames in a row: cable out
DEF LINK_DEAD_FRAMES EQU 60
; anyone hearing nothing this long: "Still waiting... check the cable"
DEF LINK_QUIET_FRAMES EQU 15 * 60
; the external-clock side restarts its transfer every this many quiet frames
DEF LINK_REARM_FRAMES EQU 32
DEF LINK_EXCHANGE_SEND_FRAMES_VC EQU 78 ; Virtual Console's wireless link is slower

DEF SERIAL_MAIL_PREAMBLE_BYTE    EQU $20
DEF SERIAL_MAIL_REPLACEMENT_BYTE EQU $21
DEF SERIAL_MAIL_PREAMBLE_LENGTH  EQU 5

; timeout duration after exchanging a byte
DEF SERIAL_LINK_BYTE_TIMEOUT EQU $5000

; How long Special_WaitForLinkedFriend waits for the other player to reach the
; Cable Club receptionist. Its inner counter starts at $ff and both counters are
; decremented once per frame, so the window is 255 + 256 * (N - 1) frames:
; N = 2 is ~511 frames (~8.6s), N = 6 is ~1535 frames (~26s) at 59.7 fps.
DEF LINK_WAIT_FOR_FRIEND_FRAMES EQU 6

; How many frames Link_CheckCommunicationError.AcknowledgeSerial spends waiting
; for the other player to acknowledge, once per handshake attempt. The Virtual
; Console (wireless) path already uses a wider value for its slower transport.
DEF LINK_ACKNOWLEDGE_FRAMES    EQU 20
DEF LINK_ACKNOWLEDGE_FRAMES_VC EQU 26

; High byte of the countdown budget CheckLinkTimeout_Gen2 hands to
; Link_CheckCommunicationError for the post-save handshake (the low byte is $32).
; Serial_ExchangeByte counts this down and gives up at zero, so a larger value is
; more tolerant of the two players saving at different speeds.
DEF LINK_HANDSHAKE_BUDGET_HI    EQU 2
DEF LINK_HANDSHAKE_BUDGET_HI_VC EQU 3

; all unique game IDs for the Polished Crystal engine
	const_def 1
	const LINK_GAME_ID_PC_FAITHFUL     ; 1
	const LINK_GAME_ID_PC_NON_FAITHFUL ; 2
	; Link Edition has its own IDs, so it never links with stock Polished
	; Crystal or with the pre-release Link Edition builds (link versions 6-10),
	; whatever their link version. That lets Link Edition restart at version 1.
	const LINK_GAME_ID_LE_FAITHFUL     ; 3
	const LINK_GAME_ID_LE_NON_FAITHFUL ; 4

; this game's ID, and the other ID that it can still trade with
if DEF(FAITHFUL)
	DEF LINK_GAME_ID EQU LINK_GAME_ID_LE_FAITHFUL
	DEF OTHER_GAME_ID EQU LINK_GAME_ID_LE_NON_FAITHFUL
else
	DEF LINK_GAME_ID EQU LINK_GAME_ID_LE_NON_FAITHFUL
	DEF OTHER_GAME_ID EQU LINK_GAME_ID_LE_FAITHFUL
endc

; this game's link version
; Bump whenever battle-affecting link logic changes (party normalization,
; healing, clauses, base stats, abilities, damage) so mismatched builds can't
; connect and desync. Link Edition 1.0 (first family release) is version 1;
; the Christmas release is 2. The expanded Cable Club formats are version 3.
DEF LINK_VERSION EQU 3
; This is the minimum link version allowed for trading (the party layout
; hasn't changed since version 1, so trades with 1.0 still work)
DEF LINK_MIN_TRADE_VERSION EQU 1

; Battle formats use a four-bit ID in the Cable Club handshake.
	const_def
	const LINK_RULE_STANDARD
	const LINK_RULE_RANDOM
	const LINK_RULE_RISING_STAR
	const LINK_RULE_UNRESTRICTED
DEF NUM_LINK_BATTLE_RULES EQU const_value
assert NUM_LINK_BATTLE_RULES <= 16

; PerformLinkChecks error codes
	const_def
	const LINK_ERR_OLD_PC_DETECT         ; 0
	const LINK_ERR_SUCCESS               ; 1
	const LINK_ERR_MISMATCH_GAME_ID      ; 2
	const LINK_ERR_MISMATCH_VERSION      ; 3
	const LINK_ERR_VERSION_TOO_LOW       ; 4
	const LINK_ERR_OTHER_VERSION_TOO_LOW ; 5
	const LINK_ERR_MISMATCH_GAME_OPTIONS ; 6
	const LINK_ERR_INCOMPATIBLE_ROOMS    ; 7
	const LINK_ERR_MISMATCH_BUILD        ; 8 (Link Edition: different ROMs)
	const LINK_ERR_MISMATCH_RULES        ; 9 (Link Edition: different battle rules)
