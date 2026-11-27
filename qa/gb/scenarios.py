"""Seeded gameplay scenarios branched from the stage checkpoints (qa/gb/ladder.py).

A scenario = (stage, map, policy, seed). It is run on a fresh game loaded from the stage
checkpoint: the player is warped to a grass tile of the map (INJECTED), walks around with
real input until a wild battle starts, plays it with the chosen policy, then the state
oracles run. A fraction of scenarios also save, reload and compare. Everything after the
warp is controller input.

    python3 -m qa.gb.scenarios --count 200 --seed 1 --jobs 2 --out DIR
"""
import argparse
import hashlib
import json
import multiprocessing as mp
import os
import random
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

GRASS = 0x18


def grass_maps():
    """Maps with grass encounters, from data/wild/*_grass.asm."""
    from qa.gb import mapdata
    out = []
    for f in ('johto_grass', 'kanto_grass', 'orange_grass'):
        for line in open(os.path.join(ROOT, 'data', 'wild', f + '.asm')):
            m = re.match(r'\s*def_grass_wildmons\s+(\w+)', line)
            if m and m.group(1) in mapdata.attributes():
                out.append(m.group(1))
    return sorted(set(out))


def make_params(seed, index, stages=None):
    from qa.gb import autobattle, ladder
    rng = random.Random(f'{seed}/{index}')
    stages = stages or [s[0] for s in ladder.STAGES]
    return dict(seed=seed, index=index, stage=rng.choice(stages), map=rng.choice(grass_maps()),
                policy=rng.choice(autobattle.POLICIES), save_cycle=rng.random() < 0.25, rng_seed=rng.randrange(1 << 30))


def signature(kind, where, detail):
    d = re.sub(r'\d+', 'N', detail)[:160]
    return hashlib.sha1(f'{kind}|{where}|{d}'.encode()).hexdigest()[:12]


def run_one(params, out, rom=None, backend='pyboy', model='CGB-E'):
    """Run one scenario; returns a result dict (never raises)."""
    from qa.gb import autobattle, collision, fixtures as F, ladder, oracles, saves
    from qa.gb.consts import map_ids
    from qa.gb.guards import OverworldGuard
    from qa.gb.nav import Navigator, Softlock
    res = dict(params=params, outcome='ok', failures=[], battles=0, frames=0)
    g = None

    def fail(kind, detail, shot=True):
        where = '%s/%s' % (params['map'], params['policy'])
        res['failures'].append(dict(kind=kind, detail=detail[:300], sig=signature(kind, params['map'], detail)))
        res['outcome'] = 'fail'
        if shot and g is not None:
            try:
                os.makedirs(out, exist_ok=True)
                tag = os.path.join(out, 'scn_%d_%s' % (params['index'], kind))
                g.screenshot(os.path.basename(tag))
                g.dump_state(tag + '.state')
            except Exception:
                pass
    try:
        if backend == 'sameboy':
            from qa.gb.sameboy import SBGame
            g = SBGame(rom=rom, workdir=out, model=model, seed=params['rng_seed'])
            g.enable_exec_guard()
            g.tick(30)
            g.load_state_file(ladder.build(params['stage'], rom) + '.sb') if False else None
            raise RuntimeError('SameBoy scenarios load stages by replaying injection: see run_one_sameboy')
        from qa.gb.emu import Game
        g = Game(rom=rom, workdir=out, seed=params['rng_seed'])
        ladder.load(g, params['stage'], rom)
        rng = random.Random(params['rng_seed'])
        guard = OverworldGuard(g)
        nav = Navigator(g, seed=params['rng_seed'])
        gr, nr = map_ids(params['map'])
        F.teleport(g, gr, nr, 2, 2, settle=60)
        w, h = g.rd('wMapWidth') * 2, g.rd('wMapHeight') * 2
        tiles = [(x, y) for y in range(h) for x in range(w) if collision.tile_collision(g, x, y) == GRASS]
        if not tiles:
            res['outcome'] = 'skip'
            res['note'] = 'no tall grass tile'
            return res
        x, y = rng.choice(tiles)
        F.teleport(g, gr, nr, x, y, settle=90)
        g.wr('wRepelEffect', 0)
        start = g.frame
        # walk around until something happens
        dirs = ['up', 'down', 'left', 'right']
        while not g.in_battle() and g.frame - start < 1500:
            nav.hold(rng.choice(dirs), 16)
            g.tick(2)
            if not nav.ready() and not g.in_battle():
                nav.settle()
        if not g.in_battle():
            res['outcome'] = 'no-encounter'
            return res

        def check():
            probs = oracles.all_problems(g)
            if probs:
                raise AssertionError('; '.join(probs[:3]))
            if guard.crash.crashed:
                raise AssertionError('crash handler ran: %r' % (guard.crash.hits[-1],))
        try:
            autobattle.play(nav, max_frames=20000, policy=params['policy'], rng=rng, check=check)
            res['battles'] = 1
            nav.settle()
            probs = oracles.all_problems(g)
            if probs:
                fail('oracle', '; '.join(probs[:3]))
            guard.check('scenario')
            if guard.violations:
                fail('corruption', '; '.join(guard.violations[:2]))
            if params['save_cycle'] and not res['failures']:
                before = (F.where(g), oracles.party_problems(g), g.rd('wPartyCount'))
                g.call('SilentGameSave')
                sram = saves.dump_sram(g)
                path = os.path.join(out, 'cycle_%d.sav' % params['index'])
                os.makedirs(out, exist_ok=True)
                open(path, 'wb').write(sram)
                g2 = Game(rom=rom, sav=path, workdir=out)
                try:
                    saves.boot_continue(g2, F.where(g))
                    if oracles.party_problems(g2) or g2.rd('wPartyCount') != before[2]:
                        fail('save-cycle', 'party differs after save + Continue: %r' % (oracles.party_problems(g2),))
                except TimeoutError as e:
                    fail('save-cycle', 'Continue unavailable after a save: %s' % e, shot=False)
                g2.close()
        except AssertionError as e:
            fail('oracle', str(e))
        except Softlock as e:
            fail('softlock', str(e))
        res['frames'] = g.frame - start
    except Exception as e:           # a harness or game error: report it, don't hide it
        import traceback
        fail('error', ''.join(traceback.format_exception_only(type(e), e)).strip() + ' | ' + traceback.format_exc().splitlines()[-3][:120])
    finally:
        if g is not None:
            try:
                g.close()
            except Exception:
                pass
    return res


def _worker(args):
    params, out, rom = args
    return run_one(params, os.path.join(out, 'scn_%d' % params['index']), rom)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--count', type=int, default=100)
    ap.add_argument('--start', type=int, default=0, help='first scenario index (to resume or shard)')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--out', required=True)
    ap.add_argument('--stages', default=None, help='comma list of ladder stages (default all)')
    ap.add_argument('--rom', default=None)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    from qa.gb import ladder
    stages = a.stages.split(',') if a.stages else None
    for s in (stages or [x[0] for x in ladder.STAGES]):
        ladder.build(s, a.rom)                                     # build checkpoints once, before forking
    jobs = [(make_params(a.seed, i, stages), a.out, a.rom) for i in range(a.start, a.start + a.count)]
    t0 = time.time()
    results, sigs = [], {}
    ctx = mp.get_context('spawn')
    with ctx.Pool(a.jobs) as pool:
        for r in pool.imap_unordered(_worker, jobs):
            results.append(r)
            for f in r['failures']:
                sigs.setdefault(f['sig'], dict(f, count=0, first=r['params']))['count'] += 1
            if len(results) % 25 == 0:
                print('%d/%d scenarios, %d failure signatures, %ds' % (len(results), len(jobs), len(sigs), time.time() - t0), flush=True)
    by = {}
    for r in results:
        by[r['outcome']] = by.get(r['outcome'], 0) + 1
    summary = dict(seed=a.seed, scenarios=len(results), outcomes=by, battles=sum(r['battles'] for r in results),
                   seconds=round(time.time() - t0), failures=list(sigs.values()),
                   by_policy={p: sum(1 for r in results if r['params']['policy'] == p and r['outcome'] != 'no-encounter')
                              for p in ('fight', 'random', 'ko', 'swap', 'run', 'pack')},
                   replay='python3 -m qa.gb.scenarios --seed %d --start INDEX --count 1 --out DIR' % a.seed)
    json.dump(summary, open(os.path.join(a.out, 'summary.json'), 'w'), indent=1, default=str)
    print(json.dumps({k: summary[k] for k in ('scenarios', 'outcomes', 'battles', 'seconds')}), len(sigs), 'failure signatures')
    return 1 if sigs else 0


if __name__ == '__main__':
    sys.exit(main())
