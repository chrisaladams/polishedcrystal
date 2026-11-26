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
	; Link Edition: Ash's Pikachu, out for the Invitational's final
	object_event  9, 12, SPRITE_PIKACHU, SPRITEMOVEDATA_STANDING_RIGHT, 0, 0, -1, PAL_NPC_YELLOW, OBJECTTYPE_SCRIPT, 0, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN
	; Link Edition: Tracey, who comes to sketch the winners
	object_event  9, 12, SPRITE_ARTIST, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, PAL_NPC_GREEN, OBJECTTYPE_SCRIPT, 0, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN

	object_const_def
	const_skip 4 ; (the townspeople and the berry tree)
	const PALLETTOWN_ASH
	const PALLETTOWN_PIKACHU
	const PALLETTOWN_TRACEY

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
	setevent EVENT_POST_RED_PERSON_HIDDEN ; (Pikachu comes out in the final)
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
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
	checkevent EVENT_WON_PALLET_INVITATIONAL
	iftruefwd .Friendly
	checkevent EVENT_RESCUED_PROF_HALE
	iffalsefwd .Friendly
	checkevent EVENT_BEAT_IRON_MASK_MARAUDER
	iffalsefwd .Friendly
	checkevent EVENT_BEAT_MEWTWO_CLONES
	iffalsefwd .Friendly
	checkevent EVENT_WON_WHIRL_CUP
	iftruefwd .Invite
.Friendly:
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

.Invite:
	writetext .InviteText
	yesorno
	iffalse_jumpopenedtext .NoText
	closetext
	scene_title .Title
	; (an establishing shot: the camera looks out across Pallet Town)
	scene_begin
	musicfadeout MUSIC_PALLET_TOWN, 8
	scene_pan RIGHT, 4
	pause 30
	scene_pan_back RIGHT, 4
	scene_end_keep_music
	special HealParty
	winlosstext .DrakeBeaten, .Loss
	loadtrainer DRAKE_T, 1
	loadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
	startbattle
	reloadmap
	iftruefwd .Retry
	showtext .AshFinal
	scene_begin ; (Pikachu jumps out beside him: a spark)
	scene_place PALLETTOWN_PIKACHU, -1, 1
	appear PALLETTOWN_PIKACHU
	cry PIKACHU
	showemote EMOTE_BOLT, PALLETTOWN_PIKACHU, 15
	scene_flash 1
	waitsfx
	scene_end
	winlosstext .BeatenText, .Loss
	loadtrainer ASH_T, 1
	loadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
	startbattle
	reloadmap
	iftruefwd .Retry
	special HealParty
	setevent EVENT_WON_PALLET_INVITATIONAL
	scene_begin ; (Tracey runs in, and sketches the winners in gold light)
	musicfadeout MUSIC_POST_CREDITS, 8
	scene_enter PALLETTOWN_TRACEY, RIGHT ; (Ash stands on your left)
	showemote EMOTE_HAPPY, PALLETTOWN_TRACEY, 15
	scene_tint TINT_GOLD
	showemote EMOTE_SPARKLE, PLAYER, 20
	showemote EMOTE_SPARKLE, PALLETTOWN_ASH, 15
	showemote EMOTE_HAPPY, PALLETTOWN_PIKACHU, 15
	showtext .Finish
	scene_end ; (Pallet's own music back)
	disappear PALLETTOWN_TRACEY
	disappear PALLETTOWN_PIKACHU
	scene_title .Ending
	end

.Title:
	db "PALLET INVITATIONAL@"
.Ending:
	db "TO BE CONTINUED...@"

.Retry:
	special HealParty
	jumpthistext

	text "Ash: Same place"
	line "tomorrow? Or we"
	cont "can try again now!"
	done

.DrakeBeaten:
	text "Drake: Well done."
	line "Ash, you're up!"
	done

.Loss:
	text "Good match!"
	done

.InviteText:
	text "Ash: Your name's"
	line "on every page of"
	cont "Tracey's book!"
	para "Drake's here from"
	line "the islands. He's"
	cont "up first, then me."
	para "Two battles. One"
	line "team. Ready?"
	done

.AshFinal:
	text "Drake steps aside."
	line "Pikachu jumps off"
	cont "Ash's shoulder."
	para "Ash: Our turn!"
	done

.Finish:
	text "Tracey sketches"
	line "the winning team."
	para "Ash: That one's"
	line "going on the wall"
	cont "at Oak's lab!"
	para "Pallet finals"
	line "Champion: <PLAYER>!"
	done
