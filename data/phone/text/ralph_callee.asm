RalphAnswerPhoneText::
	text "Yes? Ah, <PLAYER>."

	para "You're courteous"
	line "enough to state"

	para "your name when you"
	line "call on the phone."
	done

RalphAnswerPhoneDayText:
	text_far RalphAnswerPhoneText
	text_end

RalphAnswerPhoneNiteText:
	text_far RalphAnswerPhoneText
	text_end

RalphGreetText:
	text "Hiya, it's Uncle"
	line ""
	text_ram wStringBuffer3
	text "."
	done

RalphGreetDayText:
	text "Hiya, it's Uncle"
	line ""
	text_ram wStringBuffer3
	text "."
	done

RalphGreetNiteText:
	text "Hiya, it's Uncle"
	line ""
	text_ram wStringBuffer3
	text "."
	done

RalphGenericText:
	text "Are you taking"
	line "good care of your"

	para "#mon? You have"
	line "to be good to your"
	cont "partners!"
	done
