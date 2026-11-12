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
| `engine.py`  | Pragmatic 6v6 turn engine + heuristic move/switch AI (status, stat stages, hazards, recovery, priority). |
| `teams.py`   | Role-aware moveset picker + three team builders (random, role-based, synergy). |
| `sim6v6.py`  | 6v6 Monte Carlo runner → per-mon team win rate, builders compared. |
| `oracle.py`  | Ground truth: runs the ROM's real `CalcPkmnStats` under PyBoy and diffs it against `stats.py`. |
| `oracle_damage.py` | Ground truth: runs the ROM's real `damagecalc` + `stab` under PyBoy and diffs them against `calc.py`'s formula. |

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
```

On the current build `oracle.py` matches 333/333 species, and
`oracle_damage.py` finds calc.py's formula differs from the ROM on 15 of
30,276 fully-evolved pairs (the ROM truncates Atk/Def to 8 bits), never by
more than 1 HP. So the formula is faithful; calc.py's simplifications (flat
roll, ability/item/status modelling) are where its numbers lose fidelity.

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

Approximated / ignored (so don't over-read these): confusion as a flat
self-hit chance; multi-hit as average hit count; two-turn moves resolve in one
turn; Low Kick is a flat 80 BP and Avalanche never doubles; Counter/Mirror Coat
are not modelled; **no weather, screens, trapping, Perish Song**, or abilities/items
beyond the modeled subset above (see `engine.py`'s module docstring for the
full list). Consequently Ditto / Wobbuffet / Smeargle (Transform/Counter/
mechanic mons) and weather/screen teams are understated by design — that's a
known blind spot, not a balance verdict. The 6v6 numbers are *sampled*, so
deltas within ~±5% (more for rare roles with fewer games) are noise; raise
`--games` to tighten.

This is **Option A**: a clean, uniform heuristic AI chosen as a fair yardstick.
A faithful port of the ROM's trainer AI (`engine/battle/ai/*.asm`) would match
in-game trainer behavior but is large/fragile and not competitive-player-like,
so it remains an optional later phase.
