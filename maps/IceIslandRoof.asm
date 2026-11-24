IceIslandRoof_MapScriptHeader:
	def_scene_scripts

	def_callbacks

	def_warp_events
	warp_event  3,  7, ICE_ISLAND, 2

	def_coord_events

	def_bg_events
	bg_event  5,  3, BGEVENT_READ, IceIslandBeacon

	def_object_events

	object_const_def

IceIslandBeacon:
	checkevent EVENT_HEARD_SHAMOUTI_BEACONS
	iffalsefwd .Silent
	checkevent EVENT_TUNED_ICE_BEACON
	iftruefwd .Tuned
	setevent EVENT_TUNED_ICE_BEACON
	cry ARTICUNO
	showtext .Heard
	farsjump ShamoutiBeaconHandoff
.Silent:
	farjumptext ShamoutiSilentBeaconText
.Tuned:
	farjumptext ShamoutiTunedBeaconText

.Heard:
	text "Frost covers the"
	line "beacon's lens."
	para "You wipe it clean."
	line "A blue beam cuts"
	cont "through the cloud."
	para "Articuno answers"
	line "from Seafoam."
	done
