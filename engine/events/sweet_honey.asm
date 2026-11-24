_SweetHoney:
	farcall CanUseSweetHoney
	jr nc, .no_battle
	farcall GetMapEncounterRate
	and a
	jr z, .no_battle
	ld hl, wStatusFlags2
	; Items can't be used during the Bug-Catching Contest anyway
	bit STATUSFLAGS2_BUG_CONTEST_TIMER_F, [hl]
	jr nz, .no_battle
	farcall SetWildHoneyLure
	jr c, .lure
	ld hl, wStatusFlags2
	set STATUSFLAGS2_USING_SWEET_HONEY_F, [hl]

	farcall ChooseWildEncounter
	jr nz, .no_battle

	; This might do useless things due to improperly filled level data.
	; This is harmless, because we only run this to deal with Magnet Pull,
	; Static, etc.
	farcall ApplyAbilityEffectsOnEncounterMon

	; Force the mon to be the same level as the lead, not necessarily the one
	; we send out.
	ld a, [wPartyMon1Level]
	ld [wCurPartyLevel], a
	ld de, SweetHoneyBattleScript
	jr .succeeded
.lure
	ld de, SweetHoneyLureScript
.succeeded
	ld a, TRUE
	jr .done
.no_battle
	xor a
	ld [wBattleType], a
	ld de, SweetHoneyNothingScript
.done
	ld [wFieldMoveSucceeded], a
	ld hl, wStatusFlags2
	res STATUSFLAGS2_USING_SWEET_HONEY_F, [hl]
	ld h, d
	ld l, e
	jmp QueueScript

SweetHoneyBattleScript:
	scall UseSweetHoneyScript
	checkflag ENGINE_BUG_CONTEST_TIMER
	iftruefwd .BugCatchingContest
	randomwildmon
	startbattle
	reloadmapafterbattle
	end

.BugCatchingContest:
	farsjump BugCatchingContestBattleScript

SweetHoneyLureScript:
	scall UseSweetHoneyScript
	jumpopenedtext SweetHoneyLureText

SweetHoneyNothingScript:
	scall UseSweetHoneyScript
	jumpopenedtext SweetHoneyNothingText

UseSweetHoneyScript:
	refreshmap
	special UpdateTimePals
	writetext UseSweetHoneyText
	waitbutton
	end

UseSweetHoneyText:
	text_farend _UseSweetHoneyText
SweetHoneyNothingText:
	text_farend _SweetHoneyNothingText
SweetHoneyLureText:
	text "The sweet scent"
	line "hangs in the air."
	done
