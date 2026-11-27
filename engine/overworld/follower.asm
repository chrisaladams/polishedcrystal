; Link Edition: your lead Pokemon follows you around the overworld.
;
; The follower is map object FOLLOWER_OBJECT, the last slot, which no map's
; own objects reach (SpawnFollower checks), so every map's objects and scripts
; are untouched. It's drawn with SPRITE_FOLLOWER_MON: the party menu icon of
; the first healthy Pokemon in the party (wFollowerSpecies and
; wFollowerPersonality, read by GetMonSprite). It moves with the engine's own
; follow queue (StartFollow, the one cutscenes use), so it replays the
; player's steps: walking, running, biking and ledge jumps. Nothing collides
; with it (IsNPCAtCoord skips it), so it can never block the player or an
; NPC's scripted walk; it starts hidden under the player, who is drawn on top.
;
; It's taken away while surfing (and comes back under the player on the
; first step check after landing: wFollowerPending), in the Cable Club's battle and trade rooms,
; and with Options -> Follower off, and put back under the player after every
; warp, map connection, battle, Continue and start menu visit.

SpawnFollower::
; Map setup command: (re)create the follower under the player.
	xor a
	ld [wFollowerPending], a
	call RemoveFollower
	call CanHaveFollower
	jr nc, .spawn
	; No follower here. A follow link left from the previous map must not
	; outlive its follower, or every step would be queued for nobody.
	jr DropStaleFollowLink

.spawn
	ld a, [wPlayerMapX]
	ld d, a
	ld a, [wPlayerMapY]
	ld e, a
	; fallthrough

SpawnFollowerAtDE:
	ld a, FOLLOWER_OBJECT
	push de
	call GetMapObject
	pop de
	ld hl, MAPOBJECT_SPRITE
	add hl, bc
	ld a, SPRITE_FOLLOWER_MON
	ld [hli], a ; sprite
	ld a, e
	ld [hli], a ; y
	ld a, d
	ld [hli], a ; x
	ld a, SPRITEMOVEDATA_FOLLOWING
	ld [hli], a ; movement
	xor a
	ld [hli], a ; radius
	ld [hli], a ; palette (the icon's own)
	dec a
	ld [hli], a ; time of day: always
	ld a, OBJECTTYPE_SCRIPT
	ld [hli], a ; type
	xor a
	ld [hli], a ; sight range
	ld [hli], a
	ld [hli], a ; script (it can't be faced, so never talked to)
	dec a
	ld [hli], a
	ld [hl], a ; event flag: none
	ld a, FOLLOWER_OBJECT
	call _CopyObjectStruct
	ret c ; no free object struct
	; its frames come from SetFacingFollower (a Pokemon icon only has two
	; facing-down frames: it bounces between them, mirrored heading right)
	ld a, FOLLOWER_OBJECT
	call GetMapObject
	ld hl, MAPOBJECT_OBJECT_STRUCT_ID
	add hl, bc
	ld a, [hl]
	call GetObjectStruct
	ld hl, OBJECT_FLAGS1
	add hl, bc
	set INVISIBLE_F, [hl] ; until its first step (GetFollowerNextMovementByte)
	xor a
	ld [wFollowerFacingRight], a
	; remember which Pokemon is shown
	ld hl, wFollowerSpecies
	ld de, wFollowerShownSpecies
	ld bc, 3
	rst CopyBytes
	; follow the player (forget any stale follow from before)
	ld a, -1
	ld [wObjectFollow_Leader], a
	ld [wObjectFollow_Follower], a
	lb bc, PLAYER, FOLLOWER_OBJECT
	farjp StartFollow

DropStaleFollowLink:
; A map connection reloads the map's objects without ending a follow, so the
; link can point at a follower that no longer exists (Lake of Rage, which has
; no follower slot, was reached from Route 43 this way). ApplyMovementToFollower
; would then keep queueing the leader's steps with nobody to consume them and
; run off the end of wFollowMovementQueue, into wPlayerStruct. Drop the link
; unless its follower is still a live follower (a cutscene's follow is).
	ld a, [wObjectFollow_Follower]
	inc a ; -1?
	ret z
	dec a
	call GetObjectStruct
	ld hl, OBJECT_MOVEMENT_TYPE
	add hl, bc
	ld a, [hl]
	cp SPRITEMOVEDATA_FOLLOWING
	ret z
	ld a, -1
	ld [wObjectFollow_Leader], a
	ld [wObjectFollow_Follower], a
	ld hl, wPlayerFlags + 1
	res HIGH_PRIORITY_F, [hl]
	ret

RemoveFollower::
; Delete the follower, if there is one.
	ld a, FOLLOWER_OBJECT
	call GetMapObject
	ld hl, MAPOBJECT_SPRITE
	add hl, bc
	ld a, [hl]
	cp SPRITE_FOLLOWER_MON
	ret nz
	ld a, FOLLOWER_OBJECT
	call ApplyDeletionToMapObject ; stops the follow too
	ld a, FOLLOWER_OBJECT
	call GetMapObject
	ld hl, MAPOBJECT_SPRITE
	add hl, bc
	xor a
	ld [hli], a ; no sprite
	dec a
	ld [hl], a ; y = -1
	ret

RefreshFollower::
; After the start menu: the lead, or the option, may have changed.
	call CanHaveFollower
	jr c, .none
	ld a, FOLLOWER_OBJECT
	call GetMapObject
	ld hl, MAPOBJECT_SPRITE
	add hl, bc
	ld a, [hl]
	cp SPRITE_FOLLOWER_MON
	jmp nz, SpawnFollower ; none yet
	ld hl, wFollowerSpecies
	ld de, wFollowerShownSpecies
	ld c, 3
.compare
	ld a, [de]
	cp [hl]
	jmp nz, SpawnFollower ; a different Pokemon
	inc de
	inc hl
	dec c
	jr nz, .compare
	ret

.none
	jr RemoveFollower

CanHaveFollower:
; Carry if there should be no follower now. Otherwise sets wFollowerSpecies
; and wFollowerPersonality to the lead's.
	ld a, [wPlayerState]
	cp PLAYER_SURF
	jr nc, .no
	ld a, [wOptions3]
	bit FOLLOWER_OFF_F, a
	jr nz, .no
	ld a, [wCurMapObjectEventCount]
	cp FOLLOWER_OBJECT
	jr nc, .no ; the map's own objects fill every slot before the follower's (Ilex Forest)
	ld a, [wMapGroup]
	assert GROUP_TRADE_CENTER == GROUP_COLOSSEUM
	cp GROUP_COLOSSEUM
	jr nz, .map_ok
	ld a, [wMapNumber]
	cp MAP_COLOSSEUM
	jr z, .no
	cp MAP_TRADE_CENTER
	jr z, .no
.map_ok
	; the first Pokemon that isn't an egg and hasn't fainted
	ld a, [wPartyCount]
	and a
	jr z, .no
	ld b, a
	ld hl, wPartyMon1
.loop
	push hl
	ld de, MON_IS_EGG
	add hl, de
	bit MON_IS_EGG_F, [hl]
	pop hl
	jr nz, .next
	push hl
	ld de, MON_HP
	add hl, de
	ld a, [hli]
	or [hl]
	pop hl
	jr nz, .found
.next
	ld de, PARTYMON_STRUCT_LENGTH
	add hl, de
	dec b
	jr nz, .loop
.no:
	scf
	ret

.found
	; the species and personality (shininess, form) the icon needs
	ld a, [hl]
	ld [wFollowerSpecies], a
	ld de, MON_PERSONALITY
	add hl, de
	ld a, [hli]
	ld [wFollowerPersonality], a
	ld a, [hl]
	ld [wFollowerPersonality + 1], a
	and a
	ret

HideFollowerFromTrainers::
; A trainer's line of sight is blocked by any visible object in between, so
; the follower is made invisible while CheckTrainerBattle looks, so it never
; hides the player from a trainer.
	call GetFollowerFlags
	ret c
	ld a, [hl]
	ld [wFollowerSightFlags], a
	set INVISIBLE_F, [hl]
	ret

UnhideFollowerFromTrainers::
	call GetFollowerFlags
	ret c
	ld a, [wFollowerSightFlags]
	ld [hl], a
	ret

GetFollowerFlags:
; hl = the follower's OBJECT_FLAGS1, or carry if there's no follower.
	ld a, FOLLOWER_OBJECT
	call GetMapObject
	ld hl, MAPOBJECT_SPRITE
	add hl, bc
	ld a, [hl]
	cp SPRITE_FOLLOWER_MON
	scf
	ret nz
	ld hl, MAPOBJECT_OBJECT_STRUCT_ID
	add hl, bc
	ld a, [hl]
	cp NUM_OBJECT_STRUCTS
	ccf
	ret c
	call GetObjectStruct
	ld hl, OBJECT_FLAGS1
	add hl, bc
	and a
	ret

LoadFollowerSpriteGFX::
; Called by GetUsedSprite for SPRITE_FOLLOWER_MON. If the lead has a walking
; sprite (gfx/followers.asm), put its standing and walking frames in its tiles
; and return carry. Otherwise return no carry, and GetUsedSprite loads the
; party icon as usual.
	ld a, [wFollowerSpecies]
	ld [wCurIcon], a
	ld hl, wCurIconPersonality
	ld a, [wFollowerPersonality]
	ld [hli], a
	ld a, [wFollowerPersonality + 1]
	and SPECIESFORM_MASK
	ld [hl], a
	farcall GetFollowerWalkingSprite
	ld a, [wFollowerHasSprite]
	and a
	ret z ; nc
	; fallthrough

LoadWalkingSpriteGFX:
; Put the walking sprite at wFollowerSpriteBank:wFollowerSpriteAddr in the
; tiles of the sprite being loaded (hUsedSpriteTile), and return carry.
	call .Build
	; copy the frames into the follower's tiles, as GetUsedSprite does
	ldh a, [hUsedSpriteTile]
	and $7f
	swap a
	ld l, a
	and $f
	ld h, a
	xor l
	add LOW(vTiles0)
	ld l, a
	ld a, h
	adc HIGH(vTiles0)
	ld h, a
	push hl
	ld a, [wSpriteFlags]
	bit 7, a
	ld de, wDecompressScratch + 24 tiles
	ld c, 12
	call z, .ToVram
	pop hl
	ld a, [wSpriteFlags]
	bit 6, a
	jr nz, .done
	bit 5, a
	ld a, h
	jr nz, .vram1
	add 4
.vram1
	add 4
	ld h, a
	ld de, wDecompressScratch + 36 tiles
	ld c, 12
	call .ToVram
.done
	scf
	ret

.ToVram:
	ldh a, [rVBK]
	push af
	ld a, [wSpriteFlags]
	and 1 << 5
	swap a
	rra
	ldh [rVBK], a
	call Request2bppInWRA6
	pop af
	ldh [rVBK], a
	ret

.Build:
; Unpack the walking sprite (down, down walking, up, up walking, left, left
; walking) to tiles 0-23 of the decompression scratch, then put its standing
; frames in tiles 24-35 and its walking frames in tiles 36-47.
	call RunFunctionInWRA6
	ld a, [wFollowerSpriteAddr]
	ld l, a
	ld a, [wFollowerSpriteAddr + 1]
	ld h, a
	ld a, [wFollowerSpriteBank]
	ld de, wDecompressScratch
	call FarDecompressToDE
	ld hl, wDecompressScratch
	ld de, wDecompressScratch + 24 tiles
	call .EveryOtherFrame
	ld hl, wDecompressScratch + 4 tiles
	; fallthrough

.EveryOtherFrame:
	ld a, 3
.frame
	push af
	ld bc, 4 tiles
	rst CopyBytes
	ld bc, 4 tiles
	add hl, bc
	pop af
	dec a
	jr nz, .frame
	ret
