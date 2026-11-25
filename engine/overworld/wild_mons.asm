; Link Edition: wild Pokemon you can see in the overworld.
;
; Instead of random battles, up to NUM_WILD_MONS wild Pokemon (3, or 4 while the
; screen isn't busy) wander where you'd meet them: tall grass on routes, the
; floor in caves, and the water while you're surfing. Walk into one, or face it and press A, to battle it.
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
; sides of a tile with a wall along them
	const_def
	const EDGE_RIGHT_F
	const EDGE_LEFT_F
	const EDGE_UP_F
	const EDGE_DOWN_F
DEF EDGE_RIGHT EQU 1 << EDGE_RIGHT_F
DEF EDGE_LEFT  EQU 1 << EDGE_LEFT_F
DEF EDGE_UP    EQU 1 << EDGE_UP_F
DEF EDGE_DOWN  EQU 1 << EDGE_DOWN_F

DEF WILD_MON_SPOT_TRIES    EQU 12 ; places tried for each one
DEF WILD_MON_EDGE_TRIES    EQU 6 ; of those, just off the edge of the screen
DEF WILD_MON_FLEE_DISTANCE EQU 4 ; how close you get before one runs (Repel)

DEF WILD_MON_USUAL_MAX    EQU 3 ; more than this only while the screen isn't busy
DEF WILD_MON_BUSY_SCREEN  EQU 7 ; objects on screen (you, your follower and
                                ; the rest) that leave no room for another
DEF WILD_HONEY_DURATION EQU 12 ; completed player steps

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
	ld hl, wWildHoneySteps
	ld a, [hl]
	and a
	jr z, .no_honey
	dec [hl]
.no_honey
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
	ld [wWildHoneySteps], a
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

CountVisibleObjects:
; a = how many objects are on screen (the player included).
	ld hl, wObjectStructs
	ld de, OBJECT_LENGTH
	lb bc, 0, NUM_OBJECT_STRUCTS
.loop
	push hl
	ld a, [hl] ; OBJECT_SPRITE
	and a
	jr z, .next
	assert OBJECT_FLAGS2 == OBJECT_FLAGS1 + 1
	push de
	ld de, OBJECT_FLAGS1
	add hl, de
	pop de
	bit INVISIBLE_F, [hl]
	jr nz, .next
	inc hl
	bit OFF_SCREEN_F, [hl]
	jr nz, .next
	inc b
.next
	pop hl
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
.no_room
	; no room for another (every slot out, or no more allowed on this screen):
	; a roaming legendary on this map still comes as often as it would in a
	; random battle, in place of the one furthest from you
	ld a, [wWildMonSpawnMode]
	and a
	ret nz
	farcall TryRoamerSpawn
	jr z, .special
	; or today's rare Pokemon (TV news), on its map
	call TrySightingWhenFull
	ret nz
.special
	call IsSameRoamerOut
	ret z
	call FurthestOrdinaryWildMon ; a = which, or carry if none
	ret c
	ld [wWildMonSpawnSlot], a
	; (roaming legendaries are only met on land)
	ld a, [wEnvironment]
	cp FIRST_DIGGABLE_ENV
	ld a, HABITAT_FLOOR
	jr nc, .roamer_habitat
	ld a, HABITAT_GRASS
.roamer_habitat
	ld [wWildMonSpawnHabitat], a
	call FindWildMonSpot
	ret nc
	push de
	ld a, [wWildMonSpawnSlot]
	call RemoveWildMon
	pop de
	jr .place

.got_slot
	ld a, c
	ld [wWildMonSpawnSlot], a

	; leave one of the 8 object palettes free, for people coming into view
	; (two for a 4th wild Pokemon)
	call CountWildMons
	cp WILD_MON_USUAL_MAX
	ld e, 7
	jr c, .got_pal_limit
	dec e
.got_pal_limit
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
	cp e
	jr nc, .no_room

	; a 4th only while few others are on screen (the Game Boy shows 40
	; sprites, 10 on a line, and each object here takes 4)
	call CountWildMons
	cp WILD_MON_USUAL_MAX
	jr c, .room_on_screen
	call CountVisibleObjects
	cp WILD_MON_BUSY_SCREEN
	jr nc, .no_room
.room_on_screen
	ld a, [wWildMonSpawnMode]
	and SPAWN_NO_CHANCE
	call ChooseWildMon
	ret nz
	ld a, [wTempWildMonSpecies]
	and a
	ret z
	call ApplyTodaysSighting

	; at most one of each roaming legendary
	call IsSameRoamerOut
	ret z

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
.place

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
	ld [hli], a ; habitat
	push hl
	call GetWildMonTraits
	pop hl
	ld [hli], a
	ld [hl], 0 ; alert
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

IsSameRoamerOut:
; Return z if the chosen Pokemon is a roaming legendary that's already out.
	ld a, [wBattleType]
	cp BATTLETYPE_ROAMING
	jr nz, .no
	ld a, [wTempWildMonSpecies]
	ld b, a
	ld hl, wWildMons
	ld de, WILDMON_LENGTH
	ld c, NUM_WILD_MONS
.loop
	ld a, [hl]
	cp b
	ret z
	add hl, de
	dec c
	jr nz, .loop
.no
	or 1
	ret

FurthestOrdinaryWildMon:
; a = the wild Pokemon furthest from the player that isn't a roaming
; legendary or today's rare Pokemon (to make room for one), or carry if
; there's none.
	ld a, -1
	ld [wWildMonSpawnSlot], a
	ld e, 0 ; furthest so far
	xor a
.loop
	push af
	call GetWildMonSlot
	ld a, [hl]
	and a
	jr z, .next
	call IsTodaysSighting
	jr z, .next
	ld bc, WILDMON_BATTLETYPE
	add hl, bc
	ld a, [hl]
	cp BATTLETYPE_ROAMING
	jr z, .next
	pop af
	push af
	add FIRST_WILD_OBJECT
	call GetMapObject
	ld hl, MAPOBJECT_OBJECT_STRUCT_ID
	add hl, bc
	ld a, [hl]
	cp NUM_OBJECT_STRUCTS
	jr nc, .next
	call GetObjectStruct
	; distance = |dx| + |dy|
	ld hl, OBJECT_MAP_X
	add hl, bc
	ld a, [wPlayerMapX]
	sub [hl]
	jr nc, .x_ok
	cpl
	inc a
.x_ok
	ld d, a
	ld hl, OBJECT_MAP_Y
	add hl, bc
	ld a, [wPlayerMapY]
	sub [hl]
	jr nc, .y_ok
	cpl
	inc a
.y_ok
	add d
	cp e
	jr c, .next
	ld e, a
	pop af
	push af
	ld [wWildMonSpawnSlot], a
.next
	pop af
	inc a
	cp NUM_WILD_MONS
	jr c, .loop
	ld a, [wWildMonSpawnSlot]
	cp -1
	scf
	ret z
	and a
	ret

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
	call ComputeWildMonReach
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
	jp nz, CheckWildMonObjects.no
	; somewhere you can get to (not, say, the rock outside a cave's walls)
	call IsWildMonSpotReached
	ccf
	ret c
	; fallthrough

CheckWildMonObjects:
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

CheckWildMonPath:
; Carry if (d, e) is walled off from you (see ComputeWildMonReach, which
; FindWildMonSpot does once for all its tries). Keeps de.
	push de
	call ComputeWildMonReach
	pop de
	call IsWildMonSpotReached
	ccf
	ret

ComputeWildMonReach:
; Mark which tiles in the window around you (WILD_REACH_*) you can walk to
; and back without leaving it: over ordinary tiles of the Pokemon's kind
; (land or water), not across a wall along a tile's side (as at a cave's
; edges), and not through anyone standing in the way. Tiles with special
; movement (ice, currents, waterfalls, whirlpools, holes, warps, ledges)
; can't prove a path you can walk back, so they count as walls.
	ld a, [wPlayerMapX]
	ld [wWildReachPlayerX], a
	ld a, [wPlayerMapY]
	ld [wWildReachPlayerY], a
	ld a, [wMapWidth]
	add a
	ld [wWildReachMapWidth], a
	srl a
	add 6
	ld [wWildReachBlockRow], a
	ld a, [wMapHeight]
	add a
	ld [wWildReachMapHeight], a
	; the kind of tile the Pokemon lives on: water, or land
	ld a, [wWildMonSpawnHabitat]
	cp HABITAT_WATER
	ld a, WATER_TILE
	jr z, .got_kind_to_walk
	assert LAND_TILE == 0
	xor a
.got_kind_to_walk
	ld [wWildReachKind], a
	ld a, BANK(wWildMonReach)
	call StackCallInWRAMBankA

.Function:
	ld hl, CollisionPermissionTable
	ld de, wWildReachPermissions
	ld bc, 256
	ld a, BANK(CollisionPermissionTable)
	call FarCopyBytes
	ld a, WALL_TILE
	ld [wWildReachPermissions + COLL_ICE], a
	ld [wWildReachPermissions + COLL_WHIRLPOOL], a
	ld hl, wWildReachPermissions + HI_NYBBLE_CURRENT
	ld b, $10 ; waterfalls and currents
	call .Walls
	ld hl, wWildReachPermissions + COLL_HOLE
	ld b, COLL_RIGHT_WALL - COLL_HOLE ; holes, warps, counters, ledges…
	call .Walls
	ld hl, wWildReachPermissions + COLL_LEFT_WALL_GLOW + 1
	ld b, LOW($100 - (COLL_LEFT_WALL_GLOW + 1))
	call .Walls
	; (walls along one side stay walkable: EdgeWallSides blocks that side)

	; each tile: whether you could walk on it, and the walls along its sides
	ld hl, wWildMonReach
	ld a, [wWildReachPlayerY]
	sub 4 + WILD_REACH_UP
	ld e, a ; map y (from 0)
	ld c, WILD_REACH_HEIGHT
.row
	push bc
	ld a, [wWildReachMapHeight]
	ld b, a
	ld a, e
	cp b
	jr c, .in_map
	ld b, WILD_REACH_WIDTH
	xor a
.nothing
	ld [hli], a
	dec b
	jr nz, .nothing
	jmp .next_row

.in_map
	and 1
	add a
	ld [wWildReachHalf], a
	push de
	push hl
	; de = the block at the row's first column
	ld a, [wWildReachBlockRow]
	ld c, a
	ld b, 0
	ld hl, wOverworldMapBlocks + 3
	ld a, e
	srl a
	add 3 ; the border
.block_row
	add hl, bc
	dec a
	jr nz, .block_row
	ld a, [wWildReachPlayerX]
	sub 4 + WILD_REACH_LEFT
	ld c, a ; map x (from 0; may be "negative")
	sra a
	ld e, a
	add a
	sbc a
	ld d, a
	add hl, de
	ld d, h
	ld e, l
	pop hl
	ld b, WILD_REACH_WIDTH
.col
	ld a, [wWildReachMapWidth]
	cp c
	jr c, .off_map
	jr z, .off_map
	push hl
	ld a, [de] ; the block
	ld l, a
	ld h, 0
	add hl, hl
	add hl, hl
	ld a, [wWildReachHalf]
	bit 0, c
	jr z, .left_half
	inc a
.left_half
	add l
	ld l, a
	ld a, h
	add HIGH(wDecompressedCollisions)
	ld h, a
	assert LOW(wDecompressedCollisions) == 0
	ld a, BANK(wDecompressedCollisions)
	ldh [rWBK], a
	ld l, [hl] ; its collision
	ld a, BANK(wWildMonReach)
	ldh [rWBK], a
	ld h, HIGH(wWildReachPermissions)
	assert LOW(wWildReachPermissions) == 0
	ld a, [hl]
	and $f ; as GetTilePermission
	ld h, a
	ld a, [wWildReachKind]
	cp h
	ld h, 0
	jr nz, .got_kind
	ld h, 1 << WILD_REACH_WALKABLE_F
.got_kind
	ld a, l
	sub COLL_RIGHT_WALL
	cp EdgeWallSides.End - EdgeWallSides
	jr nc, .no_walls
	push de
	ld e, a
	ld d, 0
	ld a, h
	ld hl, EdgeWallSides
	add hl, de
	or [hl]
	ld h, a
	pop de
.no_walls
	ld a, h
	pop hl
	ld [hli], a
	jr .next_col

.off_map
	xor a
	ld [hli], a
.next_col
	bit 0, c
	jr z, .same_block
	inc de
.same_block
	inc c
	dec b
	jr nz, .col
	pop de
.next_row
	pop bc
	inc e
	dec c
	jmp nz, .row

	; the window's own edges are walls too
	ld hl, wWildMonReach
	ld de, wWildMonReach + (WILD_REACH_HEIGHT - 1) * WILD_REACH_WIDTH
	ld b, WILD_REACH_WIDTH
.top_bottom
	set EDGE_UP_F, [hl]
	inc hl
	ld a, [de]
	or EDGE_DOWN
	ld [de], a
	inc de
	dec b
	jr nz, .top_bottom
	ld hl, wWildMonReach
	ld de, WILD_REACH_WIDTH
	ld b, WILD_REACH_HEIGHT
.sides
	set EDGE_LEFT_F, [hl]
	add hl, de
	dec hl
	set EDGE_RIGHT_F, [hl]
	inc hl
	dec b
	jr nz, .sides

	; nobody walks through people (where they stand now, and where they live)
	ld hl, wMapObjects + MAPOBJECT_LENGTH
	ld c, NUM_OBJECTS - 1
.map_object
	push hl
	ld a, c
	cp NUM_OBJECTS - FOLLOWER_OBJECT
	jr z, .next_map_object ; your follower walks with you
	push bc
	ld de, MAPOBJECT_SPRITE
	add hl, de
	ld a, BANK(wMapObjects)
	call GetFarWRAMByte
	and a
	jr z, .no_map_object
	inc hl
	assert MAPOBJECT_Y_COORD == MAPOBJECT_SPRITE + 1
	ld a, BANK(wMapObjects)
	call GetFarWRAMByte
	ld e, a
	inc hl
	assert MAPOBJECT_X_COORD == MAPOBJECT_Y_COORD + 1
	ld a, BANK(wMapObjects)
	call GetFarWRAMByte
	ld d, a
	call .Occupied
.no_map_object
	pop bc
.next_map_object
	pop hl
	ld de, MAPOBJECT_LENGTH
	add hl, de
	dec c
	jr nz, .map_object

	ld hl, wObjectStructs + OBJECT_LENGTH
	ld c, NUM_OBJECT_STRUCTS - 1
.object_struct
	push hl
	push bc
	ld de, OBJECT_SPRITE
	add hl, de
	ld a, BANK(wObjectStructs)
	call GetFarWRAMByte
	and a
	jr z, .no_struct
	pop bc
	pop hl
	push hl
	push bc
	ld de, OBJECT_MAP_OBJECT_INDEX
	add hl, de
	ld a, BANK(wObjectStructs)
	call GetFarWRAMByte
	cp FOLLOWER_OBJECT
	jr z, .no_struct
	cp FIRST_WILD_OBJECT
	jr nc, .no_struct ; (wild Pokemon move off)
	pop bc
	pop hl
	push hl
	push bc
	ld de, OBJECT_MAP_X
	add hl, de
	ld a, BANK(wObjectStructs)
	call GetFarWRAMByte
	ld d, a
	pop bc
	pop hl
	push hl
	push bc
	push de
	ld de, OBJECT_MAP_Y
	add hl, de
	ld a, BANK(wObjectStructs)
	call GetFarWRAMByte
	pop de
	ld e, a
	call .Occupied
.no_struct
	pop bc
	pop hl
	ld de, OBJECT_LENGTH
	add hl, de
	dec c
	jr nz, .object_struct

	; walk out from you
	ld a, WILD_REACH_UP * WILD_REACH_WIDTH + WILD_REACH_LEFT
	ld [wWildMonReachQueue], a
	ld h, HIGH(wWildMonReach)
	ld l, a
	set WILD_REACH_REACHED_F, [hl]
	ld a, 1
	ld [wWildMonReachWrite], a
	ld de, wWildMonReachQueue ; e: the next one to take
	assert LOW(wWildMonReachQueue) == 0
.walk
	ld a, [wWildMonReachWrite]
	cp e
	ret z ; nowhere left to look
	ld a, [de]
	inc e
	ld b, a ; its place
	ld l, a
	ld c, [hl] ; its walls
	bit EDGE_RIGHT_F, c
	jr nz, .no_right
	ld l, b
	inc l
	ld a, EDGE_LEFT
	call .Try
.no_right
	bit EDGE_LEFT_F, c
	jr nz, .no_left
	ld l, b
	dec l
	ld a, EDGE_RIGHT
	call .Try
.no_left
	bit EDGE_DOWN_F, c
	jr nz, .no_down
	ld a, b
	add WILD_REACH_WIDTH
	ld l, a
	ld a, EDGE_UP
	call .Try
.no_down
	bit EDGE_UP_F, c
	jr nz, .walk
	ld a, b
	sub WILD_REACH_WIDTH
	ld l, a
	ld a, EDGE_DOWN
	call .Try
	jr .walk

.Try:
; Reach tile l, coming in by side a, if you can.
	or (1 << WILD_REACH_REACHED_F) | (1 << WILD_REACH_WALKABLE_F)
	and [hl]
	cp 1 << WILD_REACH_WALKABLE_F
	ret nz
	set WILD_REACH_REACHED_F, [hl]
	ld a, [wWildMonReachWrite]
	push de
	ld e, a
	ld a, l
	ld [de], a
	inc e
	ld a, e
	ld [wWildMonReachWrite], a
	pop de
	ret

.Walls:
; b tiles' permissions from hl become WALL_TILE.
	ld a, WALL_TILE
.wall
	ld [hli], a
	dec b
	jr nz, .wall
	ret

.Occupied:
; Someone stands at (d, e): you can't walk there.
	ld a, [wWildReachPlayerX]
	sub WILD_REACH_LEFT
	ld b, a
	ld a, d
	sub b
	cp WILD_REACH_WIDTH
	ret nc
	ld b, a
	ld a, [wWildReachPlayerY]
	sub WILD_REACH_UP
	ld c, a
	ld a, e
	sub c
	cp WILD_REACH_HEIGHT
	ret nc
	ld c, a
	call .Index
	res WILD_REACH_WALKABLE_F, [hl]
	ret

.Index::
; hl = the tile at (b, c) in the window. Keeps bc and de.
	assert WILD_REACH_WIDTH == 15 && WILD_REACH_HEIGHT < 16
	ld a, c
	swap a
	sub c
	add b
	ld l, a
	ld h, HIGH(wWildMonReach)
	assert LOW(wWildMonReach) == 0
	ret

IsWildMonSpotReached:
; Carry if ComputeWildMonReach reached (d, e). Keeps de.
	ld a, [wPlayerMapX]
	sub WILD_REACH_LEFT
	ld b, a
	ld a, d
	sub b
	cp WILD_REACH_WIDTH
	ret nc
	ld b, a
	ld a, [wPlayerMapY]
	sub WILD_REACH_UP
	ld c, a
	ld a, e
	sub c
	cp WILD_REACH_HEIGHT
	ret nc
	ld c, a
	call ComputeWildMonReach.Index
	ld a, BANK(wWildMonReach)
	call GetFarWRAMByte
	add a ; WILD_REACH_REACHED_F into carry
	assert WILD_REACH_REACHED_F == 7
	ret

EdgeWallSides:
; the sides of each tile collision from COLL_RIGHT_WALL with a wall along them
	db EDGE_RIGHT              ; COLL_RIGHT_WALL
	db EDGE_LEFT               ; COLL_LEFT_WALL
	db EDGE_UP                 ; COLL_TOP_WALL
	db EDGE_DOWN               ; COLL_BOTTOM_WALL
	db EDGE_DOWN | EDGE_RIGHT  ; COLL_BOTTOM_RIGHT_WALL
	db EDGE_DOWN | EDGE_LEFT   ; COLL_BOTTOM_LEFT_WALL
	db EDGE_UP | EDGE_RIGHT    ; COLL_TOP_RIGHT_WALL
	db EDGE_UP | EDGE_LEFT     ; COLL_TOP_LEFT_WALL
	db EDGE_RIGHT              ; COLL_RIGHT_WALL_GLOW
	db EDGE_LEFT               ; COLL_LEFT_WALL_GLOW
.End:
	assert COLL_LEFT_WALL_GLOW == COLL_RIGHT_WALL + .End - EdgeWallSides - 1

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
; steps (with speed), or carry to stand a while. Repel takes priority.
	ld a, [wScriptRunning]
	and a
	jmp nz, WildMonWait ; everyone stays put during events
	ld hl, OBJECT_MAP_OBJECT_INDEX
	add hl, bc
	ld a, [hl]
	sub FIRST_WILD_OBJECT
	cp NUM_WILD_MONS
	jmp nc, WildMonWait
	call GetWildMonSlot
	ld a, [hl]
	and a
	jmp z, WildMonWait
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
	call WildMonPlayerOffset
	ld a, d
	call WildMonAbs
	cp WILD_MON_FLEE_DISTANCE + 1
	jr nc, .not_scared
	ld h, a
	ld a, e
	call WildMonAbs
	cp WILD_MON_FLEE_DISTANCE + 1
	jr nc, .not_scared
	ld l, a
	push hl
	ld hl, OBJECT_RANGE
	add hl, bc
	ld [hl], 1 << WILD_STEP_REPEL_F
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
	ld [hl], 0
	ld hl, OBJECT_FLAGS1
	add hl, bc
	res MOVE_ANYWHERE_F, [hl]
	ld hl, OBJECT_MAP_OBJECT_INDEX
	add hl, bc
	ld a, [hl]
	sub FIRST_WILD_OBJECT
	call GetWildMonSlot
	ld de, WILDMON_TRAITS
	add hl, de
	jmp ResolveWildMonBehavior

WildMonWander:
	call Random
	cp 25 percent
	jr c, WildMonWait
	and 3 ; any direction
	ret

WildMonWait:
	scf
	ret

WildMonPlayerOffset:
; d = its x - the player's, e = its y - the player's
	ld a, [wPlayerMapX]
	ld d, a
	ld a, [wPlayerMapY]
	ld e, a

WildMonTargetOffset:
; d/e entered as target x/y, returned as actor x/y minus target x/y.
	ld hl, OBJECT_MAP_X
WildMonOffsetFrom:
	add hl, bc
	assert OBJECT_MAP_Y == OBJECT_MAP_X + 1
	ld a, [hli]
	sub d
	ld d, a
	ld a, [hl]
	sub e
	ld e, a
	ret

WildMonAbs:
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
	bit WILD_STEP_TERRITORY_F, [hl]
	jr z, .check_habitat
	call WildMonHomeOffset
	call WildMonDistance
	cp WILD_TERRITORY_RADIUS + 1
	jr c, .territory_ok
	; Repel can push it out of its territory. Let it walk back toward home.
	push af
	assert OBJECT_LAST_MAP_Y == OBJECT_LAST_MAP_X + 1
	ld a, OBJECT_LAST_MAP_X
	call WildMonHomeOffsetFrom
	call WildMonDistance
	ld d, a
	pop af
	cp d
	jr nc, .no
.territory_ok
	ld hl, OBJECT_RANGE
	add hl, bc
.check_habitat
	bit WILD_STEP_REPEL_F, [hl]
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
	; A lunge at the player never occupies their tile, even if the follower
	; is sharing it after a transition or turn.
	ld hl, OBJECT_RANGE
	add hl, bc
	bit WILD_STEP_ATTACK_F, [hl]
	jr z, .check_follower
	ld a, [wPlayerMapX]
	cp d
	jr nz, .check_follower
	ld a, [wPlayerMapY]
	cp e
	ret z
.check_follower
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

; Today's rare Pokemon (the TV news): each day one of these is out on its
; map, among the wild Pokemon you can see. A quarter of the ones that come
; there (on land) are it, at the level the one it replaces would have had,
; one at a time; like a roaming legendary, it takes the place of the one
; furthest from you if every slot is full. The day comes from the clock's day
; count (wRTCDayLo, 0-139), so nothing is saved.
DEF NUM_SIGHTINGS EQU 14
	assert WORLD_CLOCK_DAYS % NUM_SIGHTINGS == 0 ; sightings continue in order at the wrap
DEF SIGHTING_CHANCE EQU 25 percent

Sightings:
	table_width 3
	map_id ROUTE_29
	db EEVEE
	map_id ROUTE_32
	db CHANSEY
	map_id ROUTE_35
	db SCYTHER
	map_id ROUTE_36
	db PINSIR
	map_id ROUTE_38
	db SNORLAX
	map_id ROUTE_43
	db HERACROSS
	map_id ROUTE_45
	db LARVITAR
	map_id ROUTE_1
	db PIKACHU
	map_id ROUTE_10_NORTH
	db ELECTABUZZ
	map_id ROUTE_13
	db KANGASKHAN
	map_id ROUTE_15
	db TAUROS
	map_id ROUTE_24
	db SMEARGLE
	map_id ROUTE_26
	db SKARMORY
	map_id ROUTE_46
	db PHANPY
	assert_table_length NUM_SIGHTINGS

GetTodaysSighting:
; hl = today's Sightings entry.
	ld a, [wRTCDayLo]
.mod
	sub NUM_SIGHTINGS
	jr nc, .mod
	add NUM_SIGHTINGS
	ld hl, Sightings
	ld bc, 3
	rst AddNTimes
	ret

IsOnSightingMap:
; Return z, with hl at the species, if the player is on land on today's
; rare Pokemon's map.
	call GetPlayerStandingTile
	dec a ; cp WATER_TILE
	jr z, .no
	call GetTodaysSighting
	ld a, [wMapGroup]
	cp [hl]
	ret nz
	inc hl
	ld a, [wMapNumber]
	cp [hl]
	ret nz
	inc hl
	ret

.no
	or 1
	ret

IsTodaysSighting:
; Return z if species a is today's rare Pokemon and the player is on its map.
; Preserves bc, de and hl.
	push hl
	push bc
	ld b, a
	call IsOnSightingMap
	jr nz, .done
	ld a, [hl]
	cp b
.done
	pop bc
	pop hl
	ret

IsSpeciesOut:
; Return z if a wild Pokemon of species a is out.
	ld b, a
	ld hl, wWildMons
	ld de, WILDMON_LENGTH
	ld c, NUM_WILD_MONS
.loop
	ld a, [hl]
	cp b
	ret z
	add hl, de
	dec c
	jr nz, .loop
	or 1
	ret

ApplyTodaysSighting:
; The wild Pokemon just chosen may be today's rare one instead.
	ld a, [wBattleType]
	cp BATTLETYPE_ROAMING
	ret z
	call IsOnSightingMap
	ret nz
	ld a, [hl]
	call IsSpeciesOut
	ret z ; one at a time
	call Random
	cp SIGHTING_CHANCE
	ret nc
.it
	call IsOnSightingMap
	ld a, [hl]
	ld [wTempWildMonSpecies], a
	xor a ; plain form (all of them are below 256)
	ld [wWildMonForm], a
	ret

TrySightingWhenFull:
; Every slot is out: return z with today's rare Pokemon chosen if it comes now
; (when a random encounter would have, a quarter of the time).
	call IsOnSightingMap
	ret nz
	ld a, [hl]
	call IsSpeciesOut
	jr z, .no
	xor a ; with the encounter chance
	farcall TryWildSpawn
	ret nz
	call Random
	cp SIGHTING_CHANCE
	jr nc, .no
	xor a ; BATTLETYPE_NORMAL
	ld [wBattleType], a
	call ApplyTodaysSighting.it
	xor a
	ret

.no
	or 1
	ret

GetTodaysSightingNames::
; For the TV news: today's rare Pokemon's name in wStringBuffer3, and where
; it's been spotted in wStringBuffer4.
	call GetTodaysSighting
	ld a, [hli]
	ld b, a
	ld a, [hli]
	ld c, a
	ld a, [hl]
	ld [wNamedObjectIndex], a
	xor a
	ld [wNamedObjectIndex + 1], a
	push bc
	call GetPokemonName
	ld hl, wStringBuffer1
	ld de, wStringBuffer3
	ld bc, MON_NAME_LENGTH
	rst CopyBytes
	pop bc
	call GetWorldMapLocation
	ld e, a
	farcall GetLandmarkName
	ld hl, wStringBuffer1
	ld de, wStringBuffer4
	ld bc, STRING_BUFFER_LENGTH
	rst CopyBytes
	ret
