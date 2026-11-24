SilverCaveOutside_MapScriptHeader:
	def_scene_scripts

	def_callbacks
	callback MAPCALLBACK_OBJECTS, SilverCaveOutsideAnimeCameosCallback
	callback MAPCALLBACK_NEWMAP, SilverCaveOutsideFlyPoint

	def_warp_events
	warp_event 23, 13, SILVER_CAVE_POKECENTER_1F, 1
	warp_event 18,  5, SILVER_CAVE_ROOM_1, 1
	warp_event 10, 18, HIDDEN_CAVE_GROTTO, 1

	def_coord_events

	def_bg_events
	bg_event 17,  7, BGEVENT_JUMPTEXT, MtSilverSignText
	bg_event  9, 19, BGEVENT_ITEM + FULL_RESTORE, EVENT_SILVER_CAVE_OUTSIDE_HIDDEN_FULL_RESTORE
	bg_event 10, 17, BGEVENT_JUMPSTD, cavegrotto, HIDDENGROTTO_SILVER_CAVE

	def_object_events
	cuttree_event 31, 18, EVENT_SILVER_CAVE_OUTSIDE_CUT_TREE_1
	cuttree_event 34, 17, EVENT_SILVER_CAVE_OUTSIDE_CUT_TREE_2
	object_event 22, 15, SPRITE_YOUNGSTER, SPRITEMOVEDATA_STANDING_RIGHT, 0, 0, -1, PAL_NPC_RED, OBJECTTYPE_SCRIPT, 0, CameoRitchieScript, EVENT_ANIME_CAMEOS_HIDDEN
	object_event 25, 15, SPRITE_CAMPER, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, PAL_NPC_BLUE, OBJECTTYPE_SCRIPT, 0, CameoHarrisonScript, EVENT_ANIME_CAMEOS_HIDDEN

SilverCaveOutsideFlyPoint:
	setflag ENGINE_FLYPOINT_SILVER_CAVE
	endcallback

MtSilverSignText:
	text "Mt.Silver"
	done

SilverCaveOutsideAnimeCameosCallback:
; Link Edition: the anime cameos come after Red and the Orange League
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalsefwd .hide
	checkevent EVENT_BEAT_DRAKE
	iffalsefwd .hide
	clearevent EVENT_ANIME_CAMEOS_HIDDEN
	endcallback

.hide
	setevent EVENT_ANIME_CAMEOS_HIDDEN
	endcallback

CameoRitchieScript:
; Link Edition: an anime cameo
	faceplayer
	opentext
	writetext .IntroText
	yesorno
	iffalse_jumpopenedtext .NoText
	closetext
	winlosstext .BeatenText, 0
	loadtrainer RITCHIE_T, 1
	startbattle
	reloadmapafterbattle
	jumptext .AfterText

.IntroText:
	text "Hi! I'm Ritchie."
	para "Ash and I battled"
	line "at the Indigo"
	cont "League."
	para "Will you battle"
	line "me and Sparky?"
	done

.NoText:
	text "Okay, maybe"
	line "later!"
	done

.BeatenText:
	text "Sparky did his"
	line "best!"
	done

.AfterText:
	text "Harrison beat Ash"
	line "at the Silver"
	cont "Conference."
	para "He's right here,"
	line "if you want to"
	cont "try him!"
	done

CameoHarrisonScript:
; Link Edition: an anime cameo
	faceplayer
	opentext
	writetext .IntroText
	yesorno
	iffalse_jumpopenedtext .NoText
	closetext
	winlosstext .BeatenText, 0
	loadtrainer HARRISON_T, 1
	startbattle
	reloadmapafterbattle
	jumptext .AfterText

.IntroText:
	text "I'm Harrison,"
	line "from Hoenn."
	para "I came to Johto"
	line "for the Silver"
	cont "Conference."
	para "Ready to battle?"
	done

.NoText:
	text "Another time,"
	line "then."
	done

.BeatenText:
	text "You're as tough"
	line "as Ash was!"
	done

.AfterText:
	text "Prof.Birch would"
	line "love to hear"
	cont "about you!"
	done
