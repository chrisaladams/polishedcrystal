; Link Edition: follower sprite graphics (see data/pokemon/follower_sprites.asm).
; Each is in its own section, so the linker can tuck them into the free space
; left at the end of any bank. (The INCBINs are written out, not made by a
; macro, so the Makefile sees them and builds the graphics.)

SECTION "Follower Sprite Pikachu", ROMX
PikachuFollowerGFX:: INCBIN "gfx/followers/pikachu.2bpp.lzp"
