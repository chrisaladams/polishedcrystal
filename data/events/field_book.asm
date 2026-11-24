ReadFieldBook:
	opentext
	loadmenu .Contents
	verticalmenu
	closewindow
	ifequalfwd 1, .Next
	ifequal 2, FieldBookSideQuests
	endtext

.Contents:
	db MENU_BACKUP_TILES
	menu_coords 0, 0, 14, 5
	dw .Choices
	db 1
.Choices:
	db STATICMENU_CURSOR
	db 2
	db "Next stop@"
	db "Side quests@"

.Next:
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalsefwd .Earlier
	farsjump OaksLabFieldBook
.Earlier:
	checkevent EVENT_BEAT_ELITE_FOUR
	iftruefwd FieldBookKanto
	checkevent EVENT_GOT_A_POKEMON_FROM_ELM
	iffalse_jumpopenedtext FieldBookNotes.Starter
	checkevent EVENT_GOT_MYSTERY_EGG_FROM_MR_POKEMON
	iffalse_jumpopenedtext FieldBookNotes.Errand
	checkevent EVENT_GAVE_MYSTERY_EGG_TO_ELM
	iffalse_jumpopenedtext FieldBookNotes.ReturnEgg
	checkevent EVENT_GOT_TM70_FLASH
	iffalse_jumpopenedtext FieldBookNotes.Tower
	checkevent EVENT_VIOLET_GYM_FALKNER
	iftrue_jumpopenedtext FieldBookNotes.Cave
	checkflag ENGINE_ZEPHYRBADGE
	iffalse_jumpopenedtext FieldBookNotes.Violet
	checkevent EVENT_GOT_TOGEPI_EGG_FROM_ELMS_AIDE
	iffalse_jumpopenedtext FieldBookNotes.Aide
	checkevent EVENT_CLEARED_SLOWPOKE_WELL
	iffalse_jumpopenedtext FieldBookNotes.Well
	checkflag ENGINE_HIVEBADGE
	iffalse_jumpopenedtext FieldBookNotes.Bugsy
	checkevent EVENT_GOT_HM01_CUT
	iffalse_jumpopenedtext FieldBookNotes.Cut
	checkflag ENGINE_RADIO_CARD
	iffalse_jumpopenedtext FieldBookNotes.Quiz
	checkflag ENGINE_PLAINBADGE
	iffalse_jumpopenedtext FieldBookNotes.Whitney
	checkevent EVENT_GOT_SQUIRTBOTTLE
	iffalse_jumpopenedtext FieldBookNotes.Bottle
	checkevent EVENT_FOUGHT_SUDOWOODO
	iffalse_jumpopenedtext FieldBookNotes.Tree
	checkevent EVENT_RELEASED_THE_BEASTS
	iffalse_jumpopenedtext FieldBookNotes.BurnedTower
	checkflag ENGINE_FOGBADGE
	iffalse_jumpopenedtext FieldBookNotes.Morty
	checkevent EVENT_GOT_HM03_SURF
	iffalse_jumpopenedtext FieldBookNotes.Surf
	checkevent EVENT_JASMINE_EXPLAINED_AMPHYS_SICKNESS
	iffalse_jumpopenedtext FieldBookNotes.Lighthouse
	checkevent EVENT_GOT_SECRETPOTION_FROM_PHARMACY
	iffalse_jumpopenedtext FieldBookNotes.Medicine
	checkevent EVENT_JASMINE_RETURNED_TO_GYM
	iffalse_jumpopenedtext FieldBookNotes.Amphy
	checkflag ENGINE_STORMBADGE
	iffalse_jumpopenedtext FieldBookNotes.Chuck
	checkflag ENGINE_MINERALBADGE
	iffalse_jumpopenedtext FieldBookNotes.Jasmine
	checkevent EVENT_DECIDED_TO_HELP_LANCE
	iffalse_jumpopenedtext FieldBookNotes.Lake
	checkevent EVENT_CLEARED_ROCKET_HIDEOUT
	iffalse_jumpopenedtext FieldBookNotes.Hideout
	checkflag ENGINE_GLACIERBADGE
	iffalse_jumpopenedtext FieldBookNotes.Pryce
	checkevent EVENT_CLEARED_RADIO_TOWER
	iftruefwd .Blackthorn
	checkevent EVENT_BEAT_PETREL_1
	iffalse_jumpopenedtext FieldBookNotes.Takeover
	checkevent EVENT_RECEIVED_CARD_KEY
	iffalse_jumpopenedtext FieldBookNotes.Director
	jumpopenedtext FieldBookNotes.CardKey
.Blackthorn:
	checkevent EVENT_BEAT_CLAIR
	iffalse_jumpopenedtext FieldBookNotes.Clair
	checkflag ENGINE_RISINGBADGE
	iffalse_jumpopenedtext FieldBookNotes.DragonDen
	checkevent EVENT_GOT_HM06_WATERFALL
	iffalse_jumpopenedtext FieldBookNotes.Waterfall
	jumpopenedtext FieldBookNotes.League

FieldBookKanto:
	checkevent EVENT_OPENED_MT_SILVER
	iftrue_jumpopenedtext FieldBookNotes.Red
	readvar VAR_BADGES
	ifequalfwd 16, .LeagueRematch
	checkevent EVENT_GOT_SS_TICKET_FROM_ELM
	iffalse_jumpopenedtext FieldBookNotes.Ticket
	checkevent EVENT_FAST_SHIP_FIRST_TIME
	iffalse_jumpopenedtext FieldBookNotes.Ship
	checkflag ENGINE_THUNDERBADGE
	iffalse_jumpopenedtext FieldBookNotes.Surge
	checkevent EVENT_RESTORED_POWER_TO_KANTO
	iftruefwd .Powered
	checkevent EVENT_MET_MANAGER_AT_POWER_PLANT
	iffalse_jumpopenedtext FieldBookNotes.Plant
	checkevent EVENT_MET_ROCKET_GRUNT_AT_CERULEAN_GYM
	iffalse_jumpopenedtext FieldBookNotes.Grunt
	checkevent EVENT_LEARNED_ABOUT_MACHINE_PART
	iffalse_jumpopenedtext FieldBookNotes.Bridge
	checkevent EVENT_FOUND_MACHINE_PART_IN_CERULEAN_GYM
	iffalse_jumpopenedtext FieldBookNotes.Part
	jumpopenedtext FieldBookNotes.Restore
.Powered:
	checkevent EVENT_TRAINERS_IN_CERULEAN_GYM
	iftrue_jumpopenedtext FieldBookNotes.Cape
	checkflag ENGINE_CASCADEBADGE
	iffalse_jumpopenedtext FieldBookNotes.Misty
	checkflag ENGINE_MARSHBADGE
	iffalse_jumpopenedtext FieldBookNotes.Sabrina
	checkflag ENGINE_RAINBOWBADGE
	iffalse_jumpopenedtext FieldBookNotes.Erika
	checkflag ENGINE_SOULBADGE
	iffalse_jumpopenedtext FieldBookNotes.Janine
	checkflag ENGINE_EXPN_CARD
	iffalse_jumpopenedtext FieldBookNotes.Radio
	checkevent EVENT_FOUGHT_SNORLAX
	iffalse_jumpopenedtext FieldBookNotes.Flute
	checkflag ENGINE_BOULDERBADGE
	iffalse_jumpopenedtext FieldBookNotes.Brock
	checkflag ENGINE_VOLCANOBADGE
	iffalse_jumpopenedtext FieldBookNotes.Blaine
	checkevent EVENT_VIRIDIAN_GYM_BLUE
	iftrue_jumpopenedtext FieldBookNotes.Cinnabar
	checkflag ENGINE_EARTHBADGE
	iffalse_jumpopenedtext FieldBookNotes.Blue
.LeagueRematch:
	checkevent EVENT_BEAT_ELITE_FOUR_AGAIN
	iffalse_jumpopenedtext FieldBookNotes.Rematch
	jumpopenedtext FieldBookNotes.Oak

FieldBookSideQuests:
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
	iffalse_jumpopenedtext FieldBookNotes.Later
	checkevent EVENT_GOT_HP_UP_FROM_RANDY
	iffalse_jumpopenedtext FieldBookNotes.Kenya
	jumpopenedtext FieldBookNotes.NoLeads

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
	para "Go east on Route"
	line "44, then through"
	cont "Ice Path. Clair"
	cont "waits in the Gym."
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
	para "Pick up Waterfall"
	line "on the first floor"
	cont "before leaving for"
	cont "the League."
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
