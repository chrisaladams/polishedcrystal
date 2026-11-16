#!/usr/bin/env python3
"""Meta test: how effective is each mon at each playstyle it can play?

Every mon is entered once per playstyle it qualifies for (archetypes.py), with
a set and item built for that job. Teams are drafted from a balanced template
(two offense slots, a speed slot, a defense slot, a utility slot and a flex
slot) without stacking three shared weaknesses, then played out by engine.py.

Three kinds of evidence come out per build:

  impact     the swap test. After each battle, one build per side is swapped
             for a random other build of the same family (offense / speed /
             defense / utility) and the battle is replayed with the same
             seed. The difference in result, averaged, is how many points of
             team win rate this build is worth over a typical teammate doing
             the same job. It is the one number that compares a wall with an
             attacker fairly. Its standard error is reported alongside.
  win rate   team win rate with the build on it (context-dependent).
  job score  the build's average percentile, within its own playstyle, on the
             metrics that show whether it does that job (archetypes.JOB_METRICS:
             damage and KOs for attackers, damage absorbed and turns on the
             field for walls, statuses/screens/stat drops for supports,
             hazards, cures, pivots...).

Usage (from the repo root; a few minutes for the default on 4 cores):
  python3 meta_sim/metatest.py
  python3 meta_sim/metatest.py --battles 20000 --workers 4 --seed 7
Writes meta_sim/out/metatest.csv (one row per build) and
meta_sim/out/metatest.md (the report).
"""
import argparse
import csv
import json
import math
import os
import random
import sys
import time
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import archetypes as A                                    # noqa: E402
from engine import run_battle, STAT_KEYS                  # noqa: E402
from teams import build_pool, defensive_profile           # noqa: E402

TEMPLATE = ['offense', 'offense', 'speed', 'defense', 'utility', None]  # None = flex
FAMILIES = ['offense', 'speed', 'defense', 'utility']

_G = {}   # per-worker globals


def load(name):
    return json.load(open(os.path.join(HERE, 'data', name)))


def _init(args_dict):
    args = argparse.Namespace(**args_dict)
    mons, moves, chart, learnsets = (load(f) for f in
                                     ('pokemon.json', 'moves.json', 'typechart.json', 'learnsets.json'))
    pool = build_pool(mons, learnsets, args)
    builds = A.build_pool_builds(pool, moves)
    by_family = {f: [b for b in builds if A.FAMILY[b.style] == f] for f in FAMILIES}
    _G.update(moves=moves, chart=chart, builds=builds, by_family=by_family)


def draft(rng):
    """One balanced team of builds: distinct species, no 3 sharing a weakness."""
    chart, by_family = _G['chart'], _G['by_family']
    team, weak_count = [], {}
    for slot in TEMPLATE:
        fam = slot or rng.choice(FAMILIES)
        cands = by_family[fam]
        if slot is None:
            # Weather teams: pair a setter with a sweeper that uses its weather
            # (and vice versa) most of the time, as a real team would.
            setters = {b.weather for b in team if b.style == A.WEATHER_SETTER}
            sweepers = {b.weather for b in team if b.style == A.WEATHER_SWEEPER}
            want = ([b for b in _G['builds'] if b.style == A.WEATHER_SWEEPER and b.weather in setters]
                    or [b for b in _G['builds'] if b.style == A.WEATHER_SETTER and b.weather in sweepers])
            want = [b for b in want if all(t.mid != b.mid for t in team)]
            if want and rng.random() < 0.7:
                cands = want
        pick = None
        for _ in range(40):
            b = rng.choice(cands)
            if any(t.mid == b.mid for t in team):
                continue
            weak, _ = defensive_profile(b.mon['types'], chart)
            if any(weak_count.get(w, 0) >= 2 for w in weak):
                continue
            pick = b
            break
        if pick is None:                   # rare: relax synergy, keep species unique
            pick = next(b for b in rng.sample(cands, len(cands))
                        if all(t.mid != b.mid for t in team))
        team.append(pick)
        for w in defensive_profile(pick.mon['types'], _G['chart'])[0]:
            weak_count[w] = weak_count.get(w, 0) + 1
    return team


def _score(res, side):
    return 0.5 if res == -1 else (1.0 if res == side else 0.0)


def _battle(ta, tb, seed, detail=False):
    return run_battle([b.as_team_entry() for b in ta], [b.as_team_entry() for b in tb],
                      _G['moves'], _G['chart'], seed=seed, detail=detail)


def _replacement(rng, team, k):
    old = team[k]
    cands = _G['by_family'][A.FAMILY[old.style]]
    for _ in range(40):
        b = rng.choice(cands)
        if b is not old and all(t.mid != b.mid for t in team):
            return b
    return None


def worker(job):
    seed0, n, swaps = job
    rng = random.Random(seed0)
    rec = {}
    def slot(b):
        r = rec.get(b.key)
        if r is None:
            r = rec[b.key] = {'games': 0, 'score': 0.0, 'survived': 0,
                              'swap_n': 0, 'swap_sum': 0.0, 'swap_sq': 0.0,
                              **{k: 0.0 for k in STAT_KEYS}}
        return r
    for _ in range(n):
        ta, tb = draft(rng), draft(rng)
        seed = rng.randrange(1 << 30)
        res, ca, cb = _battle(ta, tb, seed, detail=True)
        for side, team, contrib in ((0, ta, ca), (1, tb, cb)):
            sc = _score(res, side)
            for b, c in zip(team, contrib):
                r = slot(b)
                r['games'] += 1
                r['score'] += sc
                r['survived'] += c['survived']
                for k in STAT_KEYS:
                    r[k] += c[k]
        # swap test: `swaps` slots per side, same seed (common random numbers)
        for side, team in ((0, ta), (1, tb)):
            for k in rng.sample(range(6), swaps):
                rep = _replacement(rng, team, k)
                if rep is None:
                    continue
                swapped = team[:k] + [rep] + team[k + 1:]
                res2, _, _ = (_battle(swapped, tb, seed) if side == 0
                              else _battle(ta, swapped, seed))
                d = _score(res, side) - _score(res2, side)
                r = slot(team[k])
                r['swap_n'] += 1
                r['swap_sum'] += d
                r['swap_sq'] += d * d
    return rec


def merge(recs):
    out = {}
    for rec in recs:
        for key, r in rec.items():
            o = out.setdefault(key, {k: 0.0 for k in r})
            for k, v in r.items():
                o[k] += v
    return out


def percentile_ranks(values):
    """value -> percentile (0-100) within the list."""
    s = sorted(values)
    n = len(s)
    return lambda v: 100.0 * sum(1 for x in s if x <= v) / n if n else 50.0


def analyse(builds, agg, min_samples):
    rows = []
    for b in builds:
        r = agg.get(b.key)
        if not r or not r['games']:
            continue
        g, n = r['games'], r['swap_n']
        mean = r['swap_sum'] / n if n else 0.0
        var = max(0.0, r['swap_sq'] / n - mean * mean) if n else 0.0
        se = math.sqrt(var / n) if n > 1 else float('nan')
        attacks = [m for m in b.moves if _G['moves'][m]['cat'] != 'STATUS'
                   and _G['moves'][m]['power'] > 0 and (_G['moves'][m]['effect'] not in A.NEVER
                                                        or _G['moves'][m]['effect'] == 'EFFECT_COUNTER')]
        row = {'mon': b.mid, 'playstyle': b.style, 'family': A.FAMILY[b.style],
               'modelled': bool(attacks) or b.ability == 'IMPOSTER',
               'games': int(g), 'win_rate': round(100 * r['score'] / g, 1),
               'impact': round(100 * mean, 2), 'impact_se': round(100 * se, 2),
               'swap_samples': int(n), 'survival': round(100 * r['survived'] / g, 1),
               'item': b.item, 'ability': b.ability, 'moves': ' / '.join(b.moves)}
        for k in STAT_KEYS:
            row[k] = round(r[k] / g, 3)
        rows.append(row)
    # job score: mean percentile on the playstyle's job metrics, within playstyle
    for style in A.PLAYSTYLES:
        group = [r for r in rows if r['playstyle'] == style]
        if not group:
            continue
        ranks = {k: percentile_ranks([r[k] for r in group]) for k in A.JOB_METRICS[style]}
        for r in group:
            r['job_score'] = round(sum(ranks[k](r[k]) for k in ranks) / len(ranks), 1)
    for r in rows:
        r['reliable'] = r['swap_samples'] >= min_samples and r['modelled']
    return rows


def fmt_table(rows, cols, heads):
    out = ['| ' + ' | '.join(heads) + ' |', '|' + '---|' * len(heads)]
    for r in rows:
        out.append('| ' + ' | '.join(str(r[c]) for c in cols) + ' |')
    return '\n'.join(out)


def report(rows, args, n_builds, n_mons, secs):
    ok = [r for r in rows if r['reliable']]
    ses = sorted(r['impact_se'] for r in ok if r['impact_se'] == r['impact_se'])
    typical_se = ses[len(ses) // 2] if ses else float('nan')
    L = [f'# Meta test',
         '',
         f'{args.battles:,} battles ({args.battles * (1 + 2 * args.swaps):,} including swap-test replays), '
         f'{n_builds} builds over {n_mons} mons, seed {args.seed}, {secs:.0f}s.',
         '',
         '**Impact** = points of team win rate a build adds over a random other build of the '
         'same family (offense / speed / defense / utility), from replaying the same battle with '
         f'it swapped out. Typical standard error here: ±{typical_se:.1f} points, so treat '
         f'differences under ~{2 * typical_se:.0f} points as noise. **Job** = average percentile, '
         'within the playstyle, on the metrics for that job. Builds with fewer than '
         f'{args.min_samples} swap samples are left out of the rankings (still in the CSV).',
         '']
    cols = ['mon', 'playstyle', 'impact', 'impact_se', 'win_rate', 'job_score']
    heads = ['Mon', 'Playstyle', 'Impact', '±', 'Win %', 'Job']
    by_impact = sorted(ok, key=lambda r: r['impact'], reverse=True)
    L += ['## Strongest builds overall', '', fmt_table(by_impact[:15], cols, heads), '',
          '## Weakest builds overall', '', fmt_table(by_impact[-15:][::-1], cols, heads), '']

    # per-mon: best playstyle
    best = {}
    for r in ok:
        if r['mon'] not in best or r['impact'] > best[r['mon']]['impact']:
            best[r['mon']] = r
    bests = sorted(best.values(), key=lambda r: r['impact'], reverse=True)
    over = [r for r in bests if r['impact'] - 2 * r['impact_se'] > 0
            and r['impact'] >= bests[max(0, len(bests) // 10 - 1)]['impact']]
    under = [r for r in bests if r['impact'] + 2 * r['impact_se'] < 0]
    L += ['## Overtuned candidates',
          '',
          'Mons whose best playstyle is in the top 10% and clearly above an average teammate.',
          '', fmt_table(over, cols, heads) if over else '_none_', '',
          '## Undertuned candidates',
          '',
          'Mons that are clearly worse than an average teammate even in their best playstyle.',
          '', fmt_table(under[::-1], cols, heads) if under else '_none_', '']

    unmod = sorted({r['mon'] for r in rows if not r['modelled']})
    if unmod:
        L += ['## Not modelled', '',
              'These mons rely on moves the engine does not simulate (Sketch, Transform '
              'outside Imposter), so they are left out of the rankings: '
              + ', '.join(unmod) + '.', '']
    for style in A.PLAYSTYLES:
        group = sorted((r for r in ok if r['playstyle'] == style),
                       key=lambda r: r['impact'], reverse=True)
        if not group:
            continue
        jm = A.JOB_METRICS[style]
        c = ['mon', 'impact', 'impact_se', 'job_score'] + jm + ['survival', 'item']
        h = ['Mon', 'Impact', '±', 'Job'] + jm + ['Survives %', 'Item']
        show = group if len(group) <= 12 else group[:6] + group[-6:]
        L += [f'## {style.capitalize()} ({len(group)} builds)', '',
              'Top and bottom by impact.' if len(group) > 12 else '', '',
              fmt_table(show, c, h), '']
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser(description='Per-playstyle meta test with a swap-test impact score.')
    ap.add_argument('--battles', type=int, default=30000)
    ap.add_argument('--swaps', type=int, default=6, choices=range(1, 7),
                    help='slots per side replayed with a stand-in after each battle')
    ap.add_argument('--workers', type=int, default=os.cpu_count() or 2)
    ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--min-samples', type=int, default=150,
                    help='swap samples a build needs to be ranked')
    ap.add_argument('--include-legendary', action='store_true')
    ap.add_argument('--include-unevolved', action='store_true')
    ap.add_argument('--out', default=os.path.join(HERE, 'out'))
    args = ap.parse_args()

    pool_args = {'include_legendary': args.include_legendary,
                 'include_unevolved': args.include_unevolved}
    _init(pool_args)
    builds = _G['builds']
    n_mons = len({b.mid for b in builds})
    chunks = max(args.workers * 8, 1)
    per = [args.battles // chunks + (1 if i < args.battles % chunks else 0) for i in range(chunks)]
    master = random.Random(args.seed)
    jobs = [(master.randrange(1 << 30), n, args.swaps) for n in per if n]
    print(f'{args.battles:,} battles x{1 + 2 * args.swaps} (with swap test), {len(builds)} builds, '
          f'{args.workers} workers...', flush=True)
    t = time.time()
    with Pool(args.workers, initializer=_init, initargs=(pool_args,)) as p:
        recs = p.map(worker, jobs)
    secs = time.time() - t
    rows = analyse(builds, merge(recs), args.min_samples)

    os.makedirs(args.out, exist_ok=True)
    cpath, mpath = os.path.join(args.out, 'metatest.csv'), os.path.join(args.out, 'metatest.md')
    with open(cpath, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r['playstyle'], -r['impact'])))
    with open(mpath, 'w') as f:
        f.write(report(rows, args, len(builds), n_mons, secs))
    print(f'done in {secs:.0f}s. Report: {mpath}\nCSV: {cpath}')


if __name__ == '__main__':
    main()
