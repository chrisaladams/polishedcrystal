GetWildMonTraits:
; Lookup when the spawn is created, once its species and form are settled.
	ld a, [wCurForm]
	and EXTSPECIES_MASK
	jr nz, .passive
	ld a, [wTempWildMonSpecies]
	ld e, a
	ld hl, WildMonTraits
.loop
	ld a, [hli]
	and a
	jr z, .passive
	cp e
	ld a, [hli]
	ret z
	jr .loop
.passive
	xor a
	ret

SetWildHoneyLure::
; Retain the normal Sweet Honey encounter on maps without visible wild mons.
	call CheckVisibleWildMons
	ret nc
	ld a, [wPlayerMapX]
	ld [wWildHoneyX], a
	ld a, [wPlayerMapY]
	ld [wWildHoneyY], a
	ld a, WILD_HONEY_DURATION
	ld [wWildHoneySteps], a
	scf
	ret

ResolveWildMonBehavior:
; hl = this slot's traits, with its alert state in the following byte.
	ld a, [wWildHoneySteps]
	and a
	jr z, .check_night
	bit WILD_HONEY_F, [hl]
	jr z, .check_night
	push hl
	ld a, [wWildHoneyX]
	ld d, a
	ld a, [wWildHoneyY]
	ld e, a
	call WildMonTargetOffset
	call WildMonDistance
	pop hl
	cp 6
	jr nc, .check_night
	inc hl
	ld [hl], 0 ; it loses interest in the player
	cp 2
	jmp c, WildMonWait
	jmp WildMonApproach

.check_night
	bit WILD_NOCTURNAL_F, [hl]
	jr z, .dispatch
	ld a, [wTimeOfDay]
	cp NITE
	jmp nz, WildMonStationary
.dispatch
	ld a, [hli]
	and WILD_BEHAVIOR_MASK
	add a
	ld d, 0
	ld e, a
	push hl
	ld hl, .Profiles
	add hl, de
	ld a, [hli]
	ld h, [hl]
	ld l, a
	pop de ; alert pointer
	jp hl

.Profiles:
	table_width 2
	dw WildMonWander
	dw WildMonTimid
	dw WildMonCurious
	dw WildMonAggressive
	dw WildMonTerritorial
	dw WildMonStationary
	dw WildMonElusive
	dw WildMonSchooling
	assert_table_length WILD_BEHAVIOR_MASK + 1

WildMonStationary:
	call Random
	cp 16 ; a small chance to change tiles
	jmp nc, WildMonWait
	and 3
	ret

WildMonTimid:
	call WildMonNoise
	jmp z, WildMonWander
	ld l, a
	ld h, STEP_WALK << 2
	jr WildMonFlee

WildMonElusive:
	call WildMonNoise
	jmp z, WildMonWait ; give patient players a chance to get close
	inc a
	ld l, a
	ld h, STEP_BIKE << 2

WildMonFlee:
	push hl ; flee radius and speed
	call WildMonPlayerOffset
	call WildMonDistance
	pop hl
	and a
	jmp z, WildMonWait
	cp l
	jmp z, .run
	jmp nc, WildMonWander
.run
	push hl
	call WildMonTowardTarget
	xor 1 ; opposite direction
	pop hl
	or h
	ld hl, OBJECT_RANGE
	add hl, bc
	ld [hl], 1 << WILD_STEP_QUICK_F
	ret

WildMonCurious:
	call WildMonPlayerOffset
	call WildMonDistance
	cp 5
	jmp nc, WildMonWander
	cp 2
	jmp c, WildMonWait
	call WildMonNoise
	jmp nz, WildMonWait

WildMonApproach:
	call WildMonTowardTarget
	ld hl, OBJECT_RANGE
	add hl, bc
	ld [hl], 1 << WILD_STEP_QUICK_F
	and a ; slow step
	ret

WildMonAggressive:
	push de ; alert pointer
	call WildMonPlayerOffset
	call WildMonDistance
	cp 4
	pop hl
	jr c, WildMonPursue
	ld [hl], 0
	jmp WildMonWander

WildMonTerritorial:
	push de ; alert pointer
	ld hl, OBJECT_RANGE
	add hl, bc
	set WILD_STEP_TERRITORY_F, [hl]
	call WildMonHomeOffset
	push de ; actor minus home
	call WildMonPlayerOffset
	pop hl
	ld a, h
	sub d
	ld h, a
	ld a, l
	sub e
	ld l, a ; player minus home
	push de ; actor minus player
	ld d, h
	ld e, l
	call WildMonDistance
	cp WILD_TERRITORY_RADIUS + 1
	pop de
	pop hl
	jr c, WildMonPursue
	ld [hl], 0
	call WildMonHomeOffset
	call WildMonDistance
	jmp z, WildMonWait
	call WildMonTowardTarget
	or STEP_WALK << 2
	ret

WildMonPursue:
; The first reaction is a turn toward the player, followed by a pause.
; Attack steps still go through the habitat and collision checks.
	call WildMonDistance
	jmp z, WildMonWait
	ld a, [hl]
	and a
	jr nz, .pursue
	inc [hl]
	call WildMonTowardTarget
	add a
	add a
	ld hl, OBJECT_DIRECTION
	add hl, bc
	ld [hl], a
	jmp WildMonWait
.pursue
	ld hl, OBJECT_RANGE
	add hl, bc
	set WILD_STEP_QUICK_F, [hl]
	set WILD_STEP_ATTACK_F, [hl]
	call WildMonTowardTarget
	or STEP_WALK << 2
	ret

WildMonSchooling:
; Orient toward the first local schoolmate. The first fish sets the pace.
	call WildMonSchoolmateOffset
	jmp nc, WildMonWander
	call WildMonDistance
	cp 5
	jmp nc, WildMonWander
	cp 2
	jmp c, WildMonWait
	jr z, .alongside
	call WildMonTowardTarget
	and a
	ret
.alongside
	ld a, [hl] ; schoolmate's packed walking direction
	cp STANDING
	jmp z, WildMonWait
	and 3
	ret

WildMonSchoolmateOffset:
; Carry and d/e offset from the first earlier fish with a live object.
; On success hl points to the schoolmate's walking direction.
	ld hl, OBJECT_MAP_OBJECT_INDEX
	add hl, bc
	ld a, [hl]
	sub FIRST_WILD_OBJECT
	ret z
	ld d, a
	ld e, FIRST_WILD_OBJECT
	ld hl, wWildMons
.loop
	ld a, [hl]
	cp MAGIKARP
	jr nz, .next
	inc hl
	bit MON_EXTSPECIES_F, [hl]
	dec hl
	jr nz, .next
	push hl
	push de
	push bc
	ld a, e
	call GetMapObject
	ld hl, MAPOBJECT_OBJECT_STRUCT_ID
	add hl, bc
	ld a, [hl]
	cp NUM_OBJECT_STRUCTS
	jr c, .found
	pop bc
	pop de
	pop hl
.next
	push de
	ld de, WILDMON_LENGTH
	add hl, de
	pop de
	inc e
	dec d
	jr nz, .loop
	and a
	ret
.found
	call GetObjectStruct
	ld hl, OBJECT_MAP_X
	add hl, bc
	ld d, [hl]
	inc hl
	ld e, [hl]
	ld hl, OBJECT_WALKING
	add hl, bc
	pop bc
	pop af
	pop af
	push hl
	call WildMonTargetOffset
	pop hl
	scf
	ret

WildMonNoise:
; The awareness radius for the player's current movement, or zero at rest.
	ldh a, [hJoyDown]
	and PAD_CTRL_PAD
	jr nz, .moving
	ld a, [wPlayerWalking]
	cp STANDING
	jr nz, .moving
	xor a
	ret
.moving
	ld a, [wPlayerState]
	cp PLAYER_RUN
	jr z, .running
	jr c, .quiet
	cp PLAYER_SKATE + 1
	jr nc, .quiet
	ld a, 4
	jr .done
.running
	ld a, 3
	jr .done
.quiet
	ld a, 1 ; walking and surfing
.done
	and a
	ret

WildMonHomeOffset:
	ld a, OBJECT_MAP_X
WildMonHomeOffsetFrom:
	ld hl, OBJECT_INIT_X
	add hl, bc
	assert OBJECT_INIT_Y == OBJECT_INIT_X + 1
	ld d, [hl]
	inc hl
	ld e, [hl]
	ld l, a
	ld h, 0
	jmp WildMonOffsetFrom

WildMonDistance:
; Manhattan distance in tiles. Preserves hl and the signed offset in de.
	push hl
	ld a, d
	call WildMonAbs
	ld l, a
	ld a, e
	call WildMonAbs
	add l
	pop hl
	ret

WildMonTowardTarget:
	ld a, d
	call WildMonAbs
	ld h, a
	ld a, e
	call WildMonAbs
	cp h
	jr z, .horizontal
	jr nc, .vertical
.horizontal
	bit 7, d
	ld a, LEFT
	ret z
	ld a, RIGHT
	ret
.vertical
	bit 7, e
	ld a, UP
	ret z
	ld a, DOWN
	ret

INCLUDE "data/wild/behaviors.asm"
