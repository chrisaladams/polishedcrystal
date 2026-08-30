MACRO base_exception
; mon, actual yield
	dp \1, \2
	dw \3
ENDM

; These are the canonical base exp yields, so the percentages below are relative
; to each mon's canonical (FAITHFUL) BST. The Polished branch retunes some of
; those BSTs but deliberately keeps the canonical yield.
NewBaseExpExceptions:
	base_exception CHANSEY, PLAIN_FORM, 395 ; BST x 87.7% as of gen V (unchanged in VIII)
	base_exception BLISSEY, PLAIN_FORM, 635 ; BST x 117.5% as of gen VIII
	base_exception HAPPINY, PLAIN_FORM, 110 ; BST x 50.0% as of gen V (unchanged in VIII)
	dw -1
