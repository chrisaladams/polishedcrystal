if DEF(FAITHFUL)
	bst  90,  18,  14,  14,  14,  16,  14
else
	bst  90,  18,  14,  14,  14,  16,  14
endc
	;   bst   hp  atk  def  sat  sdf  spe

	db NORMAL, NORMAL ; type
	db 255 ; catch rate
	db 10 ; base exp
	db NO_ITEM, NO_ITEM ; held items
	dn GENDER_F50, HATCH_FASTER ; gender ratio, step cycles to hatch

	abilities_for EGG, NO_ABILITY, NO_ABILITY, NO_ABILITY
	db GROWTH_SLOW ; growth rate
	dn EGG_NONE, EGG_NONE ; egg groups

	ev_yield

	; tm/hm learnset
	tmhm
	; end
