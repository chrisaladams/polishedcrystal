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
| `teams.py`   | Role-aware moveset picker + two team builders (random, role-based). |
| `sim6v6.py`  | 6v6 Monte Carlo runner → per-mon team win rate, both builders compared. |

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
python3 meta_sim/sim6v6.py                    # both builders, 3000 battles each
python3 meta_sim/sim6v6.py --games 5000       # more battles = tighter signal
python3 meta_sim/sim6v6.py --mode role --top 40
python3 meta_sim/sim6v6.py --include-legendary --csv meta_sim/out/sim6v6.csv
```

`sim6v6.py` writes `meta_sim/out/sim6v6.csv` (per-mon role + `random_win` /
`role_win` / `delta`) and prints top/bottom outliers plus the biggest
role-vs-random movers.

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

For each battle two teams are built (random or role-based) with role-aware
movesets, and a **heuristic AI** plays both sides identically: pick the best
damaging move, but set up / status / heal / lay hazards when it's the better
play, and switch out of clearly losing matchups. Each mon on the winning team
is credited a win; aggregated over thousands of battles this gives a team win
rate per mon. Running both builders and taking `role − random` (`delta`) flags
mons that depend on team synergy (the support/stall mons 1v1 understates).

Modelled (the high-impact ~80%): damage + stat stages, the major statuses
(sleep/paralysis/burn/poison/toxic/freeze + confusion), on-hit secondary
effects, self-stat setup moves, recovery, Leech Seed, entry hazards
(Spikes/Toxic Spikes), priority, switching. **Sleep Clause is mirrored** from
the shipped game (toggle `SLEEP_CLAUSE` in `engine.py`).

Approximated / ignored (so don't over-read these): confusion as a flat
self-hit chance; multi-hit as average hit count; two-turn moves resolve in one
turn; **no weather, screens, trapping, Perish Song, held items, or abilities**.
Consequently Ditto / Wobbuffet / Smeargle (Transform/Counter/mechanic mons) and
weather/screen teams are understated by design — that's a known blind spot, not
a balance verdict. The 6v6 numbers are *sampled*, so deltas within ~±5% (more
for rare roles with fewer games) are noise; raise `--games` to tighten.

This is **Option A**: a clean, uniform heuristic AI chosen as a fair yardstick.
A faithful port of the ROM's trainer AI (`engine/battle/ai/*.asm`) would match
in-game trainer behavior but is large/fragile and not competitive-player-like,
so it remains an optional later phase.
