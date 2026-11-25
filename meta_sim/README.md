# meta_sim — L50 meta-tuning analysis

Data-driven tooling to flag over-/under-tuned Pokémon by reading this ROM's
`.asm` data directly. It does **not** touch the game build — it's isolated
Python that parses source into JSON and analyzes it. Live emulator/link
playtesting isn't available in this environment, so this provides a fast,
reproducible statistical signal that stays in sync with the source.

## Files

| file | what it does |
|------|--------------|
| `extract.py` | Parses `data/**` → `data/*.json` (Pokémon, moves, type chart, learnsets). Mirrors the shipped non-faithful (Polished) values. |
| `stats.py`   | L50 stat calc, reproducing `CalcPkmnStatC` (`engine/pokemon/mon_stats.asm`). |
| `calc.py`    | Gen damage formula + STAB + type effectiveness; best-move selection. |
| `matrix.py`  | All-vs-all 1v1 best-move threat matrix → CSV + ranked leaderboard. |
| `engine.py`  | Pragmatic 6v6 turn engine + heuristic move/switch AI (status, stat stages, hazards, recovery, priority, screens, pivoting, phazing and other support moves). |
| `archetypes.py` | The 17 playstyles, who qualifies for each, and a set + item built for each playstyle. |
| `metatest.py` | **The meta test**: every mon at every playstyle it can play, scored by a swap-test impact number and by job metrics. |
| `test_engine.py` | Scripted checks for the engine's move mechanics. |
| `teams.py`   | Role-aware moveset picker + three team builders (random, role-based, synergy). |
| `sim6v6.py`  | 6v6 Monte Carlo runner → per-mon team win rate, builders compared. |
| `oracle.py`  | Ground truth: runs the ROM's real `CalcPkmnStats` under PyBoy and diffs it against `stats.py`. |
| `oracle_damage.py` | Ground truth: runs the ROM's real `damagecalc` + `stab` under PyBoy and diffs them against `calc.py`'s formula. |
| `rom_damage.py` | The ROM's damage pipeline (crit, stats, stat stages, abilities, items, STAB, weather, roll, conditional boosts) ported step for step with the same integer arithmetic. `engine.py` uses it for every hit. |
| `oracle_pipeline.py` | Ground truth for `rom_damage.py`: runs the ROM's `damagestats` → `damagecalc` → `stab` → `conditionalboost` (and `damagevariation`) under PyBoy on random scenarios and diffs them. |
| `mechanics.py` | Non-damage rules ported from the ROM: accuracy/evasion (`checkhit`), status immunities (`CanStatusTarget`), stat-stage changes (`FarChangeStat`, Defiant/Competitive/Contrary/Clear Body...), Speed (`GetSpeed`), turn order (priority, Prankster, Quick Claw, Quick Draw, Custap, Lagging Tail), Hidden Power typing. |
| `oracle_turn.py` | Ground truth for whole turns: plays real link-battle turns in the ROM (one emulator, menus and the link exchange answered by script, random numbers chosen per sample) and compares who moved first, HP, fainting, status and stat stages with `engine.resolve_turn`, over many samples. |
| `oracle_accuracy.py`, `oracle_status.py`, `oracle_speed.py` | Ground truth for `mechanics.py`: run `checkhit` (with the link RNG pinned), `CanXTarget` and `GetSpeed` under PyBoy and diff them. |
| `optimize.py` | Finds each build's best set (moves, item, ability, Hidden Power type) with paired battles, and writes `data/best_sets.json`, which the meta test then uses. |

Three complementary tools:

- **`metatest.py` (playstyles)**: the one to start with. It answers "how good is
  this mon at the job it's doing?" for attackers, walls, supports and pivots
  alike. See [The meta test](#the-meta-test-metatestpy) below.
- **`matrix.py` (1v1)** — fast, fully deterministic check of *raw* stat / typing /
  movepool tuning. Trustworthy but blind to team context (walls/support mons
  look bad).
- **`sim6v6.py` (6v6)** — Monte Carlo battles with a heuristic AI; surfaces the
  support / stall / synergy mons the 1v1 matrix structurally can't see. Noisier
  (it's sampled), and *not* a port of the ROM trainer AI — a uniform yardstick.

## The meta test (`metatest.py`)

```sh
python3 meta_sim/metatest.py              # ~4 min on 4 cores
python3 meta_sim/metatest.py --battles 8000   # quicker, noisier
python3 meta_sim/test_engine.py           # check the engine's move mechanics
```

It writes `meta_sim/out/metatest.md` (the report) and `meta_sim/out/metatest.csv`
(one row per build, with every metric).

**Playstyles.** `archetypes.py` decides which of 17 playstyles each mon can
really play, from its L50 stats (against the pool's own percentiles) and what it
can learn: physical, special or mixed attacker, setup sweeper, revenge killer,
weather sweeper, Baton Passer, physical or special wall, bulky tank, support,
hazard setter, cleric, pivot, weather setter, Trick Room setter, trapper. Each
gets a set and item for that job: walls carry recovery and status (RestTalk when
their recovery is Rest), supports their screens/Encore/Haze/Pain Split, hazard
setters Spikes, pivots U-turn/Volt Switch or Regenerator, revenge killers Choice
Scarf and priority (and Trick, if they learn it), weather setters their weather
move or ability and the matching rock, weather sweepers the ability that needs
it, Baton Passers a setup move, Substitute and Baton Pass, trappers Shadow
Tag/Arena Trap/Magnet Pull or Mean Look (with Perish Song where available), and
Wobbuffet Counter and Mirror Coat. A mon is entered once per playstyle (about 4
each).

**Teams.** Every battle uses two balanced drafts (two offense slots, a speed slot,
a defense slot, a utility slot and a flex slot, no three members sharing a
weakness). When a team has a weather setter, its flex slot takes a sweeper that
uses that weather 70% of the time (and vice versa), as a real weather team
would.

**Impact (the headline number).** After each battle, every slot is replayed with
a random other build of the same family (offense / speed / defense / utility),
using the same random seed. The average change in the result is how many
points of team win rate the build adds over a typical teammate doing the same
kind of job. It is the one number that compares a wall with an attacker fairly,
because it measures what the team gains, not what the mon did. By construction
the average is about 0 in each family. The report prints each build's standard
error (about ±2 points at the default size), so differences under about 4
points are noise.

**Job score.** Each build's average percentile, within its own playstyle, on the
metrics that show whether it is doing that job:

| playstyle | job metrics |
|---|---|
| attackers, setup sweepers | damage dealt, KOs |
| revenge killer | KOs, damage dealt |
| walls | damage absorbed, turns on the field, HP healed |
| bulky tank | damage absorbed, damage dealt, turns on the field |
| support | statuses inflicted, screens set, foe stat drops, phazes |
| hazard setter | hazard layers, statuses |
| cleric | team statuses cured, HP healed |
| pivot | pivot switches, damage dealt |
| weather setter | times weather was set, damage dealt |
| weather sweeper | damage dealt, KOs |
| Baton Passer | Baton Passes, Substitutes made |
| Trick Room setter | Trick Rooms set, damage dealt |
| trapper | foes trapped, Perish Song KOs, KOs |

Damage absorbed is counted as a fraction of the mon's own max HP, so a wall that
heals and keeps tanking scores above 1.0.

**Reading it.** A high job score with average impact means the mon does its job
well but the job isn't worth much in this meta (or other mons do it as well). A
mon that is clearly negative in *every* playstyle it qualifies for is a real buff
candidate; one in the top 10% and clearly positive is a nerf candidate. The
report lists both, plus a top/bottom table for every playstyle.

**What the engine simulates** is listed at the top of `engine.py`: on top of
damage, status and stat stages it covers weather (moves, abilities, rocks,
speed and recovery abilities, accuracy and damage effects), screens, hazards and
Rapid Spin, Substitute, Baton Pass, Trick, Trick Room, Protect, Encore, Roar,
Haze, Pain Split, Heal Bell, Curse, U-turn/Volt Switch, Knock Off, Pursuit,
trapping, Perish Song, Counter/Mirror Coat, Rest/Sleep Talk, two-turn moves
(Solar Beam outside sun, Fly/Dig), Dream Eater, Future Sight and more.
`test_engine.py` checks each one.

**Rules from the ROM, not from memory.** Accuracy and evasion stages, status
immunities, stat changes, Speed and turn order come from `mechanics.py`, which
is ported from the assembly and checked against it (see the oracles below). The
engine also follows each move's battle script from `data/moves/effects.asm`
(whether it rolls accuracy, its secondary effect, damage doublings), tracks PP
(with PP Max) and Pressure, falls back to Struggle, and models genders
(Attract, Rivalry, Cute Charm), weights (Low Kick), berries and most competitive
held items. A few things it found the simulator had wrong: paralysis halves
Speed (it was quartering it), sleep from a move lasts 1-3 turns and Rest 2 (both
were a turn short), and Toxic / Will-O-Wisp / Thunder Wave respect type
immunities.

**Damage is the ROM's own math.** Every hit goes through `rom_damage.py`, a
step-for-step port of the move script's damage commands with the same integer
arithmetic and order of operations, so stat stages, screens, Eviolite, abilities
(including Mold Breaker, Pixilate/Galvanize, pinch abilities, Analytic, Fluffy,
Fur Coat, Marvel Scale), items, STAB, weather, the 85-100% roll and the
post-roll boosts (Facade, Hex, Venoshock, Acrobatics, Avalanche, Pursuit, Knock
Off) round exactly as on the cartridge. `oracle_pipeline.py` checks it against
the real routines: 20,000 of 20,000 random scenarios match exactly. Critical
hits use the ROM's stages and odds (1/24, 1/8, 1/2, always; Focus Energy,
high-crit moves, Scope Lens/Razor Claw, Leek/Lucky Punch, Super Luck, Sniper,
Battle/Shell Armor), and multi-hit moves roll their hit count (2-5, with 2
and 3 twice as likely) and each hit's crit and roll separately. Confusion lasts
1-4 turns with a 1/3 chance per turn of a 40-power typeless self-hit; flinching
needs the attacker to move first and the target to be awake, unfrozen and not
behind a Substitute (Inner Focus, Steadfast, Stench and King's Rock included). The AI avoids feeding Counter/Mirror Coat a
hit it can't KO with.

**Not modelled.** Smeargle (Sketch) and Ditto without Imposter are listed but not
ranked. The heuristic AI plays every team the same way, so strategies that need
long-term planning (Baton Pass chains, weather turn management) are probably
understated.

## Usage (run from the repo root)

```sh
python3 meta_sim/extract.py          # refresh JSON from the .asm source
python3 meta_sim/matrix.py           # fully-evolved, non-legendary pool
python3 meta_sim/matrix.py --include-legendary --top 40
python3 meta_sim/matrix.py --include-unevolved --csv meta_sim/out/all.csv
```

`matrix.py` writes `meta_sim/out/threats.csv` (per-mon stats + W/L/D + win
rate) and prints the top/bottom outliers.

```sh
python3 meta_sim/sim6v6.py                    # random + role, 3000 battles each
python3 meta_sim/sim6v6.py --mode all         # random + role + synergy
python3 meta_sim/sim6v6.py --games 5000       # more battles = tighter signal
python3 meta_sim/sim6v6.py --mode role --top 40
python3 meta_sim/sim6v6.py --include-legendary --csv meta_sim/out/sim6v6.csv
```

`sim6v6.py` writes `meta_sim/out/sim6v6.csv` (per-mon role, `<mode>_win`,
games, damage/KO/status/heal contribution, and `delta`) and prints top/bottom
outliers plus the biggest movers. `delta` is the most structured mode present
(synergy, else role) minus random. `--seed` makes a run exactly reproducible,
and `--min-games` hides under-sampled mons from the printed tables (they stay
in the CSV).

### Ground-truth oracles

Both need a built ROM (`make`) and PyBoy (`pip install pyboy`); addresses come
from the `.sym` beside the ROM, so they keep working after rebuilds.

```sh
python3 meta_sim/oracle.py          # all species: ROM stats vs stats.py
python3 meta_sim/oracle_damage.py   # 7-case self-test + calc.py fidelity sweep
python3 meta_sim/oracle_pipeline.py 20000   # engine damage (rom_damage.py) vs the ROM
python3 meta_sim/oracle_accuracy.py 3000     # accuracy / evasion vs checkhit
python3 meta_sim/oracle_status.py 4000       # status immunities vs CanStatusTarget
python3 meta_sim/oracle_speed.py 4000        # Speed vs GetSpeed
python3 meta_sim/oracle_turn.py --scenarios 40   # whole turns: the ROM vs engine.py
```

`oracle_turn.py` is the end-to-end check. It builds two random optimised sets
(plus a bench Pokemon each, so a faint doesn't end the battle) with the
game's own party code, starts a link battle in a single emulator, and saves
the state at the first menu. Each sample reloads it, writes new link random
numbers, and plays three turns of a fixed pair of moves; the engine plays the
same three turns from the same stats, abilities and genders. A difference is
reported when it is both clear (over 4 standard errors) and big enough to
matter (4% of HP, 8 points of a probability, a quarter of a stat stage).

`oracle_accuracy.py` matches 6,000/6,000 scenarios (two seeds), `oracle_status.py`
12,000/12,000 and `oracle_speed.py` 4,000/4,000. Hidden Power typing matched
`GetHiddenPowerType` on 2,000/2,000 DV sets and Low Kick power `BattleCommand_lowkick`
on all species. Building these found three upstream ROM bugs, now fixed: Thunder
never missed in sun, sun let a freeze chance skip every check, and Low Kick's
weight table mixed units.

Re-run at link version 4 (the consolidation, 2026-11): `oracle.py` 333/333,
`oracle_damage.py` 0/30,276 pairs differ, `oracle_pipeline.py` 3,000/3,000,
`oracle_accuracy.py` 2,000/2,000, `oracle_status.py` 4,000/4,000,
`oracle_speed.py` 3,000/3,000, and `oracle_turn.py` 47/48 matchups: the 48th
stops after Baton Pass: the oracle's stand-in for choosing who comes in
(fine for a fainted Pokémon) leaves the ROM in an animation that never ends,
so those samples can't be compared (a gap in the oracle, not a difference).

On the current build `oracle.py` matches 333/333 species, `oracle_damage.py`
finds calc.py's core formula matches the ROM on all 30,276 fully-evolved pairs
(including the ROM's 8-bit Atk/Def truncation), and `oracle_pipeline.py`
matches 20,000/20,000 random full-pipeline scenarios per seed plus every
85-100% damage roll. calc.py (the 1v1 matrix) still uses a flat average roll
and a simpler ability model; the 6v6 engine uses the exact pipeline.

## The model

For every ordered pair (A, B) in the pool, each side picks its highest
average-damage legal move, and the 1v1 is resolved by hits-to-KO with turn
order (move **priority**, then **Speed**). Equal hits-to-KO → the faster mover
wins; neither can damage → draw. Per mon we aggregate wins/losses/draws into a
win rate ("threat score").

Baseline build (uniform for everyone, so comparison is fair): **L50, the stat
profile's DVs and EVs in every stat (below), neutral nature, average damage roll
(0.925), crits off.**

### Stat profiles

`stats.py` gives every mon the same DVs and EVs, set by `META_STAT_PROFILE`:

| profile | DV | EV | what it models |
|---|---|---|---|
| `family` (default) | 8 | 64 | the family's real link teams, read from their saves |
| `random` | 15 | 0 | Random Battle teams |
| `max` | 15 | 252 | the theoretical maximum build (the old default) |

The real teams have random DVs (about 8 on average), EVs from ordinary play
(0 to 510 in total, spread over every stat; the 510 cap applies) and random
natures. The profile matters for balance: DVs and EVs add the same number of
points to every mon's stats (about 52 under `max`, about 21 for real teams), and
the bigger that number, the smaller the gap between a high base stat and a low
one looks. Under `max` a base-130 attacker against a base-80 wall hits about 8%
softer, relative to everyone else, than it does in real play.

## What this does NOT model (read before trusting a number)

This is a **first-order signal for raw stat / typing / movepool / speed
tuning**, not a battle simulator. It ignores:

- switching, team composition, and the 6v6 AI
- items, and abilities beyond plain type multipliers
- status and residual damage over time (so Toxic/Spikes/sleep stallers and
  Wobbuffet/Ditto/Smeargle-style mechanic mons rank near the bottom — expected)
- multi-turn / charge / recoil / recovery move dynamics
- secondary effects and accuracy (damage uses average roll, ignores miss)

Known bias: pure Normal-types over-perform in the 1v1 matrix because Normal is
neutral vs almost everything and the model can't punish them by switching in a
Ghost. Read the 1v1 leaderboard as "who hits hard and fast into a neutral
field," then cross-check with the 6v6 run, which *can* switch.

## The 6v6 model (`sim6v6.py`)

For each battle two teams are built (random, role-based, or synergy-drafted)
with role-aware movesets, and a **heuristic AI** plays both sides identically.
It looks one move ahead: it estimates the foe's best hit back, takes a KO
whenever one is available, and only sets up / statuses / heals / lays hazards
when it will survive to benefit; it switches out of clearly losing matchups.
Each mon on the winning team is credited a win; aggregated over thousands of
battles this gives a team win rate per mon.

The synergy builder drafts the role template but refuses a pick that would
make a third teammate share a weakness, then prefers mons that resist what the
team is weak to and widen its coverage. It cuts stacked shared weaknesses to
~0 per team (role ~0.8, random ~1.8) while still drafting nearly the whole
roster, so `synergy − random` shows how much a mon gains from a cohesive team
(the support/stall mons 1v1 understates).

Modelled (the high-impact ~80%): damage + stat stages, the major statuses
(sleep/paralysis/burn/poison/toxic/freeze + confusion), on-hit secondary
effects, self-stat setup moves, recovery, Leech Seed, entry hazards
(Spikes/Toxic Spikes), priority, switching, held items (Choice items, Life
Orb, Leftovers, Eviolite, Focus Sash, Toxic/Flame Orb), variable/fixed-power
moves (Seismic Toss/Night Shade, Super Fang, Gyro Ball, Reversal, Return,
Magnitude, Facade/Hex/Venoshock/Acrobatics), move-flag abilities (Iron Fist,
Tough Claws, Mega Launcher, Sharpness, Reckless, Bulletproof, Soundproof,
powder immunity, contact-triggered Static/Flame Body/Poison Point using the
ROM's contact rule), and a broad ability subset: switch-in/event
abilities (Imposter, Intimidate, Levitate, Sturdy, Regenerator), type-absorb
abilities (Flash Fire, Water/Volt Absorb, Sap Sipper, Dry Skin, Motor Drive,
Lightning Rod), damage modifiers (Guts, Thick Fat, Solid Rock/Filter,
Multiscale, Unaware, Hustle, Tinted Lens), residual-turn abilities (Magic
Guard, Speed Boost, Poison Heal, Quick Feet, Rock Head), and status-immunity abilities
(Insomnia/Vital Spirit, Own Tempo, Limber, Water Veil, Immunity, Magma
Armor). Each mon commits to one ability for the whole battle, picked by
`abilities.pick_ability`'s impact-ordered priority list (not just "first
listed") so it doesn't default to a no-op ability over a modeled one.
**Sleep Clause is mirrored** from the shipped game (toggle `SLEEP_CLAUSE` in
`engine.py`).

Approximated / ignored (so don't over-read these): Low Kick is a flat 80 BP;
abilities/items beyond the modeled subset above (see `engine.py`'s module
docstring for the full list). Weather, screens, trapping, Perish Song,
Counter/Mirror Coat, crits, confusion and flinching are now simulated (see
"Damage is the ROM's own math" above). Consequently Ditto / Wobbuffet / Smeargle (Transform/Counter/
mechanic mons) and weather/screen teams are understated by design — that's a
known blind spot, not a balance verdict. The 6v6 numbers are *sampled*, so
deltas within ~±5% (more for rare roles with fewer games) are noise; raise
`--games` to tighten.

This is **Option A**: a clean, uniform heuristic AI chosen as a fair yardstick.
A faithful port of the ROM's trainer AI (`engine/battle/ai/*.asm`) would match
in-game trainer behavior but is large/fragile and not competitive-player-like,
so it remains an optional later phase.
