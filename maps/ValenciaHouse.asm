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
	writetext .IntroText
	waitbutton
	closetext
	winlosstext .BeatenText, 0
	loadtrainer LUANA_T, 1
	startbattle
	reloadmapafterbattle
	setevent EVENT_BEAT_ORANGE_CREW_LUANA
	opentext
	writetext .BadgeText
	playsound SFX_GET_BADGE
	waitsfx
	promptbutton
	farscall GiveNextStoryLead
	endtext

.Rematch:
	farwritetext OrangeLeagueRematchText
	yesorno
	iffalsefwd .No
	closetext
	winlosstext .BeatenText, 0
	loadtrainer LUANA_T, 1
	startbattle
	reloadmapafterbattle
	end

.No:
	closetext
	end

.IntroText:
	text "I'm Luana of the"
	line "Orange Crew."
	para "My son wants to be"
	line "a great trainer,"
	cont "just like you."
	para "Let me show you"
	line "how a mother"
	cont "battles!"
	done

.BeatenText:
	text "You and your"
	line "#mon move as"
	cont "one!"
	done

.BadgeText:
	text "<PLAYER> received"
	line "the Jade Star"
	cont "Badge!"
	done

