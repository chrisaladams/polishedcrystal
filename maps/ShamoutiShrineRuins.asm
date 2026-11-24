ShamoutiShrineRuins_MapScriptHeader:
	def_scene_scripts

	def_callbacks
	callback MAPCALLBACK_OBJECTS, ShamoutiShrineLawrenceCallback

	def_warp_events
	warp_event  2, 18, NOISY_FOREST, 3
	warp_event  2, 19, NOISY_FOREST, 4

	def_coord_events

	def_bg_events
	bg_event  7, 10, BGEVENT_ITEM + MAX_REVIVE, EVENT_SHAMOUTI_SHRINE_RUINS_HIDDEN_MAX_REVIVE

	def_object_events
	object_event  8, 11, SPRITE_LAWRENCE, SPRITEMOVEDATA_SPINRANDOM_SLOW, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, ShamoutiShrineRuinsLawrenceScript, EVENT_LAWRENCE_SHAMOUTI_SHRINE_RUINS
	object_event 10, 17, SPRITE_GRAMPS, SPRITEMOVEDATA_STANDING_UP, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, ShamoutiShrineKeeper, -1
	object_event 14, 13, SPRITE_LADY, SPRITEMOVEDATA_WALK_UP_DOWN, 2, 0, -1, PAL_NPC_BLUE, OBJECTTYPE_SCRIPT, 0, ShamoutiShrineMelody, -1
	itemball_event  4, 27, RARE_CANDY, 1, EVENT_SHAMOUTI_SHRINE_RUINS_RARE_CANDY

	object_const_def
	const SHAMOUTISHRINERUINS_LAWRENCE

ShamoutiShrineLawrenceCallback:
	checkevent EVENT_BEAT_LAWRENCE
	iftruefwd .Hide
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalsefwd .Done
	appear SHAMOUTISHRINERUINS_LAWRENCE
.Done:
	endcallback
.Hide:
	disappear SHAMOUTISHRINERUINS_LAWRENCE
	endcallback

ShamoutiShrineRuinsLawrenceScript:
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalsefwd .Battle
	scall ShamoutiCheckBeacons
	iffalse_jumptextfaceplayer .Waiting
.Battle:
	special Special_FadeOutMusic
	pause 15
	playmusic MUSIC_ZINNIA_ENCOUNTER_ORAS
	showtextfaceplayer .SeenText
	winlosstext .BeatenText, 0
	setlasttalked SHAMOUTISHRINERUINS_LAWRENCE
	loadtrainer LAWRENCE, 1
	startbattle
	dontrestartmapmusic
	reloadmapafterbattle
	special DeleteSavedMusic
	playmusic MUSIC_ZINNIA_ENCOUNTER_ORAS
	opentext
	writetext .AfterText
	promptbutton
	scall ShamoutiGiveSilverWing
	closetext
	readvar VAR_FACING
	ifequalfwd UP, .up
	ifequalfwd DOWN, .down
	ifequalfwd LEFT, .left
.right
	turnobject SHAMOUTISHRINERUINS_LAWRENCE, RIGHT
	sjumpfwd .continue
.up
	turnobject SHAMOUTISHRINERUINS_LAWRENCE, UP
	sjumpfwd .continue
.down
	turnobject SHAMOUTISHRINERUINS_LAWRENCE, DOWN
	sjumpfwd .continue
.left
	turnobject SHAMOUTISHRINERUINS_LAWRENCE, LEFT
.continue
	pause 40
	showtextfaceplayer .GoodbyeText
	playsound SFX_WARP_TO
	special Special_FadeBlackQuickly
	special Special_ReloadSpritesNoPalettes
	disappear SHAMOUTISHRINERUINS_LAWRENCE
	waitsfx
	special Special_FadeInQuickly
	setevent EVENT_BEAT_LAWRENCE
	playmapmusic
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iftrue ShamoutiRestoreBeacons
	end

.Waiting:
	text "Lawrence: The sea"
	line "won't answer."
	para "Help the keeper"
	line "light the towers."
	cont "Then talk to me."
	done

.SeenText:
	text "Lawrence: I sought"
	line "across many"

	para "regions to catch"
	line "Articuno, Zapdos,"
	cont "and Moltres."

	para "Without the"
	line "complete set, I"

	para "cannot awaken the"
	line "guardian of the"
	cont "sea…"

	para "You're going to"
	line "help me complete"
	cont "my collection!"
	done

.BeatenText:
	text "Unbelievable."
	line "You beat my legen-"
	cont "dary collection…"
	done

.AfterText:
	text "Lawrence: I rang"
	line "each beacon alone"
	cont "to lure each bird."
	para "Ships lost their"
	line "way. I blamed the"
	cont "storm until now."
	para "Your team listened"
	line "even when it could"
	cont "have walked away."
	para "I can't collect"
	line "that, can I?"
	done

.GoodbyeText:
	text "I'm going to the"
	line "harbor. I owe a"
	cont "few people there"
	cont "an explanation."
	done

ShamoutiGiveSilverWing:
	checkkeyitem SILVER_WING
	iftrue DoNothingScript
	verbosegivekeyitem SILVER_WING
	writetext .WingText
	promptbutton
	end

.WingText:
	text "That's a feather"
	line "from the guardian."
	para "Bring it to the"
	line "Whirl Islands if"
	cont "you wish to meet."
	done

ShamoutiShrineKeeper:
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalse_jumptextfaceplayer ShamoutiShrineRuinsGrampsText
	faceplayer
	checkevent EVENT_RESTORED_SHAMOUTI_BEACONS
	iftrue_jumptext .Calm
	checkevent EVENT_HEARD_SHAMOUTI_BEACONS
	iftruefwd .Check
	setevent EVENT_HEARD_SHAMOUTI_BEACONS
	callasm SetCurrentWeather
	jumptext .Start
.Check:
	scall ShamoutiCheckBeacons
	iffalse_jumptext .Pending
	checkevent EVENT_BEAT_LAWRENCE
	iftrue ShamoutiRestoreBeacons
	jumptext .Lawrence

.Start:
	text "The old ferry"
	line "lights went dark."
	para "Melody says all"
	line "three must shine"
	cont "to calm this sea."
	para "Surf along the"
	line "coast. On each"
	cont "peak is a tower."
	para "Fire, Ice and"
	line "Lightning. Start"
	cont "with any of them."
	done
.Pending:
	text "I can see some of"
	line "the colors. The"
	cont "rest are dark."
	para "Your map shows"
	line "which towers need"
	cont "a visit."
	done
.Lawrence:
	text "All three lights!"
	line "Lawrence is by"
	cont "the upper steps."
	para "Ask him why he"
	line "put them out."
	done
.Calm:
	text "The first ferry"
	line "back sounded its"
	cont "horn all the way."
	done

ShamoutiShrineMelody:
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalse_jumptextfaceplayer ShamoutiShrineRuinsLadyText
	checkevent EVENT_RESTORED_SHAMOUTI_BEACONS
	iftrue_jumptextfaceplayer .After
	jumpthistextfaceplayer

	text "I'm Melody. See"
	line "the three marks"
	cont "on the old shrine?"
	para "Three lights make"
	line "one channel. Out"
	cont "there, that means"
	cont "the way home."
	para "The guardian only"
	line "hears our song if"
	cont "the lights meet."
	para "Ask the keeper"
	line "where to look."
	done
.After:
	text "Melody: That's the"
	line "first song I ever"
	cont "finished without"
	cont "losing my breath."
	done

ShamoutiCheckBeacons:
	checkevent EVENT_TUNED_FIRE_BEACON
	iffalse DoNothingScript
	checkevent EVENT_TUNED_ICE_BEACON
	iffalse DoNothingScript
	checkevent EVENT_TUNED_LIGHTNING_BEACON
	end

ShamoutiBeaconHandoff:
	scall ShamoutiCheckBeacons
	iftrue_jumptext .Return
	end

.Return:
	text "All three beams"
	line "meet over the sea."
	para "Return to the"
	line "Shamouti shrine."
	done

ShamoutiSilentBeaconText:
	text "An unlit beacon."
	para "Three symbols are"
	line "cut into its base."
	done

ShamoutiTunedBeaconText:
	text "The beacon sends"
	line "a steady beam over"
	cont "the water."
	done

ShamoutiRestoreBeacons:
	setevent EVENT_RESTORED_SHAMOUTI_BEACONS
	callasm SetCurrentWeather
	playmusic MUSIC_LUGIAS_SONG_2000
	showtext .Song
	cry LUGIA
	waitsfx
	showtext .Calm
	opentext
	scall ShamoutiGiveSilverWing
	closetext
	playmapmusic
	end

.Song:
	text "Melody's song"
	line "carries out where"
	cont "the lights meet."
	para "Something huge"
	line "passes underneath."
	done
.Calm:
	text "The waves settle."
	para "A ferry sounds its"
	line "horn beyond the"
	cont "reef, then turns"
	cont "toward the lights."
	done

ShamoutiShrineRuinsGrampsText:
	text "This shrine was"
	line "magnificent when"
	cont "I was a child."

	para "But alas, it was"
	line "wrecked by a storm"
	cont "many years ago."

	para "The storm threat-"
	line "ened the entire"
	cont "island, but we"

	para "were protected by"
	line "the Guardian of"
	cont "the Seas."

	para "Every year, I give"
	line "thanks in honor"

	para "of the great"
	line "#mon who kept"
	cont "us safe."
	done

ShamoutiShrineRuinsLadyText:
	text "I simply had to"
	line "stop at Shamouti"

	para "Island on my"
	line "world tour."

	para "Apparently there's"
	line "a talking #mon"
	cont "here somewhere."
	done
