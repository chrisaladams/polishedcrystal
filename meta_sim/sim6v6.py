"""6v6 Monte Carlo meta-tuning runner (pragmatic heuristic AI).

Runs many AI-vs-AI 6v6 battles between teams drawn from the viable pool and
aggregates each mon's team win rate -- a usage-stats style signal for which
mons over-/under-perform *in team contexts* (the thing the 1v1 matrix can't
see). Builds teams two ways and diffs them:

  random  win% : raw power across arbitrary teams
  role    win% : performance when slotted into a balanced, type-diverse team
  delta        : role - random. Large positive = synergy/support-dependent mon
                 that the 1v1 matrix and random teams understate.

Each of the 6 mons on the winning team is credited a win (draws = half), so
with enough games a mon that consistently lifts its teams' win rate rises.

Usage (from repo root):
    python3 meta_sim/sim6v6.py                       # both modes, default games
    python3 meta_sim/sim6v6.py --games 4000 --seed 1
    python3 meta_sim/sim6v6.py --mode random --top 30
    python3 meta_sim/sim6v6.py --include-legendary --csv meta_sim/out/sim6v6.csv

NOTE: This is Option A -- a uniform heuristic AI, not a port of the ROM's
trainer AI. See engine.py for the full list of modelled vs approximated
mechanics. Ditto/Wobbuffet/Smeargle and weather/screen teams are understated
by design (their mechanics are out of scope).
"""
import os, sys, json, argparse, csv, random

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from engine import run_battle, SLEEP_CLAUSE          # noqa: E402
from teams import build_pool, random_team, role_team  # noqa: E402


def load(name):
    return json.load(open(os.path.join(HERE, 'data', name)))


def run_mode(builder, ids, pool, moves, chart, games, rng):
    rec = {mid: dict(games=0, win=0.0, dmg=0.0, kos=0) for mid in ids}
    for g in range(games):
        ta = builder(ids, pool, moves, chart, rng)
        tb = builder(ids, pool, moves, chart, rng)
        res, contrib_a, contrib_b = run_battle(ta, tb, moves, chart,
                                                seed=rng.randrange(1 << 30))
        a_ids = [t[0] for t in ta]
        b_ids = [t[0] for t in tb]
        for mid in a_ids:
            rec[mid]['games'] += 1
        for mid in b_ids:
            rec[mid]['games'] += 1
        for mid, (dmg, kos) in zip(a_ids, contrib_a):
            rec[mid]['dmg'] += dmg
            rec[mid]['kos'] += kos
        for mid, (dmg, kos) in zip(b_ids, contrib_b):
            rec[mid]['dmg'] += dmg
            rec[mid]['kos'] += kos
        if res == 0:
            for mid in a_ids: rec[mid]['win'] += 1
        elif res == 1:
            for mid in b_ids: rec[mid]['win'] += 1
        else:
            for mid in a_ids: rec[mid]['win'] += 0.5
            for mid in b_ids: rec[mid]['win'] += 0.5
    return {mid: (r['win'] / r['games'] if r['games'] else 0.0, r['games'],
                  r['dmg'] / r['games'] if r['games'] else 0.0,
                  r['kos'] / r['games'] if r['games'] else 0.0)
            for mid, r in rec.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--games', type=int, default=3000, help='battles per mode')
    ap.add_argument('--mode', choices=['random', 'role', 'both'], default='both')
    ap.add_argument('--include-legendary', action='store_true')
    ap.add_argument('--include-unevolved', action='store_true')
    ap.add_argument('--top', type=int, default=25)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--csv', default='meta_sim/out/sim6v6.csv')
    args = ap.parse_args()

    mons = load('pokemon.json')
    moves = load('moves.json')
    chart = load('typechart.json')
    learnsets = load('learnsets.json')
    pool = build_pool(mons, learnsets, args)
    ids = sorted(pool)
    rng = random.Random(args.seed)

    modes = ['random', 'role'] if args.mode == 'both' else [args.mode]
    results = {}
    for mode in modes:
        builder = random_team if mode == 'random' else role_team
        print(f"running {args.games} battles  [{mode} teams]  pool={len(ids)} ...",
              flush=True)
        results[mode] = run_mode(builder, ids, pool, moves, chart, args.games, rng)

    rows = []
    for mid in ids:
        row = dict(id=mid, types='/'.join(pool[mid]['types']),
                   bst=pool[mid]['bst'], role=pool[mid]['_role'],
                   spe=pool[mid]['stats']['spe'])
        for mode in modes:
            wr, gms, dmg, kos = results[mode][mid]
            row[f'{mode}_win'] = round(wr, 4)
            row[f'{mode}_games'] = gms
            row[f'{mode}_dmg'] = round(dmg, 3)
            row[f'{mode}_kos'] = round(kos, 3)
        if len(modes) == 2:
            row['delta'] = round(row['role_win'] - row['random_win'], 4)
        rows.append(row)

    sort_key = 'role_win' if 'role' in modes else f'{modes[0]}_win'
    rows.sort(key=lambda r: r[sort_key], reverse=True)

    os.makedirs(os.path.dirname(args.csv), exist_ok=True)
    with open(args.csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # ---------------- report ----------------
    pool_desc = ("fully-evolved" if not args.include_unevolved else "all") + \
                (", incl. legendary" if args.include_legendary else ", non-legendary")
    clause_desc = "Sleep Clause on" if SLEEP_CLAUSE else "Sleep Clause off (matches shipped game)"
    print(f"\n6v6 Monte Carlo  |  pool: {len(ids)} ({pool_desc})  |  "
          f"{args.games} battles/mode  |  heuristic AI, {clause_desc}")
    print(f"CSV: {args.csv}")

    def col(mode):
        return f'{mode}_win'

    def show(title, items):
        print('\n' + title)
        hdr = f"  {'rank':>4} {'mon':<22}{'types':<16}{'role':<8}{'BST':>4} {'spe':>4}"
        for mode in modes:
            hdr += f" {mode[:4]+'%':>7}"
        if len(modes) == 2:
            hdr += f" {'delta':>7}"
        print(hdr)
        for i, r in items:
            line = f"  {i:>4} {r['id']:<22}{r['types']:<16}{r['role']:<8}{r['bst']:>4} {r['spe']:>4}"
            for mode in modes:
                line += f" {r[col(mode)]*100:>6.1f}"
            if len(modes) == 2:
                line += f" {r['delta']*100:>+6.1f}"
            print(line)

    ranked = list(enumerate(rows, 1))
    show(f"TOP {args.top}  (overtuned candidates):", ranked[:args.top])
    show(f"BOTTOM {args.top}  (undertuned candidates):", ranked[-args.top:])

    if len(modes) == 2:
        movers = sorted(rows, key=lambda r: r['delta'], reverse=True)
        show(f"\nBIGGEST role-vs-random GAINERS (synergy-dependent, 1v1 understates):",
             list(enumerate(movers[:15], 1)))
        show(f"BIGGEST role-vs-random LOSERS (lone-wolf mons):",
             list(enumerate(movers[-10:], 1)))


if __name__ == '__main__':
    main()
