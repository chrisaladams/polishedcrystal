; The World Championship's results for the trainers' own matches
; (maps/IndigoPlateauPokecenter1F.asm: its script section is nearly full).

_WorldCupResultText::
	text_ram wStringBuffer4
	text " beat"
	line "@"
	text_ram wStringBuffer5
	text "."
	done

_WorldCupUpsetText::
	text_ram wStringBuffer4
	text " upset"
	line "@"
	text_ram wStringBuffer5
	text "!"
	done

_WorldLinkSemifinalText::
	text "Your bracket with"
	line "@"
	text_ram wStringBuffer3
	text "!"

	para "Semifinal:"
	line "@"
	text_ram wStringBuffer4
	text ", who beat"

	para "@"
	text_ram wStringBuffer5
	text ". Ready?"
	done

_WorldLinkSemifinalUpsetText::
	text "Your bracket with"
	line "@"
	text_ram wStringBuffer3
	text "!"

	para "Semifinal:"
	line "@"
	text_ram wStringBuffer4
	text ", who upset"

	para "@"
	text_ram wStringBuffer5
	text "! Ready?"
	done

_WorldLinkFinalText::
	text "@"
	text_ram wStringBuffer3
	text " is out,"
	line "so the final is"

	para "against @"
	text_ram wStringBuffer4
	text ","
	line "who beat @"
	text_ram wStringBuffer5
	text "."

	para "Ready?"
	done

_WorldLinkFinalUpsetText::
	text "@"
	text_ram wStringBuffer3
	text " is out,"
	line "so the final is"

	para "against @"
	text_ram wStringBuffer4
	text ","
	line "who upset @"
	text_ram wStringBuffer5
	text "!"

	para "Ready?"
	done

_WorldLinkMakeRoomText::
	text "Make room in your"
	line "Bag, then come"
	cont "back for your"
	cont "prize."
	done
