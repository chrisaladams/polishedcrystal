ValenciaHouse_MapScriptHeader:
	def_scene_scripts

	def_callbacks

	def_warp_events
	warp_event  2,  7, VALENCIA_ISLAND, 3
	warp_event  3,  7, VALENCIA_ISLAND, 3

	def_coord_events

	def_bg_events

	def_object_events
	object_event  2,  3, SPRITE_CUTE_GIRL, SPRITEMOVEDATA_STANDING_RIGHT, 0, 0, -1, PAL_NPC_RED, OBJECTTYPE_COMMAND, jumptextfaceplayer, ValenciaHouseLassText, -1
	object_event  6,  3, SPRITE_LADY, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, PAL_NPC_PURPLE, OBJECTTYPE_SCRIPT, 0, OrangeCrewLuanaScript, -1

ValenciaHouseLassText:
	text "Prof.Ivy is really"
	line "cool!"

	para "She helped my"
	line "#mon when they"
	cont "were sick!"
	done

OrangeCrewLuanaScript:
; Link Edition: the Orange League
	faceplayer
	opentext
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iftruefwd .SeasonOpen
	farsjump OrangeLeagueClosed
.SeasonOpen:
	checkevent EVENT_BEAT_ORANGE_CREW_LUANA
	iftruefwd .Rematch
	closetext
	scene_title .CrewTitle
	opentext
	writetext .IntroText
	sjumpfwd .Confirm
.Rematch:
	farwritetext OrangeLeagueRematchText
.Confirm:
	yesorno
	iffalse_endtext
	writetext .PairText
.Choose:
	promptbutton
	loadmem wCupId, CUP_LUANA
	callasm CupSelectTeam
	ifequalfwd CUPTEAM_CANCEL, .Cancel
	ifnotequal CUPTEAM_OK, .InvalidPair
	closetext
	callasm CupBegin
	; (partners: a heart over her, then over you)
	showemote EMOTE_HEART, LAST_TALKED, 15
	showemote EMOTE_HEART, PLAYER, 15
	winlosstext .BeatenText, .LossText
	loadtrainer LUANA_T, 1
	loadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
	startbattle
	reloadmap
	iftruefwd .Lost
	callasm CupEnd
	opentext
	checkevent EVENT_BEAT_ORANGE_CREW_LUANA
	iftrue_jumpopenedtext .ReturnText
	setevent EVENT_BEAT_ORANGE_CREW_LUANA
	writetext .BadgeText
	playsound SFX_GET_BADGE
	waitsfx
	promptbutton
	farscall OrangeCrewTally
	farscall GiveNextStoryLead
	endtext

.Cancel:
	endtext
.InvalidPair:
	writetext .InvalidPairText
	sjump .Choose
.Lost:
	callasm CupEnd
	jumptext .ReturnText

.CrewTitle:
	db "ORANGE CREW: LUANA@"

.IntroText:
	text "I'm Luana of the"
	line "Orange Crew."
	para "My son learned to"
	line "battle with just"
	cont "two partners."
	para "Let's each pick"
	line "two for singles,"
	cont "at Lv.50. Ready?"
	done

.PairText:
	text "Pick your lead,"
	line "then one partner."
	done

.InvalidPairText:
	text "Please pick two"
	line "different #mon."
	para "Eggs sit this out."
	done

.BeatenText:
	text "You and your"
	line "#mon move as"
	cont "one!"
	done

.LossText:
	text "My pair held on!"
	done

.ReturnText:
	text "Come back anytime."
	line "Try a new pair!"
	done

.BadgeText:
	text "<PLAYER> received"
	line "the Jade Star"
	cont "Badge!"
	done

