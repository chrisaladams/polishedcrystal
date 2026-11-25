SECTION "Stack", WRAM0

wRAM0Start::
wStackBottom::
	ds $100 - 1
wStack::
wStackTop::
	db


SECTION "Audio RAM", WRAM0

wMusic::
wMusicPlaying:: db ; nonzero if playing

wChannels::
for n, 1, NUM_MUSIC_CHANS + 1
wChannel{d:n}:: channel_struct wChannel{d:n}
endr

wSFXChannels::
for n, NUM_MUSIC_CHANS + 1, NUM_CHANNELS + 1
wChannel{d:n}:: channel_struct wChannel{d:n}
endr

wCurTrackDuty:: db
wCurTrackIntensity:: db
wCurTrackFrequency:: dw
wCurNoteDuration:: db ; used in MusicE0 and LoadNote

wCurMusicByte:: db
wCurChannel:: db
wVolume::
; corresponds to rAUDVOL
; Channel control / ON-OFF / Volume (R/W)
;   bit 7 - Vin->SO2 ON/OFF
;   bit 6-4 - SO2 output level (volume) (# 0-7)
;   bit 3 - Vin->SO1 ON/OFF
;   bit 2-0 - SO1 output level (volume) (# 0-7)
	db
wSoundOutput::
; corresponds to rAUDTERM
; bit 4-7: ch1-4 so2 on/off
; bit 0-3: ch1-4 so1 on/off
	db
wSoundInput::
; corresponds to rAUDENA
; bit 7: global on/off
; bit 0: ch1 on/off
; bit 1: ch2 on/off
; bit 2: ch3 on/off
; bit 3: ch4 on/off
	db

wMusicID::
wMusicIDLo:: db
wMusicIDHi:: db
wMusicBank:: db
wNoiseSampleAddress::
wNoiseSampleAddressLo:: db
wNoiseSampleAddressHi:: db
wNoiseSampleDelay:: db ; noise delay?
wMusicNoiseSampleSet:: db
wSFXNoiseSampleSet:: db
wLowHealthAlarm::
; bit 7: on/off
; bit 4: pitch
; bit 0-3: counter
	db
wMusicFade::
; fades volume over x frames
; bit 7: fade in/out
; bit 0-5: number of frames for each volume level
; $00 = none (default)
	db
wMusicFadeCount:: db
wMusicFadeID::
wMusicFadeIDLo:: db
wMusicFadeIDHi:: db
wCryPitch:: dw
wCryLength:: dw
wLastVolume:: db
wSFXPriority:: db ; if nonzero, turn off music when playing sfx
wStereoPanningMask:: db
wCryTracks::
; plays only in left or right track depending on what side the monster is on
; both tracks active outside of battle
	db
wSFXDuration:: db
wCurSFX:: db ; id of sfx currently playing
wChannelsEnd::

wMapMusic:: db
wDontPlayMapMusicOnReload:: db
wMusicEnd::

; Has to be outside the area used to save/load audio state
wCh3LoadedWaveform:: db

; Music player
; audio engine input
wChannelSelectorSwitches:: ds 4
wPitchTransposition:: db
wTempoAdjustment:: db
; audio engine output
wNoiseHit:: db


SECTION "Video", WRAM0

wBGMapBuffer:: ds 48
wBGMapBufferEnd::
wBGMapPalBuffer:: ds 48
wBGMapPalBufferEnd::
wBGMapBufferPtrs:: ds 48 ; 24 bg map addresses (16x8 tiles)
wTileAnimationTimer:: db


SECTION "Sprite Animations", WRAM0

; wSpriteAnimDict is a 10x2 dictionary.
; keys: taken from third column of SpriteAnimSeqData
; values: vTiles
wSpriteAnimDict:: ds 10 * 2

wSpriteAnimationStructs::
; Field  0: Index
; Fields 1-3: Loaded from SpriteAnimSeqData
for n, 1, NUM_SPRITE_ANIM_STRUCTS + 1
wSpriteAnim{d:n}:: sprite_anim_struct wSpriteAnim{d:n}
endr
wSpriteAnimationStructsEnd::

wSpriteAnimCount:: db
wCurSpriteOAMAddr:: db

wCurIcon::
wCurIconSpecies:: db
wCurIconPersonality::
wCurIconShiny:: db
wCurIconForm:: db
wCurIconTile:: db

wSpriteAnimAddrBackup::
wCurSpriteAddSubFlags::
	dw
wCurAnimVTile:: db
wCurAnimXCoord:: db
wCurAnimYCoord:: db
wCurAnimXOffset:: db
wCurAnimYOffset:: db
wGlobalAnimYOffset:: db
wGlobalAnimXOffset:: db
wSpriteAnimsEnd::


SECTION "Sprites", WRAM0

wShadowOAM::
for n, OAM_COUNT
wShadowOAMSprite{02d:n}:: sprite_oam_struct wShadowOAMSprite{02d:n}
endr
wShadowOAMEnd::


SECTION "Tilemap and Attrmap", WRAM0

; Some code depend on these being next to each other in memory.
; Walking streams directly to wBGMapBuffer/wBGMapPalBuffer and does not
; maintain these screen buffers. Call LoadMapPart before consuming a full
; overworld screen (as map loading and ReanchorBGMap already do).
wTilemap::
; 20x18 grid of 8x8 tiles
	ds SCREEN_AREA
wTilemapEnd::

wAttrmap::
; 20x18 grid of palettes for 8x8 tiles
; read horizontally from the top row
; bit 7: priority
; bit 6: y flip
; bit 5: x flip
; bit 4: pal # (non-cgb)
; bit 3: vram bank (cgb only)
; bit 2-0: pal # (cgb only)
	ds SCREEN_AREA
wAttrmapEnd::


SECTION UNION "Misc 404", WRAM0
; music player

wMusicPlayerWRAM::
wSongSelection:: dw
wNumNoteLines:: db
wTmpCh:: db
wChLastNotes:: ds 3
wVolTimer:: db
wC1Vol:: db
wC1VolSub:: db
wC2Vol:: db
wC2VolSub:: db
wC3Vol:: db
wC3VolSub:: db
wC4Vol:: db
wC4VolSub:: db
wNoteEnded:: ds 3
wSongInfoSwitch:: db
;wRenderedWaveform:: db
wPitchesTmp:: ds 4
;wWaveformTmp:: ds 16
wTmpValue:: db
; song list
wSelectorTop:: db
wSelectorCur:: db
; song editor
wChannelSelector:: db
wAdjustingTempo:: db
wMusicPlayerWRAMEnd::


SECTION UNION "Misc 404", WRAM0
; odd egg

wOddEgg:: party_struct wOddEgg
wOddEggName:: ds MON_NAME_LENGTH
wOddEggOTName:: ds MON_NAME_LENGTH


SECTION UNION "Misc 404", WRAM0
; hall of fame temp struct

wHallOfFameTemp:: hall_of_fame wHallOfFameTemp


SECTION UNION "Misc 404", WRAM0
; timeset temp storage

wTimeSetBuffer:: ds 20
wInitHourBuffer:: ds 13
wInitMinuteBuffer:: ds 17


SECTION UNION "Misc 404", WRAM0
; link patch lists

wPlayerPatchLists:: ds 200
wOTPatchLists:: ds 200


SECTION UNION "Misc 404", WRAM0
; link engine

wLinkMisc:: ds 10
wLinkPlayerFixedPartyMon1ID:: ds 3
	ds 37


SECTION UNION "Misc 404", WRAM0
; polished link transfer buffer

wLinkReceivedPolishedMiscBuffer:: ds LINK_MISC_BUFFER_LENGTH
wLinkPolishedMiscBuffer:: ds LINK_MISC_BUFFER_LENGTH


SECTION UNION "Misc 404", WRAM0
; Link Edition: the linked World Championship's exchange (engine/link/world_link.asm)

wWorldLinkSend:: ds WORLD_LINK_BUFFER_LENGTH
wWorldLinkReceive:: ds WORLD_LINK_BUFFER_LENGTH
wWorldLinkMine:: ds WORLD_LINK_MESSAGE_LENGTH
wWorldLinkTheirs:: ds WORLD_LINK_MESSAGE_LENGTH
wWorldLinkMineFirst:: ds WORLD_LINK_MESSAGE_LENGTH
wWorldLinkTheirsFirst:: ds WORLD_LINK_MESSAGE_LENGTH
wWorldLinkPlan:: db
; (also at the Indigo Plateau's desk, outside battle)
wWorldLinkRecord:: ds WORLD_LINK_LENGTH


SECTION UNION "Misc 404", WRAM0
; battle + pokédex (merged because pokédex can be called from battle)

; wLCDPokedex is defined in a LOAD UNION block in engine/pokedex/lcd.asm
; Reserve space for it at the beginning of this LOAD UNION
	ds 15
	assert wLCDPokedexEnd - wLCDPokedex == @ - STARTOF("Misc 404")

; Battle data
wBattle::

wEnemyMoveStruct::  move_struct wEnemyMoveStruct
wPlayerMoveStruct:: move_struct wPlayerMoveStruct

wEnemyMonNickname::  ds MON_NAME_LENGTH
wBattleMonNickname:: ds MON_NAME_LENGTH

wBattleMon:: battle_struct wBattleMon

wWildMon:: db
wBadgeBaseLevel:: db
wEnemyTrainerItem1:: db
wEnemyTrainerItem2:: db
wEnemyTrainerBaseReward:: db
wEnemyTrainerAIFlags:: ds 3
wOTClassName:: ds TRAINER_CLASS_NAME_LENGTH

wCurOTMon:: db

wTypeModifier::
; >$10: super effective
;  $10: normal
; <$10: not very effective
; bit 7: stab
	db

wMoveHitState::
; bit 0: move was a critical hit
; bit 1: move hit a substitute
	db

wAttackMissed::
; nonzero for a miss
	db

wBattleSubStatusWRAM::
wPlayerSubStatus1::
; bit
; 7 attract
; 6 flash fire
; 5 endure
; 4 unused
; 3 identified
; 2 protect
; 1 curse
; 0 unburden
	db
wPlayerSubStatus2::
; bit
; 7 cant run
; 6 destiny bond
; 5 lock-on
; 4 transformed
; 3 magic bounce
; 2 fainted
; 1 minimized
; 0 unused
	db
wPlayerSubStatus3::
; NOTE: these should all stay together!
; bit
; 7 confused
; 6 flying
; 5 underground
; 4 charged
; 3 recharge
; 2 in loop
; 1 rampage
; 0 rollout
	db
wPlayerSubStatus4::
; bit
; 7 leech seed
; 6 rage
; 5 flinched
; 4 substitute
; 3 roost
; 2 focus energy
; 1 unused
; 0 curled
	db

wEnemySubStatus1::
; see wPlayerSubStatus1
	db
wEnemySubStatus2::
; see wPlayerSubStatus2
	db
wEnemySubStatus3::
; see wPlayerSubStatus3
	db
wEnemySubStatus4::
; see wPlayerSubStatus4
	db

; Some code (e.g. HandleRampage) depend on the order of these
wPlayerAbility:: db
wPlayerRolloutCount:: db
wPlayerConfuseCount:: db
wPlayerToxicCount:: db
wPlayerDisableCount:: db
wPlayerEncoreCount:: db ; also for choice-locking
wPlayerPerishCount:: db
wPlayerProtectCount:: db

wEnemyAbility:: db
wEnemyRolloutCount:: db
wEnemyConfuseCount:: db
wEnemyToxicCount:: db
wEnemyDisableCount:: db
wEnemyEncoreCount:: db
wEnemyPerishCount:: db
wEnemyProtectCount:: db

wCriticalCount:: ds PARTY_LENGTH ; for g-Farfetch'd evolution
wBattleSubStatusWRAMEnd::

wDamageTaken::
; Format: $xy yy, x = total multihit hits, y = total damage
	dw

wBattleReward:: ds 3
wBattleAnimParam:: db

wPartyBackupItems::
; Back up of party items before a battle. Modified in-battle for consumed/harvested.
; Berries and items stolen from wild Pokémon since those changes are retained.
	ds PARTY_LENGTH

wPartyUsedItems::
; For the benefit of Pickup/Harvest
	ds PARTY_LENGTH

wOTPartyUsedItems::
; See PartyUsedItems
	ds PARTY_LENGTH

; What move was selected last.
; Used for Choice locking and the Metronome item
wPlayerSelectedMove:: db
wEnemySelectedMove:: db

; How much the Metronome item is boosted. (Counts even if you don't have the item.)
wPlayerMetronomeCount:: db
wEnemyMetronomeCount:: db

wPlayerCudChewBerry:: db
wEnemyCudChewBerry:: db

wPartyParticipants:: ds PARTY_LENGTH

wDeferredSwitch:: db

wPlayerSwitchTarget:: db
wEnemySwitchTarget:: db

wBattleScriptBufferLoc:: dw
wMoveState:: db

wPlayerStatLevels::
; 07 neutral
wPlayerAtkLevel:: db
wPlayerDefLevel:: db
wPlayerSpeLevel:: db
wPlayerSAtkLevel:: db
wPlayerSDefLevel:: db
wPlayerAccLevel:: db
wPlayerEvaLevel:: db
	ds 1

wEnemyStatLevels::
; 07 neutral
wEnemyAtkLevel:: db
wEnemyDefLevel:: db
wEnemySpeLevel:: db
wEnemySAtkLevel:: db
wEnemySDefLevel:: db
wEnemyAccLevel:: db
wEnemyEvaLevel:: db
	ds 1

wEnemyTurnsTaken:: db
wPlayerTurnsTaken:: db

wPlayerSubstituteHP:: dw
wEnemySubstituteHP:: dw

wBackupEnemyMonBaseExp:: db

wCurPlayerMove:: db
wCurEnemyMove:: db

wLinkBattleRNCount:: db ; how far through the prng stream

wEnemyItemState:: db

wCurEnemyMoveNum:: db

wEnemyHPAtTimeOfPlayerSwitch:: dw
wPayDayMoney:: ds 3

wSafariMonAngerCount:: db
wSafariMonEating:: db

wAlreadyDisobeyed:: db

wAlreadyExecuted:: db

wAlreadySawWeather:: db

wWhichMonFaintedFirst:: db

; exists so you can't counter on switch
wLastPlayerCounterMove:: db
wLastEnemyCounterMove:: db

wTrickRoom:: db

wBattleLowHealthAlarm:: db

	ds 3 ; unused

wPlayerHazards::
; bit
; 6-7 toxic spikes
; 4-5 spikes
; 0-3 unused
	db

wEnemyHazards::
; see wPlayerHazards
	db

wPlayerScreens::
; bit
; 4-7 light screen
; 0-3 reflect
	db
wPlayerGuards::
; bit
; 4-7 mist
; 0-3 safeguard
	db

	ds 2

wEnemyScreens::
; see wPlayerScreens
	db
wEnemyGuards::
; see wPlayerGuards
	db

	ds 2

wBattleWeather::
; 00 normal
; 01 rain
; 02 sun
; 03 sandstorm
; 04 rain stopped
; 05 sunlight faded
; 06 sandstorm subsided
	db

wWeatherCount:: db ; # turns remaining

wChangedStat::
; bit 4-7: how many stages to raise/lower + 1 (between +1 and +12)
; bit 0-3: which stat to raise/lower
	db

wEffectFailed:: db
wFailedMessage:: db
wEnemyGoesFirst:: db

wPlayerUsedMoves::
; add a move that has been used once by the player
; added in order of use
	ds NUM_MOVES

wEnemyAISwitchScore:: db
wEnemySwitchMonParam:: db
wEnemySwitchMonIndex:: db

wTempLevel:: db

wLastPlayerMon:: db

wLastPlayerMove:: db
wLastEnemyMove:: db

wEnemyUsingItem:: db

wPlayerFutureSightCount:: db
wEnemyFutureSightCount:: db
wPlayerFutureSightDamage:: dw
wEnemyFutureSightDamage:: dw
wPlayerTrappingMove:: db
wEnemyTrappingMove:: db
wPlayerWrapCount:: db
wEnemyWrapCount:: db
wPlayerCharging:: db
wEnemyCharging:: db

wGivingExperienceToExpShareHolders:: db

wInAbility::
; bit 4: enemy ability visible
; bit 3: player ability visible
; bit 2: enemy ability pending
; bit 1: player ability pending
; bit 0: ongoing ability trigger
	db

wBattleEnded:: db

wAmuletCoin:: db

	ds 1

wDVAndPersonalityBuffer:: ds 5
wBattleEnd::

; Pokédex data.

; For setting up a new HBlank trigger
wPokedex_PendingLYC:: db
wPokedex_PendingHBlankFunction:: dw

; Palettes and tile offset for listview minis
UNION
wPokedex_UnownCursor: db
NEXTU
wPokedex_Pals::
wPokedex_Row1::
wPokedex_Row1Tile: db ; Sprite offset for dex minis col 2-4
wPokedex_Row1Pals:: ds COLOR_SIZE * 3 * 5 ; 3 15bit colors per pal, 5 columns
wPokedex_Row2::
wPokedex_Row2Tile: db
wPokedex_Row2Pals:: ds COLOR_SIZE * 3 * 5
wPokedex_Row3::
wPokedex_Row3Tile: db
wPokedex_Row3Pals:: ds COLOR_SIZE * 3 * 5
wPokedex_PalsEnd::
ENDU

; Pokémon info (frontpic, types, etc) is stored in either vbk0 or vbk1. This is
; cycled each time we move the cursor. The reason for this is so that we can
; update the entire display smoothly in a single frame without noticeable delay.
wPokedex_MonInfoBank:: db

wPokedex_Personality::
; bit 7 = shiny
; bit 0 = has other form (eligible to switch to)
wPokedex_Shiny::
wPokedex_OtherForm:: db
wPokedex_Form:: db

wPokedexOAM_DexNoX:: db
wPokedexOAM_DexNoY:: db
wPokedexOAM_IsCaught:: db

wPokedex_NumSeen:: dw
wPokedex_NumOwned:: dw
wPokedex_CursorPos:: db
wPokedex_Offset:: db
wPokedex_FirstIconTile:: db
UNION
wPokedex_Rows:: db
wPokedex_LastCol:: db ; 1-5 in case the final row isn't completely filled
NEXTU
wPokedex_FinalEntry:: dw ; Final entry. Overwritten with rows/lastcol later.
ENDU
wPokedex_GFXFlags:: db ; flags for various gfx update types
wPokedex_DisplayMode:: db ; current pokédex display

wPokedex_InSearchMode:: db

; 0 when not in a current search, otherwise vblank counter at search start.
; If vblank counter happens to be zero, it's treated as 255.
wPokedex_SearchInProgress:: db

wPokedex_Search::
wPokedex_SearchOrder:: db
wPokedex_SearchData::
wPokedex_SearchType1:: db
wPokedex_SearchType2:: db
wPokedex_SearchGroup1:: db
wPokedex_SearchGroup2:: db
wPokedex_SearchColor:: db
wPokedex_SearchBody:: db
wPokedex_SearchDataEnd::
wPokedex_SearchEnd::
wPokedex_MenuCursorY:: db


SECTION UNION "Misc 404", WRAM0
; trade
	ds 172

wTrademons::
wPlayerTrademon:: trademon wPlayerTrademon
wOTTrademon:: trademon wOTTrademon
wTrademonsEnd::
wTradeAnimPointer:: dw
wLinkPlayer1Name:: ds NAME_LENGTH
wLinkPlayer2Name:: ds NAME_LENGTH
wLinkTradeSendmonData::
wLinkTradeSendmonSpecies:: db
wLinkTradeSendmonPersonality::
wLinkTradeSendmonShiny:: db
wLinkTradeSendmonForm:: db
wLinkTradeGetmonData::
wLinkTradeGetmonSpecies:: db
wLinkTradeGetmonPersonality::
wLinkTradeGetmonShiny:: db
wLinkTradeGetmonForm:: db


SECTION UNION "Misc 404", WRAM0
; naming screen
	ds 172

wNamingScreenDestinationPointer:: dw
wNamingScreenCurNameLength:: db
wNamingScreenMaxNameLength:: db
wNamingScreenType:: db
wNamingScreenCursorObjectPointer:: dw
wNamingScreenLastCharacter:: db
wNamingScreenStringEntryCoord:: dw
wNamingScreenKeyboardWidth:: db


SECTION UNION "Misc 404", WRAM0
; pokegear
	ds 132

wRadioCompressedText:: ds 2 * SCREEN_WIDTH

wPokegearPhoneLoadNameBuffer:: db
wPokegearPhoneCursorPosition:: db
wPokegearPhoneScrollPosition:: db
wPokegearPhoneSelectedPerson:: db
wPokegearPhoneSubmenuCursor:: db
wPokegearMapCursorObjectPointer:: dw
wPokegearMapCursorLandmark:: db
wPokegearMapPlayerIconLandmark:: db
wPokegearRadioChannelBank:: db
wPokegearRadioChannelAddr:: dw
wPokegearRadioMusicPlaying:: db
wPokegearNumberBuffer:: db
wPokegearMapCursorSpawnpoint:: db
wPokegearPhoneMaxContact:: db
; Only live while the Pokégear map is open.
wQuestMapCount:: db
wQuestMapSelected:: db
wQuestMapMain:: db
wQuestMapRegion:: db
wQuestMapLeads:: ds NUM_LANDMARKS ; goal table size is asserted against this capacity


SECTION UNION "Misc 404", WRAM0
; slot machine
	ds 172

wSlots::
wReel1:: slot_reel wReel1
wReel2:: slot_reel wReel2
wReel3:: slot_reel wReel3
wReel1Stopped:: ds 3
wReel2Stopped:: ds 3
wReel3Stopped:: ds 3
wSlotBias:: db
wSlotBet:: db
wFirstTwoReelsMatching:: db
wFirstTwoReelsMatchingSevens:: db
wSlotMatched:: db
wCurReelStopped:: ds 3
wPayout:: dw
wCurReelXCoord:: db
wCurReelYCoord:: db
	ds 2
wSlotBuildingMatch:: db
wSlotsDataEnd::
	ds 28
wSlotsEnd::


SECTION UNION "Misc 404", WRAM0
; card flip
	ds 172

wCardFlip::
wDeck:: ds 24
wDeckEnd::
wCardFlipNumCardsPlayed:: db
wCardFlipFaceUpCard:: db
wDiscardPile:: ds 24
wDiscardPileEnd::
wCardFlipEnd::


SECTION UNION "Misc 404", WRAM0
; Unown puzzle
	ds 172

wUnownPuzzle::
wPuzzlePieces:: ds 6 * 6
wUnownPuzzleEnd::


SECTION UNION "Misc 1300", WRAM0
; overworld map

; large enough for 32x27 Route41.ablk; (32+6)x(27+6) = 1254
wOverworldMapBlocks:: ds 1300
wOverworldMapBlocksEnd::


SECTION UNION "Misc 1300", WRAM0
; psychic inver party

; large enough for 4x4 KantoHouse1.asm in wOverworldMapBlocks
	ds (4 + 6) * (4 + 6)

wInverIndexes:: ds NUM_INVER_MONS

wInverGroup::
	ds 8 ; length + "Inver@" + flags
	rept PARTY_LENGTH
		ds 3 ; dbp <level>, <species>, <form>
		ds 3 ; db <item>, <dvs>, <nat | abil>
		ds NUM_MOVES ; moves
	endr


SECTION UNION "Misc 1300", WRAM0
; credits image

wCreditsBlankFrame2bpp:: ds 16 tiles


SECTION UNION "Misc 1300", WRAM0
; Bill's PC

	; LCD hblank code block. Labels are defined as part of the code.
	ds $cf
	assert BillsPC_LCDCode.End - BillsPC_LCDCode == @ - STARTOF("Misc 1300")

; If you change ordering of this, remember to fix LCD hblank code too.
; Note that (as of when comment was written), hblank can't always keep up
; if doing 4 pals in one go during party shifting.
wBillsPC_CurPals::
wBillsPC_CurPartyPals:: ds 2 * 2 * 2 ; 2 bytes per color, 2 colors, 2 mons
wBillsPC_CurMonPals:: ds 2 * 2 * 4 ; 2 bytes per color, 2 colors, 4 mons

; Stores palettes used for party+box.
wBillsPC_PalList::
wBillsPC_PokepicPal:: ds 2 * 2 * 1
wBillsPC_PokerusShinyPal:: ds 2 * 2 * 1
wBillsPC_MonPals1:: ds 2 * 2 * 4

	ds 2 * 2 * 2 ; unused row2 BG2-3

wBillsPC_MonPals2:: ds 2 * 2 * 4
wBillsPC_PartyPals3:: ds 2 * 2 * 2
wBillsPC_MonPals3:: ds 2 * 2 * 4
wBillsPC_PartyPals4:: ds 2 * 2 * 2
wBillsPC_MonPals4:: ds 2 * 2 * 4
wBillsPC_PartyPals5:: ds 2 * 2 * 2
wBillsPC_MonPals5:: ds 2 * 2 * 4

; Species lists
wBillsPC_PartyList:: ds 6 * 2
wBillsPC_BoxList:: ds 20 * 2

wBillsPC_HeldIcon:: dw
wBillsPC_QuickIcon:: dw

; Cursor data
wBillsPC_CursorItem:: db ; what item is selected.
wBillsPC_CursorPos:: db ; 0-3 * 4*row, row 0 is title. Bit 7 means in party.
wBillsPC_CursorHeldBox:: db ; 0 for party, 1-15 otherwise
wBillsPC_CursorHeldSlot:: db ; 0 for nothing held, or 1-20 (1-6 if party)
wBillsPC_CursorDestBox:: db ; 0 for party, 1-15 otherwise
wBillsPC_CursorDestSlot:: db ; 0 for release, or 1-20 (1-6 if party)
wBillsPC_CursorMode:: db ; 0 for regular mode (red), 1 for swap mode (blue), 2 for item mode (green)
wBillsPC_CursorAnimFlag:: db ; manage cursor behaviour
wBillsPC_ItemVWF:: ds 10 tiles

; Quick-move sprite data.
wBillsPC_QuickFrom::
wBillsPC_QuickFromBox:: db
wBillsPC_QuickFromSlot:: db
wBillsPC_QuickFromX:: db
wBillsPC_QuickFromY:: db

wBillsPC_QuickTo::
wBillsPC_QuickToBox:: db
wBillsPC_QuickToSlot:: db
wBillsPC_QuickToX:: db
wBillsPC_QuickToY:: db
wBillsPC_QuickFrames:: db

wBillsPC_ApplyThemePals:: db ; used by _CGB_BillsPC

wSummaryScreenPals:: ds 8 palettes

wSummaryScreenOAM::
for n, OAM_COUNT
wSummaryScreenOAMSprite{02d:n}:: sprite_oam_struct wSummaryScreenOAMSprite{02d:n}
endr
wSummaryScreenTypes:: ds 6
wSummaryScreenStep:: db
wSummaryScreenInterrupts:: ds 2 * 16
wSummaryScreenPage:: db
wSummaryScreenMoveCount:: db
wSummaryMoveSwap:: db

; Used to align window buffer for DMA copying
; Feel free to use or move data, an assert will fail if the memory becomes misaligned
ds 9
assert @ % 16 == 0

wSummaryScreenWindowBuffer:: ds 32 * 10
wSummaryScreenPPTileBuffer:: ds 3 * TILE_1BPP_SIZE


SECTION UNION "Misc 1300", WRAM0
; raw link data

wLinkData:: ds 1300
wLinkDataEnd::


SECTION UNION "Misc 1300", WRAM0
; decoded link data members (without the serial preamble)

wLinkPlayerName:: ds NAME_LENGTH
wLinkPartyCount:: db

UNION
; link player data
wLinkPlayerID:: dw
wLinkPlayerData::
for n, 1, PARTY_LENGTH + 1
wLinkPlayerPartyMon{d:n}:: party_struct wLinkPlayerPartyMon{d:n}
endr

wLinkPlayerPartyMonOTs::
for n, 1, PARTY_LENGTH + 1
wLinkPlayerPartyMon{d:n}OT:: ds NAME_LENGTH
endr

wLinkPlayerPartyMonNicknames::
for n, 1, PARTY_LENGTH + 1
wLinkPlayerPartyMon{d:n}Nickname:: ds MON_NAME_LENGTH
endr
wLinkPlayerDataEnd::

NEXTU
; link patch lists
wLinkPatchList1:: ds SERIAL_PATCH_LIST_LENGTH
wLinkPatchList2:: ds SERIAL_PATCH_LIST_LENGTH
ENDU


SECTION UNION "Misc 1300", WRAM0
; link mail data
	ds 500

wLinkPlayerMail::
wLinkPlayerMailPreamble:: ds SERIAL_MAIL_PREAMBLE_LENGTH
wLinkPlayerMailMessages:: ds (MAIL_MSG_LENGTH + 1) * PARTY_LENGTH
wLinkPlayerMailMetadata:: ds (MAIL_STRUCT_LENGTH - (MAIL_MSG_LENGTH + 1)) * PARTY_LENGTH
wLinkPlayerMailPatchSet:: ds 103
wLinkPlayerMailEnd::
	ds 10
wLinkOTMail::
wLinkOTMailMessages:: ds (MAIL_MSG_LENGTH + 1) * PARTY_LENGTH
wLinkOTMailMetadata:: ds (MAIL_STRUCT_LENGTH - (MAIL_MSG_LENGTH + 1)) * PARTY_LENGTH
wOTPlayerMailPatchSet:: ds 103 + SERIAL_MAIL_PREAMBLE_LENGTH
wLinkOTMailEnd::
	ds 10


SECTION UNION "Misc 1300", WRAM0
; received link mail data
	ds 500

wLinkReceivedMail:: ds MAIL_STRUCT_LENGTH * PARTY_LENGTH
wLinkReceivedMailEnd:: db


SECTION UNION "Misc 1300", WRAM0

; GB Printer data
wGameboyPrinterRAM::
wGameboyPrinter2bppSource:: ds 40 tiles
wGameboyPrinter2bppSourceEnd::
wPrinterRowIndex:: db

; Printer data
wPrinterData:: ds 4
wPrinterChecksum:: dw
wPrinterHandshake:: db
wPrinterStatusFlags::
; bit 7: set if error 1 (battery low)
; bit 6: set if error 4 (too hot or cold)
; bit 5: set if error 3 (paper jammed or empty)
; if this and the previous byte are both $ff: error 2 (connection error)
	db

wHandshakeFrameDelay:: db
wPrinterSerialFrameDelay:: db
wPrinterSendByteOffset:: dw
wPrinterSendByteCounter:: dw

; tilemap backup?
wPrinterTilemapBuffer:: ds SCREEN_AREA
wPrinterStatus:: db
	ds 1
; High nibble is for margin before the image, low nibble is for after.
wPrinterMargins:: db
wPrinterExposureTime:: db
	ds 16
wGameboyPrinterRAMEnd::

wPrinterOpcode:: db


SECTION UNION "Misc 1300", WRAM0

wMPNotes:: ds 3 * 256


SECTION "WRAM 0", WRAM0

wMonType:: db

wCurSpecies::
wCurMove::
wCreditsSpawn::
	db

wTimeSinceText:: db

wCurOptionsPage:: db

wBattleTowerBattleEnded:: db

wCurForm:: db

wRNGState:: ds 4
wRNGCumulativeDividerPlus:: dw
wRNGCumulativeDividerMinus:: db

wBoxAlignment:: db
wInputType:: db
wAutoInputAddress:: dw
wAutoInputBank:: db
wAutoInputLength:: db

wMonStatusFlags:: db
wGameLogicPaused:: db
wSpriteUpdatesEnabled:: db
wMapTimeOfDay:: db

wPrevDexEntry:: db

wPrevLandmark:: db
wCurLandmark:: db
wLandmarkSignTimer:: dw
wLinkMode::
; 0 not in link battle
; 1 link battle
; 4 mobile battle
	db

wPlayerNextMovement:: db

wNumHits:: db

wMovementObject:: db
wMovementDataPointer:: ds 3 ; dba

wMovementByteWasControlSwitch:: db

UNION
wObjectPriorities:: ds NUM_OBJECT_STRUCTS
NEXTU
wMovementPointer:: dw
	ds 2
wTempObjectCopyMapObjectIndex:: db
wTempObjectCopySprite:: db
wTempObjectCopySpriteVTile:: db
wTempObjectCopyPalette:: db
wTempObjectCopyMovement:: db
wTempObjectCopyRange:: db
wTempObjectCopyX:: db
wTempObjectCopyY:: db
wTempObjectCopyRadius:: db
ENDU

wTileDown:: db
wTileUp:: db
wTileLeft:: db
wTileRight:: db

wTilePermissions::
; set if tile behavior prevents
; you from walking in that direction
; bit 3: down
; bit 2: up
; bit 1: left
; bit 0: right
	db

wPanningAroundTinyMap:: db
wSavedXCoord:: db

wLinkOtherPlayerGameID:: db
wLinkOtherPlayerVersion:: dw
wLinkOtherPlayerMinTradeVersion:: dw
wLinkOtherPlayerGender:: db

wPalFlags:: db

wPlayerCurrentOAMSlot:: db

wMapSetupFlags:: db

wPrinterConnectionOpen:: db

wMemCGBLayout:: db

UNION
wCreditsPos:: dw
wCreditsTimer:: db
NEXTU
wTrainerCardBadgePaletteAddr:: dw
NEXTU
wPlayerHPPal:: db
wEnemyHPPal:: db
wHPPals:: ds PARTY_LENGTH
wCurHPPal:: db
wHPPalIndex:: db
ENDU

; link data
UNION
wOtherPlayerLinkMode:: db
wOtherPlayerLinkAction:: db
	ds 3
wPlayerLinkAction:: db
	ds 4
NEXTU
wLinkReceivedSyncBuffer:: ds 5
wLinkPlayerSyncBuffer:: ds 5
ENDU

wLinkTimeoutFrames:: dw
wLinkByteTimeout:: dw

wJumptableIndex:: db ; must come right before the union

UNION
; intro and title data
wIntroSceneFrameCounter:: db
wIntroSceneTimer:: db

NEXTU
; title data
	ds 1
wTitleScreenTimer:: dw

NEXTU
; credits data
wCreditsBorderFrame:: db
wCreditsBorderMon:: db
wCreditsLYOverride:: db

NEXTU
; pokedex
wPrevDexEntryJumptableIndex:: db
wPrevDexEntryBackup:: db

NEXTU
; pokegear
wPokegearCard:: db
wPokegearMapRegion:: db
wTownMapCanFlyHere:: db

NEXTU
; pack
wCurPocket:: db
wPackUsedItem:: db

NEXTU
; trainer card badges
wTrainerCardBadgeFrameCounter:: db
wTrainerCardBadgeTileID:: db
NEXTU
wLinkCardPage:: db ; zero-based roster page
wLinkCardPeriod:: db ; zero for lifetime, nonzero for current year
wLinkCardMore:: db

NEXTU
; slot machine
wSlotsDelay:: db

NEXTU
; card flip
wCardFlipCursorY:: db
wCardFlipCursorX:: db
wCardFlipWhichCard:: db

NEXTU
; magnet train
wMagnetTrainOffset:: db
wMagnetTrainPosition:: db
wMagnetTrainWaitCounter:: db

NEXTU
; unown puzzle data
wHoldingUnownPuzzlePiece:: db
wUnownPuzzleCursorPosition:: db
wUnownPuzzleHeldPiece:: db

NEXTU
; battle transitions
wBattleTransitionCounter:: db
wBattleTransitionSineWaveOffset::
wBattleTransitionSpinQuadrant:: db

NEXTU
; summary screen
wSummaryScreenFlags:: db

NEXTU
; miscellaneous
wFrameCounter::
wMomBankDigitCursorPosition::
wNamingScreenLetterCase::
wHallOfFameMonCounter::
wTradeDialog::
wRandomValue::
wEchoRAMTest::
	db
wPrinterQueueLength::
wFrameCounter2::
	db

ENDU

wPalFadeMode::
; bit 0-1: which (0: everything, 1: BG, 2: OBJ)
; bit 2: perform a smooth dark flash
; bit 3: partial fade (fade b of c frames)
; bit 4: skip the last palette
	db

wMenuMetadata::
wWindowStackPointer:: dw
wMenuJoypad:: db
wMenuSelection:: db
wMenuSelectionQuantity:: db
wWhichIndexSet:: db
wScrollingMenuCursorPosition:: db
wWindowStackSize:: db
	ds 8
wMenuMetadataEnd::

; menu header
wMenuHeader::
wMenuFlags:: db
wMenuBorderTopCoord:: db
wMenuBorderLeftCoord:: db
wMenuBorderBottomCoord:: db
wMenuBorderRightCoord:: db
wMenuDataPointer:: dw
wMenuCursorBuffer:: dw
; end menu data header
wMenuDataBank:: db ; menu data bank?
	ds 6
wMenuHeaderEnd::

; TODO: organize this section better (integrate unions from pret/pokecrystal)
wMenuData::
wMenuDataFlags::
; bit 7: When set, start printing text one tile to the right of the border
;        In scrolling menus, SELECT is functional
; bit 6: When set, start printing text one tile below the border
;        In scrolling menus, START is functional
; bit 5: ????
; bit 4: ????
; bit 3: ????
; bit 2: Enable Start button
; bit 1: Enable Select button
; bit 0: Disable B button
	db
wMenuData_ScrollingMenuHeight::
wMenuDataItems::
	db
wMenuDataIndicesPointer::
wMenuDataSpacing::
wMenuData_ScrollingMenuWidth::
	db
wMenuData_2DMenuItemStringsBank::
wMenuData_ScrollingMenuSpacing::
	db
wMenuData_2DMenuItemStringsAddr::
wMenuDataDisplayFunctionPointer::
wMenuData_ItemsPointerBank::
	db
wMenuData_ItemsPointerAddr::
	db
wMenuDataPointerTableAddr::
wMenuData_2DMenuFunctionBank::
	db
wMenuData_2DMenuFunctionAddr::
wMenuData_ScrollingMenuFunction1::
	ds 3
wMenuData_ScrollingMenuFunction2::
	ds 3
wMenuData_ScrollingMenuFunction3::
	ds 3
wMenuDataEnd::

w2DMenuData::
w2DMenuCursorInitY:: db
w2DMenuCursorInitX:: db
w2DMenuNumRows:: db
w2DMenuNumCols:: db
w2DMenuFlags1::
; bit 7: Disable checking of wMenuJoypadFilter
; bit 6: Enable sprite animations
; bit 5: Wrap around vertically
; bit 4: Wrap around horizontally
; bit 3: Set bit 7 in w2DMenuFlags2 and exit the loop if bit 5 is disabled and we tried to go too far down
; bit 2: Set bit 7 in w2DMenuFlags2 and exit the loop if bit 5 is disabled and we tried to go too far up
; bit 1: Set bit 7 in w2DMenuFlags2 and exit the loop if bit 4 is disabled and we tried to go too far left
; bit 0: Set bit 7 in w2DMenuFlags2 and exit the loop if bit 4 is disabled and we tried to go too far right
	db
w2DMenuFlags2:: db
w2DMenuCursorOffsets:: db
wMenuJoypadFilter:: db

wMenuCursorY:: db
wMenuCursorX:: db
wCursorOffCharacter:: db
wCursorCurrentTile:: dw
	ds 3
w2DMenuDataEnd::

wMonPicSize:: db
wMonAnimationSize:: db

wPendingOverworldGraphics:: db
wTextDelayFrames:: db

wGenericDelay:: db

wGameTimerPaused:: db

wInputFlags::
; bits 7, 6, and 4 can be used to disable joypad input
; bit 4
; bit 6: mon fainted?
; bit 7: SGB flag?
	db

wOverworldDelayTimer::
; amount of overworld frames to skip DelayFrame for
	db

wInBattleTowerBattle::
; 0 not in BattleTower-Battle
; 1 BattleTower-Battle
	db

wBattleMenuFlags::
; bit 0-2: quick-access buttons (b/start/select)
; bit 3: quick-select last pack item
	db

wFXAnimID::
wFXAnimIDLo:: db
wFXAnimIDHi:: db

wPlaceBallsX:: db
wPlaceBallsY:: db

; palette backups?
wBGP:: db
wOBP0:: db
wOBP1:: db

wOverworldWeatherTimer:: db
wOverworldWeatherCooldown:: db
wSpriteOverlapCount:: db
wWeatherFlags:: db
wPrevWeather:: db
wCurWeather:: db
wPrevOvercastIndex:: db

wPalState:: db
wPalWhiteState:: db

wPalStates::
wPrevPalStates::
wPrevPalWeatherState:: db
wPrevPalDarknessState:: db
wPrevPalOvercastIndexState:: db
wPrevPalTimeOfDayPalState:: db

wCurPalStates::
wCurPalWeatherState:: db
wCurPalDarknessState:: db
wCurPalOvercastIndexState:: db
wCurPalTimeOfDayPalState:: db

; volatile footprints in sand
wFootprintQueue:: ds 3 * 2 + 1

wColoredMaleFemaleShinyTiles:: ds 3 tiles

wSpecialPalStart:: db
wSpecialPalCount:: db

wSPBuffer:: dw


SECTION "Options", WRAM0

wOptions3::
; bit 0: keyword abc/qwerty
; bit 1: nicknames always ("Yes")
; bit 2: nicknames never ("No")
; bit 3: reserved by older saves
; (bits 1 and 2 are never both set; both clear = "Ask")
; bits 3-7: unused
	db

wOptions::

wOptions1::
; bit 0-1: text delay
;   inst 0; fast 1; mid 2; slow 3
; bit 2-3: text autoscroll
;   none 0; start 1; b 2; a or b 3
; bit 4: turning step
; bit 5: no text delay
; bit 6: stereo off/on
; bit 7: battle scene off/on
	db

wSaveFileExists:: db

wTextboxFrame::
; bits 0-4: textbox frame 1-20
	db
wTextboxFlags::
; bit 0: 1-frame text delay
; bit 1: no text delay
; bit 2: no line spacing
; bit 3: use bg map width
	db

wOptions2::
; bit 0-2: typeface
; bit 3: running shoes off/on
; bit 4: clock format 12/24-hour
; bit 5: pokédex units imperial/metric
; bit 6: battle style set/switch
; bit 7: battle style set/predict
; (bits 6 and 7 are never both set)
	db

wInitialOptions::
; bit 0: natures off/on
; bit 1: abilities off/on
; bit 2: color variation off/on
; bit 3: perfect IVs off/on
; bit 4: traded behavior off/on
; bit 5: affection bonuses off/on
; bit 6: scaled exp on/off (cannot be set together with no exp)
; bit 7: physical-special split on/off
	db

wInitialOptions2::
; bits 0-1: EVs (cannot be set to %11)
; - %00: EVs disabled
; - %01: classic EVs (no 510 cap)
; - %10: modern EVs (510 cap)
; bit 2: no exp on/off (cannot be set together with scaled exp)
; bit 3: reserved by older saves
; bit 4: evolve in battle
; bits 5-6: unused
; bit 7: ask to reset at start
	db
wOptionsEnd::

; Time buffer, for counting the amount of time since an event began
	ds 4 ; formerly clock delta scratch space

; Temporary backup for options
wOptionsBuffer:: db


SECTION "SRAM Access Count", WRAM0

; Contains a count of the number of times SRAM has been opened in a
; session. Protects against bugs from emulators that do not load SRAM
; when loading a savestate.
wSRAMAccessCount:: db


SECTION "ROM Checksum", WRAM0

; Contains a copy of the rom checksum, read from the header. Used as
; protection against people trying to load a save state for a save in
; a different rom version.
wRomChecksum:: dw


SECTION "Object Palette Scan Scratch", WRAM0

; Per-call results of the first dynamic object palette allocation pass.
wResolvedObjectPals:: ds NUM_OBJECT_STRUCTS

; Invalidate the selected map rectangle palettes across text/menu rendering.
wPaletteSwapNeedsReload:: db
wPaletteSwapReloadMask:: db


SECTION "Link Failsafe", WRAM0

; Link battle safeguards (engine/link/link_failsafe.asm and
; LinkBattleSendReceiveAction).
; The first serial tag of the current action exchange's set; exchanges cycle
; through four sets so a stale byte is never taken for this exchange's.
wLinkBattleExchangeTag:: db
; The format chosen at the battle desk and its agreed battle level.
wLinkBattleRules:: db
wLinkBattleLevel:: db
; Random Battle team building: how many team members have each type and are
; weak to each type, and picks rejected in a row.
wRandomTypeCounts:: ds NUM_RANDOM_TYPES
wRandomWeakCounts:: ds NUM_RANDOM_TYPES
wRandomTries:: db
; Fingerprint of our party as sent before a link battle.
wLinkSentPartyHash:: dw
; Nonzero if the two games didn't receive the same battle.
wLinkSetupFailed:: db
; Team swap attempts so far for this battle.
wLinkSetupTries:: db
wLinkCheckSend:: ds LINK_CHECK_LENGTH
wLinkCheckRecv:: ds LINK_CHECK_LENGTH
wLinkVerdictSend:: ds LINK_VERDICT_LENGTH
wLinkVerdictRecv:: ds LINK_VERDICT_LENGTH
; Per-turn action exchange (LinkFailsafe_ExchangeAction): what we send this
; exchange, and what we sent last exchange (still answered, in case the other
; game missed it). Each is the action followed by the fingerprint.
wLinkCurSent:: db
wLinkBattleFingerprint:: db
wLinkPrevSent:: db
wLinkPrevFingerprint:: db
wLinkQuietFrames:: dw ; frames without a byte for this exchange
wLinkDeadFrames:: db ; frames the clock side has read a dead line ($ff)
wLinkLostShown:: db ; 1: "still waiting" shown, 2: "cable out" shown
wLinkBattleDesynced:: db
wLinkExchangePhase:: db
wLinkExchangeCandidates:: ds 3
wLinkExchangeReceived:: ds 3


SECTION "Follower RAM", WRAM0

; Link Edition: the Pokemon following you (engine/overworld/follower.asm).
; The lead's species and personality (shininess, form), for its icon...
wFollowerSpecies:: db
wFollowerPersonality:: dw
; ...and the ones the follower on screen was made from.
wFollowerShownSpecies:: db
wFollowerShownPersonality:: dw
; Set when the player steps off the water: spawn the follower once on land.
wFollowerPending:: db
; The follower's object flags while trainers look past it.
wFollowerSightFlags:: db
; Whether the follower's icon is mirrored (it last headed right).
wFollowerFacingRight:: db
; Whether the follower has its own sprite (back and side views), and where.
wFollowerHasSprite:: db
wFollowerSpriteBank:: db
wFollowerSpriteAddr:: dw


SECTION "Wild Mon RAM", WRAM0

; Link Edition: the wild Pokemon you can see (engine/overworld/wild_mons.asm).
; Their map objects, FIRST_WILD_OBJECT on (GetMapObject finds them here), are
; not part of the save.
wWildMapObjects::
for n, NUM_WILD_MONS
wWildMap{d:n}Object:: map_object wWildMap{d:n}
endr
; What each one is (WILDMON_* struct, species 0 if none).
wWildMons:: ds NUM_WILD_MONS * WILDMON_LENGTH
; 1 + which one you're battling, so it's gone afterwards.
wWildMonBattling:: db
; 1 + which one the player just walked into.
wWildMonBumped:: db
; For the battle: the Pokemon's shininess (SHINY_MASK or 0) plus 1, so it's
; the one you saw; 0 to roll it as usual.
wWildMonForcedShiny:: db
; The lead's level while a Repel is working (weaker Pokemon run from you), or 0.
wWildMonRepelLevel:: db
; While one is brought out: how (see TrySpawnWildMon), which, and where it lives.
wWildMonSpawnMode:: db
wWildMonSpawnSlot:: db
wWildMonSpawnHabitat:: db
; Set when one was due but there was nowhere to put it (it comes next step).
wWildMonSpawnPending:: db
; Copied for ComputeWildMonReach, which runs in another WRAM bank.
wWildReachPlayerX:: db
wWildReachPlayerY:: db
wWildReachMapWidth:: db ; in tiles
wWildReachMapHeight:: db ; in tiles
wWildReachBlockRow:: db ; wMapWidth + 6 (with the border)
wWildReachKind:: db ; LAND_TILE or WATER_TILE, what you're on
wWildReachHalf:: db ; 2 in a block's bottom half

; Link Edition: during a cup (engine/events/cups.asm), its level (no
; experience or items in its battles), else 0; and which cup
wCupLevel:: db
wCupId:: db
; Friend Battles: the desk's friend team, and (plus one) the one battling
wFriendTeamSlot:: db
wFriendBattleSlot:: db
; a generated team for the next trainer battle: how many (then cleared), of
; what type (CUPTYPE_ANY: any); and CupMakeTeam's count
wCupFoeSize:: db
wCupFoeType:: db
wCupMakeCount:: db
; World Championship: remaining seeds in bracket order, player at index 0.
wWorldCupBracket:: ds WORLD_CUP_CONTESTANTS
wWorldCupRoundSize:: db
wWorldCupPairCursor:: db
; Sweet Honey's remaining player steps and where it was used.
wWildHoneySteps:: db
wWildHoneyX:: db
wWildHoneyY:: db
