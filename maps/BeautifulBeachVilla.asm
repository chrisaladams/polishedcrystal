BeautifulBeachVilla_MapScriptHeader:
	def_scene_scripts

	def_callbacks

	def_warp_events
	warp_event  2,  7, BEAUTIFUL_BEACH, 3
	warp_event  3,  7, BEAUTIFUL_BEACH, 3

	def_coord_events

	def_bg_events

	def_object_events
	object_event  5,  4, SPRITE_DARACH, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, (1 << MORN) | (1 << DAY) | (1 << EVE), 0, OBJECTTYPE_COMMAND, jumptextfaceplayer, DarachMornDayText, -1
	object_event 10,  4, SPRITE_DARACH, SPRITEMOVEDATA_STANDING_RIGHT, 0, 0, (1 << NITE), 0, OBJECTTYPE_COMMAND, jumptextfaceplayer, DarachNiteText, -1
	object_event  1,  4, SPRITE_CAITLIN, SPRITEMOVEDATA_WALK_UP_DOWN, 1, 0, (1 << MORN) | (1 << DAY) | (1 << EVE), 0, OBJECTTYPE_COMMAND, jumptextfaceplayer, CaitlinMornDayText, -1
	object_event  9,  2, SPRITE_WEIRD_TREE, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, (1 << NITE), PAL_NPC_RED, OBJECTTYPE_SCRIPT, 0, CaitlinNiteScript, -1
	object_event 11,  4, SPRITE_BOOK_PAPER_POKEDEX, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, (1 << NITE), 0, OBJECTTYPE_COMMAND, jumptext, DarachsBookText, -1

DarachMornDayText::
	text "Darach: Welcome"
	line "to the villa."

	para "My lady Caitlin"
	line "is resting here"
	cont "away from the"
	cont "Battle Castle."

	para "I would ask you"
	line "not to disturb"
	cont "her."
	done

DarachNiteText:
	text "Darach: My lady"
	line "has retired for"
	cont "the night."

	para "Forgive me, but"
	line "callers must wait"
	cont "until morning."
	done

CaitlinMornDayText:
	text "Caitlin: The sea"
	line "breeze here is so"
	cont "gentle…"

	para "At the Castle,"
	line "every battle must"
	cont "be elegant. Here,"
	cont "I can simply"
	cont "rest."
	done

CaitlinNiteScript:
	jumpthistext

	text "A potted tree by"
	line "the window."

	para "Its leaves sway"
	line "a little, though"
	cont "there's no wind…"
	done

DarachsBookText:
	text "It's a book of"
	line "battle records,"
	cont "kept in very neat"
	cont "handwriting."

	para "Every page ends:"
	line "“For my lady.”"
	done
