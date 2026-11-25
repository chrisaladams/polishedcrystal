PokemonMansionB1F_MapScriptHeader:
	def_scene_scripts

	def_callbacks

	def_warp_events
	warp_event 25, 24, POKEMON_MANSION_1F, 3

	def_coord_events

	def_bg_events
	bg_event 26,  4, BGEVENT_ITEM + MAX_ELIXIR, EVENT_POKEMON_MANSION_B1F_HIDDEN_MAX_ELIXIR
	bg_event  8, 13, BGEVENT_ITEM + RARE_CANDY, EVENT_POKEMON_MANSION_B1F_HIDDEN_RARE_CANDY
	bg_event 20, 27, BGEVENT_ITEM + BERSERK_GENE, EVENT_POKEMON_MANSION_B1F_HIDDEN_BERSERK_GENE
	bg_event 20, 27, BGEVENT_JUMPTEXT, PokemonMansion1FMewtwoStatueText
	bg_event 22,  5, BGEVENT_JUMPTEXT, PokemonMansion1FMewtwoStatueText
	bg_event  8, 13, BGEVENT_JUMPTEXT, PokemonMansion1FFlowerPotText
	bg_event  9, 13, BGEVENT_JUMPTEXT, PokemonMansion1FFlowerPotText
	bg_event  4, 17, BGEVENT_JUMPTEXT, PokemonMansion1FFlowerPotText
	bg_event  5, 17, BGEVENT_JUMPTEXT, PokemonMansion1FFlowerPotText
	bg_event  8, 17, BGEVENT_JUMPTEXT, PokemonMansion1FFlowerPotText
	bg_event  9, 17, BGEVENT_JUMPTEXT, PokemonMansion1FFlowerPotText

	def_object_events
	object_event 18,  5, SPRITE_SCIENTIST, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, 0, OBJECTTYPE_TRAINER, 4, TrainerScientistBraydon, -1
	object_event 18, 22, SPRITE_BOOK_PAPER_POKEDEX, SPRITEMOVEDATA_STANDING_UP, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, PokemonMansionDiary, -1
	itemball_event 13,  5, CARBOS, 1, EVENT_POKEMON_MANSION_B1F_CARBOS
	itemball_event  7,  6, CALCIUM, 1, EVENT_POKEMON_MANSION_B1F_CALCIUM
	itemball_event 16, 27, HP_UP, 1, EVENT_POKEMON_MANSION_B1F_HP_UP
	keyitemball_event  4, 23, OLD_SEA_MAP, EVENT_POKEMON_MANSION_B1F_OLD_SEA_MAP

TrainerScientistBraydon:
	trainer SCIENTIST, BRAYDON, EVENT_BEAT_SCIENTIST_BRAYDON, ScientistBraydonSeenText, ScientistBraydonBeatenText, 0, .Script

.Script:
	endifjustbattled
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iftrue_jumptextfaceplayer .Witness
	jumpthistextfaceplayer

	text "This place was"
	line "once the site of"

	para "serious #mon"
	line "research."
	done

.Witness:
	text "I came back for"
	line "the flight log."
	para "The last entry is"
	line "in the diary near"
	cont "the stairs."
	para "Tell Oak I should"
	line "have spoken up"
	cont "years ago."
	done

ScientistBraydonSeenText:
	text "I miss the old"
	line "Cinnabar Lab…"
	done

ScientistBraydonBeatenText:
	text "Whew!"
	line "Overwhelming!"
	done

PokemonMansionDiary:
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalse_jumptext PokemonMansionDiaryText
	; (a story scene: the lab's lights flicker and dim while you read, and a
	; psychic pulse answers from far away: engine/events/cinematic.asm)
	scene_begin
	scene_pulse TINT_DARK
	scene_tint TINT_DARK
	showtext .Report
	cry MEWTWO
	scene_pulse TINT_PURPLE
	scene_end
	checkevent EVENT_READ_CINNABAR_CLONE_REPORT
	iftrue DoNothingScript
	setevent EVENT_READ_CINNABAR_CLONE_REPORT
	opentext
	writetext .Filed
	promptbutton
	farscall GiveNextStoryLead
	endtext

.Report:
	text "Lab flight log"
	para "We copied Mew's"
	line "cells to create"
	cont "Mewtwo. We gave it"
	cont "a number, no name."
	para "It broke out when"
	line "we ordered it to"
	cont "attack its keeper."
	para "I watched it fly"
	line "north. Its shadow"
	cont "vanished over the"
	cont "Cerulean river."
	para "Oak's note: What"
	line "did it see in us"
	cont "that made it run?"
	done

.Filed:
	text "You copy the log"
	line "into your book."
	done

PokemonMansionDiaryText:
	text "Diary: July 5"

	para "A new #mon was"
	line "discovered deep in"
	cont "the jungle."

	para "Diary: July 10"

	para "We christened the"
	line "newly discovered"
	cont "#mon, Mew."

	para "Diary: Feb. 6"

	para "Mew gave birth."
	line "We named the"
	cont "newborn Mewtwo."

	para "Diary: Sept. 1"

	para "Mewtwo is far"
	line "too powerful."

	para "We have failed to"
	line "curb its vicious"
	cont "tendencies…"
	done
