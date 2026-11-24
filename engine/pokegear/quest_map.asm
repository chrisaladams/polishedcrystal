; The Field Book owns each objective's directions. A map entry adds only its
; landmark and short caption. Multiple entries may share a physical location.
MACRO map_goal
	DEF QMAP_\1 EQU (@ - QuestMapGoals) / 2
	dw QuestMapGoal_\1
ENDM
QuestMapGoals:
INCLUDE "data/events/quest_map_goals.asm"
DEF NUM_QUEST_MAP_GOALS EQU (@ - QuestMapGoals) / 2
	assert NUM_QUEST_MAP_GOALS <= NUM_LANDMARKS
PURGE map_goal
MACRO map_goal
QuestMapGoal_\1:
	dw FieldBookNotes.\1
	db \2, \3, "@"
ENDM
INCLUDE "data/events/quest_map_goals.asm"
PURGE map_goal

QuestMapLookup:
	ld hl, QuestMapGoals
	add a
	add l
	ld l, a
	adc h
	sub l
	ld h, a
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ret

AddQuestMapLead:
	ld d, a
	ld a, [wQuestMapCount]
	ld b, a
	ld hl, wQuestMapLeads
.loop
	ld a, b
	and a
	jr z, .append
	ld a, [hli]
	cp d
	ret z
	dec b
	jr .loop
.append
	ld [hl], d
	ld hl, wQuestMapCount
	inc [hl]
	ret

MACRO map_pending_event
	eventflagcheck \1
	ld a, QMAP_\2
	call z, AddQuestMapLead
ENDM

MACRO map_pending_badge
	flagcheck wJohtoBadges, (\1 - ENGINE_BADGES)
	ld a, QMAP_\2
	call z, AddQuestMapLead
ENDM

BuildQuestMapLeads:
	xor a
	ld [wQuestMapCount], a
	ld [wQuestMapSelected], a
	dec a
	ld [wQuestMapMain], a
	farcall GetCurrentFieldBookPage
	ld d, h
	ld e, l
	ld b, 0
.find_main
	ld a, b
	call QuestMapLookup
	ld a, [hli]
	cp e
	jr nz, .next
	ld a, [hl]
	cp d
	jr z, .main
.next
	inc b
	ld a, b
	cp NUM_QUEST_MAP_GOALS
	jr c, .find_main
	jr .parallel
.main
	ld a, b
	ld [wQuestMapMain], a
	call AddQuestMapLead
.parallel
	eventflagcheck EVENT_GOT_MYSTICTICKET_FROM_RED
	jr nz, .post_red
	eventflagcheck EVENT_BEAT_ELITE_FOUR
	jr nz, .league
	call QuestMapJohtoLeads
	call QuestMapLateJohtoLeads
	jr .errands
.league
	eventflagcheck EVENT_FAST_SHIP_FIRST_TIME
	call nz, QuestMapKantoLeads
	jr .errands
.post_red
	call QuestMapPostRedLeads
.errands
	; Each errand contributes its own current step.
	eventflagcheck EVENT_GOT_HP_UP_FROM_RANDY
	jr nz, .farm
	eventflagcheck EVENT_GAVE_KENYA
	ld a, QMAP_Reward
	jr nz, .mail
	eventflagcheck EVENT_GOT_KENYA
	ld a, QMAP_Deliver
	jr nz, .mail
	flagcheck wVisitedSpawns, SPAWN_GOLDENROD
	jr z, .farm
	ld a, QMAP_Kenya
.mail
	call AddQuestMapLead
.farm
	flagcheck wVisitedSpawns, SPAWN_OLIVINE
	jr z, .doll
	map_pending_event EVENT_HEALED_MOOMOO, Berries
.doll
	eventflagcheck EVENT_RESTORED_POWER_TO_KANTO
	ret z
	eventflagcheck EVENT_GOT_PASS_FROM_COPYCAT
	ret nz
	eventflagcheck EVENT_MET_COPYCAT_FOUND_OUT_ABOUT_LOST_ITEM
	ld a, QMAP_Copycat
	jp z, AddQuestMapLead
	eventflagcheck EVENT_GOT_LOST_ITEM_FROM_FAN_CLUB
	ld a, QMAP_Club
	jp z, AddQuestMapLead
	ld a, QMAP_Pass
	jmp AddQuestMapLead

QuestMapJohtoLeads:
	eventflagcheck EVENT_GAVE_MYSTERY_EGG_TO_ELM
	ret z
	map_pending_event EVENT_GOT_TM70_FLASH, Tower
	eventflagcheck EVENT_VIOLET_GYM_FALKNER
	ld a, QMAP_Cave
	call nz, AddQuestMapLead
	eventflagcheck EVENT_VIOLET_GYM_FALKNER
	jr nz, .azalea
	map_pending_badge ENGINE_ZEPHYRBADGE, Violet
.azalea
	flagcheck wJohtoBadges, (ENGINE_ZEPHYRBADGE - ENGINE_BADGES)
	jr z, .check_well
	map_pending_event EVENT_GOT_TOGEPI_EGG_FROM_ELMS_AIDE, Aide
.check_well
	flagcheck wVisitedSpawns, SPAWN_AZALEA
	jr z, .east
	eventflagcheck EVENT_CLEARED_SLOWPOKE_WELL
	ld a, QMAP_Well
	jr z, .add_azalea
	map_pending_badge ENGINE_HIVEBADGE, Bugsy
	map_pending_event EVENT_GOT_HM01_CUT, Cut
	jr .east
.add_azalea
	call AddQuestMapLead
.east
	flagcheck wVisitedSpawns, SPAWN_GOLDENROD
	call nz, QuestMapGoldenrodLeads
	eventflagcheck EVENT_FOUGHT_SUDOWOODO
	ret z
	eventflagcheck EVENT_RELEASED_THE_BEASTS
	ld a, QMAP_BurnedTower
	call z, AddQuestMapLead
	eventflagcheck EVENT_RELEASED_THE_BEASTS
	jr z, .surf
	map_pending_badge ENGINE_FOGBADGE, Morty
.surf
	map_pending_event EVENT_GOT_HM03_SURF, Surf
	map_pending_event EVENT_JASMINE_EXPLAINED_AMPHYS_SICKNESS, Lighthouse
	flagcheck wJohtoBadges, (ENGINE_FOGBADGE - ENGINE_BADGES)
	ret z
	eventflagcheck EVENT_GOT_HM03_SURF
	ret z
	map_pending_badge ENGINE_STORMBADGE, Chuck
	eventflagcheck EVENT_JASMINE_EXPLAINED_AMPHYS_SICKNESS
	jr z, .lake
	eventflagcheck EVENT_GOT_SECRETPOTION_FROM_PHARMACY
	ld a, QMAP_Medicine
	jr z, .add_lighthouse
	eventflagcheck EVENT_JASMINE_RETURNED_TO_GYM
	ld a, QMAP_Amphy
	jr z, .add_lighthouse
	map_pending_badge ENGINE_MINERALBADGE, Jasmine
	jr .lake
.add_lighthouse
	call AddQuestMapLead
.lake
	eventflagcheck EVENT_DECIDED_TO_HELP_LANCE
	ld a, QMAP_Lake
	jp z, AddQuestMapLead
	eventflagcheck EVENT_CLEARED_ROCKET_HIDEOUT
	ld a, QMAP_Hideout
	jp z, AddQuestMapLead
	map_pending_badge ENGINE_GLACIERBADGE, Pryce
	ret

QuestMapGoldenrodLeads:
	flagcheck wPokegearFlags, POKEGEAR_RADIO_CARD_F
	ld a, QMAP_Quiz
	jp z, AddQuestMapLead
	flagcheck wJohtoBadges, (ENGINE_PLAINBADGE - ENGINE_BADGES)
	ld a, QMAP_Whitney
	jp z, AddQuestMapLead
	eventflagcheck EVENT_FOUGHT_SUDOWOODO
	ret nz
	eventflagcheck EVENT_GOT_SQUIRTBOTTLE
	ld a, QMAP_Bottle
	jp z, AddQuestMapLead
	ld a, QMAP_Tree
	jmp AddQuestMapLead

QuestMapLateJohtoLeads:
	eventflagcheck EVENT_CLEARED_RADIO_TOWER
	ret z
	map_pending_event EVENT_GOT_HM06_WATERFALL, Waterfall
	eventflagcheck EVENT_BEAT_CLAIR
	ld a, QMAP_Clair
	jp z, AddQuestMapLead
	map_pending_badge ENGINE_RISINGBADGE, DragonDen
	ret

QuestMapKantoLeads:
	map_pending_badge ENGINE_THUNDERBADGE, Surge
	map_pending_badge ENGINE_MARSHBADGE, Sabrina
	map_pending_badge ENGINE_RAINBOWBADGE, Erika
	map_pending_badge ENGINE_SOULBADGE, Janine
	eventflagcheck EVENT_RESTORED_POWER_TO_KANTO
	jr nz, .restored
	eventflagcheck EVENT_MET_MANAGER_AT_POWER_PLANT
	ld a, QMAP_Plant
	jp z, AddQuestMapLead
	eventflagcheck EVENT_MET_ROCKET_GRUNT_AT_CERULEAN_GYM
	ld a, QMAP_Grunt
	jp z, AddQuestMapLead
	eventflagcheck EVENT_LEARNED_ABOUT_MACHINE_PART
	ld a, QMAP_Bridge
	jp z, AddQuestMapLead
	eventflagcheck EVENT_FOUND_MACHINE_PART_IN_CERULEAN_GYM
	ld a, QMAP_Part
	jp z, AddQuestMapLead
	ld a, QMAP_Restore
	jmp AddQuestMapLead
.restored
	eventflagcheck EVENT_TRAINERS_IN_CERULEAN_GYM
	jr z, .misty
	ld a, QMAP_Cape
	call AddQuestMapLead
	jr .radio
.misty
	map_pending_badge ENGINE_CASCADEBADGE, Misty
.radio
	flagcheck wPokegearFlags, POKEGEAR_EXPN_CARD_F
	ld a, QMAP_Radio
	jp z, AddQuestMapLead
	eventflagcheck EVENT_FOUGHT_SNORLAX
	ld a, QMAP_Flute
	jp z, AddQuestMapLead
	map_pending_badge ENGINE_BOULDERBADGE, Brock
	map_pending_badge ENGINE_VOLCANOBADGE, Blaine
	ret

QuestMapPostRedLeads:
	eventflagcheck EVENT_RESCUED_PROF_HALE
	jr nz, .ilex
	eventflagcheck EVENT_BEAT_MOLLY
	ld a, QMAP_Alph
	jr z, .ruins
	ld a, QMAP_Hale
.ruins
	call AddQuestMapLead
.ilex
	eventflagcheck EVENT_BEAT_IRON_MASK_MARAUDER
	jr nz, .cave
	eventflagcheck EVENT_TIME_TRAVEL_FINISHED
	ld a, QMAP_Shrine
	jr z, .forest
	ld a, QMAP_Mask
.forest
	call AddQuestMapLead
.cave
	eventflagcheck EVENT_BEAT_MEWTWO_CLONES
	jr nz, .islands
	eventflagcheck EVENT_READ_CINNABAR_CLONE_REPORT
	ld a, QMAP_CloneReport
	jr z, .clone_lead
	ld a, QMAP_Echo
.clone_lead
	call AddQuestMapLead
.islands
	call QuestMapShamoutiLeads
	map_pending_event EVENT_WON_WHIRL_CUP, Cup
	eventflagcheck EVENT_BEAT_DRAKE
	ret nz ; the book already includes Pallet when all the stories are finished
	map_pending_event EVENT_BEAT_ORANGE_CREW_CISSY, Cissy
	map_pending_event EVENT_BEAT_ORANGE_CREW_DANNY, Danny
	map_pending_event EVENT_BEAT_ORANGE_CREW_RUDY, Rudy
	map_pending_event EVENT_BEAT_ORANGE_CREW_LUANA, Luana
	eventflagcheck EVENT_BEAT_ORANGE_CREW_CISSY
	ret z
	eventflagcheck EVENT_BEAT_ORANGE_CREW_DANNY
	ret z
	eventflagcheck EVENT_BEAT_ORANGE_CREW_RUDY
	ret z
	eventflagcheck EVENT_BEAT_ORANGE_CREW_LUANA
	ret z
	ld a, QMAP_Drake
	jmp AddQuestMapLead

QuestMapShamoutiLeads:
	eventflagcheck EVENT_RESTORED_SHAMOUTI_BEACONS
	jr nz, .guardian
	eventflagcheck EVENT_HEARD_SHAMOUTI_BEACONS
	jr nz, .beacons
	eventflagcheck EVENT_GOT_ORANGE_TICKET
	ret z
	ld a, QMAP_ShoreKeeper
	jmp AddQuestMapLead
.beacons
	map_pending_event EVENT_TUNED_FIRE_BEACON, FireBeacon
	map_pending_event EVENT_TUNED_ICE_BEACON, IceBeacon
	map_pending_event EVENT_TUNED_LIGHTNING_BEACON, LightningBeacon
	eventflagcheck EVENT_TUNED_FIRE_BEACON
	ret z
	eventflagcheck EVENT_TUNED_ICE_BEACON
	ret z
	eventflagcheck EVENT_TUNED_LIGHTNING_BEACON
	ret z
	ld a, QMAP_ShoreReturn
	jmp AddQuestMapLead
.guardian
	map_pending_event EVENT_FOUGHT_LUGIA, SeaGuardian
	ret

; Return HL at the caption and E at its landmark. Until the Valencia ferry
; opens, Luana's actionable first stop is Ivy at Shamouti's Pokémon Center.
QuestMapLocation:
	cp QMAP_Luana
	jr nz, .normal
	eventflagcheck EVENT_GOT_A_POKEMON_FROM_IVY
	jr nz, .normal
	ld e, SHAMOUTI_ISLAND
	ld hl, .Ivy
	ret
.normal
	call QuestMapLookup
	inc hl
	inc hl
	ld e, [hl]
	inc hl
	ret
.Ivy: db "Meet Ivy for Luana@"

QuestMapGetRegion:
	ld a, e
	cp KANTO_LANDMARK
	ld a, JOHTO_REGION
	ret c
	ld a, e
	cp SHAMOUTI_LANDMARK
	ld a, KANTO_REGION
	ret c
	ld a, ORANGE_REGION
	ret

DrawLocalQuestMapPins:
	ld a, [wPokegearMapPlayerIconLandmark]
	ld e, a
	call QuestMapGetRegion
	ld [wQuestMapRegion], a
	ld a, [wQuestMapMain]
	call DrawQuestMapPins
	hlcoord 3, 2
	ld de, .Hint
	rst PlaceString
	hlcoord 3, 2, wAttrmap
	ld bc, 14
	xor a
	rst ByteFill
	ret
.Hint: db "SELECT: Quests@"

; Draw every open lead on this regional map, then its focus on top so two
; goals sharing a tile stay individually selectable without hiding the focus.
DrawQuestMapPins:
	push af
	ld a, [wQuestMapCount]
	ld b, a
	ld hl, wQuestMapLeads
.loop
	ld a, b
	and a
	jr z, .focus
	push bc
	ld a, [hli]
	push hl
	ld c, '!'
	call .pin
	pop hl
	pop bc
	dec b
	jr .loop
.focus
	pop af
	cp $ff
	ret z
	ld c, '★'
.pin
	push bc
	call QuestMapLocation
	call QuestMapGetRegion
	ld hl, wQuestMapRegion
	cp [hl]
	jr nz, .skip
	farcall GetLandmarkCoords
	ld a, d
	sub 16
	srl a
	srl a
	srl a
	ld hl, wTilemap
	ld bc, SCREEN_WIDTH
	rst AddNTimes
	ld a, e
	sub 8
	srl a
	srl a
	srl a
	ld e, a
	ld d, 0
	add hl, de
	pop bc
	ld [hl], c
	ld de, wAttrmap - wTilemap
	add hl, de
	ld [hl], 0 ; use an upright font tile, independent of terrain flips
	ret
.skip
	pop bc
	ret

BrowseQuestMap:
	call ClearSprites
	xor a
	ld [wQuestMapSelected], a
.redraw
	call DrawQuestMapBrowser
.input
	call DelayFrame
	call GetJoypad
	ldh a, [hJoyPressed]
	and PAD_B | PAD_SELECT
	ret nz
	ld a, [wQuestMapCount]
	and a
	jr z, .input
	ld b, a
	ldh a, [hJoyPressed]
	bit B_PAD_A, a
	jr nz, .read
	and PAD_DOWN | PAD_RIGHT
	jr nz, .next
	ldh a, [hJoyPressed]
	and PAD_UP | PAD_LEFT
	jr z, .input
	ld hl, wQuestMapSelected
	ld a, [hl]
	and a
	jr nz, .prev
	ld [hl], b
.prev
	dec [hl]
	jr .redraw
.next
	ld hl, wQuestMapSelected
	inc [hl]
	ld a, [hl]
	cp b
	jr c, .redraw
	xor a
	ld [hl], a
	jr .redraw
.read
	call SelectedQuestMapGoal
	call QuestMapLookup
	ld a, [hli]
	ld h, [hl]
	ld l, a
	ld a, BANK(FieldBookNotes)
	call FarPrintText
	call WaitPressAorB_BlinkCursor
	jr .redraw

SelectedQuestMapGoal:
	ld a, [wQuestMapSelected]
	ld e, a
	ld d, 0
	ld hl, wQuestMapLeads
	add hl, de
	ld a, [hl]
	ret

DrawQuestMapBrowser:
	ld a, [wQuestMapCount]
	and a
	jr z, .background
	call SelectedQuestMapGoal
	call QuestMapLocation
	call QuestMapGetRegion
	ld [wQuestMapRegion], a
.background
	ld a, [wQuestMapRegion]
	cp ORANGE_REGION
	jr z, .orange
	cp KANTO_REGION
	jr z, .kanto
	farcall FillJohtoMap
	farcall TownMapPals
	farcall TownMapJohtoFlips
	ld de, .Johto
	jr .header
.kanto
	farcall FillKantoMap
	farcall TownMapPals
	farcall TownMapKantoFlips
	ld de, .Kanto
	jr .header
.orange
	farcall FillOrangeMap
	farcall TownMapPals
	farcall TownMapOrangeFlips
	ld de, .Orange
.header
	push de
	ld hl, wTilemap
	ld bc, SCREEN_WIDTH * 3
	ld a, ' '
	rst ByteFill
	ld hl, wAttrmap
	ld bc, SCREEN_WIDTH * 3
	xor a
	rst ByteFill
	hlcoord 0, 17
	ld bc, SCREEN_WIDTH
	ld a, ' '
	rst ByteFill
	hlcoord 0, 17, wAttrmap
	ld bc, SCREEN_WIDTH
	xor a
	rst ByteFill
	pop de
	hlcoord 0, 0
	rst PlaceString
	ld a, [wQuestMapCount]
	and a
	jr z, .empty
	call SelectedQuestMapGoal
	push af
	call QuestMapLocation
	ld d, h
	ld e, l
	hlcoord 0, 1
	rst PlaceString
	pop af
	call DrawQuestMapPins
	hlcoord 0, 2
	ld de, .Controls
	rst PlaceString
	hlcoord 0, 17
	ld de, .Legend
	jr .finish
.empty
	hlcoord 0, 1
	ld de, .NoLeads
.finish
	rst PlaceString
	jmp ApplyAttrAndTilemapInVBlank
.Johto: db "Johto / Quest map@"
.Kanto: db "Kanto / Quest map@"
.Orange: db "Orange / Quest map@"
.Controls: db "▲▼Goal A:Read B:Back@"
.Legend: db "★ Selected   ! Open@"
.NoLeads: db "No open leads. B:OK@"
