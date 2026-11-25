#!/usr/bin/env python3
"""Find each build's best set: the moves, item, ability and Hidden Power type
that win the most, so no mon is judged by a weak auto-picked set.

For each build (a mon in one playstyle) it hill-climbs one choice at a time:
ability, then held item, then each attacking move slot, then the Hidden Power
type. The status moves the playstyle picked (Spikes for a hazard setter,
Recover for a wall...) stay, so a build keeps its job.

Candidates are compared with common random numbers: the build is dropped into
a random team, the battle is played with the current set and with the
candidate on the same teams and the same battle seed, and the win rates are
compared pairwise, so team luck and battle luck cancel out. Every candidate in
a round is screened on the same contexts; the best one must then win again on
a fresh, larger sample (and by more than 2.5 standard errors) to be accepted,
so picking the luckiest of many candidates doesn't fool it. To save time,
screening is done in two stages (every candidate on a third of the contexts,
then the best few on all), and confirmation stops early once a candidate
clearly can't pass, or clearly passes (by 3 standard errors, after at least
200 contexts).

Writes data/best_sets.json; archetypes.build_pool_builds applies it, so the
meta test uses the optimised sets.

Run: python3 meta_sim/optimize.py [--screen 100] [--confirm 500] [--workers N]
     [--only MON[,MON...]]
"""
import argparse
import json
import math
import os
import random
import sys
import time
import zlib
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import archetypes as A                                   # noqa: E402
import items as I                                        # noqa: E402
import mechanics                                         # noqa: E402
import metatest as MT                                    # noqa: E402

OUT = os.path.join(HERE, 'data', 'best_sets.json')

GENERAL_ITEMS = ['LEFTOVERS', 'LIFE_ORB', 'CHOICE_BAND', 'CHOICE_SPECS', 'CHOICE_SCARF',
                 'FOCUS_SASH', 'ASSAULT_VEST', 'SITRUS_BERRY', 'LUM_BERRY', 'EXPERT_BELT',
                 'ROCKY_HELMET', 'MUSCLE_BAND', 'WISE_GLASSES', 'SHELL_BELL', 'AIR_BALLOON',
                 'WHITE_HERB', 'QUICK_CLAW', 'SCOPE_LENS']
TYPE_ITEM = {v['param']: k for k, v in mechanics.ITEM_DATA.items()
             if v.get('held') == 'HELD_TYPE_BOOST'}
SPECIES_ITEM = {'marowak': 'THICK_CLUB', 'cubone': 'THICK_CLUB', 'pikachu': 'LIGHT_BALL',
                'farfetch_d': 'LEEK', 'sirfetch_d': 'LEEK', 'chansey': 'LUCKY_PUNCH',
                'ditto': 'QUICK_POWDER'}
HP_TYPES = mechanics.TYPE_ORDER[1:]

_W = {}


def _winit(args_dict, overrides):
    A.BEST_SETS = None                     # optimise against the heuristic sets
    MT._init(args_dict)
    _W['overrides'] = overrides


def _variant(b, change):
    """A copy of build b with fields changed."""
    nb = A.Build(b.mid, b.style, list(b.moves), b.ability, b.item, b.mon, b.weather, b.hp_type)
    for k, v in change.items():
        setattr(nb, k, list(v) if k == 'moves' else v)
    return nb


def _context(rng, b):
    """A random team containing b (in place of a same-family slot or a clash)
    and a random opposing team."""
    team = MT.draft(rng)
    clash = next((i for i, t in enumerate(team) if t.mid == b.mid), None)
    k = clash if clash is not None else rng.randrange(6)
    team[k] = b
    return team, k, MT.draft(rng), rng.randrange(1 << 30)


def _eval_job(job):
    """Play one batch of contexts: baseline set vs each candidate, same seeds.
    Returns per-candidate lists of score differences."""
    key, base, cands, seed, n = job
    b0 = _resolve(key, base)
    variants = [_variant(b0, c) for c in cands]
    rng = random.Random(seed)
    diffs = [[] for _ in cands]
    for _ in range(n):
        team, k, foes, bseed = _context(rng, b0)
        side = rng.randrange(2)
        def play(build):
            t = team[:k] + [build] + team[k + 1:]
            res, _, _ = MT._battle(t, foes, bseed) if side == 0 else MT._battle(foes, t, bseed)
            return MT._score(res, side)
        s0 = play(b0)
        for i, v in enumerate(variants):
            diffs[i].append(play(v) - s0)
    return diffs


def _resolve(key, base):
    b = next(x for x in MT._G['builds'] if x.key == key)
    return _variant(b, base)


def _stats(xs):
    n = len(xs)
    m = sum(xs) / n
    var = sum((x - m) ** 2 for x in xs) / max(1, n - 1)
    return m, math.sqrt(var / n)


def evaluate(pool, key, base, cands, n, seed, workers):
    """Mean score difference and SE of each candidate vs base over n contexts."""
    per = max(1, n // workers)
    jobs = [(key, base, cands, seed * 1000 + j, per) for j in range(workers)]
    out = [[] for _ in cands]
    for diffs in pool.map(_eval_job, jobs):
        for i, d in enumerate(diffs):
            out[i].extend(d)
    return [_stats(d) for d in out]


SCREEN_KEEP = 4        # candidates kept after the first screening stage
CONFIRM_TRIES = 2      # screened candidates tried in turn until one is confirmed
CONFIRM_CHUNK = 100    # contexts per confirmation chunk
CONFIRM_MIN = 200      # contexts before a change can be accepted


def confirm(pool, key, base, cand, args, seed):
    """Confirm a candidate on fresh contexts, in chunks: stop as soon as it
    clearly can't pass (its mean plus 2.5 standard errors is no better than
    the base), or once it clearly passes after at least CONFIRM_MIN contexts
    (by 3 standard errors before the full args.confirm, to allow for having
    looked early). Returns the mean and standard error of what was played."""
    diffs = []
    chunk = 0
    while len(diffs) < args.confirm:
        n = min(CONFIRM_CHUNK, args.confirm - len(diffs))
        per = max(1, n // args.workers)
        jobs = [(key, base, [cand], seed * 1000 + chunk * args.workers + j, per)
                for j in range(args.workers)]
        for d in pool.map(_eval_job, jobs):
            diffs.extend(d[0])
        chunk += 1
        m, se = _stats(diffs)
        if m + 2.5 * se <= 0.01:
            break                                   # can't pass
        if len(diffs) >= CONFIRM_MIN and len(diffs) < args.confirm and m > 3 * se and m > 0.01:
            break                                   # clearly passes
    return _stats(diffs)


def candidates(b, moves):
    """The options for each dimension, from what the mon can use."""
    mon = b.mon
    abilities_ = sorted({a for a in mon['abilities'] if a})
    sp = mechanics.rom_damage.species(type('M', (), {'id': b.mid})())
    items_ = list(GENERAL_ITEMS)
    for t in mon['types']:
        if t in TYPE_ITEM:
            items_.append(TYPE_ITEM[t])
    if sp in SPECIES_ITEM:
        items_.append(SPECIES_ITEM[sp])
    if I.eviolite_eligible(b.mid, mon):
        items_.append('EVIOLITE')
    if 'POISON' in mon['types']:
        items_.append('BLACK_SLUDGE')
    if b.weather and b.style == A.WEATHER_SETTER:
        items_.append(A.WEATHER_ROCK[b.weather])
    for ab in abilities_:
        if ab in I.ORB_FOR_ABILITY:
            items_.append(I.ORB_FOR_ABILITY[ab])
    # Choice items lock the first move used; a build whose job is two or more
    # status moves (setup, walls, support...) can't use them
    if sum(moves[mv]['cat'] == 'STATUS' for mv in b.moves) >= 2:
        items_ = [i for i in items_ if not i.startswith('CHOICE_')]
    # an Assault Vest stops its holder using status moves (the simulator
    # models only its Special Defense), so it's no choice for a build with one
    if any(moves[mv]['cat'] == 'STATUS' for mv in b.moves):
        items_ = [i for i in items_ if i != 'ASSAULT_VEST']
    attacks = A._attacks(mon, moves, n=10)
    if 'HIDDEN_POWER' in mon['_pool'] and 'HIDDEN_POWER' not in attacks:
        attacks.append('HIDDEN_POWER')
    return abilities_, sorted(set(items_)), attacks


def optimise_build(pool, b, moves, args, log):
    """Hill-climb b; returns the accepted changes as a dict."""
    base = {}
    abilities_, items_, attacks = candidates(b, moves)
    seed = zlib.crc32(b.key.encode()) % 100000

    def round_(dim, options):
        nonlocal base, seed
        cur = dict(base)
        cands = [o for o in options if o != cur.get(dim, getattr(b, dim))]
        if not cands:
            return
        seed += 1
        # screen in two stages: every candidate on a third of the contexts,
        # then only the best few on all of them
        if len(cands) > SCREEN_KEEP:
            first = evaluate(pool, b.key, cur, [{**cur, dim: o} for o in cands],
                             max(args.workers, args.screen // 3), seed, args.workers)
            order = sorted(range(len(cands)), key=lambda i: -first[i][0])
            # a species' own item (Thick Club, Light Ball...) always goes on to
            # the full screening: the first stage is too short to rule it out
            # (it once dropped Thick Club, worth +5 points, for Alolan Marowak)
            keep = [cands[i] for i in order[:SCREEN_KEEP]]
            keep += [o for o in cands if dim == 'item' and o in SPECIES_ITEM.values()
                     and o not in keep]
            cands = keep
            seed += 1
        screened = evaluate(pool, b.key, cur, [{**cur, dim: o} for o in cands],
                            args.screen, seed, args.workers)
        # confirm the best of the screening, and if it fails (screening is
        # noisy), the runner-up
        order = sorted(range(len(cands)), key=lambda i: -screened[i][0])
        for best_i in order[:CONFIRM_TRIES]:
            if screened[best_i][0] <= 0:
                return
            seed += 1
            m, se = confirm(pool, b.key, cur, {**cur, dim: cands[best_i]}, args, seed + 50000)
            if m > 2.5 * se and m > 0.01:
                base = {**cur, dim: cands[best_i]}
                log(f'    {dim}: {getattr(b, dim) if dim not in cur else cur[dim]} -> '
                    f'{cands[best_i]}  (+{100 * m:.1f} pts, SE {100 * se:.1f})')
                return

    round_('ability', abilities_)
    round_('item', items_)
    # attacking slots: swap one move at a time, keeping the role's status moves
    for slot in range(len(b.moves)):
        cur_moves = list(base.get('moves', b.moves))
        if moves[cur_moves[slot]]['cat'] == 'STATUS':
            continue
        opts = [cur_moves[:slot] + [mv] + cur_moves[slot + 1:]
                for mv in attacks if mv not in cur_moves]
        round_('moves', [tuple(o) for o in opts])
        if 'moves' in base:
            base['moves'] = list(base['moves'])
    if 'HIDDEN_POWER' in base.get('moves', b.moves):
        round_('hp_type', HP_TYPES)
    return base


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--screen', type=int, default=100, help='contexts per screening round')
    ap.add_argument('--confirm', type=int, default=500, help='contexts to confirm a change')
    ap.add_argument('--workers', type=int, default=os.cpu_count() or 2)
    ap.add_argument('--only', default='', help='comma-separated mon ids')
    ap.add_argument('--resume', action='store_true', help='skip builds already in the output')
    ap.add_argument('--out', default=OUT, help='where to write the sets (default: data/best_sets.json)')
    ap.add_argument('--include-legendary', action='store_true')
    ap.add_argument('--include-unevolved', action='store_true')
    args = ap.parse_args()
    margs = dict(battles=1, swaps=6, workers=1, seed=0, min_samples=150,
                 include_legendary=args.include_legendary,
                 include_unevolved=args.include_unevolved, out=os.path.join(HERE, 'out'))
    # optimise against the heuristic sets (ignore any previous best_sets.json)
    A.BEST_SETS = None
    MT._init(margs)
    moves = MT._G['moves']
    builds = [b for b in MT._G['builds'] if not args.only or b.mid in args.only.split(',')]
    out = args.out
    best = json.load(open(out)) if os.path.exists(out) and (args.only or args.resume) else {}
    if args.resume:
        builds = [b for b in builds if b.key not in best]
    t0 = time.time()
    with Pool(args.workers, initializer=_winit, initargs=(margs, None)) as pool:
        for i, b in enumerate(builds):
            lines = []
            change = optimise_build(pool, b, moves, args, lines.append)
            nb = _variant(b, change)
            best[b.key] = {'moves': list(nb.moves), 'item': nb.item, 'ability': nb.ability,
                           'hp_type': nb.hp_type}
            print(f'[{i + 1}/{len(builds)} {time.time() - t0:.0f}s] {b.key}: '
                  f'{"unchanged" if not change else "improved"}', flush=True)
            for ln in lines:
                print(ln, flush=True)
            json.dump(best, open(out, 'w'), indent=1)
    print(f'wrote {out} ({len(best)} builds) in {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main()
