Emotes:
; entries correspond to EMOTE_* constants
	table_width 2
	farbank "Emote Graphics"
	fardw ShockEmote
	fardw QuestionEmote
	fardw HappyEmote
	fardw SadEmote
	fardw HeartEmote
	fardw BoltEmote
	fardw SleepEmote
	fardw FishEmote
	fardw SparkleEmote ; EMOTE_SPARKLE
	fardw SparkleEmote ; EMOTE_SPARKLE_GREEN
	fardw SparkleEmote ; EMOTE_SPARKLE_PURPLE
	fardw DustEmote    ; EMOTE_DUST
	fardw DropsEmote   ; EMOTE_DROPS
	assert_table_length NUM_EMOTES

EmotePalettes:
; entries correspond to EMOTE_* constants
	table_width 1
	db PAL_OW_EMOTE_BLACK  ; EMOTE_SHOCK
	db PAL_OW_EMOTE_BLACK  ; EMOTE_QUESTION
	db PAL_OW_EMOTE_GREEN  ; EMOTE_HAPPY
	db PAL_OW_EMOTE_PURPLE ; EMOTE_SAD
	db PAL_OW_EMOTE_RED    ; EMOTE_HEART
	db PAL_OW_EMOTE_ORANGE ; EMOTE_BOLT
	db PAL_OW_EMOTE_BLUE   ; EMOTE_SLEEP
	db PAL_OW_EMOTE_BLUE   ; EMOTE_FISH
	db PAL_OW_EMOTE_ORANGE ; EMOTE_SPARKLE
	db PAL_OW_EMOTE_GREEN  ; EMOTE_SPARKLE_GREEN
	db PAL_OW_EMOTE_PURPLE ; EMOTE_SPARKLE_PURPLE
	db PAL_OW_EMOTE_GRAY   ; EMOTE_DUST
	db PAL_OW_EMOTE_BLUE   ; EMOTE_DROPS
	assert_table_length NUM_EMOTES
