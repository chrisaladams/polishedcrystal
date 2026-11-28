# Johto expansion: discovery and direction (for discussion, nothing implemented)

Purpose: agree the creative direction for a richer early and mid-game Johto **before** any content is built. This document
gathers facts from the repository, the constraints that will shape the work, a few candidate directions, and the
questions that need the owner's answer. The candidate directions are proposals, not decisions.

## 1. What the repository shows today

Counted from the maps and data in the checkout (structural facts; they say what exists, not how it plays):

| | Johto | Kanto | Orange Islands |
|---|---:|---:|---:|
| Maps | 287 | 282 | 45 |
| Object events (NPCs, items, trainers) | 1,566 | 1,242 | 157 |
| Trainer entries | 346 | 299 | 36 |
| Scene scripts | 55 | 29 | 7 |
| Trigger-tile events | 195 | 84 | 9 |

So Johto is already large; the question is depth and presence, not map count.

- **Story already built:** four movie campaigns (Mewtwo Strikes Back, The Power of One, Spell of the Unown, Celebi: Voice of the
  Forest), the Orange League, the Pallet Invitational, six cup formats, the Field Book and Quest Map, a software clock with
  daily and weekly rotations, visible wild Pokemon with behaviour profiles.
- **Postgame weight:** 37 maps change what they show after the Elite Four or the champion, and only 3 check for Red.
  Much of the added narrative is gated behind the Hall of Fame, which matches the observation that the expansion leans postgame.
- **Legendaries touching Johto maps:** Suicune on six maps (Eusine's thread, the route sightings, Cianwood), Raikou and Entei
  (roamers, plus Entei in Spell of the Unown), Ho-Oh (Tin Tower roof, the Ruins of Alph Ho-Oh chamber puzzle), Lugia (the Whirl
  Islands), Celebi (Ilex Forest), Mew, and the three birds and Mewtwo mostly outside Johto.
- **Existing building blocks:** a cinematic effects library (`docs/cinematics.md`), `showemote`, weather and palette effects, the
  Field Book (a place to record mysteries), time-dependent NPCs and sightings, scene scripts and trigger tiles.
- **Not measured:** how the early game plays. That is the owner's call and the most important input here.

## 2. Constraints that will shape any expansion

| Constraint | Value | Consequence |
|---|---|---|
| **Event flags** | 2,304 bits in total, save size locked, **16 free** (ledger L42) | A story expansion needs more flags than exist. This needs an architecture decision (consolidate per-trainer beat flags, or an extension array in free SRAM with a versioned save record) before large content is built. |
| ROM0 (home bank) | 146 bytes free | New engine code must live in ROMX; only tiny hooks fit in the home bank. |
| ROM | **2,782 bytes free in the 2 MiB image** (the 128 empty banks belong to the reserved 4 MiB layout, not to 2 MiB) | Any real expansion needs a 4 MiB decision; see `johto-technical-investigation.md`. |
| SRAM | 923 bytes free, largest gap 393 | Any new persistent state must fit there or replace something. |
| WRAM0 / HRAM | 9 / 5 bytes free | No room for new fixed state; use WRAMX banks with gaps. |
| Sprites | 13 object structs, 40 OAM entries; the engine drops the last drawn (ledger L36) | Crowded scenes need care; this is also the design input for the living-world work. |
| Scripts | map callbacks must not wait for frames or input (ledger L33) | Cinematic openings belong in scene scripts. |
| Saves | older saves must keep loading | New content gates on new flags, never on reinterpreted old ones. |

## 3. Candidate directions (to choose from, combine or discard)

Every adventure would need a discovery, a payoff that changes the world, and no fetch-quest padding.

**A. The omen thread (legendary presence across the whole adventure).** From Route 29 on, the world carries traces of
things that are not seen yet: scorched grass and shocked Pokemon where Entei passed, storm signs around Raikou, rainbow light
at certain hours near Ecruteak, a sailor's story about Lugia before the Whirl Islands. The Burned Tower reveal becomes a
mid-game turning point instead of a side stop, and the roaming beasts' routes tie to weather and time. Mostly presentation and
scene scripts; few flags if the traces key off existing story flags.

**B. The Alph mystery as an early investigation.** The Unown ruins as a long, optional investigation that starts in the first
third (researchers and Prof. Hale already exist), with chambers that open as the player learns more elsewhere in Johto.

**C. The bell and the sea.** A coastal arc linking Olivine Lighthouse, Cianwood and the Whirl Islands: sailors' legends, storms
at sea, Lugia as lore before it is a place. Pairs naturally with A.

**D. The forest guardian.** An earlier, smaller Ilex Forest story with Celebi in a time-travel register, as a template for the
other short adventures.

**E. People you meet again.** A handful of recurring characters (Eusine, Kurt, the Elm lab staff, rivals) who appear in more
than one place, change with the story and the clock, and give reasons to revisit towns. Recorded in the Field Book so players
can follow the threads.

**Recommendation to discuss (not a decision):** one spine (A with C woven in) for the "legendary presence" you asked for, plus two
short optional adventures (B and D) for variety, with E as the connective tissue. That keeps the engineering mostly in scene
scripts and presentation, and keeps the flag cost small if we settle the flag question first.

Anime and movie material that could be integrated without new captures: the Johto-era sightings of Ho-Oh and the rainbow feather,
Team Rocket's recurring pair as cameo characters, and the legend structure of the Ecruteak towers. Which sources you want
treated as canon for this project is your call.

## 4. Questions

1. Where does the early and mid-game feel thinnest to you (which towns, routes or badge range)?
2. Tone: faithful Crystal mystery, or more anime-flavoured?
3. Legendaries: presence only (omens, cinematics, lore), or changes to encounters and captures? Anything off limits?
4. Do you prefer one long thread, or several independent short adventures?
5. Graphics and music: may I add new overworld sprites and tunes, and who produces assets?
6. May I investigate the flag budget (consolidation or an SRAM extension) now, because it constrains how much story fits?
7. Roaming Raikou and Entei: keep random roaming, or add scripted route events around it?
8. Existing saves: must every expansion load on older saves in a sensible state?

## 5. Proposed process

1. You answer the questions above and pick a direction.
2. I write beat sheets for the chosen adventures (characters, places, scenes, flags and ROM cost estimates) for your approval.
3. Decide the flag-budget approach.
4. Build in thin vertical slices (one adventure at a time), keeping the game buildable and playable, with only the critical
   checks from the new policy (`make qa-regression`).
5. Defer polish items to stabilization.
