; Link Edition: wild Pokemon you can see in the overworld.
;
; Instead of random battles, up to NUM_WILD_MONS wild Pokemon wander where you'd
; meet them: tall grass on routes, the floor in caves, and the water while
; you're surfing. Walk into one, or face it and press A, to battle it.
;
; They're chosen just as random encounters are (ChooseWildEncounter: the same
; tables and odds, time of day, swarms, roaming legendaries, lead abilities,
; music and Cleanse Tag). Two are there when you arrive, and each step brings
; one more, while there's room, with the map's usual encounter chance
; (TryWildSpawn). Shininess is rolled when one appears, with the usual odds,
; and kept for the battle (wWildMonForcedShiny), so a shiny one shows its shiny
; colors. While a Repel works, the ones it would keep away run from you, and
; run off if you walk into them. One that wanders off screen is gone, making
; room for another.
;
; They're map objects FIRST_WILD_OBJECT on, after the follower, kept apart in
; wWildMapObjects (see GetMapObject), so no map's own objects or the save are
; touched. They're drawn with SPRITE_WILD_MON_1 on, using their walking sprites
; (LoadWildMonSpriteGFX) in their overworld colors.
;
; The Pokemon Tower's ghosts, without the Silph Scope, are still met at random.

DEF WILD_MON_PREFILL       EQU 2 ; how many are there when you arrive
DEF WILD_MON_SPOT_TRIES    EQU 12 ; places tried for each one
DEF WILD_MON_EDGE_TRIES    EQU 6 ; of those, just off the edge of the screen
DEF WILD_MON_FLEE_DISTANCE EQU 4 ; how close you get before one runs (Repel)

; TrySpawnWildMon modes
DEF SPAWN_NO_CHANCE EQU 1 ; without the encounter chance
DEF SPAWN_ANYWHERE  EQU 2 ; anywhere near you, not just past the edge of the screen

SpawnWildMons::
; Map setup command: the wild Pokemon you can see when you arrive.
	call ClearWildMons
	call CheckVisibleWildMons
	ret nc
	call UpdateWildMonRepelLevel
	ld c, WILD_MON_PREFILL * 4 ; tries
.loop
	push bc
	ld a, SPAWN_ANYWHERE | SPAWN_NO_CHANCE ; already here when you arrive
	call TrySpawnWildMon
	call CountWildMons
	pop bc
	cp WILD_MON_PREFILL
	ret nc
	dec c
	jr nz, .loop
	ret

WildMonStep::
; Called at each step instead of RandomEncounter. Return carry if the wild
; Pokemon you can see take the place of random battles here.
	xor a
	ld [wWildMonBumped], a ; (a bump is handled at once; never keep a stale one)
	call CheckVisibleWildMons
	ret nc
	call UpdateWildMonRepelLevel
	call RemoveFarWildMons
	xor a ; with the encounter chance, at the edge of the screen
	call TrySpawnWildMon
	scf
	ret

CheckVisibleWildMons:
; Return carry if wild Pokemon you can see take the place of random battles
; here: the map has wild Pokemon, and they aren't turned off.
	ld hl, wStatusFlags
	bit STATUSFLAGS_NO_WILD_ENCOUNTERS_F, [hl]
	jr nz, .no
	ld hl, wStatusFlags2
	bit STATUSFLAGS2_BUG_CONTEST_TIMER_F, [hl]
	jr nz, .yes
	; without the Silph Scope, the Pokemon Tower's ghosts can't be told apart
	; (as in ChooseWildEncounter)
	ld a, [wMapGroup]
	cp GROUP_SOUL_HOUSE_B1F
	jr nz, .not_ghost
	ld a, [wMapNumber]
	cp MAP_SOUL_HOUSE_B1F
	jr c, .not_ghost
	cp MAP_ROUTE_16_WEST
	jr z, .not_ghost
	ld a, [wCurKeyItem]
	push af
	ld a, SILPHSCOPE2
	ld [wCurKeyItem], a
	call CheckKeyItem
	pop bc
	ld a, b
	ld [wCurKeyItem], a
	jr nc, .no
.not_ghost
	farjp MapHasWildMons ; carry if it has some

.yes
	scf
	ret

.no
	and a
	ret

ClearWildMons:
; Take away every wild Pokemon you can see, and any object struct left over
; for one (from a saved game, say).
	ld bc, wObjectStructs + OBJECT_LENGTH
	ld a, NUM_OBJECT_STRUCTS - 1
.loop
	push af
	ld hl, OBJECT_MAP_OBJECT_INDEX
	add hl, bc
	ld a, [hl]
	sub FIRST_WILD_OBJECT
	cp NUM_WILD_MONS
	jr nc, .next
	farcall DeleteMapObject
.next
	ld hl, OBJECT_LENGTH
	add hl, bc
	ld b, h
	ld c, l
	pop af
	dec a
	jr nz, .loop

	ld hl, wWildMapObjects
	ld bc, NUM_WILD_MONS * MAPOBJECT_LENGTH
	xor a
	rst ByteFill
	ld hl, wWildMapObjects + MAPOBJECT_OBJECT_STRUCT_ID
	ld bc, MAPOBJECT_LENGTH
	ld a, NUM_WILD_MONS
.unassociate
	ld [hl], UNASSOCIATED_MAPOBJECT
	add hl, bc
	dec a
	jr nz, .unassociate

	ld hl, wWildMons
	ld bc, NUM_WILD_MONS * WILDMON_LENGTH
	xor a
	rst ByteFill
	xor a
	ld [wWildMonBattling], a
	ld [wWildMonBumped], a
	ld [wWildMonForcedShiny], a
	ld [wWildMonSpawnPending], a
	ret

GetWildMonSlot:
; hl = the wWildMons entry of wild Pokemon a. Preserves bc and de.
	push bc
	ld hl, wWildMons
	ld bc, WILDMON_LENGTH
	rst AddNTimes
	pop bc
	ret

CountWildMons:
; a = how many wild Pokemon you can see there are.
	ld hl, wWildMons
	ld de, WILDMON_LENGTH
	lb bc, 0, NUM_WILD_MONS
.loop
	ld a, [hl]
	and a
	jr z, .next
	inc b
.next
	add hl, de
	dec c
	jr nz, .loop
	ld a, b
	ret

UpdateWildMonRepelLevel:
; While a Repel works, the wild Pokemon below the lead's level run from you.
	ld a, [wRepelEffect]
	and a
	jr z, .done
	farcall SetBattlerLevel ; c = the lead's level
	ld a, c
.done
	ld [wWildMonRepelLevel], a
	ret

RemoveFarWildMons:
; The ones that left the screen are gone (making room for others).
	xor a
.loop
	push af
	call GetWildMonSlot
	ld a, [hl]
	and a
	jr z, .next
	pop af
	push af
	add FIRST_WILD_OBJECT
	call GetMapObject
	ld hl, MAPOBJECT_OBJECT_STRUCT_ID
	add hl, bc
	ld a, [hl]
	cp NUM_OBJECT_STRUCTS
	jr nc, .remove ; its object struct is gone: it went too far
	call GetObjectStruct
	ld hl, OBJECT_FLAGS2
	add hl, bc
	bit OFF_SCREEN_F, [hl]
	jr z, .next
.remove
	pop af
	push af
	call RemoveWildMon
.next
	pop af
	inc a
	cp NUM_WILD_MONS
	jr c, .loop
	ret

RemoveWildMon:
; Take away wild Pokemon a.
	push af
	add FIRST_WILD_OBJECT
	call ApplyDeletionToMapObject
	pop af
	push af
	add FIRST_WILD_OBJECT
	call GetMapObject
	ld hl, MAPOBJECT_SPRITE
	add hl, bc
	xor a
	ld [hli], a ; no sprite
	dec a
	ld [hl], a ; y = -1
	pop af
	call GetWildMonSlot
	ld [hl], 0 ; no species
	ret

TrySpawnWildMon:
; Maybe bring out one more wild Pokemon, if there's room. a = 0: with the
; map's encounter chance, just off the edge of the screen if it can be;
; a = SPAWN_ANYWHERE: always, anywhere near you. If the chance came up but
; there was nowhere to put it, the next try doesn't roll it again.
	call .Try
	; what was chosen is kept with it: leave no battle set up (as
	; TryWildEncounter does when there's no battle)
	xor a ; BATTLETYPE_NORMAL
	ld [wBattleType], a
	ld [wTempWildMonSpecies], a
	ld [wWildMonForm], a
	ret

.Try:
	ld b, a
	ld a, [wWildMonSpawnPending]
	and a
	ld a, b
	jr z, .got_mode
	or SPAWN_NO_CHANCE
.got_mode
	ld [wWildMonSpawnMode], a
	; a free slot
	ld hl, wWildMons
	ld de, WILDMON_LENGTH
	ld c, 0
.find_slot
	ld a, [hl]
	and a
	jr z, .got_slot
	add hl, de
	inc c
	ld a, c
	cp NUM_WILD_MONS
	jr c, .find_slot
	ret

.got_slot
	ld a, c
	ld [wWildMonSpawnSlot], a

	; leave one of the 8 object palettes free, for people coming into view
	ld a, [wUsedObjectPals]
	ld c, 0
.count_pals
	and a
	jr z, .counted_pals
	ld b, a
	dec a
	and b ; clear the lowest set bit
	inc c
	jr .count_pals
.counted_pals
	ld a, c
	cp 7
	ret nc
	ld a, [wWildMonSpawnMode]
	and SPAWN_NO_CHANCE
	call ChooseWildMon
	ret nz
	ld a, [wTempWildMonSpecies]
	and a
	ret z

	; at most one of each roaming legendary
	ld a, [wBattleType]
	cp BATTLETYPE_ROAMING
	jr nz, .not_roaming
	ld a, [wTempWildMonSpecies]
	ld b, a
	ld hl, wWildMons
	ld de, WILDMON_LENGTH
	ld c, NUM_WILD_MONS
.roamer_loop
	ld a, [hl]
	cp b
	ret z
	add hl, de
	dec c
	jr nz, .roamer_loop
.not_roaming

	; where it lives, and a free spot for it there
	call GetPlayerStandingTile
	dec a ; cp WATER_TILE
	ld a, HABITAT_WATER
	jr z, .got_habitat
	ld a, [wEnvironment]
	cp FIRST_DIGGABLE_ENV
	ld a, HABITAT_FLOOR
	jr nc, .got_habitat
	ld a, HABITAT_GRASS
.got_habitat
	ld [wWildMonSpawnHabitat], a
	call FindWildMonSpot
	jr c, .found_spot
	; nowhere for it now: it comes next time, without rolling again
	ld a, [wWildMonSpawnMode]
	and SPAWN_ANYWHERE
	ret nz
	ld a, TRUE
	ld [wWildMonSpawnPending], a
	ret

.found_spot
	xor a
	ld [wWildMonSpawnPending], a

	; what it is
	push de
	ld a, [wWildMonSpawnSlot]
	call GetWildMonSlot
	ld a, [wTempWildMonSpecies]
	ld [hli], a ; species
	push hl
	call GetSpawnForm
	pop hl
	ld [hli], a ; form
	push hl
	call RollWildMonShininess
	pop hl
	ld [hli], a ; shininess
	ld a, [wCurPartyLevel]
	ld [hli], a ; level
	ld a, [wBattleType]
	ld [hli], a ; battle type
	ld a, [wWildMonSpawnHabitat]
	ld [hl], a ; habitat
	pop de

	; its map object
	ld a, [wWildMonSpawnSlot]
	add FIRST_WILD_OBJECT
	call GetMapObject
	ld h, b
	ld l, c
	ld a, UNASSOCIATED_MAPOBJECT
	ld [hli], a ; object struct
	ld a, [wWildMonSpawnSlot]
	add SPRITE_WILD_MON_1
	ld [hli], a ; sprite
	ld a, e
	ld [hli], a ; y
	ld a, d
	ld [hli], a ; x
	ld a, [wWildMonSpawnHabitat]
	cp HABITAT_WATER
	ld a, SPRITEMOVEDATA_WILD_MON
	jr nz, .got_movement
	ld a, SPRITEMOVEDATA_WILD_MON_SWIM
.got_movement
	ld [hli], a ; movement
	xor a
	ld [hli], a ; radius
	ld [hli], a ; palette (its own colors)
	dec a
	ld [hli], a ; time of day: always
	ld a, OBJECTTYPE_SCRIPT
	ld [hli], a ; type
	xor a
	ld [hli], a ; sight range
	ld [hli], a
	ld [hli], a ; script (WildMonEncounter instead)
	dec a
	ld [hli], a
	ld [hl], a ; event flag: none

	; and its object struct (it's in range)
	ld a, [wWildMonSpawnSlot]
	add FIRST_WILD_OBJECT
	ldh [hMapObjectIndexBuffer], a
	call GetMapObject
	farcall CopyObjectStruct
	ret nc
	; no free object struct
	ld a, [wWildMonSpawnSlot]
	jmp RemoveWildMon

ChooseWildMon:
; Choose a wild Pokemon as a random encounter would be (if a is nonzero,
; without the encounter chance). Return z with it in wTempWildMonSpecies,
; wWildMonForm, wCurPartyLevel and wBattleType.
	ld hl, wStatusFlags2
	bit STATUSFLAGS2_BUG_CONTEST_TIMER_F, [hl]
	jr nz, .bug_contest
	farjp TryWildSpawn

.bug_contest
	and a
	jr nz, .contest_mon
	farcall TryWildEncounter_BugContest ; carry if one
	jr nc, .none
.contest_mon
	farcall ChooseBugContestMon
	xor a ; BATTLETYPE_NORMAL (the contest's battle script sets its own)
	ld [wBattleType], a
	ret ; z

.none
	or 1
	ret

GetSpawnForm:
; a = the form the chosen Pokemon has (as LoadEnemyWildmon would choose it).
	ld a, [wTempEnemyMonSpecies]
	push af
	ld a, [wTempWildMonSpecies]
	ld [wTempEnemyMonSpecies], a
	farcall GenerateWildForm
	pop af
	ld [wTempEnemyMonSpecies], a
	ld a, [wCurForm]
	ret

RollWildMonShininess:
; a = SHINY_MASK 1/4096 of the time, 3/4096 with the Shiny Charm (as
; GeneratePartyMonStats would), else 0.
	call Random
	and a
	jr nz, .not_shiny
	ld a, [wCurKeyItem]
	push af
	ld a, SHINY_CHARM
	ld [wCurKeyItem], a
	call CheckKeyItem
	pop bc
	ld a, b
	ld [wCurKeyItem], a
	ld b, SHINY_NUMERATOR
	jr nc, .got_odds
	ld b, CHARMED_SHINY_NUMERATOR
.got_odds
	call Random
	cp b
	jr nc, .not_shiny
	ld a, SHINY_MASK
	ret

.not_shiny
	xor a
	ret

FindWildMonSpot:
; Return carry and a free spot (x, y) in de for a new wild Pokemon near you.
	ld b, WILD_MON_SPOT_TRIES
.loop
	push bc
	ld a, [wWildMonSpawnMode]
	and SPAWN_ANYWHERE
	jr nz, .anywhere
	ld a, b
	cp WILD_MON_SPOT_TRIES - WILD_MON_EDGE_TRIES + 1
	jr c, .anywhere
	call .EdgeSpot
	jr .got_spot
.anywhere
	call .NearbySpot
.got_spot
	call nc, CheckWildMonSpot
	pop bc
	jr nc, .found
	dec b
	jr nz, .loop
	and a
	ret

.found
	scf
	ret

.NearbySpot:
; Anywhere an object stays in range (just past each edge of the screen), but
; not right by the player.
	call .RandomOffsets
	ld a, d
	add 2
	cp 5
	jr nc, .Offset
	ld a, e
	add 2
	cp 5
	ret c ; too close
	jr .Offset

.EdgeSpot:
; Just past an edge of the screen: half the time the one the player faces, so
; it comes into view as they walk.
	call .RandomOffsets
	call Random
	cp 50 percent
	jr nc, .any_edge
	ld a, [wPlayerDirection]
	rrca
	rrca
	jr .got_edge
.any_edge
	call Random
.got_edge
	and 3
	assert DOWN == 0 && UP == 1 && LEFT == 2 && RIGHT == 3
	jr z, .bottom
	dec a
	jr z, .top
	dec a
	ld d, -5
	jr z, .Offset
	ld d, 6
	jr .Offset

.top
	ld e, -5
	jr .Offset

.bottom
	ld e, 5
.Offset:
	ld a, [wPlayerMapX]
	add d
	ld d, a
	ld a, [wPlayerMapY]
	add e
	ld e, a
	and a
	ret

.RandomOffsets:
; d = -5 to 6, e = -5 to 5 (the player is 4 tiles from the top left of the
; screen, and objects stay in range one tile past each edge)
	ld a, 12
	call RandomRange
	sub 5
	ld d, a
	ld a, 11
	call RandomRange
	sub 5
	ld e, a
	ret

CheckWildMonSpot:
; Carry if a new wild Pokemon can't be put at (d, e).
	call IsOutsideMap
	ret c
	push de
	call GetCoordTileCollision
	ld hl, wWildMonSpawnHabitat
	ld e, [hl]
	call IsWildMonTile
	pop de
	jr nz, .no
	; nobody there, or coming there
	ldh a, [hMapObjectIndexBuffer]
	push af
	ld a, -1 ; not an object struct
	ldh [hMapObjectIndexBuffer], a
	push de
	farcall IsNPCAtCoord
	pop de
	pop bc
	ld a, b
	ldh [hMapObjectIndexBuffer], a
	ret c
	; no other object there yet (it may not be on screen)
	ld hl, wMapObjects + MAPOBJECT_LENGTH
	ld b, NUM_OBJECTS - 1
	call .CheckObjects
	ret c
	ld hl, wWildMapObjects
	ld b, NUM_WILD_MONS
.CheckObjects:
	push hl
	inc hl ; MAPOBJECT_SPRITE
	ld a, [hli]
	and a
	jr z, .next
	assert MAPOBJECT_Y_COORD == MAPOBJECT_SPRITE + 1
	ld a, [hli]
	cp e
	jr nz, .next
	assert MAPOBJECT_X_COORD == MAPOBJECT_Y_COORD + 1
	ld a, [hl]
	cp d
	jr nz, .next
	pop hl
.no
	scf
	ret

.next
	pop hl
	ld a, l
	add MAPOBJECT_LENGTH
	ld l, a
	adc h
	sub l
	ld h, a
	dec b
	jr nz, .CheckObjects
	and a
	ret

IsOutsideMap:
; Carry if (d, e) isn't in the map itself (but a neighbor's, past a
; connection, or the border).
	ld a, [wMapWidth]
	add a
	ld h, a
	ld a, d
	sub 4
	ret c
	cp h
	ccf
	ret c
	ld a, [wMapHeight]
	add a
	ld h, a
	ld a, e
	sub 4
	ret c
	cp h
	ccf
	ret

IsWildMonTile:
; Return z if collision a is the kind of tile for habitat e. Clobbers d.
	ld d, a
	ld a, e
	cp HABITAT_WATER
	ld a, d
	jr z, .water
	cp COLL_TALL_GRASS
	ret z
	cp COLL_LONG_GRASS
	ret z
	ld a, e
	cp HABITAT_FLOOR
	ret nz
	ld a, d
	cp COLL_FLOOR
	ret

.water
	cp COLL_WATER
	ret

GetWildMonStep::
; Movement for a wild Pokemon (bc = its object struct): a = the direction it
; steps, or carry to stand a while. While a Repel keeps it away, it runs from
; you (and OBJECT_RANGE is set, so it doesn't stop between steps).
	ld a, [wScriptRunning]
	and a
	jmp nz, .wait ; everyone stays put during events
	ld hl, OBJECT_MAP_OBJECT_INDEX
	add hl, bc
	ld a, [hl]
	sub FIRST_WILD_OBJECT
	cp NUM_WILD_MONS
	jmp nc, .wait
	call GetWildMonSlot
	ld a, [hl]
	and a
	jmp z, .wait
	push hl
	push bc
	call UpdateWildMonRepelLevel ; a Repel may have just been used
	pop bc
	pop hl
	ld de, WILDMON_LEVEL
	add hl, de
	ld d, a
	ld a, [hl]
	cp d
	jr nc, .not_scared

	; is the player close?
	call .PlayerOffset
	ld a, d
	call .Abs
	cp WILD_MON_FLEE_DISTANCE + 1
	jr nc, .not_scared
	ld h, a
	ld a, e
	call .Abs
	cp WILD_MON_FLEE_DISTANCE + 1
	jr nc, .not_scared
	ld l, a
	push hl
	ld hl, OBJECT_RANGE
	add hl, bc
	ld [hl], TRUE
	; it may leave its kind of tiles, and the screen
	ld hl, OBJECT_FLAGS1
	add hl, bc
	set MOVE_ANYWHERE_F, [hl]
	pop hl
	call .AwayFromPlayer
	or STEP_WALK << 2 ; quicker than wandering
	ret

.AwayFromPlayer:
; away from the player, mostly the way they're further apart
	ld a, h
	cp l
	push af ; carry: further apart vertically
	call Random
	cp 40 percent
	jr nc, .keep_way
	pop af
	ccf
	push af
.keep_way
	pop af
	jr c, .vertical
	ld a, d
	and a
	jr z, .either_horizontal
	bit 7, a
	ld a, RIGHT
	ret z
	ld a, LEFT
	ret

.either_horizontal
	call Random
	and 1
	add LEFT
	assert LEFT + 1 == RIGHT
	ret

.vertical
	ld a, e
	and a
	jr z, .either_vertical
	bit 7, a
	ld a, DOWN
	ret z
	ld a, UP
	ret

.either_vertical
	call Random
	and 1
	assert DOWN + 1 == UP
	ret

.not_scared
	ld hl, OBJECT_RANGE
	add hl, bc
	ld [hl], FALSE
	ld hl, OBJECT_FLAGS1
	add hl, bc
	res MOVE_ANYWHERE_F, [hl]
	call Random
	cp 25 percent
	jmp c, .wait
	and 3 ; any direction
	ret

.wait
	scf
	ret

.PlayerOffset:
; d = its x - the player's, e = its y - the player's
	ld hl, OBJECT_MAP_X
	add hl, bc
	ld a, [wPlayerMapX]
	ld d, a
	ld a, [hl]
	sub d
	ld d, a
	ld hl, OBJECT_MAP_Y
	add hl, bc
	ld a, [wPlayerMapY]
	ld e, a
	ld a, [hl]
	sub e
	ld e, a
	ret

.Abs:
	bit 7, a
	ret z
	cpl
	inc a
	ret

CheckWildMonStepTile::
; Carry if the wild Pokemon (bc = its object struct) can't step where it's
; heading: not its kind of tile (unless it's running from you), outside the
; map, or where the follower is.
	ld hl, OBJECT_RANGE
	add hl, bc
	ld a, [hl]
	and a
	jr nz, .any_tile
	ld hl, OBJECT_MAP_OBJECT_INDEX
	add hl, bc
	ld a, [hl]
	sub FIRST_WILD_OBJECT
	call GetWildMonSlot
	ld de, WILDMON_HABITAT
	add hl, de
	ld e, [hl]
	ld hl, OBJECT_TILE_COLLISION
	add hl, bc
	ld a, [hl]
	call IsWildMonTile
	jr nz, .no
.any_tile
	ld hl, OBJECT_MAP_X
	add hl, bc
	ld d, [hl]
	ld hl, OBJECT_MAP_Y
	add hl, bc
	ld e, [hl]
	call IsOutsideMap
	ret c
	; not onto the follower (nothing else collides with it)
	push bc
	ld a, FOLLOWER_OBJECT
	call GetMapObject
	ld hl, MAPOBJECT_SPRITE
	add hl, bc
	ld a, [hl]
	cp SPRITE_FOLLOWER_MON
	jr nz, .ok
	ld hl, MAPOBJECT_OBJECT_STRUCT_ID
	add hl, bc
	ld a, [hl]
	cp NUM_OBJECT_STRUCTS
	jr nc, .ok
	call GetObjectStruct
	ld hl, OBJECT_MAP_X
	call .Compare
	jr c, .done
	ld hl, OBJECT_LAST_MAP_X
	call .Compare
	jr .done

.ok
	and a
.done
	pop bc
	ret

.no
	scf
	ret

.Compare:
; Carry if the follower's x at hl (and its y after it) is (d, e).
	assert OBJECT_MAP_Y == OBJECT_MAP_X + 1
	assert OBJECT_LAST_MAP_Y == OBJECT_LAST_MAP_X + 1
	add hl, bc
	ld a, [hli]
	cp d
	jr nz, .different
	ld a, [hl]
	cp e
	jr nz, .different
	scf
	ret

.different
	and a
	ret

WildMonEncounter::
; The player walked into wild Pokemon a (its map object), or faced it and
; pressed A. Start the battle (returning carry, as CallScript does), or if a
; Repel keeps it away, it runs off (no carry).
	ldh [hLastTalked], a
	sub FIRST_WILD_OBJECT
	ld [wWildMonSpawnSlot], a
	call GetWildMonSlot
	ld a, [hl]
	and a
	ret z ; nobody there now (no carry)

	; a Repel keeps it away: it runs off
	push hl
	call UpdateWildMonRepelLevel
	pop hl
	push hl
	ld de, WILDMON_LEVEL
	add hl, de
	ld a, [wWildMonRepelLevel]
	ld d, a
	ld a, [hl]
	cp d
	pop hl
	jr c, .runs_off

	ld a, [hli]
	ld [wTempWildMonSpecies], a
	ld a, [hli]
	ld [wWildMonForm], a
	ld a, [hli]
	inc a
	ld [wWildMonForcedShiny], a
	ld a, [hli]
	ld [wCurPartyLevel], a
	ld a, [hl]
	ld [wBattleType], a
	ld a, [wWildMonSpawnSlot]
	inc a
	ld [wWildMonBattling], a

	; it turns to face the player
	ldh a, [hLastTalked]
	call GetMapObject
	ld hl, MAPOBJECT_OBJECT_STRUCT_ID
	add hl, bc
	ld a, [hl]
	cp NUM_OBJECT_STRUCTS
	jr nc, .faced
	call GetObjectStruct
	ld a, [wPlayerDirection]
	xor (OW_UP ^ OW_DOWN) ; the other way
	assert (OW_LEFT ^ OW_RIGHT) == (OW_UP ^ OW_DOWN)
	call SetSpriteDirection
.faced

	; the battle, as RandomEncounter starts it
	ld hl, wStatusFlags2
	bit STATUSFLAGS2_SAFARI_GAME_F, [hl]
	jr nz, .safari_game
	bit STATUSFLAGS2_BUG_CONTEST_TIMER_F, [hl]
	jr nz, .bug_contest
	ld a, [wTempWildMonSpecies]
	cp SUICUNE
	ld a, BANK(RoamingSuicuneBattleScript)
	ld hl, RoamingSuicuneBattleScript
	jr z, .got_script
	ld a, [wTempWildMonSpecies]
	cp RAIKOU
	ld a, BANK(RoamingRaikouBattleScript)
	ld hl, RoamingRaikouBattleScript
	jr z, .got_script
	ld a, [wTempWildMonSpecies]
	cp ENTEI
	ld a, BANK(RoamingEnteiBattleScript)
	ld hl, RoamingEnteiBattleScript
	jr z, .got_script
	ld a, BANK(WildBattleScript)
	ld hl, WildBattleScript
.got_script
	jmp CallScript

.safari_game
	ld a, BANK(SafariGameBattleScript)
	ld hl, SafariGameBattleScript
	jr .got_script

.bug_contest
	ld a, BANK(BugCatchingContestBattleScript)
	ld hl, BugCatchingContestBattleScript
	jr .got_script

.runs_off
	ld de, SFX_RUN
	call PlaySFX
	ld a, [wWildMonSpawnSlot]
	call RemoveWildMon
	and a
	ret

FinishWildMonBattle::
; After a battle: the wild Pokemon you battled is gone.
	xor a
	ld [wWildMonForcedShiny], a
	ld hl, wWildMonBattling
	ld a, [hl]
	and a
	ret z
	ld [hl], 0
	dec a
	jmp RemoveWildMon

GetWildMonSpriteSpecies::
; a = SPRITE_WILD_MON_* -> a = species, d = shininess, e = form.
	sub SPRITE_WILD_MON_1
	call GetWildMonSlot
	ld a, [hli]
	push af
	ld a, [hli]
	and SPECIESFORM_MASK
	ld e, a
	ld d, [hl]
	pop af
	ret

LoadWildMonSpriteGFX::
; Called by GetUsedSprite for SPRITE_WILD_MON_*: put the Pokemon's walking
; sprite in its tiles and return carry.
	ldh a, [hUsedSpriteIndex]
	call GetWildMonSpriteSpecies
	and a
	ret z ; no carry
	ld [wCurIcon], a
	ld hl, wCurIconPersonality
	ld a, d
	ld [hli], a
	ld [hl], e
	; GetFollowerWalkingSprite also says whether the follower has one: keep it
	ld a, [wFollowerHasSprite]
	push af
	farcall GetFollowerWalkingSprite
	ld a, [wFollowerHasSprite]
	ld e, a
	pop af
	ld [wFollowerHasSprite], a
	ld a, e
	and a
	ret z ; no carry
	farjp LoadWalkingSpriteGFX
