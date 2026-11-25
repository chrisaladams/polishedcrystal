; Link Edition: bedroom achievements. Beside the Indigo Plateau's trophies,
; the Orange Trophy (yours once Drake is beaten) and the Cup Trophy (once
; you've won a cup: bronze, then silver at three cups, gold at all six) are
; bedroom ornaments, and the Adventure Album (the bedroom PC) lists what
; you've done. All of it reads the story flags and cup records already kept,
; so an older save's wins count too, and nothing new is saved.

DEF NUM_ALBUM_CUPS EQU 6

CountCupsWon::
; a = how many of the six cups you've won.
	farcall CupCheckRecords
	ld a, [wCupRecords]
	ld b, 0
	ld c, a
	ld a, 1 << CUPWON_RISING_STAR_F | 1 << CUPWON_DRAGON_F | 1 << CUPWON_RENTAL_F | 1 << CUPWON_WORLD_F
	and c
.bits
	jr z, .whirl
	srl a
	jr nc, .bits
	inc b
	and a
	jr .bits
.whirl
	push bc
	ld de, EVENT_WON_WHIRL_CUP
	ld b, CHECK_FLAG
	call EventFlagAction
	pop bc
	and a
	jr z, .kimono
	inc b
.kimono
	ld a, [wCupRecords + 1]
	ld c, a
	ld a, [wCupRecords + 2]
	or c
	ld c, a
	ld a, [wCupRecords + 3]
	or c
	jr z, .done
	inc b
.done
	ld a, b
	ret

CupTrophySprite::
; a = the Cup Trophy's sprite: bronze for one or two cups, silver for three to
; five, gold for all six.
	call CountCupsWon
	cp 3
	ld a, SPRITE_BRONZE_TROPHY
	ret c
	call CountCupsWon
	cp NUM_ALBUM_CUPS
	ld a, SPRITE_SILVER_TROPHY
	ret c
	ld a, SPRITE_GOLD_TROPHY
	ret

CupTrophyDescScript::
	callasm .Describe
	jumptext .Text

.Describe:
	call CountCupsWon
	ldh [hScriptVar], a
	ld hl, .Bronze
	cp 3
	jr c, .got
	ld hl, .Silver
	cp NUM_ALBUM_CUPS
	jr c, .got
	ld hl, .Gold
.got
	ld de, wStringBuffer3
	ld bc, 7
	rst CopyBytes
	ret

.Bronze: db "bronze@"
.Silver: db "silver@"
.Gold:   db "gold@  "

.Text:
	text "It's the "
	line "@"
	text_ram wStringBuffer3
	text " Cup Trophy:"
	para "@"
	text_decimal hScriptVar, 1, 1
	text " of 6 cups won."
	done

; The Adventure Album (the bedroom bookshelf): a page each for the leagues,
; the movie stories and the cups, a star by each one done.

	const_def
	const ALBUM_EVENT ; done if the event flag is set
	const ALBUM_CUP   ; done if the wCupRecords bit is set
	const ALBUM_COUNT ; a count of AlbumCounts' kind, done when full

MACRO album
; kind, flag/bit/count, name
	db \1
	dw \2
	db \3, "@"
ENDM

	const_def
	const ALBUMCOUNT_BADGES
	const ALBUMCOUNT_CREW
	const ALBUMCOUNT_KIMONO

Special_AdventureAlbum::
	call FadeToMenu_BackupSprites
	call LoadStandardFont
	call LoadFrame
	call _AdventureAlbum
	jmp ExitAllMenus

_AdventureAlbum:
	farcall CupCheckRecords
	ld hl, AlbumPages
.page
	ld a, [hli]
	ld e, a
	ld a, [hli]
	ld d, a
	or e
	ret z
	push hl
	call AlbumShowPage
	pop hl
	jr .page

AlbumShowPage:
; Show the page at de, and wait for a button.
	push de
	call ClearTileMap
	call ClearSprites
	hlcoord 0, 0
	lb bc, SCREEN_HEIGHT - 2, SCREEN_WIDTH - 2
	call Textbox
	pop de
	hlcoord 2, 1
	call AlbumPlaceString
	hlcoord 1, 3
.entry
	ld a, [de]
	cp -1
	jr z, .shown
	push hl
	call AlbumEntry
	pop hl
	ld bc, SCREEN_WIDTH * 2
	add hl, bc
	jr .entry
.shown
	hlcoord 0, 0, wAttrmap
	xor a
	ld bc, SCREEN_AREA
	rst ByteFill
	call ApplyAttrAndTilemapInVBlank
	ld a, CGB_PLAIN
	call GetCGBLayout
	call SetDefaultBGPAndOBP
	ld c, 8
	call DelayFrames
	jmp WaitPressAorB_BlinkCursor

AlbumPlaceString:
; Place the string at de at hl; de = after it.
	push hl
	rst PlaceString
	pop hl
.skip
	ld a, [de]
	inc de
	cp '@'
	jr nz, .skip
	ret

AlbumEntry:
; Show the entry at de at hl (its star, name and any count); de = the next.
	ld a, [de] ; kind
	inc de
	ld c, a
	ld a, [de]
	inc de
	ld b, a ; flag, bit or count kind (low byte)
	ld a, [de]
	inc de
	push hl
	push de
	ld e, b
	ld d, a
	ld a, c
	cp ALBUM_COUNT
	jr z, .count
	cp ALBUM_CUP
	jr z, .cup
	ld b, CHECK_FLAG
	call EventFlagAction
	and a
	jr .star

.cup
	ld a, [wCupRecords]
	ld c, e
	inc c
.shift
	dec c
	jr z, .bit
	rrca
	jr .shift
.bit
	and 1
	jr .star

.count
	ld a, e
	call AlbumCount ; b = count, c = how many make it full
	ld a, b
	ldh [hScriptVar], a
	ld a, c
	ld [wStringBuffer4], a
	pop de
	pop hl
	push hl
	push de
	; "n/m" against the right edge: columns 14-18, or 16-18 for one digit
	ld a, c
	cp 10
	ld bc, 13
	ld d, 2
	jr nc, .place
	ld bc, 15
	ld d, 1
.place
	add hl, bc
	ld b, 1
	ld c, d
	push bc
	ld de, hScriptVar
	call PrintNum
	ld [hl], '/'
	inc hl
	pop bc
	ld de, wStringBuffer4
	call PrintNum
	ld a, [wStringBuffer4]
	ld b, a
	ldh a, [hScriptVar]
	cp b
	ld a, 0
	jr nz, .star
	inc a
.star
	pop de
	pop hl
	and a
	ld a, '-'
	jr z, .mark
	ld a, '★'
.mark
	ld [hli], a
	inc hl
	jmp AlbumPlaceString

AlbumCount:
; b = the count of kind a, c = the most it can be.
	and a
	jr nz, .not_badges
	ld hl, wBadges
	ld b, wBadgesEnd - wBadges
	call CountSetBits
	ld b, a
	ld c, NUM_BADGES
	ret

.not_badges
	dec a
	jr nz, .kimono
	ld b, 0
	ld de, EVENT_BEAT_ORANGE_CREW_CISSY
	assert EVENT_BEAT_ORANGE_CREW_DANNY == EVENT_BEAT_ORANGE_CREW_CISSY + 1
	assert EVENT_BEAT_ORANGE_CREW_RUDY == EVENT_BEAT_ORANGE_CREW_CISSY + 2
	assert EVENT_BEAT_ORANGE_CREW_LUANA == EVENT_BEAT_ORANGE_CREW_CISSY + 3
	ld c, 4
.crew
	push bc
	push de
	ld b, CHECK_FLAG
	call EventFlagAction
	pop de
	pop bc
	and a
	jr z, .next_crew
	inc b
.next_crew
	inc de
	dec c
	jr nz, .crew
	ld c, 4
	ret

.kimono
	ld hl, wCupRecords + 1
	ld b, 3
	call CountSetBits
	ld b, a
	ld c, NUM_KIMONO_TYPES
	ret

AlbumPages:
	dw .Leagues, .Stories, .Cups
	dw 0

.Leagues:
	db "Leagues@"
	album ALBUM_EVENT, EVENT_BEAT_ELITE_FOUR,           "Elite Four"
	album ALBUM_COUNT, ALBUMCOUNT_BADGES,               "Badges"
	album ALBUM_EVENT, EVENT_BEAT_RED,                  "Red"
	album ALBUM_EVENT, EVENT_BEAT_LEAF,                 "Leaf"
	album ALBUM_COUNT, ALBUMCOUNT_CREW,                 "Orange Crew"
	album ALBUM_EVENT, EVENT_BEAT_DRAKE,                "Drake"
	db -1

.Stories:
	db "Stories@"
	album ALBUM_EVENT, EVENT_BEAT_MEWTWO_CLONES,        "Mewtwo's clones"
	album ALBUM_EVENT, EVENT_RESTORED_SHAMOUTI_BEACONS, "The beacons"
	album ALBUM_EVENT, EVENT_BEAT_LAWRENCE,             "Lawrence III"
	album ALBUM_EVENT, EVENT_RESCUED_PROF_HALE,         "Prof. Hale"
	album ALBUM_EVENT, EVENT_BEAT_IRON_MASK_MARAUDER,   "The Marauder"
	album ALBUM_EVENT, EVENT_OAK_WAS_SAMMY,             "Sammy"
	db -1

.Cups:
	db "Cups@"
	album ALBUM_CUP,   CUPWON_RISING_STAR_F,            "Rising Star"
	album ALBUM_EVENT, EVENT_WON_WHIRL_CUP,             "Whirl"
	album ALBUM_COUNT, ALBUMCOUNT_KIMONO,               "Kimono"
	album ALBUM_CUP,   CUPWON_DRAGON_F,                 "Dragon Masters"
	album ALBUM_CUP,   CUPWON_RENTAL_F,                 "Rental"
	album ALBUM_CUP,   CUPWON_WORLD_F,                  "World"
	db -1
