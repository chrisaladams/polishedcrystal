IvysHouse_MapScriptHeader:
	def_scene_scripts

	def_callbacks

	def_warp_events
	warp_event  2,  7, VALENCIA_ISLAND, 2
	warp_event  3,  7, VALENCIA_ISLAND, 2

	def_coord_events

	def_bg_events

	def_object_events
	object_event  2,  3, SPRITE_BATTLE_GIRL, SPRITEMOVEDATA_STANDING_RIGHT, 0, 0, -1, PAL_NPC_PURPLE, OBJECTTYPE_COMMAND, jumptextfaceplayer, IvysHouseFaithText, -1
	object_event  6,  4, SPRITE_BATTLE_GIRL, SPRITEMOVEDATA_WALK_UP_DOWN, 1, 0, -1, PAL_NPC_PURPLE, OBJECTTYPE_COMMAND, jumptextfaceplayer, IvysHouseCharityText, -1

IvysHouseFaithText:
	text "Faith: I'm one of"
	line "Prof. Ivy's"
	cont "assistants."

	para "She studies how"
	line "#mon here can"
	cont "differ from the"
	cont "ones on the main-"
	cont "land."

	para "Even the same"
	line "species can look"
	cont "different!"
	done

IvysHouseCharityText:
	text "Charity: The"
	line "professor is out"
	cont "on the beach"
	cont "again, taking"
	cont "notes."

	para "We take turns"
	line "cooking, cleaning"
	cont "and feeding the"
	cont "#mon. It's busy,"
	cont "but I love it."
	done
