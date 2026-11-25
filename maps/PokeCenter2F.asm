PokeCenter2F_MapScriptHeader:
	def_scene_scripts
	scene_script DoNothingScript, SCENE_POKECENTER2F_NOOP
	scene_script PokeCenter2FLeaveTradeCenterScene, SCENE_POKECENTER2F_LEAVE_TRADE_CENTER
	scene_script PokeCenter2FLeaveColosseumScene, SCENE_POKECENTER2F_LEAVE_COLOSSEUM

	def_callbacks
	callback MAPCALLBACK_TILES, PokeCenter2FTileCallback

	def_warp_events
	warp_event  0,  7, POKECENTER_2F, -1
	warp_event  5,  0, TRADE_CENTER, 1
	warp_event  9,  0, COLOSSEUM, 1

	def_coord_events

	def_bg_events
	bg_event  7,  3, BGEVENT_READ, PokeCenter2FLinkRecordSign

	def_object_events
	object_event  5,  2, SPRITE_LINK_RECEPTIONIST, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, LinkReceptionistScript_Trade, -1
	object_event  9,  2, SPRITE_LINK_RECEPTIONIST, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, LinkReceptionistScript_Battle, -1
	object_event 13,  3, SPRITE_LINK_RECEPTIONIST, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, 0, OBJECTTYPE_SCRIPT, 0, FriendBattleDeskScript, -1

	object_const_def
	const POKECENTER2F_TRADE_RECEPTIONIST
	const POKECENTER2F_BATTLE_RECEPTIONIST

PokeCenter2FTileCallback:
	callasm .CheckKanto
	iffalsefwd .done
	changemapblocks KantoPokeCenter2F_BlockData
.done
	endcallback

.CheckKanto:
	call RegionCheck
	dec e ; KANTO_REGION?
	ld a, TRUE
	jr z, .ok
	dec a ; FALSE
.ok
	ldh [hScriptVar], a
	ret

PokeCenter2FLeaveTradeCenterScene:
	sdefer .Script
	end

.Script:
	special WaitForOtherPlayerToExit
	applymovement POKECENTER2F_TRADE_RECEPTIONIST, PokeCenter2FMovementData_ReceptionistWalksUpAndLeft_LookRight
	applymovement PLAYER, PokeCenter2FMovementData_PlayerTakesThreeStepsDown
	applymovement POKECENTER2F_TRADE_RECEPTIONIST, PokeCenter2FMovementData_ReceptionistStepsRightAndDown
	setscene SCENE_POKECENTER2F_NOOP
	setmapscene TRADE_CENTER, SCENE_TRADECENTER_INITIALIZE
	end

PokeCenter2FLeaveColosseumScene:
	sdefer .Script
	end

.Script:
	special WaitForOtherPlayerToExit
	applymovement POKECENTER2F_BATTLE_RECEPTIONIST, PokeCenter2FMovementData_ReceptionistWalksUpAndLeft_LookRight
	applymovement PLAYER, PokeCenter2FMovementData_PlayerTakesThreeStepsDown
	applymovement POKECENTER2F_BATTLE_RECEPTIONIST, PokeCenter2FMovementData_ReceptionistStepsRightAndDown
	setscene SCENE_POKECENTER2F_NOOP
	setmapscene COLOSSEUM, SCENE_COLOSSEUM_INITIALIZE
	end

PokeCenter2FLinkRecordSign:
	reanchormap
	special Special_DisplayLinkRecord
	endtext

LinkReceptionistScript_Trade:
	; Link Edition: the link rooms are open from the start (upstream waits
	; until the Mystery Egg has been delivered to Elm)
	checkevent EVENT_GOT_A_POKEMON_FROM_ELM
	iffalse Script_TradeCenterClosed ; (too far for iffalsefwd)
	special FixPlayerEVsAndStats ; no (trivial) cheating
	opentext
	writetext Text_TradeReceptionistIntro
	yesorno
	iffalse_endtext
	callasm CheckPartyForMail
	iftruefwd LinkReceptionistScript_HasMail
	special Special_SetBitsForLinkTradeRequest
	; fallthrough
LinkReceptionistScript_DoTradeOrBattle:
	writetext Text_PleaseWait
	special Special_WaitForLinkedFriend
	iffalsefwd .FriendNotReady
	writetext Text_MustSaveGame
	yesorno
	iffalsefwd .DidNotSave
	special Special_TryQuickSave
	iffalsefwd .DidNotSave
	writetext Text_PleaseWait
	special Special_CheckLinkTimeout
	iffalsefwd .LinkTimedOut
	readmem wOtherPlayerLinkMode
	iffalsefwd .LinkedToFirstGen
	special PerformLinkChecks
	iffalsefwd .OldVersionDetected ; LINK_ERR_OLD_PC_DETECT
	ifequalfwd LINK_ERR_MISMATCH_GAME_ID, .WrongGameID
	ifequalfwd LINK_ERR_MISMATCH_VERSION, .WrongVersion
	ifequalfwd LINK_ERR_VERSION_TOO_LOW, .WrongMinVersion
	ifequalfwd LINK_ERR_OTHER_VERSION_TOO_LOW, .OtherPlayerWrongMinVersion
	ifequalfwd LINK_ERR_MISMATCH_GAME_OPTIONS, .WrongOptions
	ifequalfwd LINK_ERR_MISMATCH_BUILD, .WrongBuild
	ifequalfwd LINK_ERR_MISMATCH_RULES, .WrongRules
	ifequalfwd LINK_ERR_INCOMPATIBLE_ROOMS, .IncompatibleRooms
	; (the trade desk comes here too, with the rules of the last battle)
	readmem wChosenCableClubRoom
	ifnotequal LINK_COLOSSEUM - 1, .ComeIn
	readmem wLinkBattleRules
	ifequalfwd LINK_RULE_WORLD, .Championship
.ComeIn:
	writetext Text_PleaseComeIn
	waitbutton
	closetext
	scall PokeCenter2F_EnterRoom
	warpcheck
	end

.FriendNotReady:
	special WaitForOtherPlayerToExit
	writetext Text_FriendNotReady
	yesorno
	iftrue LinkReceptionistScript_DoTradeOrBattle
	endtext

.LinkedToFirstGen:
	special Special_FailedLinkToPast
	writetext Text_CantLinkToThePast
	sjumpfwd .CloseLink

.OldVersionDetected:
	writetext Text_OldVersionDetected
	sjumpfwd .CloseLink

.WrongGameID
	writetext Text_WrongGameID
	sjumpfwd .CloseLink

.WrongVersion
	writetext Text_WrongVersion
	sjumpfwd .CloseLink

.WrongMinVersion
	writetext Text_WrongMinVersion
	sjumpfwd .CloseLink

.OtherPlayerWrongMinVersion
	writetext Text_OtherPlayerWrongMinVersion
	sjumpfwd .CloseLink

.WrongOptions
	writetext Text_WrongOptions
	sjumpfwd .CloseLink

.WrongBuild
	writetext Text_WrongBuild
	sjumpfwd .CloseLink

.WrongRules
	writetext Text_WrongRules
	sjumpfwd .CloseLink

.Championship:
	; Link Edition: the linked World Championship (engine/link/world_link.asm)
	special Special_WorldLinkSession
	ifequalfwd WORLDSESSION_FINAL, .ChampionshipFinal
	ifequalfwd WORLDSESSION_REGISTERED, .Registered
	ifequalfwd WORLDSESSION_SYNCED, .Synced
	ifequalfwd WORLDSESSION_MISMATCH, .OtherBrackets
	writetext Text_WorldLinkError
	sjumpfwd .CloseLink

.ChampionshipFinal:
	writetext Text_WorldLinkFinal
	promptbutton
	sjump .ComeIn

.Registered:
	writetext Text_WorldLinkRegistered
	sjumpfwd .CloseLink

.Synced:
	writetext Text_WorldLinkSynced
	sjumpfwd .CloseLink

.OtherBrackets:
	writetext Text_WorldLinkOtherBrackets
	sjumpfwd .CloseLink

.IncompatibleRooms:
	writetext Text_IncompatibleRooms
.CloseLink:
	special Special_CloseLink
	endtext

.LinkTimedOut:
	special WaitForOtherPlayerToExit
	writetext Text_LinkTimedOut
	yesorno
	iftrue LinkReceptionistScript_DoTradeOrBattle
	endtext

.DidNotSave:
	writetext Text_PleaseComeAgain
.AbortLink:
	special WaitForOtherPlayerToExit
	endtext

LinkReceptionistScript_HasMail:
	writethistext
		text "I am sorry, but"
		line "we are unable to"

		para "trade #mon"
		line "carrying mail"
		cont "at this time."
		done
	waitbutton
	endtext

Script_TradeCenterClosed:
	jumpthistextfaceplayer

	text "I'm sorry--the"
	line "Trade Machine is"
	cont "being adjusted."
	done

LinkReceptionistScript_Battle:
	checkevent EVENT_GOT_A_POKEMON_FROM_ELM
	iffalsefwd .BattleRoomClosed
	special FixPlayerEVsAndStats ; no (trivial) cheating
	opentext
	writetext Text_BattleReceptionistIntro
	yesorno
	iffalse_endtext
	writetext Text_WhichRules
	loadmenu .RulesMenuHeader
	verticalmenu
	closewindow
	iffalse_endtext
	addval -1
	writemem wLinkBattleRules
	ifequalfwd LINK_RULE_RANDOM, .RandomRules
	ifequalfwd LINK_RULE_RISING_STAR, .RisingRules
	ifequalfwd LINK_RULE_UNRESTRICTED, .UnrestrictedRules
	ifequalfwd LINK_RULE_WORLD, .WorldRules
	sjumpfwd .Validate

.WorldRules:
	checkevent EVENT_GOT_MYSTICTICKET_FROM_RED
	iffalse_jumpopenedtext Text_WorldNotYet
	writetext Text_WorldRules
	sjumpfwd .ReadRules

.RandomRules:
	writetext Text_RandomRules
	sjumpfwd .ReadRules
.RisingRules:
	writetext Text_RisingRules
	sjumpfwd .ReadRules
.UnrestrictedRules:
	writetext Text_UnrestrictedRules
.ReadRules:
	promptbutton
.Validate:
	callasm CheckLocalLinkBattleParty
	iffalsefwd .InvalidParty
	special Special_SetBitsForBattleRequest
	sjump LinkReceptionistScript_DoTradeOrBattle

.InvalidParty:
	readmem wLinkBattleRules
	ifequalfwd LINK_RULE_RISING_STAR, .InvalidRising
	ifequalfwd LINK_RULE_WORLD, .InvalidWorld
	jumpopenedtext Text_NoLinkTeam
.InvalidWorld:
	jumpopenedtext Text_InvalidWorld
.InvalidRising:
	jumpopenedtext Text_InvalidRising

.RulesMenuHeader:
	db MENU_BACKUP_TILES
	menu_coords 0, 1, 15, 12
	dw .RulesMenuData
	db 1 ; default option

.RulesMenuData:
	db $80 ; flags
	db NUM_LINK_BATTLE_RULES ; items in wire ID order
	db "Standard@"
	db "Random teams@"
	db "Rising Star@"
	db "Unrestricted@"
	db "Championship@"

.BattleRoomClosed:
	jumpthistextfaceplayer

	text "I'm sorry--the"
	line "Battle Machine is"
	cont "being adjusted."
	done

PokeCenter2F_EnterRoom:
	applymovementlasttalked PokeCenter2FMovementData_ReceptionistWalksUpAndLeft_LookRight
	applymovement PLAYER, PokeCenter2FMovementData_PlayerTakesThreeStepsUp
	readmem wLinkOtherPlayerGender
	scalltable .LinkTrainerTable
	end

.LinkTrainerTable:
	table_width 2
	dw .Male
	dw .Female
	dw .Enby
	dw .Beta
	assert_table_length NUM_PLAYER_GENDERS
.Male:
	variablesprite SPRITE_LINK_TRAINER, SPRITE_CHRIS
	end
.Female:
	variablesprite SPRITE_LINK_TRAINER, SPRITE_KRIS
	end
.Enby:
	variablesprite SPRITE_LINK_TRAINER, SPRITE_CRYS
	end
.Beta:
	variablesprite SPRITE_LINK_TRAINER, SPRITE_BETA
	end

PokeCenter2FMovementData_ReceptionistWalksUpAndLeft_LookRight:
	slow_step_up
	slow_step_left
	turn_head_right
	step_end

PokeCenter2FMovementData_PlayerTakesThreeStepsUp:
	step_up
	step_up
	step_up
	step_end

PokeCenter2FMovementData_PlayerTakesThreeStepsDown:
	step_down
	step_down
	step_down
	step_end

PokeCenter2FMovementData_ReceptionistStepsRightAndDown:
	slow_step_right
	slow_step_down
	step_end

Text_BattleReceptionistIntro:
	text "Welcome to Cable"
	line "Club Colosseum."

	para "You may battle a"
	line "friend here."

	para "Would you like to"
	line "battle?"
	done

Text_TradeReceptionistIntro:
	text "Welcome to Cable"
	line "Trade Center."

	para "You may trade your"
	line "#mon here with"
	cont "a friend."

	para "Would you like to"
	line "trade?"
	done

Text_FriendNotReady:
	text "Your friend is not"
	line "ready."

	para "Would you like to"
	line "keep waiting?"
	done

Text_MustSaveGame:
	text "Before opening the"
	line "link, you must"
	cont "save your game."
	done

Text_PleaseWait:
	text "Please wait."
	done

Text_LinkTimedOut:
	text "The link has been"
	line "closed because of"
	cont "inactivity."

	para "Would you like to"
	line "try again?"
	done

Text_PleaseComeAgain:
	text "Please come again."
	prompt

Text_PleaseComeIn:
	text "Please come in."
	prompt

Text_CantLinkToThePast:
	text "You can't link to"
	line "the past here."
	prompt

Text_OldVersionDetected:
	text "You are connected"
	line "to an old"

	para "version of"
	line "Polished Crystal."
	prompt

Text_WrongGameID:
	text "Your game is not"
	line "compatible with"
	cont "the other game."
	prompt

Text_WrongVersion:
	text "Your game versions"
	line "do not match."

	para "In order to play"
	line "Link Colosseum,"

	para "your game versions"
	line "must match."
	prompt

Text_WrongMinVersion:
	text "Your game does not"
	line "meet the minimum"
	cont "version"

	para "requirement for"
	line "the other game."
	prompt

Text_OtherPlayerWrongMinVersion:
	text "The other game"
	line "system does not"

	para "meet the"
	line "minimum version"
	cont "requirement."
	prompt

Text_WrongOptions:
	text "Your game options"
	line "are not compatible"

	para "with the other"
	line "player."
	prompt

Text_WhichRules:
	text "Which rules would"
	line "you like to use?"
	done

Text_RandomRules:
	text "Random teams: you"
	line "each get six ran-"
	cont "dom #mon at"
	cont "level 50."

	para "Your own team is"
	line "safe. It's back"
	cont "after the battle."
	done

Text_RisingRules:
	text "Bring three #mon"
	line "for Lv.30 battles."
	para "No Eggs, Mewtwo,"
	line "Mew, Lugia, Ho-Oh"
	cont "or Celebi."
	done

Text_UnrestrictedRules:
	text "Bring up to six at"
	line "level 50."
	para "Legendaries and"
	line "any evasion boost"
	cont "are allowed."
	done

Text_NoLinkTeam:
	text "Bring at least one"
	line "usable #mon."
	done

Text_InvalidRising:
	text "This format needs"
	line "three eligible"
	cont "#mon in your"
	cont "party."
	done

Text_WrongRules:
	text "You and your"
	line "friend chose"
	cont "different rules."

	para "Choose the same"
	line "rules to battle."
	prompt

Text_WrongBuild:
	text "Your games are not"
	line "the same build."

	para "To battle, both"
	line "games must be"
	cont "from the same ROM"
	cont "file."
	prompt

Text_IncompatibleRooms:
	text "Incompatible rooms"
	line "were chosen."
	prompt

FriendBattleDeskScript:
; Link Edition: Friend Battles (engine/link/friend_teams.asm), at the desk
; that was the Time Capsule's.
	faceplayer
	opentext
	callasm FriendDeskFirst
	iffalse_jumpopenedtext .NoneText
	writetext .WelcomeText
	promptbutton
.Team:
	writetext .TeamText
	loadmenu .Menu
	verticalmenu
	closewindow
	ifequalfwd 1, .Battle
	ifequalfwd 2, .Look
	ifequalfwd 3, .Remove
	ifequalfwd 4, .Next
	endtext

.Look:
	closetext
	special Special_FriendTeamPreview
	opentext
	sjump .Team

.Next:
	callasm FriendDeskNext
	sjump .Team

.Remove:
	writetext .RemoveText
	yesorno
	iffalse .Team
	callasm FriendDeskRemove
	writetext .RemovedText
	promptbutton
	callasm FriendDeskFirst
	iftrue .Team
	endtext

.Battle:
	callasm FriendDeskArm
	callasm CupSelectTeam
	ifequalfwd CUPTEAM_OK, .Begin
	callasm FriendDeskDone
	ifequal CUPTEAM_CANCEL, .Team
	writetext .RulesText
	promptbutton
	sjump .Team

.Begin:
	writetext .BeginText
	waitbutton
	closetext
	callasm CupBegin
	callasm FriendDeskArm ; (again, after the party's swapped)
	winlosstext .WinText, .LossText
	loadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
	startbattle
	reloadmap
	iftruefwd .Lost
	callasm FriendDeskDone
	callasm CupEnd
	jumptext .WonText

.Lost:
	callasm FriendDeskDone
	callasm CupEnd
	jumptext .LostText

.Menu:
	db MENU_BACKUP_TILES
	menu_coords 0, 0, 10, 9
	dw .Choices
	db 1
.Choices:
	db STATICMENU_CURSOR
	db 4
	db "Battle@"
	db "Look@"
	db "Remove@"
	db "Next@"

.NoneText:
	text "Friend Battles!"

	para "Battle a friend in"
	line "the Colosseum, and"

	para "we'll keep their"
	line "team here, so you"

	para "can battle it"
	line "any time."
	done

.WelcomeText:
	text "Friend Battles!"
	line "Your friends'"
	cont "teams are here."
	done

.TeamText:
	text "This is"
	line "@"
	text_ram wStringBuffer3
	text "'s team."
	done

.RemoveText:
	text "Remove @"
	text_ram wStringBuffer3
	text "'s"
	line "team? Your link"
	cont "records stay."
	done

.RemovedText:
	text "Removed."
	done

.RulesText:
	text "Your team doesn't"
	line "fit the rules"
	cont "this team kept."
	done

.BeginText:
	text "Please enjoy"
	line "your battle!"
	done

.WinText:
	text "Good game!"
	done

.LossText:
	text "Good game!"
	done

.WonText:
	text "You won! Your"
	line "#mon are back"
	cont "to normal."
	done

.LostText:
	text "So close! Your"
	line "#mon are back"
	cont "to normal."
	done

Text_WorldRules:
	text "Championship: the"
	line "linked World"
	cont "Championship."

	para "Link here to join"
	line "a bracket, to hear"

	para "how each other"
	line "did, and for the"
	cont "final."

	para "Six #mon each,"
	line "at level 50."
	done

Text_WorldNotYet:
	text "Championship rules"
	line "are for trainers"

	para "who have beaten"
	line "Red at Mt.Silver."
	done

Text_InvalidWorld:
	text "Bring six #mon,"
	line "and no Eggs."
	done

Text_WorldLinkRegistered:
	text "You and @"
	text_ram wStringBuffer3
	line "are in a World"
	cont "Championship!"

	para "You're in opposite"
	line "halves. Win your"

	para "rounds at the"
	line "Indigo Plateau,"

	para "then link up here"
	line "again."
	done

Text_WorldLinkSynced:
	text "You heard how"
	line "@"
	text_ram wStringBuffer3
	text " is doing."

	para "Ask at the Indigo"
	line "Plateau what's"
	cont "next."
	done

Text_WorldLinkFinal:
	text "You both made the"
	line "final! It's time"
	cont "for the final"
	cont "battle!"
	done

Text_WorldLinkOtherBrackets:
	text "You're each in a"
	line "bracket with"
	cont "someone else."

	para "Finish or leave it"
	line "at the Indigo"
	cont "Plateau first."
	done

Text_WorldLinkError:
	text "The link was"
	line "interrupted."

	para "Nothing changed."
	line "Please try again."
	done
