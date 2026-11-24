CeruleanCaveB1F_MapScriptHeader:
	def_scene_scripts

	def_callbacks

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

	object_const_def
	const CERULEANCAVEB1F_MEWTWO

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
	showtext .ClonesText
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

	para "I am Mewtwo."
	line "Humans made me,"
	cont "a copy of Mew."

	para "Are copies weaker"
	line "than those they"
	cont "were copied from?"

	para "I have cloned"
	line "your own #mon."

	para "Now, let them"
	line "face each other!"
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

	done

MewtwoText:
	text "Myuu!"
	done
