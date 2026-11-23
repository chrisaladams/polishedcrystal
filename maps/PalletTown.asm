PalletTown_MapScriptHeader:
	def_scene_scripts

	def_callbacks
	callback MAPCALLBACK_OBJECTS, PalletTownAnimeCameosCallback
	callback MAPCALLBACK_NEWMAP, PalletTownFlyPoint

	def_warp_events
	warp_event  5,  5, REDS_HOUSE_1F, 1
	warp_event 13,  5, BLUES_HOUSE_1F, 1
	warp_event 12, 11, OAKS_LAB, 1

	def_coord_events

	def_bg_events
	bg_event  7,  9, BGEVENT_JUMPTEXT, PalletTownSignText
	bg_event  3,  5, BGEVENT_JUMPTEXT, RedsHouseSignText
	bg_event 13, 13, BGEVENT_JUMPTEXT, OaksLabSignText
	bg_event 11,  5, BGEVENT_JUMPTEXT, BluesHouseSignText

	def_object_events
	object_event  3,  8, SPRITE_AROMA_LADY, SPRITEMOVEDATA_WANDER, 2, 2, -1, 0, OBJECTTYPE_COMMAND, jumptextfaceplayer, PalletTownTeacherText, -1
	object_event 12, 14, SPRITE_FAT_GUY, SPRITEMOVEDATA_WALK_LEFT_RIGHT, 0, 2, -1, PAL_NPC_GREEN, OBJECTTYPE_COMMAND, jumptextfaceplayer, PalletTownFisherText, -1
	object_event 17,  7, SPRITE_SCHOOLBOY, SPRITEMOVEDATA_WALK_UP_DOWN, 2, 0, -1, 0, OBJECTTYPE_COMMAND, jumptextfaceplayer, PalletTownYoungsterText, -1
	fruittree_event 12, 21, FRUITTREE_ROUTE_21, ENIGMA_BERRY, PAL_NPC_BLACK
	object_event  9, 12, SPRITE_RED, SPRITEMOVEDATA_STANDING_RIGHT, 0, 0, -1, PAL_NPC_BLUE, OBJECTTYPE_SCRIPT, 0, CameoAshScript, EVENT_ANIME_CAMEOS_HIDDEN

PalletTownFlyPoint:
	setflag ENGINE_FLYPOINT_PALLET
	endcallback

PalletTownTeacherText:
	text "I'm raising #-"
	line "mon too."

	para "They serve as my"
	line "private guards."
	done

PalletTownFisherText:
	text "Technology is"
	line "incredible!"

	para "You can now make"
	line "games just by"

	para "writing code in-"
	line "stead of editing"
	cont "binary data."
	done

PalletTownYoungsterText:
	text "Smell ya later!"

	para "…People started"
	line "saying that around"
	cont "here, but it's"

	para "kinda weird if you"
	line "think about it."
	done

PalletTownSignText:
	text "Pallet Town"

	para "A Tranquil Setting"
	line "of Peace & Purity"
	done

RedsHouseSignText:
	text "Red's House"
	done

OaksLabSignText:
	text "Oak #mon"
	line "Research Lab"
	done

BluesHouseSignText:
	text "Blue's House"
	done

PalletTownAnimeCameosCallback:
; Link Edition: the anime cameos come after Red and the Orange League
	checkevent EVENT_BEAT_RED
	iffalsefwd .hide
	checkevent EVENT_BEAT_DRAKE
	iffalsefwd .hide
	clearevent EVENT_ANIME_CAMEOS_HIDDEN
	endcallback

.hide
	setevent EVENT_ANIME_CAMEOS_HIDDEN
	endcallback

CameoAshScript:
; Link Edition: an anime cameo
	faceplayer
	opentext
	writetext .IntroText
	yesorno
	iffalse_jumpopenedtext .NoText
	closetext
	winlosstext .BeatenText, 0
	loadtrainer ASH_T, 1
	startbattle
	reloadmapafterbattle
	jumptext .AfterText

.IntroText:
	text "I'm Ash, from"
	line "right here in"
	cont "Pallet Town!"
	para "I'm gonna be a"
	line "#mon Master!"
	para "Want to battle?"
	done

.NoText:
	text "Aw, come on!"
	line "Next time, then."
	done

.BeatenText:
	text "Wow, you're"
	line "really strong!"
	done

.AfterText:
	text "Pikachu and I"
	line "will keep"
	cont "training."
	para "We'll beat you"
	line "next time!"
	done
