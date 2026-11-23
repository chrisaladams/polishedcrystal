CeruleanCaveB1F_MapScriptHeader:
	def_scene_scripts

	def_callbacks

	def_warp_events
	warp_event  5,  7, CERULEAN_CAVE_1F, 5

	def_coord_events

	def_bg_events
	bg_event  8,  6, BGEVENT_ITEM + MAX_REVIVE, EVENT_CERULEAN_CAVE_B1F_HIDDEN_MAX_REVIVE
	bg_event 24, 11, BGEVENT_ITEM + ULTRA_BALL, EVENT_CERULEAN_CAVE_B1F_HIDDEN_ULTRA_BALL

	def_object_events
	object_event  7, 13, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, MEWTWO, -1, PAL_MON_PURPLE, OBJECTTYPE_SCRIPT, PLAIN_FORM, CeruleanCaveMewtwo, EVENT_CERULEAN_CAVE_MEWTWO
	itemball_event 26,  9, MAX_ELIXIR, 1, EVENT_CERULEAN_CAVE_B1F_MAX_ELIXIR
	itemball_event 26,  3, ULTRA_BALL, 1, EVENT_CERULEAN_CAVE_B1F_ULTRA_BALL

	object_const_def
	const CERULEANCAVEB1F_MEWTWO

CeruleanCaveMewtwo:
	faceplayer
	opentext
	writetext MewtwoText
	cry MEWTWO
	pause 15
; Link Edition: Mewtwo Strikes Back
	writetext .ClonesText
	waitbutton
	closetext
	winlosstext .ClonesBeatenText, 0
	loadtrainer MEWTWO_T, 1
	startbattle
	reloadmapafterbattle
	showtext .ClonesAfterText
	cry MEWTWO
	pause 15
	loadwildmon MEWTWO, 80
	loadvar VAR_BATTLETYPE, BATTLETYPE_LEGENDARY
	startbattle
	disappear CERULEANCAVEB1F_MEWTWO
	setevent EVENT_CERULEAN_CAVE_MEWTWO
	reloadmapafterbattle
	special CheckBattleCaughtResult
	iffalsefwd .nocatch
	setflag ENGINE_PLAYER_CAUGHT_MEWTWO
.nocatch
	end

.ClonesText:
	text "A voice echoes"
	line "in your mind…"

	para "I am Mewtwo."
	line "Humans made me,"
	cont "a copy of Mew."

	para "Are copies weaker"
	line "than those they"
	cont "were copied from?"

	para "My clones will"
	line "show you!"
	done

.ClonesBeatenText:
	text "My clones…"
	line "were defeated?"
	done

.ClonesAfterText:
	text "…How one is born"
	line "does not matter."

	para "What matters is"
	line "what one does"
	cont "with one's life."

	para "Now, show me your"
	line "strength yourself!"
	done

MewtwoText:
	text "Myuu!"
	done
