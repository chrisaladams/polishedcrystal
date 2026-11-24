BlackthornDragonSpeechHouse_MapScriptHeader:
	def_scene_scripts

	def_callbacks

	def_warp_events
	warp_event  2,  7, BLACKTHORN_CITY, 2
	warp_event  3,  7, BLACKTHORN_CITY, 2

	def_coord_events

	def_bg_events
	bg_event  7,  1, BGEVENT_JUMPSTD, difficultbookshelf

	def_object_events
	object_event  2,  3, SPRITE_GRANNY, SPRITEMOVEDATA_SPINRANDOM_SLOW, 0, 0, -1, 0, OBJECTTYPE_COMMAND, jumptextfaceplayer, BlackthornDragonSpeechHouseGrannyText, -1
	pokemon_event  5,  5, DRATINI, SPRITEMOVEDATA_POKEMON, -1, PAL_MON_BLUE, BlackthornDragonSpeechHouseDratiniText, -1
	object_event  5,  2, SPRITE_DRAGON_TAMER, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, DragonMastersCupScript, -1

BlackthornDragonSpeechHouseGrannyText:
	text "A clan of trainers"
	line "who can freely"

	para "command dragons"
	line "live right here in"
	cont "Blackthorn."

	para "As a result, there"
	line "are many legends"

	para "about dragons in"
	line "this town."
	done

BlackthornDragonSpeechHouseDratiniText:
	text "Dratini: Draa!"
	done

DragonMastersCupScript:
; Link Edition: the Dragon Masters Cup, after the Rising Badge: your whole
; party (three to six, one at least a Dragon type) at level 50 against Dragon
; Tamers Erick and Aegon, then Clair. The first win gives a Dragon Scale,
; each one after a PP Up.
	faceplayer
	opentext
	checkevent EVENT_DRAGON_MASTERS_PRIZE_PENDING
	iftruefwd .FirstPrize
	checkflag ENGINE_RISINGBADGE
	iffalse_jumpopenedtext .NoBadgeText
	writetext .WelcomeText
	yesorno
	iffalse_jumpopenedtext .NoText
	loadmem wCupId, CUP_DRAGON
	callasm CupSelectTeam
	ifequalfwd CUPTEAM_OK, .Begin
	ifequalfwd CUPTEAM_SIZE, .TooFew
	jumpopenedtext .NoDragonText

.TooFew:
	jumpopenedtext .TooFewText

.Begin:
	writetext .Round1Text
	waitbutton
	closetext
	callasm CupBegin
	winlosstext .WinText, .LossText
	loadtrainer DRAGON_TAMER, ERICK
	loadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
	startbattle
	reloadmap
	iftruefwd .Lost
	callasm CupHealTeam
	opentext
	writetext .Round2Text
	waitbutton
	closetext
	winlosstext .WinText, .LossText
	loadtrainer DRAGON_TAMER, AEGON
	loadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
	startbattle
	reloadmap
	iftruefwd .Lost
	callasm CupHealTeam
	opentext
	writetext .FinalText
	waitbutton
	closetext
	winlosstext .ClairWinText, .LossText
	loadtrainer CLAIR, 1
	loadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
	startbattle
	reloadmap
	iftruefwd .Lost
	callasm CupEnd
	callasm CupWin
	opentext
	writetext .ChampionText
	playsound SFX_GET_BADGE
	waitsfx
	promptbutton
	iffalsefwd .Again
	setevent EVENT_DRAGON_MASTERS_PRIZE_PENDING
.FirstPrize:
	verbosegiveitem DRAGON_SCALE, iffalse_endtext
	clearevent EVENT_DRAGON_MASTERS_PRIZE_PENDING
	jumpopenedtext .ComeBackText

.Again:
	verbosegiveitem PP_UP, iffalse_endtext
	jumpopenedtext .ComeBackText

.Lost:
	callasm CupEnd
	jumptext .OutText

.NoBadgeText:
	text "The Dragon Masters"
	line "Cup is for those"

	para "who hold Clair's"
	line "Rising Badge."
	done

.WelcomeText:
	text "Welcome to the"
	line "Dragon Masters"
	cont "Cup!"

	para "Your whole party"
	line "enters, at level"
	cont "50, with at least"
	cont "one Dragon type."

	para "Three rounds, the"
	line "last against"
	cont "Clair herself."

	para "No penalty if you"
	line "lose. Enter?"
	done

.NoText:
	text "The dragons will"
	line "wait for you."
	done

.NoDragonText:
	text "Your party needs"
	line "a Dragon-type"
	cont "#mon to enter."
	done

.TooFewText:
	text "You'll need at"
	line "least three"
	cont "#mon to enter."
	done

.Round1Text:
	text "Round one: Dragon"
	line "Tamer Erick!"
	done

.Round2Text:
	text "Round two: Dragon"
	line "Tamer Aegon!"
	done

.FinalText:
	text "The final round:"
	line "Clair!"
	done

.WinText:
	text "A true dragon"
	line "tamer!"
	done

.ClairWinText:
	text "Hmph. You've"
	line "earned the title."
	done

.LossText:
	text "The dragons have"
	line "spoken…"
	done

.ChampionText:
	text "<PLAYER> won the"
	line "Dragon Masters"
	cont "Cup!"
	done

.ComeBackText:
	text "Come back and"
	line "defend the title!"
	done

.OutText:
	text "Train with your"
	line "dragons and come"
	cont "back."
	done
