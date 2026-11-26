RuinsOfAlphInnerChamber_MapScriptHeader:
	def_scene_scripts
	scene_script DoNothingScript, SCENE_RUINSOFALPHINNERCHAMBER_NOOP
	scene_script RuinsOfAlphInnerChamberStrangePresenceScene, SCENE_RUINSOFALPHINNERCHAMBER_STRANGE_PRESENCE

	def_callbacks
	callback MAPCALLBACK_OBJECTS, HideAlphRescueActors

	def_warp_events
	warp_event 10, 13, RUINS_OF_ALPH_ENTRANCE_CHAMBER, 3
	warp_event  3, 15, RUINS_OF_ALPH_HO_OH_CHAMBER, 3
	warp_event  4, 15, RUINS_OF_ALPH_HO_OH_CHAMBER, 4
	warp_event 15,  3, RUINS_OF_ALPH_KABUTO_CHAMBER, 3
	warp_event 16,  3, RUINS_OF_ALPH_KABUTO_CHAMBER, 4
	warp_event  3, 21, RUINS_OF_ALPH_OMANYTE_CHAMBER, 3
	warp_event  4, 21, RUINS_OF_ALPH_OMANYTE_CHAMBER, 4
	warp_event 15, 24, RUINS_OF_ALPH_AERODACTYL_CHAMBER, 3
	warp_event 16, 24, RUINS_OF_ALPH_AERODACTYL_CHAMBER, 4

	def_coord_events

	def_bg_events
	bg_event  2,  3, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  5,  3, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  8,  3, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 11,  3, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 14,  3, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 17,  3, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  2,  8, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  5,  8, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  8,  8, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 11,  8, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 14,  8, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 17,  8, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  2, 13, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  5, 13, BGEVENT_READ, HaleStatueScript
	bg_event 14, 13, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 17, 13, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  2, 18, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  5, 18, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  8, 18, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 11, 18, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 14, 18, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 17, 18, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  2, 24, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  5, 24, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event  8, 24, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 11, 24, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 14, 24, BGEVENT_JUMPTEXT, RuinsofAlphStatueText
	bg_event 17, 24, BGEVENT_JUMPTEXT, RuinsofAlphStatueText

	def_object_events
	object_event  3,  7, SPRITE_FISHER, SPRITEMOVEDATA_SPINRANDOM_SLOW, 0, 0, -1, PAL_NPC_GREEN, OBJECTTYPE_COMMAND, jumptextfaceplayer, RuinsOfAlphInnerChamberFisherText, EVENT_RUINS_OF_ALPH_INNER_CHAMBER_TOURISTS
	object_event 14, 14, SPRITE_POKEFAN_F, SPRITEMOVEDATA_WANDER, 1, 1, -1, PAL_NPC_RED, OBJECTTYPE_COMMAND, jumptextfaceplayer, RuinsOfAlphInnerChamberTeacherText, EVENT_RUINS_OF_ALPH_INNER_CHAMBER_TOURISTS
	object_event 11, 19, SPRITE_GRAMPS, SPRITEMOVEDATA_STANDING_UP, 0, 0, -1, 0, OBJECTTYPE_COMMAND, jumptextfaceplayer, RuinsOfAlphInnerChamberGrampsText, EVENT_RUINS_OF_ALPH_INNER_CHAMBER_TOURISTS
	object_event  7, 11, SPRITE_SCIENTIST, SPRITEMOVEDATA_STANDING_UP, 0, 0, -1, PAL_NPC_BROWN, OBJECTTYPE_COMMAND, jumptextfaceplayer, RuinsOfAlphInnerChamberScientistText, EVENT_RUINS_OF_ALPH_INNER_CHAMBER_TOURISTS
	object_event  4, 12, SPRITE_MON_ICON, SPRITEMOVEDATA_STILL, 0, ENTEI, -1, PAL_MON_RED, OBJECTTYPE_SCRIPT, PLAIN_FORM, ObjectEvent, EVENT_TEMPORARY_UNTIL_MAP_RELOAD_1
	object_event  6, 12, SPRITE_SCIENTIST, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, PAL_NPC_BROWN, OBJECTTYPE_SCRIPT, 0, ObjectEvent, EVENT_TEMPORARY_UNTIL_MAP_RELOAD_2
	object_event  4, 14, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, TEDDIURSA, -1, PAL_MON_BROWN, OBJECTTYPE_SCRIPT, PLAIN_FORM, AlphIllusionTeddiursaScript, EVENT_TEMPORARY_UNTIL_MAP_RELOAD_4
	object_event  6, 14, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, PHANPY, -1, PAL_MON_BLUE, OBJECTTYPE_SCRIPT, PLAIN_FORM, AlphIllusionPhanpyScript, EVENT_TEMPORARY_UNTIL_MAP_RELOAD_5
	; Link Edition: the letters the illusion breaks into (the statue scene)
	object_event  4, 13, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, UNOWN, -1, PAL_MON_PURPLE, OBJECTTYPE_SCRIPT, UNOWN_M_FORM, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN
	object_event  4, 13, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, UNOWN, -1, PAL_MON_PURPLE, OBJECTTYPE_SCRIPT, UNOWN_O_FORM, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN
	object_event  4, 13, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, UNOWN, -1, PAL_MON_PURPLE, OBJECTTYPE_SCRIPT, UNOWN_L_FORM, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN
	object_event  4, 13, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, UNOWN, -1, PAL_MON_PURPLE, OBJECTTYPE_SCRIPT, UNOWN_Y_FORM, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN
	; Link Edition: the Unown's crystals, spreading from the statue (the scene)
	object_event  4, 13, SPRITE_SCENE_PROPS, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, PAL_NPC_ROCK_CRYSTAL, OBJECTTYPE_SCRIPT, 0, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN
	object_event  4, 13, SPRITE_SCENE_PROPS, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, PAL_NPC_ROCK_CRYSTAL, OBJECTTYPE_SCRIPT, 0, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN
	object_event  4, 13, SPRITE_SCENE_PROPS, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, PAL_NPC_ROCK_CRYSTAL, OBJECTTYPE_SCRIPT, 0, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN
	object_event  4, 13, SPRITE_SCENE_PROPS, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, PAL_NPC_ROCK_CRYSTAL, OBJECTTYPE_SCRIPT, 0, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN

	object_const_def
	const_skip 4
	const ALPH_DREAM_ENTEI
	const ALPH_PROF_HALE
	const_skip 2 ; (the two illusions)
	const ALPH_UNOWN_1
	const ALPH_UNOWN_2
	const ALPH_UNOWN_3
	const ALPH_UNOWN_4
	const ALPH_CRYSTAL_1
	const ALPH_CRYSTAL_2
	const ALPH_CRYSTAL_3
	const ALPH_CRYSTAL_4

HideAlphRescueActors:
	setevent EVENT_POST_RED_PERSON_HIDDEN ; (the statue scene's letters)
	disappear ALPH_DREAM_ENTEI
	disappear ALPH_PROF_HALE
	; Link Edition: the Unown's illusions guard the statue after Molly's
	; battle, until her father is free (each one broken stays gone until you
	; come back)
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalsefwd .NoIllusions
	checkevent EVENT_BEAT_MOLLY
	iffalsefwd .NoIllusions
	checkevent EVENT_RESCUED_PROF_HALE
	iffalsefwd .Done
.NoIllusions:
	setevent EVENT_TEMPORARY_UNTIL_MAP_RELOAD_4
	setevent EVENT_TEMPORARY_UNTIL_MAP_RELOAD_5
.Done:
	endcallback

AlphIllusionTeddiursaScript:
	loadwildmon TEDDIURSA, 62
	sjumpfwd AlphIllusionBattle

AlphIllusionPhanpyScript:
	loadwildmon PHANPY, 62
AlphIllusionBattle:
; Link Edition: Spell of the Unown: one of the friends the Unown dreamed up
; for Molly. It can't be caught or fled from.
	showtext .Text
	loadvar VAR_BATTLETYPE, BATTLETYPE_SHADOW
	startbattle
	disappear LAST_TALKED
	reloadmapafterbattle
	jumptext .BrokenText

.Text:
	text "Its outline"
	line "flickers like"
	cont "Unown letters…"

	para "It's one of the"
	line "Unown's dreams!"
	done

.BrokenText:
	text "It breaks apart"
	line "into rows of tiny"
	cont "letters."
	done

RuinsOfAlphInnerChamberStrangePresenceScene:
	sdefer .Script
	end

.Script:
	showtext RuinsOfAlphStrangePresenceText
	setscene SCENE_RUINSOFALPHINNERCHAMBER_NOOP
	setevent EVENT_MADE_UNOWN_APPEAR_IN_RUINS
	clearevent EVENT_RUINS_OF_ALPH_OUTSIDE_TOURIST_FISHER
	digmod 5, RUINS_OF_ALPH_OUTSIDE
	end

RuinsOfAlphStrangePresenceText:
	text "There is a strange"
	line "presence here…"
	done

RuinsOfAlphInnerChamberFisherText:
	text "This is a big"
	line "room, but there's"
	cont "nothing here."
	done

RuinsOfAlphInnerChamberTeacherText:
	text "This place has a"
	line "mystical quality"
	cont "to it."

	para "It feels sort of"
	line "ethereal even."
	done

RuinsOfAlphInnerChamberGrampsText:
	text "The ruins have not"
	line "been robbed or"
	cont "tampered with."

	para "Something here"
	line "must make people"
	cont "want to preserve"
	cont "it."
	done

RuinsOfAlphInnerChamberScientistText:
	text "The patterns on"
	line "the wall appear to"
	cont "be words!"

	para "And those sliding"
	line "stone panels seem"

	para "to be signals of"
	line "some kind."

	para "I think they make"
	line "#mon appear,"

	para "but it's not clear"
	line "yet…"
	done

HaleStatueScript:
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalse_jumptext RuinsofAlphStatueText
	checkevent EVENT_BEAT_MOLLY
	iffalse_jumptext RuinsofAlphStatueText
	checkevent EVENT_RESCUED_PROF_HALE
	iftrue_jumptext .Empty
	scene_begin ; (the illusion in a dream's purple light)
	musicfadeout MUSIC_RUINS_OF_ALPH_RADIO, 8 ; (the Unown's own signal)
	showtext .Knocks
	; the Unown's crystals spread out from the statue, one by one
	scene_tint TINT_PURPLE
	scene_place ALPH_CRYSTAL_1, -1, -1
	appear ALPH_CRYSTAL_1
	playsound SFX_GLASS_TING
	showemote EMOTE_SPARKLE_PURPLE, ALPH_CRYSTAL_1, 10
	scene_place ALPH_CRYSTAL_2, 1, -1
	appear ALPH_CRYSTAL_2
	playsound SFX_GLASS_TING_2
	showemote EMOTE_SPARKLE_PURPLE, ALPH_CRYSTAL_2, 10
	scene_place ALPH_CRYSTAL_3, -3, 0
	appear ALPH_CRYSTAL_3
	playsound SFX_GLASS_TING
	showemote EMOTE_SPARKLE_PURPLE, ALPH_CRYSTAL_3, 10
	scene_place ALPH_CRYSTAL_4, 3, 0
	appear ALPH_CRYSTAL_4
	playsound SFX_GLASS_TING_2
	showemote EMOTE_SPARKLE_PURPLE, ALPH_CRYSTAL_4, 10
	waitsfx
	scene_restore
	playsound SFX_PROTECT
	special Special_FadeBlackQuickly
	; The alternate statue and floor blocks have identical collisions.
	changeblock 4, 12, $0f
	changeblock 6, 12, $2b
	refreshmap
	appear ALPH_DREAM_ENTEI
	scene_shadow ALPH_DREAM_ENTEI ; (a dream's shape at first)
	special Special_ReloadSpritesNoPalettes
	special Special_FadeInQuickly
	scene_tint TINT_PURPLE
	pause 20
	cry ENTEI
	scene_unshadow ALPH_DREAM_ENTEI ; (it takes its colors as it roars)
	earthquake 12
	pause 20
	; it breaks into letters around you
	scene_shadow ALPH_DREAM_ENTEI
	playsound SFX_PROTECT
	scene_place ALPH_UNOWN_1, -2, -2
	appear ALPH_UNOWN_1
	showemote EMOTE_SPARKLE_PURPLE, ALPH_UNOWN_1, 8
	scene_place ALPH_UNOWN_2, 2, -2
	appear ALPH_UNOWN_2
	showemote EMOTE_SPARKLE_PURPLE, ALPH_UNOWN_2, 8
	scene_place ALPH_UNOWN_3, -2, 1
	appear ALPH_UNOWN_3
	showemote EMOTE_SPARKLE_PURPLE, ALPH_UNOWN_3, 8
	scene_place ALPH_UNOWN_4, 2, 1
	appear ALPH_UNOWN_4
	showemote EMOTE_SPARKLE_PURPLE, ALPH_UNOWN_4, 8
	showtext .Illusion
	scene_flash 1
	disappear ALPH_UNOWN_1
	disappear ALPH_UNOWN_2
	disappear ALPH_UNOWN_3
	disappear ALPH_UNOWN_4
	scene_restore
	special Special_FadeBlackQuickly
	disappear ALPH_DREAM_ENTEI
	changeblock 4, 12, $18
	changeblock 6, 12, $0d
	refreshmap
	appear ALPH_PROF_HALE
	special Special_ReloadSpritesNoPalettes
	special Special_FadeInQuickly
	; with him free, the crystals shatter and the chamber is itself again
	playsound SFX_GLASS_TING
	scene_flash 1
	disappear ALPH_CRYSTAL_1
	disappear ALPH_CRYSTAL_2
	playsound SFX_GLASS_TING_2
	disappear ALPH_CRYSTAL_3
	disappear ALPH_CRYSTAL_4
	waitsfx
	scene_end ; (the chamber's own music back)
	showtext .Rescue
	disappear ALPH_PROF_HALE
	setevent EVENT_RESCUED_PROF_HALE
	opentext
	writetext .Note
	promptbutton
	farscall GiveNextStoryLead
	endtext

.Knocks:
	text "Three knocks come"
	line "from the stone."
	para "You knock back."
	done

.Illusion:
	text "Entei's shadow"
	line "breaks into rows"
	cont "of tiny letters."
	para "Behind them, a man"
	line "knocks on stone."
	done

.Rescue:
	text "Hale: Molly used"
	line "to knock like that"
	cont "on my study door."
	para "I was calling her."
	line "The Unown must've"
	cont "heard us both."
	para "Let's tell her I'm"
	line "coming home."
	done

.Note:
	text "Hale slips you a"
	line "page for Oak."
	para "There's a sketch"
	line "of Ilex shrine and"
	cont "a black # Ball."
	done

.Empty:
	text "A warm lantern"
	line "lights the empty"
	cont "niche."
	done
