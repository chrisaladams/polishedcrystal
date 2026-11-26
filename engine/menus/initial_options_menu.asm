SetInitialOptions:
; Link Edition: no options screen: every game setting is fixed
; (LockLinkOptions). The title music still fades before Prof. Elm.
	ld a, $10
	ld [wMusicFade], a
	xor a ; MUSIC_NONE
	ld [wMusicFadeIDLo], a
	ld [wMusicFadeIDHi], a
	ld c, 8
	call DelayFrames
	; fallthrough

LockLinkOptions::
; Link Edition: every game setting is the same on every cartridge
; (LINK_OPTS_LOCKED, GAME_OPTS2_LOCKED): set at New Game, and a game from
; before is corrected when continued. Carry if this game's were different.
	ld a, [wInitialOptions]
	ld b, a
	ld a, LINK_OPTS_LOCKED
	ld [wInitialOptions], a
	xor b
	ld c, a ; (the bits that changed)
	ld a, [wInitialOptions2]
	ld b, a
	and ~GAME_OPTS2_MASK
	or GAME_OPTS2_LOCKED
	ld [wInitialOptions2], a
	xor b
	or c
	ret z
	scf
	ret
