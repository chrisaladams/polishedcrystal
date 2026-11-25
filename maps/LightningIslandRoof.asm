LightningIslandRoof_MapScriptHeader:
	def_scene_scripts

	def_callbacks

	def_warp_events
	warp_event  3,  7, LIGHTNING_ISLAND, 2

	def_coord_events

	def_bg_events
	bg_event  5,  3, BGEVENT_READ, LightningIslandBeacon

	def_object_events

	object_const_def

LightningIslandBeacon:
	checkevent EVENT_HEARD_SHAMOUTI_BEACONS
	iffalsefwd .Silent
	checkevent EVENT_TUNED_LIGHTNING_BEACON
	iftruefwd .Tuned
	setevent EVENT_TUNED_LIGHTNING_BEACON
	scene_begin ; (the beacon's beam pulses in its guardian's color)
	cry ZAPDOS
	scene_pulse TINT_GOLD
	scene_end
	showtext .Heard
	farsjump ShamoutiBeaconHandoff
.Silent:
	farjumptext ShamoutiSilentBeaconText
.Tuned:
	farjumptext ShamoutiTunedBeaconText

.Heard:
	text "A loose wire taps"
	line "against the tower."
	para "You fasten it. The"
	line "beacon steadies to"
	cont "a yellow beam."
	para "The answer sounds"
	line "like Zapdos. It"
	cont "comes from Kanto."
	done
