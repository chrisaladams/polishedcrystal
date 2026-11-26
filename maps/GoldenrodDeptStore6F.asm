GoldenrodDeptStore6F_MapScriptHeader:
	def_scene_scripts

	def_callbacks

	def_warp_events
	warp_event 15,  0, GOLDENROD_DEPT_STORE_5F, 2
	warp_event  2,  0, GOLDENROD_DEPT_STORE_ELEVATOR, 1
	warp_event 13,  0, GOLDENROD_DEPT_STORE_ROOF, 1

	def_coord_events

	def_bg_events
	bg_event 14,  0, BGEVENT_JUMPTEXT, GoldenrodDeptStore6FDirectoryText

	def_object_events
	object_event 10,  2, SPRITE_PICNICKER, SPRITEMOVEDATA_WALK_LEFT_RIGHT, 0, 1, -1, 0, OBJECTTYPE_COMMAND, jumptextfaceplayer, GoldenrodDeptStore6FLassText, -1
	object_event  8,  2, SPRITE_POKEMANIAC, SPRITEMOVEDATA_STANDING_UP, 0, 0, -1, PAL_NPC_RED, OBJECTTYPE_SCRIPT, 0, GoldenrodRentalCup, -1

GoldenrodDeptStore6FLassText:
	text "Do you listen to"
	line "Lucky Channel?"

	para "If you want to"
	line "win, trade #mon"

	para "with as many peo-"
	line "ple as possible to"

	para "get different ID"
	line "numbers."
	done

GoldenrodDeptStore6FSuperNerdText:
	text "If you're tired,"
	line "try the vending"
	cont "machine's drinks."

	para "Your #mon will"
	line "love them too."
	done

GoldenrodDeptStore6FDirectoryText:
	text "Take a Break from"
	line "Shopping!"

	para "6F Tranquil Square"

	para "Rental Cup desk"
	line "on this floor."
	done

GoldenrodRentalCup:
	faceplayer
	opentext
	checkevent EVENT_RENTAL_CUP_PRIZE_PENDING
	iftruefwd .FirstPrize
	writetext .WelcomeText
	yesorno
	iffalse_jumpopenedtext GoldenrodDeptStore6FSuperNerdText
	loadmem wCupId, CUP_RENTAL
	callasm CupSelectTeam
.Choose:
	writetext .TeamText
	loadmenu .Menu
	verticalmenu
	closewindow
	ifequalfwd 1, .Enter
	ifequalfwd 2, .Look
	endtext

.Look:
	; Link Edition: each rental's stats, moves, item and ability
	closetext
	callasm OTPartySummary
	opentext
	sjump .Choose

.Enter:
	closetext
	callasm CupBegin
	showtext .Round1Text
	winlosstext .WinText, .LossText
	loadmem wCupFoeSize, RENTAL_CUP_TEAM_SIZE
	loadtrainer SCHOOLBOY, JACK1
	loadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
	startbattle
	reloadmap
	iftruefwd .Lost
	callasm CupHealTeam
	showtext .Round2Text
	winlosstext .WinText, .LossText
	loadmem wCupFoeSize, RENTAL_CUP_TEAM_SIZE
	loadtrainer PICNICKER, GINA1
	loadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
	startbattle
	reloadmap
	iftruefwd .Lost
	callasm CupHealTeam
	showtext .FinalText
	winlosstext .WinText, .LossText
	loadmem wCupFoeSize, RENTAL_CUP_TEAM_SIZE
	loadtrainer COOLTRAINERM, RS_REX
	loadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
	startbattle
	reloadmap
	iftruefwd .Lost
	callasm CupEnd
	callasm CupWin
	opentext
	iffalsefwd .Again
	setevent EVENT_RENTAL_CUP_PRIZE_PENDING
	writetext .ChampionText
	promptbutton
.FirstPrize:
	verbosegiveitem BOTTLE_CAP, iffalse_jumpopenedtext .PendingText
	clearevent EVENT_RENTAL_CUP_PRIZE_PENDING
	jumpopenedtext .ReturnText
.Again:
	writetext .ChampionText
	promptbutton
	verbosegiveitem BIG_PEARL, iffalse_endtext
	jumpopenedtext .ReturnText
.Lost:
	callasm CupEnd
	jumptext .OutText

.WelcomeText:
	text "The Rental Cup!"
	para "We lend both sides"
	line "three #mon at"
	cont "level 50. Win all"
	cont "three rounds."
	para "It's free. Your"
	line "own team waits"
	cont "here. Want a draw?"
	done
.Menu:
	db MENU_BACKUP_TILES
	menu_coords 0, 0, 8, 7
	dw .Choices
	db 1
.Choices:
	db STATICMENU_CURSOR
	db 3
	db "Enter@"
	db "Look@"
	db "Cancel@"

.TeamText:
	text "Your rentals are:"
	line "@"
	text_ram wOTPartyMon1Nickname
	cont "@"
	text_ram wOTPartyMon2Nickname
	cont "@"
	text_ram wOTPartyMon3Nickname
	para "Enter with these?"
	done
.Round1Text:
	text "Round one: Jack!"
	done
.Round2Text:
	text "Round two: Gina!"
	done
.FinalText:
	text "The final: Rex!"
	done
.WinText:
	text "You made good use"
	line "of those rentals."
	done
.LossText:
	text "I win this round."
	done
.ChampionText:
	text "You won the"
	line "Rental Cup!"
	done
.ReturnText:
	text "Come back for"
	line "another draw."
	done
.PendingText:
	text "I'll hold your"
	line "prize at the desk."
	done
.OutText:
	text "Here's your team."
	para "The rentals can"
	line "try again anytime."
	done
