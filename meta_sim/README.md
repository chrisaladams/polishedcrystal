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

## Usage (run from the repo root)

```sh
python3 meta_sim/extract.py          # refresh JSON from the .asm source
python3 meta_sim/matrix.py           # fully-evolved, non-legendary pool
python3 meta_sim/matrix.py --include-legendary --top 40
python3 meta_sim/matrix.py --include-unevolved --csv meta_sim/out/all.csv
```

`matrix.py` writes `meta_sim/out/threats.csv` (per-mon stats + W/L/D + win
rate) and prints the top/bottom outliers.

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

Known bias: pure Normal-types over-perform here because Normal is neutral vs
almost everything and the model can't punish them by switching in a Ghost. Read
the leaderboard as "who hits hard and fast into a neutral field," then sanity-
check candidates in context.

A full 6v6 AI Monte Carlo (abilities/items/status/clauses, with Sleep/Evasion
Clause toggles that *mirror* the shipped behavior) is a documented later phase.
