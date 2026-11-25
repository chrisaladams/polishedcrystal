RockyPeak_MapScriptHeader:
	def_scene_scripts

	def_callbacks

	def_warp_events
	warp_event  8, 15, ROCKY_BEACH, 4
	warp_event  9, 15, ROCKY_BEACH, 4

	def_coord_events
	coord_event 12,  3, SCENE_ALWAYS, RockyPeakDescentScript
	coord_event 13,  3, SCENE_ALWAYS, RockyPeakSummitScript

	def_bg_events

	def_object_events

RockyPeakSummitScript:
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalsefwd .Done
	checkevent EVENT_BEAT_ORANGE_CREW_DANNY
	iftruefwd .Done
	checkevent EVENT_REACHED_DANNYS_SUMMIT
	iftruefwd .Done
	setevent EVENT_REACHED_DANNYS_SUMMIT
	jumpthistext

	text "The summit shelf!"
	para "You can see the"
	line "ferries far below."
	para "Take the ladder"
	line "down to Danny."
	done
.Done:
	end

RockyPeakDescentScript:
	warp ROCKY_BEACH, 22, 26
	end
