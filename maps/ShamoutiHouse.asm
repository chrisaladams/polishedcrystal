ShamoutiHouse_MapScriptHeader:
	def_scene_scripts

	def_callbacks
	callback MAPCALLBACK_OBJECTS, ShamoutiHouseCastCallback

	def_warp_events
	warp_event  2,  7, SHAMOUTI_ISLAND, 5
	warp_event  3,  7, SHAMOUTI_ISLAND, 5

	def_coord_events

	def_bg_events

	def_object_events
	object_event  4,  1, SPRITE_VETERAN_M, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, OrangeLeagueDrakeScript, -1
	; Link Edition: his Dragonite, out for the final and the ceremony
	object_event  5,  1, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, DRAGONITE, -1, PAL_MON_ORANGE, OBJECTTYPE_SCRIPT, PLAIN_FORM, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN

	object_const_def
	const SHAMOUTIHOUSE_DRAKE
	const SHAMOUTIHOUSE_DRAGONITE

ShamoutiHouseCastCallback:
	setevent EVENT_POST_RED_PERSON_HIDDEN ; (Dragonite comes out in the scenes)
	endcallback

OrangeLeagueDrakeScript:
; Link Edition: the Orange League's Head Leader
	faceplayer
	opentext
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iftruefwd .SeasonOpen
	farsjump OrangeLeagueClosed
.SeasonOpen:
	checkevent EVENT_BEAT_DRAKE
	iftruefwd .Beaten
	checkevent EVENT_BEAT_ORANGE_CREW_CISSY
	iffalse_jumpopenedtext .NotYetText
	checkevent EVENT_BEAT_ORANGE_CREW_DANNY
	iffalse_jumpopenedtext .NotYetText
	checkevent EVENT_BEAT_ORANGE_CREW_RUDY
	iffalse_jumpopenedtext .NotYetText
	checkevent EVENT_BEAT_ORANGE_CREW_LUANA
	iffalse_jumpopenedtext .NotYetText
	writetext .IntroText
	waitbutton
	closetext
	scene_title .FinalTitle
	scene_begin ; (his Dragonite comes out, a shadow, and its roar shakes the room)
	scene_place SHAMOUTIHOUSE_DRAGONITE, 1, -1
	appear SHAMOUTIHOUSE_DRAGONITE
	scene_shadow SHAMOUTIHOUSE_DRAGONITE
	pause 15
	cry DRAGONITE
	earthquake 8
	scene_flash 1
	scene_unshadow SHAMOUTIHOUSE_DRAGONITE
	waitsfx
	scene_end
	winlosstext .BeatenText, 0
	loadtrainer DRAKE_T, 1
	startbattle
	reloadmapafterbattle
	setevent EVENT_BEAT_DRAKE
	scene_title .ChampionTitle
	scene_begin ; (the ceremony: the trophy in gold light, sparkles, a roar)
	scene_tint TINT_GOLD
	showemote EMOTE_SPARKLE, PLAYER, 20
	showemote EMOTE_SPARKLE, SHAMOUTIHOUSE_DRAKE, 15
	cry DRAGONITE
	showemote EMOTE_HAPPY, SHAMOUTIHOUSE_DRAGONITE, 20
	waitsfx
	opentext
	writetext .TrophyText
	playsound SFX_GET_BADGE
	waitsfx
	promptbutton
	scene_end
	disappear SHAMOUTIHOUSE_DRAGONITE
	farscall GiveNextStoryLead
.Prize:
	checkevent EVENT_GOT_ORANGE_LEAGUE_PRIZE
	iftruefwd .GotPrize
	writetext .PrizeText
	promptbutton
	verbosegiveitems BOTTLE_CAP, 3, iffalse_endtext
	setevent EVENT_GOT_ORANGE_LEAGUE_PRIZE
.GotPrize:
	jumpthisopenedtext

	text "Your name goes in"
	line "the Orange League"
	cont "record book!"
	done

.FinalTitle:
	db "ORANGE LEAGUE FINAL@"
.ChampionTitle:
	db "A NEW CHAMPION@"

.Beaten:
	checkevent EVENT_GOT_ORANGE_LEAGUE_PRIZE
	iffalse .Prize
	farwritetext OrangeLeagueRematchText
	yesorno
	iffalsefwd .No
	closetext
	winlosstext .BeatenText, 0
	loadtrainer DRAKE_T, 1
	startbattle
	reloadmapafterbattle
	end

.No:
	closetext
	end

.NotYetText:
	text "I'm Drake, Head"
	line "Leader of the"
	cont "Orange League."

	text_far OrangeLeagueHintText
	text_end

.IntroText:
	text "So, you've beaten"
	line "the Orange Crew."

	para "No challenger has"
	line "ever beaten me."

	para "Let's make this a"
	line "full battle!"
	done

.BeatenText:
	text "Incredible…"

	para "You're the new"
	line "champion of the"
	cont "Orange League!"
	done

.TrophyText:
	text "<PLAYER> received"
	line "the Winner's"
	cont "Trophy!"
	done

.PrizeText:
	text "And take these,"
	line "for the battles"
	cont "still to come."
	done

OrangeLeagueHintText::
	para "The Orange League"
	line "has four Crew"
	cont "leaders:"

	para "Cissy on Warm"
	line "Beach, Danny on"
	cont "Rocky Beach, Rudy"

	para "on Beautiful"
	line "Beach, and Luana"
	cont "on Valencia."

	para "Beat all four,"
	line "then face Head"
	cont "Leader Drake in"

	para "the house on"
	line "Shamouti Island!"
	done

OrangeLeagueRematchText::
	text "Want to battle"
	line "again?"
	done

OrangeLeagueClosed::
	jumpthisopenedtext

	text "The Crew is still"
	line "training."
	para "The season opens"
	line "once you beat Red"
	cont "on Mt.Silver."
	done
