# Competitive rules matrix

One table decides what each Cable Club format allows: `LinkBattleRuleTable` in
`engine/link/link_rules.asm`. The same checks run in three places:

- on your team at the desk (`CheckLocalLinkBattleParty`);
- on the team you receive (`CheckReceivedLinkBattleParty`);
- on your team when you replay a kept friend's team (`CheckFriendBattleTeam`,
  called by the cup runner under the rules that team was kept with).

`utils/anime_events/test_link_rules.py` checks every row below.

## Cable Club formats (link version 4)

| | Standard | Random | Rising Star | Unrestricted | Championship |
|---|---|---|---|---|---|
| Level | 50 | 50 | 30 | **their own** | 50 |
| Team | 1–6 | 6, generated | 3 | 1–6 | 6 |
| Eggs in the party | allowed, don't battle | n/a | no | allowed, don't battle | no |
| Legendaries | **at most one** (any of the 11 below, any form) | as generated | no Mewtwo, Mew, Lugia, Ho-Oh or Celebi | any | any |
| Two of a species | allowed | as generated | **no** (any form counts) | allowed | allowed |
| Two holding the same item | allowed | as generated | **no** (holding nothing is fine) | allowed | allowed |
| Evasion boosts | up to +2 | up to +2 | up to +2 | **up to +2** | up to +2 |
| Healing | full, before the battle | full | full | full | full |

The legendaries are `LegendaryMons` in `data/pokemon/legendary_mons.asm`:
Articuno, Zapdos, Moltres, Raikou, Entei and Suicune, followed by the five in
`UberMons`. A list entry with no form matches every form, so Galarian Articuno
counts as Articuno.

The evasion cap holds the target's evasion at +2 at most: neutral is 7, so the
cap is 9. Double Team, Minimize and Bright Powder still help, but can't be
stacked into a stall. Evasion drops still count in full. The cap applies to
every link battle and every Friend Battle.

Unrestricted keeps every Pokémon at its own level. Nothing is normalized, and
the received team's levels aren't checked. Stats are still recalculated from
DVs and EVs, and both teams are healed.

## What changed in version 4

Older builds can't battle version 4 (`LINK_VERSION`):

- **Standard** allows at most one legendary; before, any number.
- **Unrestricted** keeps levels; before, level 50. Evasion is capped at +2;
  before, there was no cap.
- **Rising Star** has the Species and Item Clauses, as the offline Rising Star
  Cup always had through the Battle Tower picker.
- **Friend Battles** cap evasion as link battles do. Your team must fit the
  kept team's rules: under Standard, one legendary at most; under
  Championship, six. An Unrestricted team is replayed at everyone's own
  levels. Its levels are kept beside the record (`sFriendTeamLevels1`, `2`;
  see `sram-allocation.md`). An Unrestricted team kept by an older build has
  no levels, so it reads as an empty slot.

## Offline cups (single player)

The cups use their own rules (`CupRules` in `engine/events/cups.asm`). The
deliberate differences:

| Cup | Level | Team | Rule |
|---|---|---|---|
| Rising Star | 30 | 3, Battle Tower picker | the same as link Rising Star |
| Whirl | 50 | 3–6 | all Water type |
| Kimono | 50 | 3 | all of the day's type |
| Dragon Masters | 50 | 3–6 | at least one Dragon type |
| Rental | 50 | 3 generated | |
| World (Indigo) | 50 | 6 | |
| Rudy, Luana | 50 | 1, 2 | Orange Crew rounds |

In every cup, no items are used and no experience is gained. The evasion cap
doesn't apply: cups play by the single-player battle rules.

## Not yet decided

- Early and repeated cup rewards, difficulty progression and free healing:
  the roadmap's last Phase 3 item.
- How strong the computer trainers in a championship bracket are: weighted
  outcomes are next. Their randomness stays separate from battle randomness.
