if DEF(FAITHFUL)
	bst 225,  48,  43,  34,  20,  26,  54
else
	bst 225,  48,  43,  34,  20,  26,  54
endc
	;   bst   hp  atk  def  sat  sdf  spe

	db BUG, POISON ; type
	db 255 ; catch rate
	db 52 ; base exp
	db NO_ITEM, NO_ITEM ; held items
	dn GENDER_F50, HATCH_FAST ; gender ratio, step cycles to hatch

	abilities_for WEEDLE, SHIELD_DUST, SHIELD_DUST, RUN_AWAY
	db GROWTH_MEDIUM_FAST ; growth rate
	dn EGG_BUG, EGG_BUG ; egg groups

	ev_yield 1 Spe

	; tm/hm learnset
	tmhm
	; end
