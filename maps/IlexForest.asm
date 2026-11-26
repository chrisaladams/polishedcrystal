IlexForest_MapScriptHeader:
	def_scene_scripts
	scene_script IlexForestFarfetchdQuestScene, SCENE_ILEXFOREST_FARFETCHD_QUEST
	scene_script IlexForestCutSceneScene, SCENE_ILEXFOREST_CUT_SCENE
	scene_const SCENE_ILEXFOREST_NOOP

	def_callbacks
	callback MAPCALLBACK_OBJECTS, IlexForestIronMaskCallback

	def_warp_events
	warp_event  3,  7, ROUTE_34_ILEX_FOREST_GATE, 3
	warp_event  5, 44, ILEX_FOREST_AZALEA_GATE, 1
	warp_event  5, 45, ILEX_FOREST_AZALEA_GATE, 2
	warp_event 25, 24, HIDDEN_TREE_GROTTO, 1

	def_coord_events
	coord_event  9, 31, SCENE_ILEXFOREST_NOOP, IlexForestApprenticeTrigger

	def_bg_events
	bg_event 11, 25, BGEVENT_READ, IlexForestMarauderPrizeScript
	bg_event  5, 19, BGEVENT_READ, IlexForestTrailSign
	bg_event 17, 33, BGEVENT_JUMPTEXT, IlexForestTrainerTips
	bg_event 13,  9, BGEVENT_ITEM + ETHER, EVENT_ILEX_FOREST_HIDDEN_ETHER
	bg_event 24, 16, BGEVENT_ITEM + SUPER_POTION, EVENT_ILEX_FOREST_HIDDEN_SUPER_POTION
	bg_event  3, 19, BGEVENT_ITEM + FULL_HEAL, EVENT_ILEX_FOREST_HIDDEN_FULL_HEAL
	bg_event 20,  9, BGEVENT_JUMPTEXT, Text_IlexForestMossRock
	bg_event 10, 24, BGEVENT_UP, IlexForestShrineScript
	bg_event 25, 24, BGEVENT_ITEM + SILVER_LEAF, EVENT_ILEX_FOREST_HIDDEN_SILVER_LEAF_1
	bg_event 19,  8, BGEVENT_ITEM + SILVER_LEAF, EVENT_ILEX_FOREST_HIDDEN_SILVER_LEAF_2
	bg_event 25, 23, BGEVENT_JUMPSTD, treegrotto, HIDDENGROTTO_ILEX_FOREST
	bg_event 26, 23, BGEVENT_JUMPSTD, treegrotto, HIDDENGROTTO_ILEX_FOREST

	def_object_events
	object_event 16, 33, SPRITE_FARFETCH_D, SPRITEMOVEDATA_SPINRANDOM_SLOW, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, IlexForestFarfetchdScript, EVENT_ILEX_FOREST_FARFETCHD
	object_event  7, 30, SPRITE_BLACK_BELT, SPRITEMOVEDATA_STANDING_RIGHT, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, IlexForestCharcoalMasterScript, EVENT_ILEX_FOREST_CHARCOAL_MASTER
	object_event 10, 31, SPRITE_KURT, SPRITEMOVEDATA_STANDING_UP, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, ObjectEvent, EVENT_ILEX_FOREST_KURT
	object_event  5, 26, SPRITE_PICNICKER, SPRITEMOVEDATA_STANDING_RIGHT, 0, 0, -1, 0, OBJECTTYPE_COMMAND, jumptextfaceplayer, Text_IlexForestLass, EVENT_ILEX_FOREST_LASS
	object_event 10, 26, SPRITE_CELEBI, SPRITEMOVEDATA_STANDING_UP, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, ObjectEvent, EVENT_ILEX_FOREST_CELEBI
	object_event  9, 25, SPRITE_LYRA, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, IlexForestLyraScript, EVENT_ILEX_FOREST_LYRA
	object_event  9, 30, SPRITE_SCHOOLBOY, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, PAL_NPC_GREEN, OBJECTTYPE_SCRIPT, 0, IlexForestCharcoalApprenticeScript, EVENT_ILEX_FOREST_APPRENTICE
	object_event 11, 25, SPRITE_IRON_MASK, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, IlexForestIronMaskScript, EVENT_POST_RED_PERSON_HIDDEN
	object_event 11, 25, SPRITE_SAMMY, SPRITEMOVEDATA_STANDING_RIGHT, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, ObjectEvent, EVENT_ILEX_FOREST_SAMMY
	object_event  8, 25, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, BEEDRILL, -1, PAL_MON_YELLOW, OBJECTTYPE_SCRIPT, PLAIN_FORM, IlexForestShadowBeedrillScript, EVENT_TEMPORARY_UNTIL_MAP_RELOAD_4
	object_event  9, 25, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, ARIADOS, -1, PAL_MON_RED, OBJECTTYPE_SCRIPT, PLAIN_FORM, IlexForestShadowAriadosScript, EVENT_TEMPORARY_UNTIL_MAP_RELOAD_5
	object_event 11, 26, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, NOCTOWL, -1, PAL_MON_BROWN, OBJECTTYPE_SCRIPT, PLAIN_FORM, IlexForestShadowNoctowlScript, EVENT_TEMPORARY_UNTIL_MAP_RELOAD_6
	object_event 17, 16, SPRITE_ROCKER, SPRITEMOVEDATA_STANDING_RIGHT, 0, 0, -1, PAL_NPC_GREEN, OBJECTTYPE_SCRIPT, 0, IlexForestHeadbuttGuyScript, -1
	object_event 14,  3, SPRITE_BUG_CATCHER, SPRITEMOVEDATA_STANDING_UP, 0, 0, -1, 0, OBJECTTYPE_GENERICTRAINER, 0, GenericTrainerBugCatcherWayne, -1
	object_event  4, 16, SPRITE_SCHOOLBOY, SPRITEMOVEDATA_SPINRANDOM_SLOW, 0, 0, -1, PAL_NPC_RED, OBJECTTYPE_COMMAND, jumptextfaceplayer, IlexForestHoneyBoyText, EVENT_ROUTE_34_ILEX_FOREST_GATE_LASS
	cuttree_event 10, 27, EVENT_ILEX_FOREST_CUT_TREE
	itemball_event 22, 34, REVIVE, 1, EVENT_ILEX_FOREST_REVIVE
	itemball_event 11, 19, X_ATTACK, 1, EVENT_ILEX_FOREST_X_ATTACK
	itemball_event 25, 17, ANTIDOTE, 1, EVENT_ILEX_FOREST_ANTIDOTE
	itemball_event 29,  3, MULCH, 1, EVENT_ILEX_FOREST_MULCH

	object_const_def
	const ILEXFOREST_FARFETCHD
	const ILEXFOREST_BLACK_BELT
	const ILEXFOREST_KURT
	const ILEXFOREST_LASS
	const ILEXFOREST_CELEBI
	const ILEXFOREST_LYRA
	const ILEXFOREST_YOUNGSTER
	const ILEXFOREST_IRON_MASK
	const ILEXFOREST_SAMMY
	const ILEXFOREST_SHADOW_BEEDRILL
	const ILEXFOREST_SHADOW_ARIADOS
	const ILEXFOREST_SHADOW_NOCTOWL

IlexForestCutSceneScene:
	sdefer IlexForestFinishCelebiEventScript
IlexForestFarfetchdQuestScene:
	end

IlexForestIronMaskCallback:
; Link Edition: the Iron Mask Marauder (Celebi: Voice of the Forest) waits
; by the shrine after Red and the time travel, until he's beaten
	setevent EVENT_ILEX_FOREST_SAMMY ; (Sammy is only there in the scene after)
	setevent EVENT_POST_RED_PERSON_HIDDEN
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalsefwd .NoMarauder
	checkevent EVENT_TIME_TRAVEL_FINISHED
	iffalsefwd .NoMarauder
	checkevent EVENT_BEAT_IRON_MASK_MARAUDER
	iftruefwd .NoMarauder
	clearevent EVENT_POST_RED_PERSON_HIDDEN
	sjumpfwd IlexForestFarfetchdCallback

.NoMarauder:
	; the forest Pokemon his ball holds are only here while he is (each one
	; freed stays gone until you come back)
	setevent EVENT_TEMPORARY_UNTIL_MAP_RELOAD_4
	setevent EVENT_TEMPORARY_UNTIL_MAP_RELOAD_5
	setevent EVENT_TEMPORARY_UNTIL_MAP_RELOAD_6
IlexForestFarfetchdCallback:
	checkevent EVENT_GOT_HM01_CUT
	iftruefwd .Static
	readmem wFarfetchdPosition
	ifequalfwd  1, .PositionOne
	ifequalfwd  2, .PositionTwo
	ifequalfwd  3, .PositionThree
	ifequalfwd  4, .PositionFour
	ifequalfwd  5, .PositionFive
	ifequalfwd  6, .PositionSix
	ifequalfwd  7, .PositionSeven
	ifequalfwd  8, .PositionEight
	ifequalfwd  9, .PositionNine
	ifequalfwd 10, .PositionTen
.Static:
	endcallback

.PositionOne:
	moveobject ILEXFOREST_FARFETCHD, 16, 33
	appear ILEXFOREST_FARFETCHD
	endcallback

.PositionTwo:
	moveobject ILEXFOREST_FARFETCHD, 17, 27
	appear ILEXFOREST_FARFETCHD
	endcallback

.PositionThree:
	moveobject ILEXFOREST_FARFETCHD, 22, 26
	appear ILEXFOREST_FARFETCHD
	endcallback

.PositionFour:
	moveobject ILEXFOREST_FARFETCHD, 31, 24
	appear ILEXFOREST_FARFETCHD
	endcallback

.PositionFive:
	moveobject ILEXFOREST_FARFETCHD, 30, 33
	appear ILEXFOREST_FARFETCHD
	endcallback

.PositionSix:
	moveobject ILEXFOREST_FARFETCHD, 26, 37
	appear ILEXFOREST_FARFETCHD
	endcallback

.PositionSeven:
	moveobject ILEXFOREST_FARFETCHD, 24, 33
	appear ILEXFOREST_FARFETCHD
	endcallback

.PositionEight:
	moveobject ILEXFOREST_FARFETCHD, 17, 31
	appear ILEXFOREST_FARFETCHD
	endcallback

.PositionNine:
	moveobject ILEXFOREST_FARFETCHD, 12, 37
	appear ILEXFOREST_FARFETCHD
	endcallback

.PositionTen:
	moveobject ILEXFOREST_FARFETCHD, 8, 30
	appear ILEXFOREST_FARFETCHD
	endcallback

IlexForestCharcoalApprenticeScript:
	checkevent EVENT_HERDED_FARFETCHD
	iftrue_jumptextfaceplayer IlexForestApprenticeAfterText
	setscene SCENE_ILEXFOREST_FARFETCHD_QUEST
	jumpthistextfaceplayer

	text "Oh, man… My boss"
	line "is going to be"
	cont "steaming…"

	para "The Farfetch'd"
	line "that Cuts trees"

	para "for charcoal took"
	line "off on me."

	para "I can't go looking"
	line "for it here in the"
	cont "Ilex Forest."

	para "It's too big, dark"
	line "and scary for me…"
	done

IlexForestFarfetchdScript:
	faceplayer
	readmem wFarfetchdPosition
	ifequalfwd  0, .Position1
	showcrytext Text_Kwaaaa, FARFETCH_D
	readmem wFarfetchdPosition
	ifequalfwd  2, .Position2
	ifequalfwd  3, .Position3
	ifequalfwd  4, .Position4
	ifequalfwd  5, .Position5
	ifequalfwd  6, .Position6
	ifequalfwd  7, .Position7
	ifequalfwd  8, .Position8
	ifequalfwd  9, .Position9
	ifequal 10, DoNothingScript

.Position1:
	faceplayer
	opentext
	writetext Text_ItsTheMissingPokemon
	promptbutton
	writetext Text_Kwaaaa
	cry FARFETCH_D
	waitbutton
	closetext
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetchd_Pos1_Pos2
.NewPosition2:
	moveobject ILEXFOREST_FARFETCHD, 17, 27
	setval 2
.NewPosition:
	disappear ILEXFOREST_FARFETCHD
	appear ILEXFOREST_FARFETCHD
	writemem wFarfetchdPosition
	end

.Position2:
	readvar VAR_FACING
	ifequalfwd DOWN, .Position2_Down
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetchd_Pos2_Pos3
.NewPosition3:
	moveobject ILEXFOREST_FARFETCHD, 22, 26
	setval 3
	sjump .NewPosition

.Position2_Down:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetchd_Pos2_Pos8
.NewPosition8:
	moveobject ILEXFOREST_FARFETCHD, 17, 31
	setval 8
	sjump .NewPosition

.Position3:
	readvar VAR_FACING
	ifequalfwd LEFT, .Position3_Left
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetchd_Pos3_Pos4
.NewPosition4:
	moveobject ILEXFOREST_FARFETCHD, 31, 24
	setval 4
	sjump .NewPosition

.Position3_Left:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetchd_Pos3_Pos2
	sjump .NewPosition2

.Position4:
	readvar VAR_FACING
	ifequalfwd UP, .Position4_Up
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetchd_Pos4_Pos5
.NewPosition5:
	moveobject ILEXFOREST_FARFETCHD, 30, 33
	setval 5
	sjump .NewPosition

.Position4_Up:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetchd_Pos4_Pos3
	sjump .NewPosition3

.Position5:
	readvar VAR_FACING
	ifequalfwd UP, .Position5_Up
	ifequalfwd LEFT, .Position5_Left
	ifequalfwd RIGHT, .Position5_Right
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetchd_Pos5_Pos6
.NewPosition6:
	moveobject ILEXFOREST_FARFETCHD, 26, 37
	setval 6
	sjump .NewPosition

.Position5_Left:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetchd_Pos5_Pos7
.NewPosition7:
	moveobject ILEXFOREST_FARFETCHD, 24, 33
	setval 7
	sjump .NewPosition

.Position5_Up:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos5_Pos4_Up
	sjump .NewPosition4

.Position5_Right:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos5_Pos4_Right
	sjump .NewPosition4

.Position6:
	readvar VAR_FACING
	ifequalfwd RIGHT, .Position6_Right
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos6_Pos7
	sjump .NewPosition7

.Position6_Right:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos6_Pos5
	sjump .NewPosition5

.Position7:
	readvar VAR_FACING
	ifequalfwd DOWN, .Position7_Down
	ifequalfwd LEFT, .Position7_Left
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos7_Pos8
	sjump .NewPosition8

.Position7_Left:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos7_Pos6
	sjump .NewPosition6

.Position7_Down:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos7_Pos5
	sjump .NewPosition5

.Position8:
	readvar VAR_FACING
	ifequalfwd UP, .Position8_Up
	ifequalfwd LEFT, .Position8_Left
	ifequalfwd RIGHT, .Position8_Right
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos8_Pos9
	moveobject ILEXFOREST_FARFETCHD, 12, 37
	setval 9
	sjump .NewPosition

.Position8_Right:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos8_Pos7
	sjump .NewPosition7

.Position8_Up:
.Position8_Left:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos8_Pos2
	sjump .NewPosition2

.Position9:
	readvar VAR_FACING
	ifequalfwd DOWN, .Position9_Down
	ifequalfwd RIGHT, .Position9_Right
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos9_Pos10
	appear ILEXFOREST_BLACK_BELT
	setevent EVENT_CHARCOAL_KILN_BOSS
	setevent EVENT_HERDED_FARFETCHD
	moveobject ILEXFOREST_FARFETCHD, 8, 30
	setval 10
	sjump .NewPosition

.Position9_Right:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos9_Pos8_Right
	sjump .NewPosition8

.Position9_Down:
	applymovement ILEXFOREST_FARFETCHD, MovementData_Farfetched_Pos9_Pos8_Down
	sjump .NewPosition8

IlexForestFinishCelebiEventScript:
	setevent EVENT_TIME_TRAVEL_FINISHED
	clearevent EVENT_TIME_TRAVELING
	setscene SCENE_ILEXFOREST_FARFETCHD_QUEST
	pause 30
	showemote EMOTE_SHOCK, ILEXFOREST_LYRA, 15
	applyonemovement ILEXFOREST_LYRA, slow_step_down
	turnobject ILEXFOREST_LYRA, RIGHT
	turnobject PLAYER, LEFT
	opentext
	writetext Text_IlexForestLyraWorried
	waitbutton
	writetext Text_IlexForestLyraArmorSuit
	waitbutton
	closetext
	follow ILEXFOREST_LYRA, PLAYER
	applyonemovement ILEXFOREST_LYRA, slow_step_up
	stopfollow
	turnobject PLAYER, UP
	turnobject ILEXFOREST_LYRA, DOWN
	setlasttalked ILEXFOREST_LYRA
	opentext
	sjumpfwd IlexForestLyraContinueScript

IlexForestLyraScript:
	faceplayer
	opentext
	writetext Text_IlexForestLyraArmorSuit
	promptbutton
IlexForestLyraContinueScript:
	verbosegiveitem ARMOR_SUIT, iffalse_endtext
	setevent EVENT_GOT_ARMOR_SUIT
	writetext Text_IlexForestLyraGoodbye
	waitbutton
	closetext
	readvar VAR_FACING
	ifequalfwd LEFT, .NotBlockingPath
	applymovement PLAYER, MovementData_PlayerStepAside
.NotBlockingPath
	applymovement ILEXFOREST_LYRA, MovementData_IlexForestLyraLeaves
	disappear ILEXFOREST_LYRA
	end

IlexForestApprenticeTrigger:
	showemote EMOTE_SHOCK, ILEXFOREST_YOUNGSTER, 15
	turnobject PLAYER, UP
	sjump IlexForestCharcoalApprenticeScript

IlexForestCharcoalMasterScript:
	checkevent EVENT_GOT_HM01_CUT
	iftrue_jumptextfaceplayer Text_CharcoalMasterTalkAfter
	faceplayer
	opentext
	writetext Text_CharcoalMasterIntro
	promptbutton
	verbosegivetmhm HM_CUT
	setevent EVENT_GOT_HM01_CUT
	writetext Text_CharcoalMasterOutro
	waitbutton
	closetext
	setevent EVENT_ILEX_FOREST_FARFETCHD
	setevent EVENT_ILEX_FOREST_APPRENTICE
	setevent EVENT_ILEX_FOREST_CHARCOAL_MASTER
	clearevent EVENT_CHARCOAL_KILN_FARFETCH_D
	clearevent EVENT_CHARCOAL_KILN_APPRENTICE
	clearevent EVENT_CHARCOAL_KILN_BOSS
	end

IlexForestHeadbuttGuyScript:
	faceplayer
	opentext
	checkkeyitem WING_CASE
	iftruefwd IlexForestTutorHeadbuttScript
	writetext Text_HeadbuttIntro
	promptbutton
	verbosegivekeyitem WING_CASE
	writetext Text_HeadbuttIntro2
	waitbutton
	setevent EVENT_LISTENED_TO_HEADBUTT_INTRO
IlexForestTutorHeadbuttScript:
	writetext Text_IlexForestTutorHeadbutt
	waitbutton
	checkitem SILVER_LEAF
	iffalsefwd .NoSilverLeaf
	writetext Text_IlexForestTutorQuestion
	yesorno
	iffalsefwd .TutorRefused
	setval HEADBUTT
	writetext ClearText
	special Special_MoveTutor
	ifequalfwd $0, .TeachMove
.TutorRefused
	jumpthisopenedtext

	text "Alright then."
	done

.NoSilverLeaf
	jumpthisopenedtext

	text "Oh, but you don't"
	line "have any Silver"
	cont "Leaves."

	para "Sometimes you can"
	line "find them on wild"

	para "Oddish, or lying"
	line "on the ground."
	done

.TeachMove
	takeitem SILVER_LEAF
	jumpthisopenedtext

	text "Rattle trees with"
	line "Headbutt. Some-"
	cont "times, sleeping"
	cont "#mon fall out."
	done

GenericTrainerBugCatcherWayne:
	generictrainer BUG_CATCHER, WAYNE, EVENT_BEAT_BUG_CATCHER_WAYNE, BugCatcherWayneSeenText, BugCatcherWayneBeatenText

	text "A #mon I've"
	line "never seen before"

	para "fell out of the"
	line "tree when I used"
	cont "Headbutt."

	para "I ought to use"
	line "Headbutt in other"
	cont "places too."
	done

IlexForestShrineScript:
	checkevent EVENT_FOREST_IS_RESTLESS
	iffalsefwd .DontDoCelebiEvent
	checkkeyitem GS_BALL
	iftruefwd .AskCelebiEvent
.DontDoCelebiEvent:
	checkevent EVENT_TIME_TRAVEL_FINISHED
	iftruefwd .DontDoGiovanniEvent
	checkpoke CELEBI
	iftruefwd .StartGiovanniEvent
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iftruefwd .ForestDisturbance
.DontDoGiovanniEvent
	jumptext Text_IlexForestShrine

.ForestDisturbance:
	opentext
	writetext .TrailText
	yesorno
	iffalse_endtext
	closetext
	sjumpfwd .StartGiovanniEvent

.TrailText:
	text "Tracks run up to"
	line "the shrine, then"
	cont "repeat in reverse."
	para "A traveler calls"
	line "for help from the"
	cont "other side."
	para "Call back?"
	done

.AskCelebiEvent:
	opentext
	writetext Text_ShrineCelebiEvent
	yesorno
	iftruefwd .CelebiEvent
	endtext

.CelebiEvent:
	takekeyitem GS_BALL
	clearevent EVENT_FOREST_IS_RESTLESS
	setevent EVENT_AZALEA_TOWN_KURT
	disappear ILEXFOREST_LASS
	clearevent EVENT_ROUTE_34_ILEX_FOREST_GATE_LASS
	writetext Text_InsertGSBall
	waitbutton
	closetext
	pause 20
	showemote EMOTE_SHOCK, PLAYER, 20
	special Special_FadeOutMusic
	applymovement PLAYER, IlexForestPlayerStepsDownMovement
	pause 30
	turnobject PLAYER, DOWN
	pause 20
	clearflag ENGINE_HAVE_EXAMINED_GS_BALL
	special Special_CelebiShrineEvent
	loadwildmon CELEBI, 30
	startbattle
	reloadmapafterbattle
	pause 20
	special CheckBattleCaughtResult
	iffalse DoNothingScript
	setflag ENGINE_PLAYER_CAUGHT_CELEBI
	appear ILEXFOREST_KURT
	applymovement ILEXFOREST_KURT, IlexForestKurtStepsUpMovement
	showtext Text_KurtCaughtCelebi
	applymovement ILEXFOREST_KURT, IlexFOrestKurtStepsDownMovement
	disappear ILEXFOREST_KURT
	end

.StartGiovanniEvent:
	showtext Text_IlexForestShrine
	showemote EMOTE_SHOCK, PLAYER, 15
	appear ILEXFOREST_CELEBI
	playsound SFX_BALL_POOF
	turnobject PLAYER, DOWN
	waitsfx
	pause 15
	cry CELEBI
	waitsfx
	pause 15
	applymovement ILEXFOREST_CELEBI, MovementData_CelebiDance
	pause 15
	showtext Text_CelebiDancedBeautifully
	playsound SFX_JUMP_OVER_LEDGE
	applymovement ILEXFOREST_CELEBI, MovementData_CelebiHop
	applyonemovement PLAYER, slow_step_down
	waitsfx
	special Special_FadeOutMusic
	playmusic MUSIC_LYRA_ENCOUNTER_HGSS
	moveobject ILEXFOREST_LYRA, 5, 26
	appear ILEXFOREST_LYRA
	applymovement ILEXFOREST_LYRA, MovementData_IlexForestLyraApproaches
	turnobject PLAYER, LEFT
	showtext Text_IlexForestLyraHello
	special RestartMapMusic
	pause 30
	playsound SFX_GAME_FREAK_LOGO_GS
	special FadeOutPalettes
	special LoadMapPalettes
	turnobject ILEXFOREST_CELEBI, DOWN
	pause 30
	special FadeInPalettes_EnableDynNoApply
	waitsfx
	showemote EMOTE_SHOCK, PLAYER, 15
	turnobject PLAYER, UP
	pause 15
	turnobject ILEXFOREST_LYRA, UP
	turnobject PLAYER, DOWN
	pause 15
	turnobject ILEXFOREST_LYRA, RIGHT
	turnobject PLAYER, LEFT
	showtext Text_IlexForestLyraWhatWasThat
	cry CELEBI
	showemote EMOTE_SHOCK, PLAYER, 15
	applymovement PLAYER, MovementData_PlayerStepBack
	waitsfx
	playsound SFX_PROTECT
	applymovement ILEXFOREST_CELEBI, MovementData_CelebiFloat
	waitsfx
	playsound SFX_GAME_FREAK_LOGO_GS
	special FadeOutPalettes
	pause 30
	waitsfx
	disappear ILEXFOREST_CELEBI
	disappear ILEXFOREST_LYRA
	setevent EVENT_TIME_TRAVELING
	warp ROUTE_22_PAST, 6, 7
	end

MovementData_Farfetchd_Pos1_Pos2:
	big_step_up
MovementData_Farfetched_Pos8_Pos2:
	big_step_up
	big_step_up
	big_step_up
	big_step_up
	step_end

MovementData_Farfetchd_Pos2_Pos3:
	run_step_up
	run_step_up
	run_step_right
	run_step_right
	run_step_right
	run_step_right
	run_step_right
	run_step_down
	step_end

MovementData_Farfetchd_Pos4_Pos5:
	big_step_down
MovementData_Farfetchd_Pos2_Pos8:
	run_step_down
	run_step_down
	run_step_down
	run_step_down
	run_step_down
	step_end

MovementData_Farfetchd_Pos3_Pos4:
MovementData_Farfetched_Pos7_Pos5:
	big_step_right
MovementData_Farfetched_Pos8_Pos7:
	big_step_right
	big_step_right
	big_step_right
	big_step_right
	big_step_right
	step_end

MovementData_Farfetchd_Pos3_Pos2:
	run_step_up
	run_step_left
	run_step_left
	run_step_left
	run_step_left
	step_end

MovementData_Farfetchd_Pos4_Pos3:
	run_step_left
	jump_step_left
	run_step_left
	run_step_left
	step_end

MovementData_Farfetchd_Pos5_Pos6:
	big_step_down
	big_step_down
	big_step_down
	big_step_down
	big_step_down
MovementData_Farfetchd_Pos5_Pos7:
	run_step_left
	run_step_left
	run_step_left
	run_step_left
	step_end

MovementData_Farfetched_Pos5_Pos4_Up:
	run_step_up
	run_step_up
	run_step_up
	run_step_right
	run_step_up
	step_end

MovementData_Farfetched_Pos5_Pos4_Right:
	run_step_right
	turn_head_up
	step_sleep_1
	turn_head_down
	step_sleep_1
	turn_head_up
	step_sleep_1
	run_step_down
	run_step_down
	fix_facing
	jump_step_up
	step_sleep_8
	step_sleep_8
	remove_fixed_facing
	run_step_up
	run_step_up
	run_step_up
	run_step_up
	run_step_up
	step_end

MovementData_Farfetched_Pos6_Pos7:
	run_step_left
	run_step_left
	run_step_left
	run_step_up
	run_step_up
	run_step_right
	run_step_up
	run_step_up
	step_end

MovementData_Farfetched_Pos6_Pos5:
	run_step_right
	run_step_right
	run_step_right
	run_step_right
	run_step_up
	run_step_up
	run_step_up
	run_step_up
	step_end

MovementData_Farfetched_Pos7_Pos8:
	run_step_up
	run_step_up
	run_step_left
	run_step_left
	run_step_left
	run_step_left
	run_step_left
	step_end

MovementData_Farfetched_Pos7_Pos6:
	run_step_down
	run_step_down
	run_step_left
	run_step_down
	run_step_down
	run_step_right
	run_step_right
	run_step_right
	step_end

MovementData_Farfetched_Pos8_Pos9:
	run_step_down
	run_step_left
	run_step_down
	run_step_down
	run_step_down
	run_step_down
	run_step_down
	step_end

MovementData_Farfetched_Pos9_Pos10:
	run_step_left
	run_step_left
	fix_facing
	jump_step_right
	step_sleep_8
	step_sleep_8
	remove_fixed_facing
	run_step_left
	run_step_left
	run_step_up
	run_step_up
	run_step_up
	run_step_up
	run_step_up
	run_step_up
	step_end

MovementData_Farfetched_Pos9_Pos8_Right:
	run_step_right
	run_step_right
	run_step_right
	run_step_right
	run_step_up
	run_step_up
	run_step_up
	run_step_up
	run_step_up
	step_end

MovementData_Farfetched_Pos9_Pos8_Down:
	run_step_left
	run_step_left
	fix_facing
	jump_step_right
	step_sleep_8
	step_sleep_8
	remove_fixed_facing
	run_step_right
	run_step_right
	run_step_right
	run_step_right
	run_step_up
	run_step_up
	run_step_up
	run_step_up
	run_step_up
	step_end

IlexForestKurtStepsUpMovement:
	step_up
	step_up
	step_up
	step_up
	step_end

IlexFOrestKurtStepsDownMovement:
	step_down
	step_down
	step_down
	step_down
	step_end

IlexForestPlayerStepsDownMovement:
	fix_facing
	slow_step_down
	remove_fixed_facing
	step_end

MovementData_CelebiRise:
	slow_step_up
	slow_step_up
	step_end

MovementData_CelebiDance:
	slow_step_left
	slow_step_right
	slow_step_right
	slow_step_left
	step_sleep_4
	turn_head_up
	step_sleep_4
	turn_head_left
	step_sleep_4
	turn_head_down
	step_sleep_4
	turn_head_right
	step_sleep_4
	turn_head_up
	step_sleep_4
	turn_head_left
	step_sleep_4
	turn_head_down
	step_sleep_4
	turn_head_right
	step_sleep_4
	turn_head_up
	step_sleep_4
	step_end

MovementData_CelebiHop:
	jump_step_down
	slow_step_up
	step_end

MovementData_CelebiFloat:
	turn_head_down
	fix_facing
	slow_step_up
	slow_step_up
	slow_step_up
	remove_fixed_facing
	step_end

MovementData_PlayerStepBack:
	fix_facing
	slow_step_right
	remove_fixed_facing
	step_end

MovementData_IlexForestLyraApproaches:
	slow_step_right
	slow_step_right
	slow_step_right
	slow_step_right
	step_end

MovementData_PlayerStepAside:
	slow_step_right
	turn_head_left
	step_end

MovementData_IlexForestLyraLeaves:
	slow_step_down
	slow_step_left
	slow_step_left
	slow_step_left
	slow_step_left
	step_end


IlexForestApprenticeAfterText:
	text "Wow! Thanks a"
	line "whole bunch!"

	para "My boss's #mon"
	line "won't obey me be-"
	cont "cause I don't have"
	cont "a Badge."
	done

Text_ItsTheMissingPokemon:
	text "It's the missing"
	line "#mon!"
	done

Text_Kwaaaa::
	text "Farfetch'd: Kwaa!"
	done

Text_CharcoalMasterIntro:
	text "Ah! My Farfetch'd!"

	para "You found it for"
	line "us, kid?"

	para "Without it, we"
	line "wouldn't be able"

	para "to Cut trees for"
	line "charcoal."

	para "Thanks, kid!"

	para "Now, how can I"
	line "thank you…"

	para "I know! Here, take"
	line "this."
	done

Text_CharcoalMasterOutro:
	text "That's the Cut HM."
	line "Any #mon you"

	para "have that's compat-"
	line "ible with it can"

	para "use Cut to clear"
	line "small trees."

	para "You don't have to"
	line "teach it to them"

	para "unless you want"
	line "them to use Cut"
	cont "in a battle."

	para "Of course, you"
	line "have to have the"

	para "Gym Badge from"
	line "Azalea to use it"
	cont "outside of battle."
	done

Text_CharcoalMasterTalkAfter:
	text "Do you want to"
	line "apprentice as a"

	para "charcoal maker"
	line "with me?"

	para "You'll be first-"
	line "rate in ten years!"
	done

Text_HeadbuttIntro:
	text "What am I doing?"

	para "I'm shaking trees"
	line "using Headbutt."

	para "Sometimes I flush"
	line "out a #mon,"

	para "sometimes just"
	line "their feathers."

	para "But even those"
	line "are useful!"

	para "They seem to make"
	line "my own #mon"
	cont "a little stronger."

	para "It's fun. Here,"
	line "you try it too!"

	para "You'll just need a"
	line "Case to hold any"
	cont "delicate Wings…"
	done

Text_HeadbuttIntro2:
	text "Oh, and if none"
	line "of your #mon"
	cont "know Headbutt?"

	para "No problem!"
	done

Text_IlexForestTutorHeadbutt:
	text "I can teach your"
	line "#mon to use"

	para "Headbutt in ex-"
	line "change for a"
	cont "Silver Leaf."
	done


Text_IlexForestTutorQuestion:
	text "Should I teach"
	line "your #mon"
	cont "Headbutt?"
	done



Text_IlexForestLass:
	text "Did something"
	line "happen to the"
	cont "forest's guardian?"
	done

Text_IlexForestMossRock:
	text "The rock is cover-"
	line "ed in moss."

	para "It feels pleasant-"
	line "ly cool."
	done

IlexForestTrailSign:
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalse_jumptext IlexForestSignpost
	checkevent EVENT_BEAT_IRON_MASK_MARAUDER
	iftrue_jumptext IlexForestSignpost
	jumpthistext

	text "Fresh scratches:"
	line "The same footsteps"
	cont "keep passing me."
	para "If you're here"
	line "today, meet me at"
	cont "the shrine. -Lyra"
	done

IlexForestSignpost:
	text "Ilex Forest is"
	line "so overgrown with"

	para "trees that you"
	line "can't see the sky."

	para "Please watch out"
	line "for items that may"
	cont "have been dropped."
	done

IlexForestTrainerTips:
	text "Trainer Tips"

	para "As long as you"
	line "have an HM in"
	cont "your Bag,"

	para "and a #mon in"
	line "your party that's"

	para "compatible with"
	line "it, you can use"

	para "the move outside"
	line "of battle."

	para "You don't even"
	line "have to teach it!"
	done

Text_IlexForestShrine:
	text "Ilex Forest"
	line "Shrine…"

	para "It's in honor of"
	line "the forest's"
	cont "protector…"
	done

Text_ShrineCelebiEvent:
	text "Ilex Forest"
	line "Shrine…"

	para "It's in honor of"
	line "the forest's"
	cont "protector…"

	para "Oh? What is this?"

	para "It's a hole."
	line "It looks like the"

	para "GS Ball would fit"
	line "inside it."

	para "Want to put the GS"
	line "Ball here?"
	done

Text_InsertGSBall:
	text "<PLAYER> put in the"
	line "GS Ball."
	done

Text_KurtCaughtCelebi:
	text "Whew, wasn't that"
	line "something!"

	para "<PLAYER>, that was"
	line "fantastic. Thanks!"

	para "The legends about"
	line "that Shrine were"
	cont "real after all."

	para "Maybe the legend"
	line "that people who"
	cont "tamper with it"

	para "disappear is"
	line "true, too…"

	para "I feel inspired by"
	line "what I just saw."

	para "It motivates me to"
	line "make better Balls!"

	para "I'm going!"
	done

Text_CelebiDancedBeautifully:
	text "Celebi danced"
	line "beautifully!"
	done

Text_IlexForestLyraHello:
	text "Lyra: Hi, <PLAYER>."
	line "Have you heard of"

	para "the legend of the"
	line "shrine?"

	para "They say that"
	line "people disappear"

	para "when they tamper"
	line "with it."
	done

Text_IlexForestLyraWhatWasThat:
	text "Lyra: …"
	line "What was that?"
	done

Text_IlexForestLyraWorried:
	text "Lyra: …<PLAYER>?"
	line "You're really back?"

	para "I missed you so"
	line "much! Celebi sent"

	para "me here and you"
	line "were missing…"

	para "I thought you'd be"
	line "stuck in the past"
	cont "forever!"

	para "…"

	para "At least now we're"
	line "both safely back"
	cont "to our time."
	done

Text_IlexForestLyraArmorSuit:
	text "Lyra: What strange"
	line "adventure did you"
	cont "have by yourself?"

	para "You dropped this…"
	line "thing when Celebi"
	cont "brought you back…"
	done

Text_IlexForestLyraGoodbye:
	text "Lyra: This sure"
	line "was a bizarre day."

	para "I'm exhausted, I"
	line "had better get"
	cont "going."

	para "You should rest"
	line "too, <PLAYER>."

	para "See you!"
	done

BugCatcherWayneSeenText:
	text "Don't sneak up on"
	line "me like that!"

	para "You frightened a"
	line "#mon away!"
	done

BugCatcherWayneBeatenText:
	text "I hadn't seen that"
	line "#mon before…"
	done

IlexForestHoneyBoyText:
	text "I'm slathering"
if DEF(FAITHFUL)
	line "Honey on the"
	cont "ground."
else
	line "Sweet Honey"
	cont "on the ground."
endc

	para "My sister's #-"
	line "mon collects it."

	para "It helps attract"
	line "#mon at the"

	para "same level as my"
	line "own, so they're"
	cont "a fair fight."
	done

IlexForestIronMaskScript:
; Link Edition: Celebi: Voice of the Forest. The forest darkens around him
; (engine/events/cinematic.asm), and its light is back for the battle.
	faceplayer
	scene_title .Title
	scene_begin
	playsound SFX_PROTECT
	scene_tint TINT_DARK
	earthquake 10
	showtext .IntroText
	scene_end
	winlosstext .BeatenText, 0
	loadtrainer IRON_MASK_T, 1
	startbattle
	reloadmapafterbattle
	setevent EVENT_BEAT_IRON_MASK_MARAUDER
	setevent EVENT_MARAUDER_REWARD_PENDING
	showtext .AfterText
	scene_begin
	playsound SFX_WARP_TO
	scene_flash 1
	disappear ILEXFOREST_IRON_MASK
	waitsfx
	scene_end
	cry CELEBI
	showtext .ForestCalm
	scall IlexForestSammyScene
	checkevent EVENT_RESCUED_PROF_HALE
	iffalsefwd .AnotherLead
	checkevent EVENT_BEAT_MEWTWO_CLONES
	iftruefwd .AnotherLead
	checkevent EVENT_READ_CINNABAR_CLONE_REPORT
	iftruefwd .AnotherLead
	showtext .Vision
	sjump IlexForestMarauderPrizeScript
.AnotherLead:
	farscall TraceyCallsWithALead
	sjump IlexForestMarauderPrizeScript

.Title:
	db "VOICE OF THE FOREST@"

.Vision:
	text "In Celebi's eyes"
	line "you see a cave."
	para "Your team stands"
	line "by the water. The"
	cont "ripples spread…"
	para "Across the water,"
	line "another you looks"
	cont "back."
	para "The reflection"
	line "changes to a diary"
	cont "marked Cinnabar."
	done

.IntroText:
	text "Heh heh heh…"

	para "I am the Iron"
	line "Mask Marauder of"
	cont "Team Rocket!"

	para "I came for the"
	line "#mon that"
	cont "travels through"
	cont "time: Celebi!"

	para "My ball makes the"
	line "forest's #mon"
	cont "obey me. Watch"
	cont "their eyes."
	para "With Celebi I can"
	line "go back and win"
	cont "every fight I ever"
	cont "lost. Start here."
	done

.BeatenText:
	text "No! My Dark Ball"
	line "Celebi…!"
	done

.AfterText:
	text "The ball cracked?"
	line "No. Stay with me!"
	done

.ForestCalm:
	text "One by one, the"
	line "#mon step back"
	cont "into the trees."
	para "A bird calls once."
	line "This time its song"
	cont "doesn't repeat."
	done

.ForestText:
	text "The forest feels"
	line "peaceful again."

	para "The Marauder"
	line "dropped something!"
	done

IlexForestShadowBeedrillScript:
	loadwildmon BEEDRILL, 64
	sjumpfwd IlexForestShadowBattle

IlexForestShadowAriadosScript:
	loadwildmon ARIADOS, 65
	sjumpfwd IlexForestShadowBattle

IlexForestShadowNoctowlScript:
	loadwildmon NOCTOWL, 66
IlexForestShadowBattle:
; Link Edition: forest Pokemon held by the Marauder's black ball. They
; can't be caught or fled from; beating one frees it.
	showtext .Text
	loadvar VAR_BATTLETYPE, BATTLETYPE_SHADOW
	startbattle
	disappear LAST_TALKED
	reloadmapafterbattle
	jumptext .FreedText

.Text:
	text "Its eyes glint"
	line "like the black"
	cont "ball. It attacks!"
	done

.FreedText:
	text "The glint fades"
	line "from its eyes. It"
	cont "flees into the"
	cont "trees."
	done

IlexForestSammyScene:
; Link Edition: the traveler who kept calling from the other side of the
; shrine is Sammy, a boy from decades ago. The Dark Ball hurt Celebi; the
; shrine heals it, and it takes him home. (Prof. Oak tells the rest.)
	; (a story scene: the forest dims with Celebi's glow, and the shrine's
	; green light pulses until the daylight comes back)
	scene_begin
	musicfadeout MUSIC_ETERNA_FOREST_DPPT, 8 ; (the forest's hurt)
	moveobject ILEXFOREST_CELEBI, 10, 25
	appear ILEXFOREST_CELEBI
	scene_shadow ILEXFOREST_CELEBI ; (the Dark Ball's harm: a shadow of itself)
	playsound SFX_BALL_POOF
	waitsfx
	cry CELEBI
	; the corruption: the forest dark and sickly purple around it
	scene_tint TINT_DARK
	scene_tint TINT_PURPLE
	showtext .HurtText
	; the shrine's water: green light pulses out, and the forest heals
	musicfadeout MUSIC_WHITE_TREEHOLLOW_W2, 8
	playsound SFX_GAME_FREAK_LOGO_GS
	scene_reload_map ; (the corruption lifts: IlexForestSpecialCase)
	scene_restore
	scene_tint TINT_GREEN
	scene_pulse TINT_GREEN
	scene_unshadow ILEXFOREST_CELEBI ; (healed: its own colors again)
	scene_weather OW_WEATHER_CHERRY_BLOSSOMS ; (and the forest blooms)
	showemote EMOTE_SPARKLE_GREEN, ILEXFOREST_CELEBI, 20
	waitsfx
	applymovement ILEXFOREST_CELEBI, MovementData_CelebiDance
	cry CELEBI
	showtext .HealedText
	; (time bends: a white haze as Sammy steps out of his own time)
	scene_tint TINT_WHITE
	playsound SFX_WARP_FROM
	appear ILEXFOREST_SAMMY
	waitsfx
	scene_restore
	showemote EMOTE_SHOCK, ILEXFOREST_SAMMY, 15
	showtext .SammyText
	turnobject ILEXFOREST_SAMMY, LEFT
	musicfadeout MUSIC_CELESTIAL_TOWER_BW, 8 ; (a farewell)
	cry CELEBI
	showemote EMOTE_SPARKLE_GREEN, ILEXFOREST_CELEBI, 15
	; it rises, and the camera follows it up through the trees
	playsound SFX_WARP_TO
	scene_flash 1
	disappear ILEXFOREST_SAMMY
	applymovement ILEXFOREST_CELEBI, MovementData_CelebiRise
	scene_pan UP, 2
	applymovement ILEXFOREST_CELEBI, MovementData_CelebiRise
	showemote EMOTE_SPARKLE_GREEN, ILEXFOREST_CELEBI, 15
	playsound SFX_WARP_TO
	scene_flash 2
	disappear ILEXFOREST_CELEBI
	waitsfx
	pause 30
	scene_pan_back UP, 2
	scene_end
	showtext .GoneText
	end

.HurtText:
	text "Celebi drifts out"
	line "of the shrine."

	para "Its glow is dim."
	line "The Dark Ball hurt"
	cont "it."
	done

.HealedText:
	text "The shrine's water"
	line "shines. Celebi's"
	cont "glow comes back!"
	done

.SammyText:
	text "You can hear me"
	line "now? I'm Sammy!"

	para "A man in an iron"
	line "mask was hunting"
	cont "this Celebi."

	para "It pulled me"
	line "through time to"
	cont "get away, and the"
	cont "forest kept going"
	cont "around in circles."

	para "I called and"
	line "called. You broke"
	cont "the loop!"

	para "Celebi can take me"
	line "home now. When I"
	cont "grow up, I want to"
	cont "study #mon in"
	cont "Pallet Town!"

	para "Thank you. I'll"
	line "never forget you!"
	done

.GoneText:
	text "Sammy and Celebi"
	line "vanish into the"
	cont "light."
	done

IlexForestMarauderPrizeScript:
; If the bag was full, the reward stays where he dropped it. His defeat
; stays recorded, including after reloading the map or continuing a save.
	checkevent EVENT_MARAUDER_REWARD_PENDING
	iffalsefwd .Done
	opentext
	writetext IlexForestIronMaskScript.ForestText
	promptbutton
	verbosegiveitem BIG_NUGGET, iffalse_endtext
	clearevent EVENT_MARAUDER_REWARD_PENDING
	endtext
.Done:
	end

