FireIslandRoof_MapScriptHeader:
	def_scene_scripts

	def_callbacks

	def_warp_events
	warp_event  3,  7, FIRE_ISLAND, 2

	def_coord_events

	def_bg_events
	bg_event  5,  3, BGEVENT_READ, FireIslandBeacon

	def_object_events

	object_const_def

FireIslandBeacon:
	checkevent EVENT_HEARD_SHAMOUTI_BEACONS
	iffalsefwd .Silent
	checkevent EVENT_TUNED_FIRE_BEACON
	iftruefwd .Tuned
	setevent EVENT_TUNED_FIRE_BEACON
	cry MOLTRES
	showtext .Heard
	farsjump ShamoutiBeaconHandoff
.Silent:
	farjumptext ShamoutiSilentBeaconText
.Tuned:
	farjumptext ShamoutiTunedBeaconText

.Heard:
	text "Soot jams the"
	line "beacon's shutter."
	para "You clear it away."
	line "A red beam sweeps"
	cont "over the channel."
	para "Far to the west,"
	line "Moltres calls from"
	cont "Cinnabar's crater."
	done
