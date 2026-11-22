; Link Edition: follower sprites (see engine/overworld/follower.asm).
;
; Each is a 16x32 picture in gfx/followers/: the back view on top and the
; side view (facing left) below. The front view is the Pokemon's party icon,
; so it costs nothing, and a symmetric back view compresses to about half.
; A Pokemon without one follows as its party icon.

MACRO follower_sprite
; follower_sprite SPECIES[, FORM], Label (without a form, any form matches)
	if _NARG == 3
		dp \1, \2
		dba \3
	else
		dp \1
		dba \2
	endc
ENDM

FollowerSprites:
	follower_sprite PIKACHU, PikachuFollowerGFX
	db -1 ; end
