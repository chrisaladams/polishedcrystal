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
	; (and how many of the Kimono Cup's 18 types: the cup counts once won,
	; mastering it is all 18, as the Adventure Album shows)
	farcall CupCheckRecords
	ld a, ALBUMCOUNT_KIMONO
	call AlbumCount
	ld a, b
	ld [wStringBuffer4], a
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
	text " of 6 cups won,"
	line "@"
	text_decimal wStringBuffer4, 1, 2
	text " of 18 Kimono"
	cont "types."
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

OrangeCrewTally::
; Link Edition: after a Crew badge, how many of the four you have (as the
; Adventure Album counts them).
	callasm .Count
	ifequalfwd 4, .All
	writetext .Text
	promptbutton
	end
.All:
	writetext .AllText
	promptbutton
	end

.Count:
	ld a, ALBUMCOUNT_CREW
	call AlbumCount
	ld a, b
	ldh [hScriptVar], a
	ret

.Text:
	text "That's @"
	text_decimal hScriptVar, 1, 1
	text " of the"
	line "four Crew badges."
	done

.AllText:
	text "That's all four"
	line "Crew badges!"
	done

Special_AdventureAlbum::
	call FadeToMenu_BackupSprites
	call LoadStandardFont
	call LoadFrame
	call _AdventureAlbum
	jmp ExitAllMenus

DEF NUM_ALBUM_PAGES EQU 3

_AdventureAlbum:
; A or Right: the next page (after the last, the album closes); Left: the
; one before; B: close.
	farcall CupCheckRecords
	xor a
.page
	push af
	call AlbumShowPage
	ld b, a
	pop af
	bit B_PAD_B, b
	ret nz
	bit B_PAD_LEFT, b
	jr z, .forward
	and a
	jr z, .page
	dec a
	jr .page
.forward
	inc a
	cp NUM_ALBUM_PAGES
	jr c, .page
	ret

AlbumShowPage:
; Show page a (from 0), marked "n/N"; a = the button pressed.
	push af
	call ClearTileMap
	call ClearSprites
	hlcoord 0, 0
	lb bc, SCREEN_HEIGHT - 2, SCREEN_WIDTH - 2
	call Textbox
	pop af
	hlcoord 16, 1
	push af
	add '1'
	ld [hli], a
	ld a, '/'
	ld [hli], a
	ld [hl], '0' + NUM_ALBUM_PAGES
	pop af
	add a
	ld e, a
	ld d, 0
	ld hl, AlbumPages
	add hl, de
	ld a, [hli]
	ld d, [hl]
	ld e, a
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
.wait
	call DelayFrame
	call GetJoypad
	ldh a, [hJoyPressed]
	and PAD_A | PAD_B | PAD_LEFT | PAD_RIGHT
	jr z, .wait
	ret

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
	table_width 2
	dw .Leagues, .Stories, .Cups
	assert_table_length NUM_ALBUM_PAGES

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
