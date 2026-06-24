"""All-vs-all 1v1 best-move threat matrix for L50 meta-tuning.

For every ordered pair (A, B) in the viable pool, A picks its highest-average-
damage legal move vs B (and vice-versa). The 1v1 is resolved by hits-to-KO and
turn order (move priority, then Speed). Per mon we aggregate wins / losses /
draws -> a win rate ("threat score"), then flag the high and low outliers.

WHAT THIS MODELS: raw stat / typing / movepool / speed tuning, at a uniform
"max" build (DV15, 252 EVs everywhere, neutral nature), average damage roll,
crits off, plus a small set of multiplier-style abilities (Huge Power/Pure
Power, Adaptability, Technician, Sheer Force, Drought/Drizzle, and the
defender's own Sand Stream Sp.Def boost on Rock-types -- see calc.py). WHAT IT
DOES NOT: switching, items, weather chip damage, status/residual damage over
time, hazards, multi-turn moves, the 6v6 AI. It is a fast first-order signal,
not a full battle.

Usage (from repo root):
    python3 meta_sim/matrix.py                 # fully-evolved, non-legendary
    python3 meta_sim/matrix.py --include-legendary
    python3 meta_sim/matrix.py --include-unevolved --top 40
    python3 meta_sim/matrix.py --csv meta_sim/out/threats.csv
"""
import os, sys, json, argparse, csv

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from stats import mon_stats          # noqa: E402
from calc import best_move, hits_to_ko  # noqa: E402
from pool import eligible             # noqa: E402

def load(name):
    return json.load(open(os.path.join(HERE, 'data', name)))

def build_pool(mons, args):
    return {mid: m for mid, m in mons.items() if eligible(m, args)}

def first_mover(a, b):
    """Return 1 if a moves first, -1 if b, 0 if tie. a/b = (priority, speed)."""
    if a > b: return 1
    if a < b: return -1
    return 0

def resolve(htk_a, htk_b, order):
    """1v1 result for A: 1.0 win, 0.0 loss, 0.5 draw. `order` from first_mover(A,B)."""
    if htk_a == float('inf') and htk_b == float('inf'):
        return 0.5
    if htk_a < htk_b:
        return 1.0
    if htk_a > htk_b:
        return 0.0
    # equal hits-to-KO: the faster mover lands the killing blow first
    return 1.0 if order > 0 else (0.0 if order < 0 else 0.5)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--include-legendary', action='store_true')
    ap.add_argument('--include-unevolved', action='store_true')
    ap.add_argument('--top', type=int, default=25)
    ap.add_argument('--csv', default='meta_sim/out/threats.csv')
    args = ap.parse_args()

    mons = load('pokemon.json')
    moves = load('moves.json')
    chart = load('typechart.json')
    learnsets = load('learnsets.json')
    pool = build_pool(mons, args)

    # precompute L50 stats once per mon
    for mid, m in pool.items():
        m['stats'] = mon_stats(m['stats'])

    ids = sorted(pool)
    N = len(ids)
    rec = {mid: dict(win=0.0, loss=0.0, draw=0.0, beats=0, supereff=0) for mid in ids}

    for ai in ids:
        A = pool[ai]
        lsa = learnsets[ai]
        for bi in ids:
            if ai == bi:
                continue
            B = pool[bi]
            mvA, dmgA, effA = best_move(A, B, moves, lsa, chart)
            mvB, dmgB, effB = best_move(B, A, moves, learnsets[bi], chart)
            htkA = hits_to_ko(dmgA, B['stats']['hp'])
            htkB = hits_to_ko(dmgB, A['stats']['hp'])
            prioA = moves[mvA]['prio'] if mvA else 0
            prioB = moves[mvB]['prio'] if mvB else 0
            order = first_mover((prioA, A['stats']['spe']), (prioB, B['stats']['spe']))
            res = resolve(htkA, htkB, order)
            r = rec[ai]
            if res == 1.0:   r['win'] += 1;  r['beats'] += 1
            elif res == 0.0: r['loss'] += 1
            else:            r['draw'] += 1
            if effA >= 2.0:  r['supereff'] += 1

    rows = []
    denom = N - 1
    for mid in ids:
        r = rec[mid]
        wr = (r['win'] + 0.5 * r['draw']) / denom if denom else 0
        s = pool[mid]['stats']
        rows.append(dict(
            id=mid, types='/'.join(pool[mid]['types']), bst=pool[mid]['bst'],
            hp=s['hp'], atk=s['atk'], defe=s['defe'], spe=s['spe'], spa=s['spa'], spd=s['spd'],
            wins=int(r['win']), losses=int(r['loss']), draws=int(r['draw']),
            supereff=r['supereff'], winrate=round(wr, 4)))
    rows.sort(key=lambda x: x['winrate'], reverse=True)

    os.makedirs(os.path.dirname(args.csv), exist_ok=True)
    with open(args.csv, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    # report
    pool_desc = ("fully-evolved" if not args.include_unevolved else "all") + \
                (", incl. legendary" if args.include_legendary else ", non-legendary")
    print(f"\n1v1 threat matrix  |  pool: {N} mons ({pool_desc})  |  L50 max build, avg roll, crits off")
    print(f"CSV: {args.csv}\n")
    wrs = [r['winrate'] for r in rows]
    mean = sum(wrs) / len(wrs)
    print(f"win-rate  mean {mean:.3f}  median {sorted(wrs)[len(wrs)//2]:.3f}\n")

    def show(title, items):
        print(title)
        print(f"  {'rank':>4} {'mon':<22}{'types':<16}{'BST':>4} {'spe':>4} {'win%':>6}  W/L/D")
        for i, r in items:
            print(f"  {i:>4} {r['id']:<22}{r['types']:<16}{r['bst']:>4} {r['spe']:>4} "
                  f"{r['winrate']*100:>5.1f}  {r['wins']}/{r['losses']}/{r['draws']}")
        print()

    ranked = list(enumerate(rows, 1))
    show(f"TOP {args.top}  (overtuned candidates):", ranked[:args.top])
    show(f"BOTTOM {args.top}  (undertuned candidates):", ranked[-args.top:])

if __name__ == '__main__':
    main()
