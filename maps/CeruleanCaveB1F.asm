CeruleanCaveB1F_MapScriptHeader:
	def_scene_scripts

	def_callbacks
	callback MAPCALLBACK_OBJECTS, CeruleanCaveB1FCastCallback

	def_warp_events
	warp_event  5,  7, CERULEAN_CAVE_1F, 5

	def_coord_events

	def_bg_events
	bg_event  7, 13, BGEVENT_READ, CeruleanCavePsychicEcho
	bg_event  8,  6, BGEVENT_ITEM + MAX_REVIVE, EVENT_CERULEAN_CAVE_B1F_HIDDEN_MAX_REVIVE
	bg_event 24, 11, BGEVENT_ITEM + ULTRA_BALL, EVENT_CERULEAN_CAVE_B1F_HIDDEN_ULTRA_BALL

	def_object_events
	object_event  7, 13, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, MEWTWO, -1, PAL_MON_PURPLE, OBJECTTYPE_SCRIPT, PLAIN_FORM, CeruleanCaveMewtwo, EVENT_CERULEAN_CAVE_MEWTWO
	itemball_event 26,  9, MAX_ELIXIR, 1, EVENT_CERULEAN_CAVE_B1F_MAX_ELIXIR
	itemball_event 26,  3, ULTRA_BALL, 1, EVENT_CERULEAN_CAVE_B1F_ULTRA_BALL
	; Link Edition: the copies of your team, seen only in the clone scene
	object_event  7, 12, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, MEWTWO, -1, PAL_MON_PURPLE, OBJECTTYPE_SCRIPT, PLAIN_FORM, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN
	object_event  7, 12, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, MEWTWO, -1, PAL_MON_PURPLE, OBJECTTYPE_SCRIPT, PLAIN_FORM, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN
	object_event  7, 12, SPRITE_MON_ICON, SPRITEMOVEDATA_POKEMON, 0, MEWTWO, -1, PAL_MON_PURPLE, OBJECTTYPE_SCRIPT, PLAIN_FORM, ObjectEvent, EVENT_POST_RED_PERSON_HIDDEN

	object_const_def
	const CERULEANCAVEB1F_MEWTWO
	const CERULEANCAVEB1F_MAX_ELIXIR
	const CERULEANCAVEB1F_ULTRA_BALL
	const CERULEANCAVEB1F_CLONE_1
	const CERULEANCAVEB1F_CLONE_2
	const CERULEANCAVEB1F_CLONE_3

CeruleanCaveB1FCastCallback:
	setevent EVENT_POST_RED_PERSON_HIDDEN ; (the clone scene's copies)
	endcallback

CeruleanCaveMewtwo:
	faceplayer
	opentext
	writetext MewtwoText
	cry MEWTWO
	pause 15
; Link Edition: Mewtwo Strikes Back (after Red)
; Red's ticket is permanent; EVENT_BEAT_RED resets when Leaf is beaten.
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalsefwd .NoClones
	checkevent EVENT_BEAT_MEWTWO_CLONES
	iftruefwd .NoClones
	checkevent EVENT_READ_CINNABAR_CLONE_REPORT
	iffalse_jumpopenedtext MewtwoResearchHint
	closetext
	scall CeruleanCaveCloneBattle
	showtext .ChallengeText
	cry MEWTWO
	pause 15
	scall .Battle
	farsjump TraceyCallsWithALead

.NoClones:
	closetext
.Battle:
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

.ChallengeText:
	text "Now, show me your"
	line "strength yourself!"
	done

CeruleanCavePsychicEcho:
; A captured or defeated Mewtwo must not make the later story missable.
; The echo only battles with clones: it never creates a second wild Mewtwo.
	checkevent EVENT_CERULEAN_CAVE_MEWTWO
	iffalsefwd .Quiet
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalsefwd .Quiet
	checkevent EVENT_BEAT_MEWTWO_CLONES
	iftruefwd .Quiet
	checkevent EVENT_READ_CINNABAR_CLONE_REPORT
	iffalse_jumptext MewtwoResearchHint
	opentext
	writetext .EchoText
	yesorno
	iffalse_endtext
	closetext
	scall CeruleanCaveCloneBattle
	showtext .FadedText
	farsjump TraceyCallsWithALead

.Quiet:
	jumpthistext

	text "A faint psychic"
	line "presence lingers…"
	done

.EchoText:
	text "Mewtwo's voice"
	line "echoes in your"
	cont "mind…"

	para "A memory of its"
	line "challenge remains."

	para "Face the clones?"
	done

.FadedText:
	text "The psychic echo"
	line "fades away."
	done

CeruleanCaveCloneBattle:
	; Link Edition: a story scene (engine/events/cinematic.asm): silence,
	; psychic pulses, Mewtwo a shadow in its own light while its voice
	; speaks; your team's copies rise from the pool one by one, shadows; at
	; its cry, a flash and Mewtwo in its colors, and the clones' battle
	scene_begin
	musicfadeout MUSIC_NONE, 8
	scene_shadow CERULEANCAVEB1F_MEWTWO ; (if it's here: not after it's caught)
	pause 20
	scene_pulse TINT_PURPLE
	scene_tint TINT_PURPLE
	showtext .ClonesText
	playsound SFX_PROTECT
	earthquake 8
	scene_clone CERULEANCAVEB1F_CLONE_1, 0
	scene_place CERULEANCAVEB1F_CLONE_1, -3, -1
	appear CERULEANCAVEB1F_CLONE_1
	scene_shadow CERULEANCAVEB1F_CLONE_1
	showemote EMOTE_SPARKLE_PURPLE, CERULEANCAVEB1F_CLONE_1, 15
	scene_clone CERULEANCAVEB1F_CLONE_2, 1
	scene_place CERULEANCAVEB1F_CLONE_2, 3, -1
	appear CERULEANCAVEB1F_CLONE_2
	scene_shadow CERULEANCAVEB1F_CLONE_2
	showemote EMOTE_SPARKLE_PURPLE, CERULEANCAVEB1F_CLONE_2, 15
	scene_clone CERULEANCAVEB1F_CLONE_3, 2
	scene_place CERULEANCAVEB1F_CLONE_3, 0, -3
	appear CERULEANCAVEB1F_CLONE_3
	scene_shadow CERULEANCAVEB1F_CLONE_3
	showemote EMOTE_SPARKLE_PURPLE, CERULEANCAVEB1F_CLONE_3, 15
	pause 20
	showtext .ClonesText2
	cry MEWTWO
	scene_flash 1
	scene_unshadow CERULEANCAVEB1F_MEWTWO
	disappear CERULEANCAVEB1F_CLONE_1
	disappear CERULEANCAVEB1F_CLONE_2
	disappear CERULEANCAVEB1F_CLONE_3
	scene_end_keep_music ; (the silence lasts until the battle)
	winlosstext .ClonesBeatenText, 0
	loadtrainer MEWTWO_T, 1
	startbattle
	reloadmapafterbattle
	setevent EVENT_BEAT_MEWTWO_CLONES
	showtext .ClonesAfterText
	end

.ClonesText:
	text "A voice echoes"
	line "in your mind…"

	para "The log says I"
	line "refused an order."
	cont "It leaves out why."
	para "She brought me"
	line "food. They wanted"
	cont "me to hurt her."
	para "I copied your team"
	line "in the pool. Look."
	done

.ClonesText2:
	text "They have the same"
	line "strength. I want"
	cont "to see what your"
	cont "friends choose."
	done

.ClonesBeatenText:
	text "My clones…"
	line "were defeated?"
	done

.ClonesAfterText:
	text "You called them"
	line "back when they"
	cont "were hurt."
	para "No one called me"
	line "back that way."
	para "The copies can go."
	line "They heard me say"
	cont "it this time."
	done

MewtwoResearchHint:
	text "A locked door and"
	line "a lab diary flash"
	cont "through your mind."
	para "The diary is in"
	line "the basement of"
	cont "Cinnabar Mansion."
	done

MewtwoText:
	text "Myuu!"
	done
