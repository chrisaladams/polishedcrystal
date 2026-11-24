ReadFieldBook:
	opentext
	loadmenu .Contents
	verticalmenu
	closewindow
	ifequalfwd 1, .Next
	ifequalfwd 2, .CatchUp
	ifequal 3, FieldBookSideQuests
	endtext

.Contents:
	db MENU_BACKUP_TILES
	menu_coords 0, 0, 14, 7
	dw .Choices
	db 1
.Choices:
	db STATICMENU_CURSOR
	db 3
	db "Next stop@"
	db "Catch me up@"
	db "Side quests@"

.Next:
	callasm FieldBookCurrent
	repeattext
	waitendtext

.CatchUp:
	callasm FieldBookProgress
	repeattext
	promptbutton
	writetext .NextText
	promptbutton
	callasm FieldBookCurrent
	repeattext
	promptbutton
	writetext .AheadText
	promptbutton
	callasm FieldBookAhead
	repeattext
	waitendtext

.NextText:
	text "Your next stop…"
	done

.AheadText:
	text "Looking ahead…"
	done

; Resolve all three views from the same read-only itinerary. DE holds the
; most recent completed step on this route. For a preview, skip the first
; unfinished step. No timestamp or extra save data is needed.
	const_def
	const BOOK_CURRENT
	const BOOK_AHEAD
	const BOOK_PROGRESS

FieldBookCurrent:
	call GetCurrentFieldBookPage
	jr StoreFieldBookPage
FieldBookProgress:
	ld b, BOOK_PROGRESS
	jr ReadFieldBookPage
FieldBookAhead:
	ld b, BOOK_AHEAD
ReadFieldBookPage:
	call FindFieldBookPage
StoreFieldBookPage:
	ld a, BANK(FieldBookRoute)
	ld [wScriptTextBank], a
	ld a, l
	ld [wScriptTextAddr], a
	ld a, h
	ld [wScriptTextAddr + 1], a
	ret

GetCurrentFieldBookPage:
	ld b, BOOK_CURRENT
FindFieldBookPage:
	ld hl, FieldBookRoute
	ld de, FieldBookRecap.Begin
.loop
	ld a, [hli]
	ld c, a
	ld a, [hli]
	and a
	jr z, .end
	push de
	ld d, a
	ld e, c
	ld a, [de]
	and [hl] ; bit mask
	inc hl
	cp [hl] ; value when complete
	inc hl
	pop de
	ld a, [hli]
	ld c, a
	ld a, [hli] ; high byte of the hint address (low byte in C)
	jr nz, .unfinished
	or c
	jr z, .shortcut
	ld a, [hli]
	ld e, a
	ld d, [hl]
	inc hl
	jr .loop

.shortcut
	ld a, [hli]
	ld h, [hl]
	ld l, a
	jr .loop

.unfinished
	inc hl
	inc hl
	or a ; text pointers are in ROMX
	jr z, .loop ; unmet shortcut
	bit 1, b ; BOOK_PROGRESS
	jr nz, .progress
	bit 0, b ; BOOK_AHEAD
	jr z, .current
	ld b, BOOK_CURRENT
	jr .loop
.current
	ld h, a
	ld l, c
	ret

.end
	ld a, b
	cp BOOK_PROGRESS
	jr z, .progress
	eventflagcheck EVENT_WON_PALLET_INVITATIONAL
	ld hl, FieldBookNotes.AfterFinal
	ret z ; reading one step ahead from the finale
	ld hl, FieldBookNotes.Champion
	ld a, b
	and a
	ret z
	ld hl, FieldBookNotes.FreePlay
	ret
.progress
	ld h, d
	ld l, e
	ret

; Each record names a byte in RAM, its mask and completed value, then the
; directions and recap text. A zero direction pointer jumps over the
; earlier steps of a chapter already finished on this save.
MACRO book_event
	dw wEventFlags + (\1 / 8)
	db 1 << (\1 % 8)
	if _NARG == 3
		db \3 ; a gym leader's hide flag clears when they return
	else
		db 1 << (\1 % 8)
	endc
	dw FieldBookNotes.\2, FieldBookRecap.\2
ENDM

MACRO book_bit
	dw \1
	db 1 << (\2), 1 << (\2)
	dw FieldBookNotes.\3, FieldBookRecap.\3
ENDM

MACRO book_badge
	book_bit wJohtoBadges + ((\1 - ENGINE_BADGES) / 8), (\1 - ENGINE_BADGES) % 8, \2
ENDM

MACRO book_skip
	dw wEventFlags + (\1 / 8)
	db 1 << (\1 % 8), 1 << (\1 % 8)
	dw 0, \2
ENDM

FieldBookRoute:
	book_skip EVENT_WON_PALLET_INVITATIONAL, .Final
	book_skip EVENT_GOT_MYSTICTICKET_FROM_RED, .Red
	book_skip EVENT_OPENED_MT_SILVER, .Oak
	book_skip EVENT_BEAT_ELITE_FOUR, .League
	book_event EVENT_GOT_A_POKEMON_FROM_ELM, Starter
	book_event EVENT_GOT_MYSTERY_EGG_FROM_MR_POKEMON, Errand
	book_event EVENT_GAVE_MYSTERY_EGG_TO_ELM, ReturnEgg
	book_event EVENT_GOT_TM70_FLASH, Tower
	book_event EVENT_VIOLET_GYM_FALKNER, Cave, 0
	book_badge ENGINE_ZEPHYRBADGE, Violet
	book_event EVENT_GOT_TOGEPI_EGG_FROM_ELMS_AIDE, Aide
	book_event EVENT_CLEARED_SLOWPOKE_WELL, Well
	book_badge ENGINE_HIVEBADGE, Bugsy
	book_event EVENT_GOT_HM01_CUT, Cut
	book_bit wPokegearFlags, POKEGEAR_RADIO_CARD_F, Quiz
	book_badge ENGINE_PLAINBADGE, Whitney
	book_event EVENT_GOT_SQUIRTBOTTLE, Bottle
	book_event EVENT_FOUGHT_SUDOWOODO, Tree
	book_event EVENT_RELEASED_THE_BEASTS, BurnedTower
	book_badge ENGINE_FOGBADGE, Morty
	book_event EVENT_GOT_HM03_SURF, Surf
	book_event EVENT_JASMINE_EXPLAINED_AMPHYS_SICKNESS, Lighthouse
	book_event EVENT_GOT_SECRETPOTION_FROM_PHARMACY, Medicine
	book_badge ENGINE_STORMBADGE, Chuck
	book_event EVENT_JASMINE_RETURNED_TO_GYM, Amphy
	book_badge ENGINE_MINERALBADGE, Jasmine
	book_event EVENT_DECIDED_TO_HELP_LANCE, Lake
	book_event EVENT_CLEARED_ROCKET_HIDEOUT, Hideout
	book_badge ENGINE_GLACIERBADGE, Pryce
	book_skip EVENT_CLEARED_RADIO_TOWER, .CardKey
	book_event EVENT_BEAT_PETREL_1, Takeover
	book_event EVENT_RECEIVED_CARD_KEY, Director
.CardKey:
	book_event EVENT_CLEARED_RADIO_TOWER, CardKey
	book_event EVENT_GOT_HM06_WATERFALL, Waterfall
	book_event EVENT_BEAT_CLAIR, Clair
	book_badge ENGINE_RISINGBADGE, DragonDen
.League:
	book_event EVENT_BEAT_ELITE_FOUR, League
	; In Kanto all eight local badges also qualify you for the League rematch.
	dw wKantoBadges
	db $ff, $ff
	dw 0, .Blue
	book_event EVENT_GOT_SS_TICKET_FROM_ELM, Ticket
	book_event EVENT_FAST_SHIP_FIRST_TIME, Ship
	book_badge ENGINE_THUNDERBADGE, Surge
	book_skip EVENT_RESTORED_POWER_TO_KANTO, .Restore
	book_event EVENT_MET_MANAGER_AT_POWER_PLANT, Plant
	book_event EVENT_MET_ROCKET_GRUNT_AT_CERULEAN_GYM, Grunt
	book_event EVENT_LEARNED_ABOUT_MACHINE_PART, Bridge
	book_event EVENT_FOUND_MACHINE_PART_IN_CERULEAN_GYM, Part
.Restore:
	book_event EVENT_RESTORED_POWER_TO_KANTO, Restore
	book_event EVENT_TRAINERS_IN_CERULEAN_GYM, Cape, 0
	book_badge ENGINE_CASCADEBADGE, Misty
	book_badge ENGINE_MARSHBADGE, Sabrina
	book_badge ENGINE_RAINBOWBADGE, Erika
	book_badge ENGINE_SOULBADGE, Janine
	book_bit wPokegearFlags, POKEGEAR_EXPN_CARD_F, Radio
	book_event EVENT_FOUGHT_SNORLAX, Flute
	book_badge ENGINE_BOULDERBADGE, Brock
	book_badge ENGINE_VOLCANOBADGE, Blaine
	book_event EVENT_VIRIDIAN_GYM_BLUE, Cinnabar, 0
.Blue:
	book_badge ENGINE_EARTHBADGE, Blue
	book_event EVENT_BEAT_ELITE_FOUR_AGAIN, Rematch
.Oak:
	book_event EVENT_OPENED_MT_SILVER, Oak
.Red:
	book_event EVENT_GOT_MYSTICTICKET_FROM_RED, Red
	book_event EVENT_BEAT_MOLLY, Alph
	book_event EVENT_RESCUED_PROF_HALE, Hale
	book_event EVENT_TIME_TRAVEL_FINISHED, Shrine
	book_event EVENT_BEAT_IRON_MASK_MARAUDER, Mask
	book_skip EVENT_BEAT_MEWTWO_CLONES, .Echo
	book_event EVENT_READ_CINNABAR_CLONE_REPORT, CloneReport
.Echo:
	book_event EVENT_BEAT_MEWTWO_CLONES, Echo
	book_skip EVENT_BEAT_DRAKE, .Drake
	book_event EVENT_BEAT_ORANGE_CREW_CISSY, Cissy
	book_event EVENT_BEAT_ORANGE_CREW_DANNY, Danny
	book_event EVENT_BEAT_ORANGE_CREW_RUDY, Rudy
	book_event EVENT_BEAT_ORANGE_CREW_LUANA, Luana
.Drake:
	book_event EVENT_BEAT_DRAKE, Drake
	book_event EVENT_WON_WHIRL_CUP, Cup
.Final:
	book_event EVENT_WON_PALLET_INVITATIONAL, Final
	dw 0 ; end of itinerary

FieldBookSideQuests:
	checkevent EVENT_HEARD_SHAMOUTI_BEACONS
	iffalsefwd .Errands
	checkevent EVENT_RESTORED_SHAMOUTI_BEACONS
	iffalsefwd .Beacons
.Errands:
	; Favor an errand the player has already accepted.
	checkevent EVENT_GAVE_KENYA
	iftruefwd .KenyaReward
	checkevent EVENT_GOT_KENYA
	iftrue_jumpopenedtext FieldBookNotes.Deliver
	sjumpfwd .Doll
.KenyaReward:
	checkevent EVENT_GOT_HP_UP_FROM_RANDY
	iffalse_jumpopenedtext FieldBookNotes.Reward
.Doll:
	checkevent EVENT_RESTORED_POWER_TO_KANTO
	iffalsefwd .Farm
	checkevent EVENT_GOT_PASS_FROM_COPYCAT
	iftruefwd .Farm
	checkevent EVENT_MET_COPYCAT_FOUND_OUT_ABOUT_LOST_ITEM
	iffalse_jumpopenedtext FieldBookNotes.Copycat
	checkevent EVENT_GOT_LOST_ITEM_FROM_FAN_CLUB
	iffalse_jumpopenedtext FieldBookNotes.Club
	jumpopenedtext FieldBookNotes.Pass
.Farm:
	checkflag ENGINE_FLYPOINT_OLIVINE
	iffalsefwd .Gate
	checkevent EVENT_HEALED_MOOMOO
	iffalse_jumpopenedtext FieldBookNotes.Berries
.Gate:
	checkflag ENGINE_FLYPOINT_GOLDENROD
	iffalsefwd .Shamouti
	checkevent EVENT_GOT_HP_UP_FROM_RANDY
	iffalse_jumpopenedtext FieldBookNotes.Kenya
.Shamouti:
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalsefwd .Early
	checkevent EVENT_GOT_ORANGE_TICKET
	iffalsefwd .Early
	checkevent EVENT_RESTORED_SHAMOUTI_BEACONS
	iffalse_jumpopenedtext FieldBookNotes.ShoreKeeper
	checkevent EVENT_FOUGHT_LUGIA
	iffalse_jumpopenedtext FieldBookNotes.SeaGuardian
	jumpopenedtext FieldBookNotes.NoLeads
.Early:
	checkflag ENGINE_FLYPOINT_GOLDENROD
	iffalse_jumpopenedtext FieldBookNotes.Later
	jumpopenedtext FieldBookNotes.NoLeads
.Beacons:
	checkevent EVENT_TUNED_FIRE_BEACON
	iffalse_jumpopenedtext FieldBookNotes.FireBeacon
	checkevent EVENT_TUNED_ICE_BEACON
	iffalse_jumpopenedtext FieldBookNotes.IceBeacon
	checkevent EVENT_TUNED_LIGHTNING_BEACON
	iffalse_jumpopenedtext FieldBookNotes.LightningBeacon
	jumpopenedtext FieldBookNotes.ShoreReturn

FieldBookNotes:

.Starter:
	text "New Bark Town"
	para "Visit Prof.Elm in"
	line "his lab. Pick a"
	cont "partner for his"
	cont "errand."
	done

.Errand:
	text "Mr.#mon's house"
	para "Head north from"
	line "Cherrygrove on"
	cont "Route 30. Take the"
	cont "east fork to his"
	cont "house."
	done

.ReturnEgg:
	text "Back to New Bark"
	para "Show Prof.Elm the"
	line "Mystery Egg in his"
	cont "lab."
	done

.Tower:
	text "Violet City"
	para "Climb Sprout"
	line "Tower. The elder"
	cont "at the top teaches"
	cont "Flash."
	done

.Cave:
	text "Looking for"
	line "Falkner"
	para "Enter Dark Cave"
	line "from Route 31 and"
	cont "help Falkner with"
	cont "the Ursaring."
	done

.Violet:
	text "Violet City"
	para "Falkner is back at"
	line "the Gym. Challenge"
	cont "him for a badge."
	done

.Aide:
	text "Elm sent an aide"
	para "Visit Violet's"
	line "#mon Center."
	cont "Leave a party slot"
	cont "for his Egg."
	done

.Well:
	text "Azalea Town"
	para "Go south on Route"
	line "32 through Union"
	cont "Cave. Find Kurt in"
	cont "Azalea and help"
	cont "him at Slowpoke"
	cont "Well."
	done

.Bugsy:
	text "Azalea Town"
	para "The well is safe."
	line "Bugsy is ready at"
	cont "the Gym."
	done

.Cut:
	text "Ilex Forest"
	para "West of Azalea,"
	line "herd Farfetch'd"
	cont "back to its owner."
	cont "Ask about Cut."
	done

.Quiz:
	text "Goldenrod City"
	para "Take the radio"
	line "quiz at the Radio"
	cont "Tower counter."
	cont "Whitney is there."
	done

.Whitney:
	text "Goldenrod Gym"
	para "Challenge Whitney."
	line "Talk to her again"
	cont "once she calms"
	cont "down."
	done

.Bottle:
	text "Goldenrod City"
	para "Visit the flower"
	line "shop by the Gym."
	cont "Ask to borrow a"
	cont "Squirtbottle."
	done

.Tree:
	text "Route 36"
	para "Water the odd tree"
	line "blocking the path"
	cont "to Ecruteak City."
	done

.BurnedTower:
	text "Ecruteak City"
	para "Find Morty in the"
	line "Burned Tower. See"
	cont "what stirs in the"
	cont "basement."
	done

.Morty:
	text "Ecruteak Gym"
	para "Morty has returned"
	line "to the Gym. Follow"
	cont "the path to him."
	done

.Surf:
	text "Ecruteak City"
	para "Battle the five"
	line "Kimono Girls at"
	cont "the Dance Theatre."
	cont "Speak to the man"
	cont "watching them."
	done

.Lighthouse:
	text "Olivine City"
	para "Take Routes 38 and"
	line "39 west to"
	cont "Olivine. Climb the"
	cont "lighthouse and"
	cont "speak to Jasmine."
	done

.Medicine:
	text "Cianwood City"
	para "Surf southwest"
	line "from Olivine. The"
	cont "pharmacist has"
	cont "medicine for"
	cont "Amphy."
	done

.Amphy:
	text "Olivine City"
	para "Bring the medicine"
	line "to Jasmine atop"
	cont "the lighthouse."
	done

.Chuck:
	text "Cianwood Gym"
	para "Challenge Chuck in"
	line "Cianwood. Ask at"
	cont "the #mon Center"
	cont "about Strength."
	done

.Jasmine:
	text "Olivine Gym"
	para "Amphy is better."
	line "Meet Jasmine back"
	cont "at her Gym."
	done

.Lake:
	text "Lake of Rage"
	para "Go north from"
	line "Mahogany. Find the"
	cont "red Gyarados, then"
	cont "talk to Lance on"
	cont "the shore."
	done

.Hideout:
	text "Mahogany Town"
	para "Meet Lance at the"
	line "shop. Search the"
	cont "hideout below for"
	cont "the radio signal."
	done

.Pryce:
	text "Mahogany Gym"
	para "The hideout is"
	line "quiet. Challenge"
	cont "Pryce at the Gym."
	done

.Takeover:
	text "Goldenrod City"
	para "Team Rocket has"
	line "the Radio Tower."
	cont "Find the false"
	cont "director upstairs."
	done

.Director:
	text "Goldenrod Tunnel"
	para "Use the Basement"
	line "Key underground."
	cont "Rescue the real"
	cont "director in the"
	cont "warehouse."
	done

.CardKey:
	text "Radio Tower"
	para "Return with the"
	line "Card Key. Open the"
	cont "shutter on floor"
	cont "three."
	done

.Clair:
	text "Blackthorn City"
	para "Clair waits at the"
	line "Gym east of Ice"
	cont "Path."
	done

.DragonDen:
	text "Dragon's Den"
	para "Surf behind"
	line "Clair's Gym. Visit"
	cont "the elder in the"
	cont "shrine for your"
	cont "final badge."
	done

.Waterfall:
	text "Ice Path"
	para "From Mahogany, go"
	line "east on Route 44."
	para "Pick up Waterfall"
	line "on the first floor"
	cont "on your way east"
	cont "to Blackthorn."
	done

.League:
	text "Indigo Plateau"
	para "Surf east from New"
	line "Bark. Climb Tohjo"
	cont "Falls and follow"
	cont "Victory Road to"
	cont "the Elite Four."
	done

.Ticket:
	text "New Bark Town"
	para "Prof.Elm has a"
	line "ticket for you."
	cont "Visit his lab."
	done

.Ship:
	text "Olivine Port"
	para "Sail to Vermilion"
	line "on the S.S.Aqua."
	cont "Help the old man"
	cont "find his missing"
	cont "granddaughter."
	done

.Surge:
	text "Vermilion Gym"
	para "Check the bins to"
	line "open the gates to"
	cont "Lt.Surge."
	done

.Plant:
	text "Kanto Power Plant"
	para "From Route 9, surf"
	line "down Route 10. Ask"
	cont "the plant manager"
	cont "what was stolen."
	done

.Grunt:
	text "Cerulean City"
	para "The police have a"
	line "lead. Step inside"
	cont "Cerulean Gym."
	done

.Bridge:
	text "Route 24"
	para "Follow the fleeing"
	line "grunt north to"
	cont "Nugget Bridge."
	done

.Part:
	text "Cerulean Gym"
	para "Search the water"
	line "in the middle of"
	cont "the Gym for the"
	cont "Machine Part."
	done

.Restore:
	text "Kanto Power Plant"
	para "Take the Machine"
	line "Part back to the"
	cont "manager."
	done

.Cape:
	text "Cerulean Cape"
	para "Go north over the"
	line "bridge. Head east"
	cont "on Route 25 to"
	cont "find Misty."
	done

.Misty:
	text "Cerulean Gym"
	para "Misty is back in"
	line "town. Challenge"
	cont "her at the Gym."
	done

.Sabrina:
	text "Saffron Gym"
	para "Use the warp pads"
	line "to reach Sabrina."
	done

.Erika:
	text "Celadon Gym"
	para "Visit the Gym in"
	line "Celadon City and"
	cont "challenge Erika."
	done

.Janine:
	text "Fuchsia Gym"
	para "Find the real"
	line "Janine among the"
	cont "lookalikes."
	done

.Radio:
	text "Lavender Town"
	para "Visit the Radio"
	line "Tower. Ask the"
	cont "gentleman for the"
	cont "radio upgrade."
	done

.Flute:
	text "East of Vermilion"
	para "Tune the radio to"
	line "# Flute beside"
	cont "Snorlax. Speak to"
	cont "it to clear the"
	cont "cave entrance."
	done

.Brock:
	text "Pewter City"
	para "Go through"
	line "Diglett's Cave."
	cont "Head north from"
	cont "Route 2 to Brock's"
	cont "Gym."
	done

.Blaine:
	text "Seafoam Islands"
	para "Blaine moved his"
	line "Gym here. Surf to"
	cont "the islands on"
	cont "Route 20."
	done

.Cinnabar:
	text "Cinnabar Island"
	para "Find Blue on the"
	line "island. Show him"
	cont "your seven Kanto"
	cont "badges."
	done

.Blue:
	text "Viridian Gym"
	para "Challenge Blue in"
	line "Viridian for the"
	cont "last Kanto badge."
	done

.Rematch:
	text "Indigo Plateau"
	para "With all sixteen"
	line "badges, challenge"
	cont "the Elite Four"
	cont "again."
	done

.Oak:
	text "Pallet Town"
	para "Show Prof.Oak how"
	line "far you've come."
	cont "Talk to him in his"
	cont "lab about"
	cont "Mt.Silver."
	done

.Red:
	text "Mt.Silver"
	para "Take the west exit"
	line "from the League"
	cont "gate. Climb the"
	cont "cave to find Red."
	done

.Deliver:
	text "Kenya's mail"
	para "Bring Kenya to the"
	line "sleepy man on"
	cont "Route 31."
	done

.Reward:
	text "Mail delivered"
	para "Return to Randy in"
	line "the gate north of"
	cont "Goldenrod."
	done

.Copycat:
	text "A missing doll"
	para "Visit Copycat"
	line "upstairs at her"
	cont "home in Saffron."
	done

.Club:
	text "Vermilion City"
	para "Ask about"
	line "Copycat's lost"
	cont "doll at the"
	cont "#mon Fan Club."
	done

.Pass:
	text "Back to Saffron"
	para "See Copycat at"
	line "home about her"
	cont "doll and a train"
	cont "pass."
	done

.Berries:
	text "Moomoo Farm"
	para "A Miltank is sick"
	line "in the Route 39"
	cont "barn. Feed her"
	cont "Oran or Sitrus"
	cont "Berries."
	done

.Kenya:
	text "A letter to carry"
	para "Speak to Randy in"
	line "the gate north of"
	cont "Goldenrod. Leave a"
	cont "party slot free."
	done

.Later:
	text "Local errands"
	para "Check back when"
	line "you reach a new"
	cont "city. Next stop"
	cont "has your main"
	cont "route."
	done

.NoLeads:
	text "Local errands"
	para "No new errands on"
	line "these pages yet."
	done

.Champion:
	text "Tracey's last page"
	line "is a sketch of you"
	cont "beside Ash."
	para "Oak wrote one word"
	line "below: Champion."
	done

.Alph:
	text "Field book: Alph"
	para "Molly heard"
	line "her father calling"
	cont "from a statue."
	para "Meet her at the"
	line "research center in"
	cont "the Ruins of Alph."
	done

.Hale:
	text "Ruins of Alph"
	para "In the big chamber"
	line "stand at the foot"
	cont "of the ladder."
	para "Two statues stand"
	line "to its left. Knock"
	cont "on the nearer one."
	done

.Shrine:
	text "Ilex Forest"
	para "Lyra left a note"
	line "on a forest sign."
	para "Check the shrine"
	line "west of Azalea."
	cont "Call back if you"
	cont "hear a voice."
	done

.Mask:
	text "A man in a mask"
	line "is waiting east"
	cont "of Ilex shrine."
	para "He carries a black"
	line "ball. Celebi won't"
	cont "leave his side."
	done

.CloneReport:
	text "Cinnabar Mansion"
	para "Oak wants the old"
	line "lab's flight log."
	para "In the basement,"
	line "look for the diary"
	cont "west of the steps."
	done

.Echo:
	text "A voice is calling"
	line "from the depths"
	cont "of Cerulean Cave."
	para "Examine the place"
	line "where Mewtwo stood"
	cont "if it has gone."
	done

.ShoreKeeper:
	text "Shamouti shrine"
	para "Find the keeper"
	line "past Noisy Forest."
	cont "The coastal ferry"
	cont "lights went out."
	done
.FireBeacon:
	text "Fire Island"
	para "Surf to the first"
	line "island along the"
	cont "Shamouti Coast."
	para "Check the beacon"
	line "at the summit."
	done
.IceBeacon:
	text "Ice Island"
	para "Surf to the middle"
	line "island along the"
	cont "Shamouti Coast."
	para "Check the beacon"
	line "at the summit."
	done
.LightningBeacon:
	text "Lightning Island"
	para "Surf to the far"
	line "end of Shamouti"
	cont "Coast. The beacon"
	cont "is at the summit."
	done
.ShoreReturn:
	text "Shamouti shrine"
	para "All three are lit."
	line "See Lawrence or"
	cont "the shrine keeper."
	done
.SeaGuardian:
	text "Whirl Islands"
	para "The Silver Wing"
	line "may draw Lugia out"
	cont "in the deep cave."
	done

.Cup:
	text "A page from Misty"
	line "smells of sea air."
	para "Olivine Whirl Cup"
	para "Take a Water team"
	line "to the port. Win"
	cont "all three rounds."
	done

.Final:
	text "Ash taped a ticket"
	line "inside the cover."
	para "Pallet finals"
	line "Outside Oak's lab."
	cont "Two rounds. One"
	cont "team."
	done

.Cissy:
	text "Warm Beach"
	para "Use the Orange"
	line "Ticket in"
	cont "Vermilion to reach"
	cont "Shamouti Island."
	para "At the tunnel, use"
	line "the radio's #"
	cont "Flute to wake the"
	cont "tree in your way."
	para "Take the tunnel to"
	line "Warm Beach. Cissy"
	cont "is by the water."
	done

.Danny:
	text "Rocky Beach"
	para "Head north from"
	line "Shamouti to Rocky"
	cont "Beach. Danny is on"
	cont "the sandy path."
	done

.Rudy:
	text "Beautiful Beach"
	para "Rudy is near the"
	line "ferry landing on"
	cont "Beautiful Beach."
	done

.Luana:
	text "Valencia Island"
	para "Accept a partner"
	line "from Prof.Ivy at"
	cont "Shamouti's #mon"
	cont "Center to open the"
	cont "Valencia ferry."
	para "Sail from the dock"
	line "on Beautiful Beach"
	cont "to Valencia. Visit"
	cont "Luana in the house"
	cont "west of the lab."
	done

.Drake:
	text "Shamouti Island"
	para "Take the four Crew"
	line "badges to Drake in"
	cont "his island home."
	done

.AfterFinal:
	text "Pallet Town"
	para "After both wins,"
	line "visit Oak's lab to"
	cont "see what Tracey"
	cont "drew."
	done

.FreePlay:
	text "Pallet Town"
	para "Ash is ready for a"
	line "friendly rematch."
	cont "Read Side quests"
	cont "for local errands."
	done

FieldBookRecap:
.Begin:
	text "A fresh page! Your"
	line "journey starts at"
	cont "home in New Bark."
	done

.Starter:
	text "You chose your"
	line "first partner in"
	cont "Elm's lab."
	done

.Errand:
	text "You received the"
	line "Mystery Egg for"
	cont "Prof.Elm."
	done

.ReturnEgg:
	text "You brought the"
	line "Mystery Egg back"
	cont "to Prof.Elm."
	done

.Tower:
	text "The elder at"
	line "Sprout Tower gave"
	cont "you Flash."
	done

.Cave:
	text "You found Falkner"
	line "with the Ursaring"
	cont "in Dark Cave."
	done

.Violet:
	text "Falkner gave you"
	line "your first badge"
	cont "in Violet."
	done

.Aide:
	text "Elm's aide put the"
	line "Egg in your care."
	done

.Well:
	text "You helped Kurt"
	line "save the Slowpoke"
	cont "in Azalea."
	done

.Bugsy:
	text "You earned Bugsy's"
	line "Hive Badge."
	done

.Cut:
	text "The Farfetch'd is"
	line "safe. You picked"
	cont "up Cut in Ilex."
	done

.Quiz:
	text "You passed the"
	line "radio quiz in"
	cont "Goldenrod."
	done

.Whitney:
	text "Whitney handed you"
	line "the Plain Badge."
	done

.Bottle:
	text "The flower shop"
	line "lent you its"
	cont "Squirtbottle."
	done

.Tree:
	text "You cleared the"
	line "odd tree from"
	cont "Route 36."
	done

.BurnedTower:
	text "Three beasts fled"
	line "the Burned Tower."
	done

.Morty:
	text "You won Morty's"
	line "Fog Badge."
	done

.Surf:
	text "You earned Surf at"
	line "the Dance Theatre."
	done

.Lighthouse:
	text "Jasmine asked for"
	line "medicine for Amphy"
	cont "in the lighthouse."
	done

.Medicine:
	text "The Cianwood"
	line "pharmacist gave"
	cont "you Amphy's"
	cont "medicine."
	done

.Chuck:
	text "You earned Chuck's"
	line "Storm Badge in"
	cont "Cianwood."
	done

.Amphy:
	text "Amphy is well."
	line "Jasmine returned"
	cont "to her Gym."
	done

.Jasmine:
	text "You won Jasmine's"
	line "Mineral Badge."
	done

.Lake:
	text "At the lake, you"
	line "agreed to help"
	cont "Lance."
	done

.Hideout:
	text "You and Lance shut"
	line "down the signal in"
	cont "Mahogany."
	done

.Pryce:
	text "You won Pryce's"
	line "Glacier Badge."
	done

.Takeover:
	text "Petrel gave up the"
	line "Basement Key in"
	cont "Goldenrod."
	done

.Director:
	text "The director gave"
	line "you the Card Key."
	done

.CardKey:
	text "The Radio Tower is"
	line "back on the air."
	done

.Waterfall:
	text "You found the"
	line "Waterfall HM in"
	cont "Ice Path."
	done

.Clair:
	text "You beat Clair."
	line "She sent you into"
	cont "Dragon's Den."
	done

.DragonDen:
	text "You received the"
	line "Rising Badge at"
	cont "the shrine."
	done

.League:
	text "You entered the"
	line "Hall of Fame in"
	cont "Johto."
	done

.Ticket:
	text "Elm gave you a"
	line "ticket for the"
	cont "S.S.Aqua."
	done

.Ship:
	text "You reached"
	line "Vermilion on the"
	cont "S.S.Aqua."
	done

.Surge:
	text "You won Lt.Surge's"
	line "Thunder Badge."
	done

.Plant:
	text "The plant manager"
	line "reported a stolen"
	cont "Machine Part."
	done

.Grunt:
	text "A Rocket fled the"
	line "Cerulean Gym."
	done

.Bridge:
	text "On Route 24, the"
	line "grunt told you"
	cont "where he hid the"
	cont "part."
	done

.Part:
	text "You recovered the"
	line "missing part from"
	cont "Cerulean Gym."
	done

.Restore:
	text "Power is back on"
	line "in Kanto."
	done

.Cape:
	text "You found Misty at"
	line "Cerulean Cape."
	done

.Misty:
	text "You earned Misty's"
	line "Cascade Badge."
	done

.Sabrina:
	text "You won Sabrina's"
	line "Marsh Badge."
	done

.Erika:
	text "Erika gave you the"
	line "Rainbow Badge."
	done

.Janine:
	text "You found the real"
	line "Janine and won the"
	cont "Soul Badge."
	done

.Radio:
	text "Your radio picks"
	line "up Kanto stations"
	cont "now."
	done

.Flute:
	text "You cleared the"
	line "sleeping Snorlax"
	cont "from the way."
	done

.Brock:
	text "You earned Brock's"
	line "Boulder Badge."
	done

.Blaine:
	text "You won Blaine's"
	line "Volcano Badge at"
	cont "Seafoam."
	done

.Cinnabar:
	text "Blue went back to"
	line "Viridian Gym."
	done

.Blue:
	text "You earned Blue's"
	line "Earth Badge."
	done

.Rematch:
	text "You won the League"
	line "rematch with all"
	cont "sixteen badges."
	done

.Oak:
	text "Oak opened the way"
	line "to Mt.Silver."
	done

.Red:
	text "You beat Red on"
	line "Mt.Silver. His"
	cont "note led you to"
	cont "Molly."
	done

.Alph:
	text "Molly's dream"
	line "faded. She heard"
	cont "real knocking in"
	cont "the ruins."
	done

.Hale:
	text "You helped Molly's"
	line "father home. He"
	cont "drew Ilex shrine"
	cont "for Oak."
	done

.Shrine:
	text "Celebi brought you"
	line "back from your"
	cont "journey in time."
	done

.Mask:
	text "You drove off the"
	line "masked man at Ilex"
	cont "shrine."
	done

.CloneReport:
	text "You recovered the"
	line "flight log from"
	cont "Cinnabar Mansion."
	done

.Echo:
	text "You faced copies"
	line "of your own team"
	cont "in Cerulean Cave."
	done

.Cissy:
	text "Cissy gave you the"
	line "Coral-Eye Badge."
	done

.Danny:
	text "Danny gave you the"
	line "Sea Ruby Badge."
	done

.Rudy:
	text "Rudy gave you the"
	line "Spike Shell Badge."
	done

.Luana:
	text "Luana gave you the"
	line "Jade Star Badge."
	done

.Drake:
	text "You won Drake's"
	line "trophy on Shamouti"
	cont "Island."
	done

.Cup:
	text "You beat Misty's"
	line "team to win the"
	cont "Whirl Cup."
	done

.Final:
	text "You won both bouts"
	line "in Pallet. Tracey"
	cont "drew your team."
	done

TraceyCallsWithALead:
	playsound SFX_CALL
	waitsfx
	opentext
	writetext .Call
	promptbutton
	scall GiveNextStoryLead
	endtext

.Call:
	text "The #gear rings."
	para "Tracey: Got a pen?"
	line "I've got a name"
	cont "for your book."
	done

; Spoken by the character handing off the chapter. Use the Field Book's
; current destination so a returning player hears the first unfinished lead.
GiveNextStoryLead:
	callasm .FindLead
	repeattext
	promptbutton
	end

.FindLead:
	call FieldBookCurrent
	ld d, h
	ld e, l
	ld hl, .Leads
.search
	ld a, [hli]
	ld c, a
	ld a, [hli]
	and a
	ret z ; the current book page is already set as a fallback
	cp d
	jr nz, .skip
	ld a, c
	cp e
	jr z, .found
.skip
	inc hl
	inc hl
	jr .search
.found
	ld a, [hli]
	ld [wScriptTextAddr], a
	ld a, [hl]
	ld [wScriptTextAddr + 1], a
	ret

.Leads:
	dw FieldBookNotes.Alph, .Molly
	dw FieldBookNotes.Hale, .Father
	dw FieldBookNotes.Shrine, .Celebi
	dw FieldBookNotes.Mask, .MaskedMan
	dw FieldBookNotes.CloneReport, .Research
	dw FieldBookNotes.Echo, .Mewtwo
	dw FieldBookNotes.Cissy, .Cissy
	dw FieldBookNotes.Danny, .Danny
	dw FieldBookNotes.Rudy, .Rudy
	dw FieldBookNotes.Luana, .Luana
	dw FieldBookNotes.Drake, .Drake
	dw FieldBookNotes.Cup, .Misty
	dw FieldBookNotes.Final, .Ash
	dw 0

.Molly:
	text "Molly heard her"
	line "dad calling at the"
	cont "Ruins of Alph."
	para "She's waiting in"
	line "the research lab."
	done
.Father:
	text "Molly heard three"
	line "knocks. Try the"
	cont "statue just left"
	cont "of the ladder in"
	cont "the big chamber."
	done
.Celebi:
	text "Those marks match"
	line "the shrine west of"
	cont "Azalea. Someone"
	cont "left a note there."
	done
.MaskedMan:
	text "Someone stood just"
	line "east of the Ilex"
	cont "shrine. I remember"
	cont "his iron mask."
	done
.Research:
	text "Oak left a note."
	para "Look in Cinnabar"
	line "Mansion."
	para "A diary in the"
	line "basement may tell"
	cont "us where Mewtwo"
	cont "went when it fled."
	done
.Mewtwo:
	text "Go to the depths"
	line "of Cerulean Cave."
	cont "Listen where"
	cont "Mewtwo stood."
	done
.Cissy:
	text "Cissy sent a note."
	line "“Meet me on Warm"
	cont "Beach. Bring shoes"
	cont "you can get wet!”"
	para "The Orange Ticket"
	line "gets you there via"
	cont "Vermilion ferry."
	done
.Danny:
	text "Danny went north"
	line "from Shamouti to"
	cont "Rocky Beach."
	para "Tell him to put"
	line "his fishing rod"
	cont "down for once!"
	done
.Rudy:
	text "Rudy practices his"
	line "footwork near the"
	cont "ferry landing on"
	cont "Beautiful Beach."
	done
.Luana:
	text "Luana's at home on"
	line "Valencia. Prof.Ivy"
	cont "can get you there."
	para "Look for Ivy at"
	line "Shamouti's #mon"
	cont "Center if you need"
	cont "a ferry ride."
	done
.Drake:
	text "Four Crew badges!"
	line "Show them to Drake"
	cont "at his house on"
	cont "Shamouti Island."
	done
.Misty:
	text "Misty left you a"
	line "spot in the Whirl"
	cont "Cup at Olivine"
	cont "Port."
	para "She underlined"
	line "this part twice:"
	cont "“All-Water team!”"
	done
.Ash:
	text "Ash asked me to"
	line "send you to Pallet"
	cont "Town. He's outside"
	cont "Oak's lab."
	para "Bring your best"
	line "six. Drake gets"
	cont "the first match!"
	done
