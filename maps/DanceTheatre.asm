DanceTheatre_MapScriptHeader:
	def_scene_scripts

	def_callbacks

	def_warp_events
	warp_event  5, 15, ECRUTEAK_CITY, 8
	warp_event  6, 15, ECRUTEAK_CITY, 8

	def_coord_events

	def_bg_events
	bg_event  5,  6, BGEVENT_UP, MapDanceTheatreSignpost1Script
	bg_event  6,  6, BGEVENT_UP, MapDanceTheatreSignpost1Script

	def_object_events
	object_event  0,  2, SPRITE_KIMONO_GIRL, SPRITEMOVEDATA_SPINCOUNTERCLOCKWISE, 0, 0, -1, PAL_NPC_RED, OBJECTTYPE_GENERICTRAINER, 0, GenericTrainerKimono_girlNaoko, -1
	object_event  2,  1, SPRITE_KIMONO_GIRL, SPRITEMOVEDATA_SPINRANDOM_FAST, 0, 0, -1, PAL_NPC_PURPLE, OBJECTTYPE_TRAINER, 0, GenericTrainerKimono_girlSayo, -1
	object_event  6,  2, SPRITE_KIMONO_GIRL, SPRITEMOVEDATA_SPINRANDOM_SLOW, 0, 0, -1, PAL_NPC_BLACK, OBJECTTYPE_TRAINER, 0, GenericTrainerKimono_girlZuki, -1
	object_event  9,  1, SPRITE_KIMONO_GIRL, SPRITEMOVEDATA_SPINRANDOM_FAST, 0, 0, -1, PAL_NPC_BLUE, OBJECTTYPE_TRAINER, 0, GenericTrainerKimono_girlKuni, -1
	object_event 11,  2, SPRITE_KIMONO_GIRL, SPRITEMOVEDATA_SPINCLOCKWISE, 0, 0, -1, PAL_NPC_YELLOW, OBJECTTYPE_TRAINER, 0, GenericTrainerKimono_girlMiki, -1
	object_event  7, 12, SPRITE_GENTLEMAN, SPRITEMOVEDATA_STANDING_UP, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, DanceTheaterSurfGuy, -1
	pokemon_event  6, 10, RHYDON, SPRITEMOVEDATA_POKEMON, -1, PAL_MON_BROWN, RhydonText, -1
	object_event 10, 12, SPRITE_ACE_TRAINER_M, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, 0, OBJECTTYPE_COMMAND, jumptextfaceplayer, DanceTheatreCooltrainerMText, -1
	object_event  3,  6, SPRITE_GRANNY, SPRITEMOVEDATA_STANDING_UP, 0, 0, -1, 0, OBJECTTYPE_COMMAND, jumptextfaceplayer, DanceTheatreGrannyText, -1
	object_event  1, 10, SPRITE_LADY, SPRITEMOVEDATA_STANDING_UP, 0, 0, -1, PAL_NPC_GREEN, OBJECTTYPE_COMMAND, jumptextfaceplayer, DanceTheatreLadyText, -1
	object_event  4, 12, SPRITE_GRANNY, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, PAL_NPC_PURPLE, OBJECTTYPE_SCRIPT, 0, DanceTheatreKimonoCupScript, -1

GenericTrainerKimono_girlNaoko:
	assert !DEF(TRAINERPAL_NAOKO) ; the default TRAINERPAL_KIMONO_GIRL is hers
	generictrainer KIMONO_GIRL, NAOKO, EVENT_BEAT_KIMONO_GIRL_NAOKO, Kimono_girlNaokoSeenText, Kimono_girlNaokoBeatenText

	text "I enjoyed that"
	line "bout. I would like"
	cont "to see you again."
	done

GenericTrainerKimono_girlSayo:
	trainer KIMONO_GIRL, SAYO, EVENT_BEAT_KIMONO_GIRL_SAYO, Kimono_girlSayoSeenText, Kimono_girlSayoBeatenText, 0, .Script, TRAINERPAL_SAYO

.Script:
	endifjustbattled
	jumpthistextfaceplayer

	text "Rhythm is impor-"
	line "tant for both"

	para "dancing and #-"
	line "mon."
	done

GenericTrainerKimono_girlZuki:
	trainer KIMONO_GIRL, ZUKI, EVENT_BEAT_KIMONO_GIRL_ZUKI, Kimono_girlZukiSeenText, Kimono_girlZukiBeatenText, 0, .Script, TRAINERPAL_ZUKI

.Script:
	endifjustbattled
	jumpthistextfaceplayer

	text "I put a different"
	line "flower in my bar-"
	cont "rette every month."
	done

GenericTrainerKimono_girlKuni:
	trainer KIMONO_GIRL, KUNI, EVENT_BEAT_KIMONO_GIRL_KUNI, Kimono_girlKuniSeenText, Kimono_girlKuniBeatenText, 0, .Script, TRAINERPAL_KUNI

.Script:
	endifjustbattled
	jumpthistextfaceplayer

	text "I trained a lot,"
	line "so I thought I was"

	para "a capable trainer."
	line "I guess I'm not."
	done

GenericTrainerKimono_girlMiki:
	trainer KIMONO_GIRL, MIKI, EVENT_BEAT_KIMONO_GIRL_MIKI, Kimono_girlMikiSeenText, Kimono_girlMikiBeatenText, 0, .Script, TRAINERPAL_MIKI

.Script:
	endifjustbattled
	jumpthistextfaceplayer

	text "I can keep dancing"
	line "because there are"

	para "people who enjoy"
	line "what I do."

	para "My #mon keep my"
	line "spirits up too."
	done

DanceTheaterSurfGuy:
	faceplayer
	opentext
	writetext SurfGuyNeverLeftAScratchText
	promptbutton
	checkevent EVENT_GOT_HM03_SURF
	iftrue_jumpopenedtext SurfGuyElegantKimonoGirlsText
	checkevent EVENT_BEAT_KIMONO_GIRL_NAOKO
	iffalsefwd .KimonoGirlsUndefeated
	checkevent EVENT_BEAT_KIMONO_GIRL_SAYO
	iffalsefwd .KimonoGirlsUndefeated
	checkevent EVENT_BEAT_KIMONO_GIRL_ZUKI
	iffalsefwd .KimonoGirlsUndefeated
	checkevent EVENT_BEAT_KIMONO_GIRL_KUNI
	iffalsefwd .KimonoGirlsUndefeated
	checkevent EVENT_BEAT_KIMONO_GIRL_MIKI
	iffalsefwd .KimonoGirlsUndefeated
	writetext SurfGuyLikeADanceText
	promptbutton
	verbosegivetmhm HM_SURF
	setevent EVENT_GOT_HM03_SURF
	jumpthisopenedtext

	text "That's Surf."

	para "It's a move that"
	line "lets #mon swim"
	cont "across water."
	done

.KimonoGirlsUndefeated:
	jumpthisopenedtext

	text "Kiddo! If you can"
	line "defeat all the"

	para "Kimono Girls, I'll"
	line "give you a gift."
	done

MapDanceTheatreSignpost1Script:
	jumpthistext

	text "It's a fancy panel"
	line "that's decorated"
	cont "with flowers."
	done

Kimono_girlNaokoSeenText:
	text "You have lovely"
	line "#mon. May I see"
	cont "them in battle?"
	done

Kimono_girlNaokoBeatenText:
	text "Oh, you are very"
	line "strong."
	done

Kimono_girlSayoSeenText:
	text "I always dance"
	line "with my #mon."

	para "Of course, I also"
	line "train them."
	done

Kimono_girlSayoBeatenText:
	text "Oh, so close!"
	line "I almost had you."
	done

Kimono_girlZukiSeenText:
	text "Isn't my barrette"
	line "pretty?"

	para "Oh. A #mon"
	line "battle?"
	done

Kimono_girlZukiBeatenText:
	text "I don't have any"
	line "#mon left…"
	done

Kimono_girlKuniSeenText:
	text "Oh, you're a cute"
	line "trainer. Would you"
	cont "like to battle?"
	done

Kimono_girlKuniBeatenText:
	text "You're stronger"
	line "than you look."
	done

Kimono_girlMikiSeenText:
	text "Do you like my"
	line "dancing? I'm good"
	cont "at #mon too."
	done

Kimono_girlMikiBeatenText:
	text "Ooh, you're good"
	line "at #mon too."
	done

SurfGuyNeverLeftAScratchText:
	text "Not only are the"
	line "Kimono Girls great"

	para "dancers, they're"
	line "also skilled at"
	cont "#mon."

	para "I always challenge"
	line "them, but I've"

	para "never even left a"
	line "scratch…"
	done

SurfGuyLikeADanceText:
	text "The way you bat-"
	line "tled, it was like"
	cont "watching a dance."

	para "It was a rare"
	line "treat to see!"

	para "I want you to have"
	line "this. Don't worry"
	cont "--take it!"
	done

SurfGuyElegantKimonoGirlsText:
	text "I wish my #mon"
	line "were as elegant as"
	cont "the Kimono Girls."
	done

RhydonText:
	text "Rhydon: Gugooh"
	line "gugogooh!"
	done

DanceTheatreCooltrainerMText:
	text "That man's always"
	line "with his Rhydon."

	para "Says he wants a"
	line "#mon that can"
	cont "Surf and dance."

	para "Is he trying to"
	line "make a synchro-"
	cont "nized swimming"
	cont "#mon?"
	done

DanceTheatreGrannyText:
	text "The Kimono Girls"
	line "are so beautiful…"

	para "But they have to"
	line "go through rigor-"
	cont "ous training."

	para "And they have to"
	line "learn to follow"

	para "customs before ap-"
	line "pearing in public."

	para "But if you love"
	line "something, any-"
	cont "thing is possible."
	done

DanceTheatreLadyText:
	text "Eevee can evolve"
	line "into Leafeon, Gla-"
	cont "ceon, or Sylveon,"

	para "but I don't see"
	line "any of them here."

	para "I wonder if the"
	line "Kimono Girls who"

	para "use them are"
	line "somewhere else?"
	done

DanceTheatreKimonoCupScript:
; Link Edition: the Kimono Cup: three of today's type at level 50 against
; three Kimono Girls with teams of that type. Today's type follows the world
; clock's days, all 18 in turn. The first win with a type gives its item
; (Silk Scarf for Normal, and so on), each one after a Big Pearl.
	faceplayer
	opentext
	callasm KimonoCupPendingPrize
	iftruefwd .Prize
	callasm KimonoCupToday
	callasm KimonoCupNextNew
	writetext .WelcomeText
	promptbutton
	ifequalfwd 0, .Enter
	ifequalfwd NUM_KIMONO_TYPES, .Mastered
	writetext .WonBeforeText
	sjumpfwd .WonBefore
.Mastered:
	writetext .MasteredText
.WonBefore:
	promptbutton
.Enter:
	writetext .EnterText
	yesorno
	iffalse_jumpopenedtext .NoText
	loadmem wCupId, CUP_KIMONO
	writetext .ChooseText
	promptbutton
	callasm CupSelectTeam
	ifequalfwd CUPTEAM_CANCEL, .Cancel
	ifequalfwd CUPTEAM_OK, .Begin
	ifequalfwd CUPTEAM_TYPE, .WrongType
	jumpopenedtext .RulesText

.WrongType:
	jumpopenedtext .WrongTypeText

.Cancel:
	jumpopenedtext .NoText

.Begin:
	writetext .Round1Text
	waitbutton
	closetext
	callasm CupBegin
	winlosstext .WinText, .LossText
	loadmem wCupFoeSize, 3
	loadtrainer KIMONO_GIRL, SAYO
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
	loadmem wCupFoeSize, 3
	loadtrainer KIMONO_GIRL, ZUKI
	loadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
	startbattle
	reloadmap
	iftruefwd .Lost
	callasm CupHealTeam
	opentext
	writetext .FinalText
	waitbutton
	closetext
	winlosstext .WinText, .LossText
	loadmem wCupFoeSize, 4
	loadtrainer KIMONO_GIRL, MIKI
	loadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
	startbattle
	reloadmap
	iftruefwd .Lost
	callasm CupEnd
	opentext
	writetext .ChampionText
	playsound SFX_GET_BADGE
	waitsfx
	promptbutton
	callasm CupWin
	iffalsefwd .Again
	callasm KimonoCupQueuePrize
.Prize:
	verbosegiveitem ITEM_FROM_MEM, iffalse_jumpopenedtext .NoRoomText
	callasm KimonoCupClearPrize
	callasm KimonoCupTypesWon
	getnum STRING_BUFFER_4
	ifequalfwd NUM_KIMONO_TYPES, .AllTypes
	jumpopenedtext .TypesWonText

.AllTypes:
	jumpopenedtext .AllTypesText

.Again:
	verbosegiveitem BIG_PEARL, iffalse_endtext
	jumpopenedtext .ComeBackText

.Lost:
	callasm CupEnd
	jumptext .OutText

.WelcomeText:
	text "Welcome to the"
	line "Kimono Cup!"

	para "Today's type is"
	line "@"
	text_ram wStringBuffer3
	text "."
	done

.WonBeforeText:
	text "You've won with"
	line "@"
	text_ram wStringBuffer3
	text " before."

	para "The next new type,"
	line "@"
	text_ram wStringBuffer4
	text ", is"
	cont "@"
	text_decimal hScriptVar, 1, 2
	text " day(s) away."
	done

.MasteredText:
	text "You've won with"
	line "every type. A true"
	cont "Kimono master!"
	done

.EnterText:
	text "Enter three"
	line "#mon of that"
	cont "type. They'll"
	cont "battle at level"
	cont "50 against three"
	cont "Kimono Girls."

	para "No penalty if you"
	line "lose. Enter?"
	done

.NoText:
	text "The stage is"
	line "always open!"
	done

.ChooseText:
	text "Choose three"
	line "#mon to enter."
	prompt

.WrongTypeText:
	text "Sorry, today all"
	line "three must be"
	cont "@"
	text_ram wStringBuffer3
	text "-type."
	done

.RulesText:
	text "Sorry, that team"
	line "can't enter."
	done

.Round1Text:
	text "Round one: Sayo!"
	done

.Round2Text:
	text "Round two: Zuki!"
	done

.FinalText:
	text "The final round:"
	line "Miki!"
	done

.WinText:
	text "A graceful win!"
	done

.LossText:
	text "The dance is"
	line "over…"
	done

.ChampionText:
	text "<PLAYER> won the"
	line "Kimono Cup!"
	done

.NoRoomText:
	text "Oh, you've no room"
	line "for your prize."

	para "I'll hold it here"
	line "until you return."
	done

.TypesWonText:
	text "You've won with"
	line "@"
	text_ram wStringBuffer4
	text " of 18 types."

	para "Come back for"
	line "another type!"
	done

.AllTypesText:
	text "You've won with"
	line "all 18 types!"

	para "The Kimono Girls"
	line "will remember"
	cont "your dance!"
	done

.ComeBackText:
	text "Come back for"
	line "another type!"
	done

.OutText:
	text "That's the end of"
	line "the dance for now."
	done
