if DEF(FAITHFUL)
	bst 366,  56,  76,  52,  76,  54,  52
	;   bst   hp  atk  def  sat  sdf  spe
else
	bst 366,  56,  76,  52,  76,  54,  52
	;   bst   hp  atk  def  sat  sdf  spe
endc

	db PSYCHIC, PSYCHIC ; type
	db 225 ; catch rate
	db 61 ; base exp
	db NO_ITEM, NO_ITEM ; held items
	dn GENDER_UNKNOWN, HATCH_SLOWEST ; gender ratio, step cycles to hatch

	abilities_for UNOWN, LEVITATE, LEVITATE, LEVITATE
	db GROWTH_MEDIUM_FAST ; growth rate
	dn EGG_NONE, EGG_NONE ; egg groups

	ev_yield 1 Atk, 1 SAt

	; tm/hm learnset
	tmhm HIDDEN_POWER
	; end
