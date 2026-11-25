; The Cable Club's rules texts (maps/PokeCenter2F.asm: its script section
; is full), one for each format's rules in engine/link/link_rules.asm.

_RandomRulesText::
	text "Random teams: you"
	line "each get six ran-"
	cont "dom #mon at"
	cont "level 50."

	para "Your own team is"
	line "safe. It's back"
	cont "after the battle."
	done

_StandardRulesText::
	text "Bring up to six"
	line "for Lv.50 battles."
	para "Only one of them"
	line "may be legendary."
	done

_RisingRulesText::
	text "Bring three"
	line "#mon for Lv.30"
	cont "battles."
	para "No Eggs, Mewtwo,"
	line "Mew, Lugia, Ho-Oh"
	cont "or Celebi."
	para "No two may be one"
	line "species, or hold"
	cont "the same item."
	done

_UnrestrictedRulesText::
	text "Bring up to six at"
	line "their own levels."
	para "Any #mon may"
	line "battle!"
	done

_InvalidRisingText::
	text "This format needs"
	line "three eligible"
	cont "#mon: no two of"
	cont "a species or with"
	cont "the same item."
	done

_InvalidStandardText::
	text "Bring at least one"
	line "usable #mon,"
	cont "and only one"
	cont "legendary."
	done
