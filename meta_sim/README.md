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
| `engine.py`  | Pragmatic 6v6 turn engine + heuristic move/switch AI (status, stat stages, hazards, recovery, priority, abilities, items). |
| `abilities.py` / `items.py` | Multiplier-style ability + held-item models (one fixed ability+item per mon) used by `calc.py`/`engine.py`. |
| `teams.py`   | Role-aware moveset picker + three team builders (random, role-based, synergy-aware). |
| `sim6v6.py`  | 6v6 Monte Carlo runner → per-mon team win rate, builders compared. |
| `oracle.py`  | **Ground-truth stat oracle**: calls the ROM's real `CalcPkmnStats` via mGBA and diffs it against `stats.py` (validates all 333 species, 0 mismatches). |
| `oracle_damage.py` | **Ground-truth damage oracle**: drives the ROM's real `damagecalc`+`stab` via mGBA to arbitrate `calc.py`'s formula. |

### Ground-truth oracles (`oracle.py`, `oracle_damage.py`)

`stats.py` and `calc.py` are readable hand-ports of the ROM's math; the oracles
are the arbiters. Rather than re-deriving formulas from the asm, they load the
actual built ROM in mGBA, set up minimal RAM, call the *real* routines, and read
the result back — so the hand-ports can be diffed against ground truth instead
of trusted. `oracle.py` validates every one of the 333 species' L50 stats (0
mismatches); `oracle_damage.py` confirms `calc.py`'s base damage formula is
faithful (diverges on ~0.05% of matchups, never by >1 HP, all from the engine's
8-bit Attack/Defense truncation). They require the built `polishedcrystal-3.2.3.gbc`
and the `mgba` Python bindings; run `python3 meta_sim/oracle.py` /
`python3 meta_sim/oracle_damage.py` from the repo root.

Two complementary tools:

- **`matrix.py` (1v1)** — fast, fully deterministic check of *raw* stat / typing /
  movepool tuning. Trustworthy but blind to team context (walls/support mons
  look bad).
- **`sim6v6.py` (6v6)** — Monte Carlo battles with a heuristic AI; surfaces the
  support / stall / synergy mons the 1v1 matrix structurally can't see. Noisier
  (it's sampled), and *not* a port of the ROM trainer AI — a uniform yardstick.

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
python3 meta_sim/sim6v6.py                    # random+role, 3000 battles each
python3 meta_sim/sim6v6.py --mode all         # random+role+synergy
python3 meta_sim/sim6v6.py --games 5000       # more battles = tighter signal
python3 meta_sim/sim6v6.py --mode synergy --top 40
python3 meta_sim/sim6v6.py --include-legendary --csv meta_sim/out/sim6v6.csv
```

`sim6v6.py` writes `meta_sim/out/sim6v6.csv` (per-mon role + each mode's
`*_win` + `delta`) and prints top/bottom outliers plus the biggest movers.
`delta` = (most structured mode present) − `random`, so `--mode all` reports
**synergy − random**: how much a mon gains from being drafted into a cohesive
team. Synergy drafting samples the roster unevenly, so under-sampled mons are
hidden from the printed leaderboards (tunable with `--min-games`); they remain
in the CSV.

## The model

For every ordered pair (A, B) in the pool, each side picks its highest
average-damage legal move, and the 1v1 is resolved by hits-to-KO with turn
order (move **priority**, then **Speed**). Equal hits-to-KO → the faster mover
wins; neither can damage → draw. Per mon we aggregate wins/losses/draws into a
win rate ("threat score").

Baseline build (uniform for everyone, so comparison is fair): **L50, DV 15, 252
EVs in every stat, neutral nature, average damage roll (0.925), crits off.**

## What this does NOT model (read before trusting a number)

This is a **first-order signal for raw stat / typing / movepool / speed
tuning**, not a battle simulator. It ignores:

- switching, team composition, and the 6v6 AI
- held items (a 6v6-only concern); abilities are modelled as a best-case
  subset (Huge Power, Adaptability, Technician, Sheer Force, own-weather
  Fire/Water boost, Sand Sp.Def, **and the defender's type-immunity / Thick Fat
  abilities** — see `abilities.py`), not the full set. Intimidate and field
  weather are 6v6-only (they need switch-in / turn state)
- status and residual damage over time (so Toxic/Spikes/sleep stallers and
  Wobbuffet/Ditto/Smeargle-style mechanic mons rank near the bottom — expected)
- multi-turn / charge / recoil / recovery move dynamics
- secondary effects and accuracy (damage uses average roll, ignores miss)

Known bias: pure Normal-types over-perform in the 1v1 matrix because Normal is
neutral vs almost everything and the model can't punish them by switching in a
Ghost. Read the 1v1 leaderboard as "who hits hard and fast into a neutral
field," then cross-check with the 6v6 run, which *can* switch.

## The 6v6 model (`sim6v6.py`)

For each battle two teams are built and a **heuristic AI** plays both sides
identically: pick the best damaging move, but set up / status / heal / lay
hazards when it's the better play, and switch out of clearly losing matchups.
Each mon on the winning team is credited a win; aggregated over thousands of
battles this gives a team win rate per mon.

Three team builders isolate *composition* as the only variable (movesets are
chosen the same way in all three):

- **random** — random legal 6-mon teams; the unbiased baseline.
- **role** — classify each mon (sweeper/tank/pivot/wall) and fill a balanced,
  type-diverse template, so support/stall roles are actually represented.
- **synergy** — the role template, but each slot is drafted to fit the partial
  team: it won't let a third teammate share a weakness, and nudges toward mons
  that resist what the team is weak to and widen its offensive coverage. Across
  a run this cuts stacked shared weaknesses to ~0.01 per team (role ~0.79,
  random ~1.82) while still sampling ~97% of the roster. A mon's `synergy −
  random` delta is how much it benefits from a cohesive team around it — the
  thing the 1v1 matrix and random teams structurally can't see.

Modelled: damage + stat stages, the major statuses (sleep/paralysis/burn/
poison/toxic/freeze + confusion), on-hit secondary effects, self-stat setup
moves, recovery, Leech Seed, entry hazards (Spikes/Toxic Spikes), priority,
switching, a held-item layer (Choice band/specs/scarf, Life Orb, Leftovers,
Eviolite), and a **near-complete ability layer**.

**Abilities — 94 of the ROM's 154 carry a real effect** (each mon commits to
its most battle-swinging one; see `abilities.py`), grouped by hook:
- *damage* — Huge/Pure Power, Adaptability, Technician, Sheer Force, Tough
  Claws, Iron Fist, Mega Launcher, Sharpness, Punk Rock, Reckless, Steely
  Spirit, Sand Force, Analytic, Solar Power, Guts, Hustle, Gorilla Tactics,
  the −ate set (Pixilate/Refrigerate/Aerilate/Galvanize), Tinted Lens,
  Protean/Libero, the pinch abilities (Overgrow/Blaze/Torrent/Swarm).
- *defense* — type immunities (Levitate, Flash Fire, Water/Volt Absorb, Storm
  Drain, Sap Sipper, Lightning Rod, Motor Drive, Dry Skin, Well Baked Body,
  Earth Eater, Bulletproof, Soundproof → 0 damage), halvers (Thick Fat,
  Heatproof, Fur Coat, Ice Scales, Fluffy, Punk Rock, Purifying Salt),
  Filter/Solid Rock/Prism Armor, Multiscale, Marvel Scale, Sturdy, Wonder Guard.
- *switch* — Intimidate (+ Defiant/Competitive backlash, Clear Body-style
  prevention), Download, Regenerator, Natural Cure.
- *on-hit / on-KO* — Rough Skin/Iron Barbs, Flame Body/Static/Poison Point/
  Effect Spore, Poison Touch, Tangling Hair, Aftermath, Justified/Rattled/
  Stamina/Weak Armor/Water Compaction, Berserk, Moxie/Beast Boost/Soul Heart.
- *end-of-turn* — Speed Boost, Poison Heal, Magic Guard, Rain Dish/Ice Body/
  Dry Skin/Solar Power, Shed Skin.
- *misc* — Unaware, Contrary/Simple, Scrappy/Mind's Eye, Prankster/Gale Wings/
  Triage priority, Quick Feet, Synchronize, the status-immunity set
  (Immunity/Limber/Insomnia/…), weather setters + Swift Swim/Chlorophyll/Sand/
  Slush Rush, and trapping (Shadow Tag/Arena Trap/Magnet Pull).

Of the remaining 60: ~48 are genuine no-ops in a 1v1/6v6 stat sim (Run Away,
Keen Eye, Pickup, Shield Dust, evasion abilities under the shipped evasion
clause, …) — listed in `NOOP_ABILITIES`; ~11 need mechanics this abstraction
lacks (Trace/Imposter/Forecast/form-change/Neutralizing Gas/terrain) — listed
in `UNMODELLED_ABILITIES`; and a handful are edge cases (Anger Point is moot
with crits off, Skill Link folds into the averaged multi-hit model, Magic
Bounce/Liquid Ooze).

The 1v1 matrix shares the stateless parts (damage/typing/immunity multipliers);
the switch/turn/KO hooks are 6v6-only. **Sleep Clause is mirrored** from the
shipped game (toggle `SLEEP_CLAUSE` in `engine.py`).

Approximated / ignored (so don't over-read these): confusion as a flat
self-hit chance; multi-hit as average hit count; two-turn moves resolve in one
turn; **no screens or Perish Song**; and the unmodellable abilities above
(form-change/copy/terrain). Consequently Ditto / Wobbuffet / Smeargle
(Transform/Counter/mechanic mons) are understated by design — a known blind
spot, not a balance verdict. The 6v6 numbers are *sampled*, so deltas within
~±5% (more for rare roles with fewer games) are noise; raise `--games` to
tighten.

This is **Option A**: a clean, uniform heuristic AI chosen as a fair yardstick.
A faithful port of the ROM's trainer AI (`engine/battle/ai/*.asm`) would match
in-game trainer behavior but is large/fragile and not competitive-player-like,
so it remains an optional later phase.
