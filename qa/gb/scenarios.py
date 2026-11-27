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


STATUSES = [0, 0, 0, 'PSN', 'BRN', 'PAR', 'FRZ', 'TOX', 'SLP']


def make_params(seed, index, stages=None, kinds=None, backend='pyboy'):
    """Everything a scenario does is derived from (seed, index): replayable."""
    from qa.gb import autobattle, ladder
    rng = random.Random(f'{seed}/{index}')
    stages = stages or [s[0] for s in ladder.STAGES]
    kind = rng.choice(kinds or (['inject'] * 6 + ['walk']))
    p = dict(seed=seed, index=index, kind=kind, stage=rng.choice(stages), map=rng.choice(grass_maps()),
             policy=rng.choice(autobattle.POLICIES), save_cycle=rng.random() < 0.25 and backend == 'pyboy',
             rng_seed=rng.randrange(1 << 30))
    # variation: what the wild Pokemon is, the lead's condition, weather, repeats
    p.update(species=rng.randrange(1, 252), level=rng.choice([2, 5, 10, 20, 35, 50, 70, 100]), status=rng.choice(STATUSES),
             lead_hp=rng.choice([1.0, 1.0, 0.5, 0.1]), weather=rng.choice([None, None, None, 'WEATHER_RAIN', 'WEATHER_SUN', 'WEATHER_SANDSTORM', 'WEATHER_HAIL']),
             repeats=rng.choice([1, 1, 1, 2, 3]), backend=backend)
    return p


def signature(kind, where, detail):
    d = re.sub(r'\d+', 'N', detail)[:160]
    return hashlib.sha1(f'{kind}|{where}|{d}'.encode()).hexdigest()[:12]


def _inject_wild(g, p):
    """Start a wild battle the way the overworld does after a roll succeeds: the species and level go
    into the encounter variables and the ROM's own WildBattleScript is queued (INJECTED encounter)."""
    g.wr('wRepelEffect', 0)
    g.wr('wTempWildMonSpecies', p['species'])
    g.wr('wWildMonForm', 0)
    g.wr('wCurPartyLevel', p['level'])
    bank, addr = g.sym['WildBattleScript']
    # what LoadMemScript does, written directly (no routine call: the call mechanism is the part PyBoy
    # occasionally wedges on): the overworld's PlayerEvents runs the queued script on its next pass
    g.wr('wMapReentryScriptQueueFlag', 1)
    g.wr('wMapReentryScriptBank', bank)
    g.wr('wMapReentryScriptAddress', addr & 0xff)
    g.wr('wMapReentryScriptAddress', addr >> 8, 1)
    for _ in range(900):
        g.tick(1)
        if g.in_battle():
            return True
    return False


def _prepare_lead(g, p):
    """INJECTED: the lead's status and HP, so battles also start from a statused or weak lead."""
    from qa.gb.consts import C
    st = p['status']
    if st:
        g.wr('wPartyMon1Status', 3 if st == 'SLP' else 1 << C[st])
    mx = g.rd('wPartyMon1MaxHP') << 8 | g.rd('wPartyMon1MaxHP', 1)
    hp = max(1, int(mx * p['lead_hp']))
    g.wr('wPartyMon1HP', hp >> 8)
    g.wr('wPartyMon1HP', hp & 0xff, 1)


def _load_game(params, out, rom, model):
    """A game at the scenario's stage checkpoint, on the requested backend."""
    from qa.gb import ladder
    if params['backend'] == 'sameboy':
        from qa.gb.sameboy import SBGame
        g = SBGame(rom=rom, workdir=out, model=model, seed=params['rng_seed'])
        g.tick(30)
        g.load_state_file(ladder.build_sb(params['stage'], rom, model))
        g.tick(5)
        return g
    from qa.gb.emu import Game
    g = Game(rom=rom, workdir=out, seed=params['rng_seed'])
    ladder.load(g, params['stage'], rom)
    return g


def run_one(params, out, rom=None, model='CGB-E'):
    """Run one scenario; returns a result dict (never raises).

    outcome: ok (every battle ran to its end and the checks ran), fail, skip (could not be set up),
    no-battle (the injected encounter never began a battle), no-encounter (walking found none).
    Only `ok` and `fail` count as completed scenarios; `battles` counts battles that ended."""
    from qa.gb import autobattle, collision, fixtures as F, oracles, saves
    from qa.gb.consts import C, map_ids
    from qa.gb.guards import OverworldGuard
    from qa.gb.nav import Navigator, Softlock
    res = dict(params=params, outcome='ok', failures=[], battles=0, frames=0)
    g = None

    def fail(kind, detail, shot=True):
        res['failures'].append(dict(kind=kind, detail=detail[:300], sig=signature(kind, params['map'] if params['kind'] == 'walk' else params['stage'], detail)))
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
        g = _load_game(params, out, rom, model)
        rng = random.Random(params['rng_seed'])
        sb = params['backend'] == 'sameboy'
        guard = None if sb else OverworldGuard(g)
        nav = Navigator(g, seed=params['rng_seed'])
        start = g.frame
        if params['kind'] == 'walk':
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
            dirs = ['up', 'down', 'left', 'right']
            while not g.in_battle() and g.frame - start < 1500:
                nav.hold(rng.choice(dirs), 16)
                g.tick(2)
                if not nav.ready() and not g.in_battle():
                    nav.settle()
            if not g.in_battle():
                res['outcome'] = 'no-encounter'
                return res
        else:
            _prepare_lead(g, params)
            if not _inject_wild(g, params):
                res['outcome'] = 'no-battle'
                return res
        if sb:
            g.enable_exec_guard()
        crash = guard.crash if guard else None

        def check():
            probs = oracles.all_problems(g)
            if probs:
                raise AssertionError('; '.join(probs[:3]))
            if crash is not None and crash.crashed:
                raise AssertionError('crash handler ran: %r' % (crash.hits[-1],))
            if sb:
                bad = g.exec_events()
                if bad:
                    raise AssertionError('execution guard: %r' % (bad[:2],))

        def weather(g_):
            if params['weather']:
                g_.wr('wBattleWeather', C[params['weather']])
                g_.wr('wWeatherCount', 5)
        try:
            for rep in range(params['repeats']):
                if rep:
                    nav.settle()
                    _prepare_lead(g, dict(params, status=0, lead_hp=1.0))
                    if not _inject_wild(g, dict(params, species=1 + (params['species'] + rep * 37) % 251)):
                        res['outcome'] = 'no-battle'
                        break
                autobattle.play(nav, max_frames=20000, policy=params['policy'] if rep == 0 else 'fight', rng=rng, check=check,
                                on_first_menu=weather if rep == 0 else None)
                res['battles'] += 1
            nav.settle()
            probs = oracles.all_problems(g)
            if probs:
                fail('oracle', '; '.join(probs[:3]))
            if guard:
                guard.check('scenario')
                if guard.violations:
                    fail('corruption', '; '.join(guard.violations[:2]))
            if params['save_cycle'] and not res['failures'] and not sb:
                before = (F.where(g), oracles.party_problems(g), g.rd('wPartyCount'))
                g.call('SilentGameSave')
                sram = saves.dump_sram(g)
                path = os.path.join(out, 'cycle_%d.sav' % params['index'])
                os.makedirs(out, exist_ok=True)
                open(path, 'wb').write(sram)
                from qa.gb.emu import Game
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
    params, out, rom, model = args
    return run_one(params, os.path.join(out, 'scn_%d' % params['index']), rom, model)


def build_stage_safely(stage, rom, backend, model, tries=4, timeout=420):
    """Build a stage checkpoint in a child process; PyBoy occasionally wedges inside a frame, which would hang
    the campaign before it starts. Retries (the wedge is timing dependent) and fails loudly after `tries`."""
    import subprocess
    code = ('import sys; sys.path.insert(0, %r); from qa.gb import ladder; '
            'ladder.%s(%r, %r%s)' % (ROOT, 'build_sb' if backend == 'sameboy' else 'build', stage, rom, ', %r' % model if backend == 'sameboy' else ''))
    for n in range(tries):
        try:
            r = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True, timeout=timeout)
            if r.returncode == 0:
                return
            err = r.stderr[-300:]
        except subprocess.TimeoutExpired:
            err = 'timeout after %ds' % timeout
        print('stage %s build attempt %d failed: %s' % (stage, n + 1, err), flush=True)
    raise SystemExit('cannot build stage %s' % stage)


def _serve(conn):
    """Worker process: run scenarios sent over the pipe until told to stop."""
    while True:
        job = conn.recv()
        if job is None:
            return
        conn.send(_worker(job))


def run_isolated(jobs, nworkers, timeout):
    """Yield one result per job. Each worker is a separate process that is killed if a scenario does not
    finish within `timeout` seconds (an emulator or game hang must not stall the campaign); the job is retried
    once on a fresh worker and, if it hangs again, recorded as outcome 'hang' (a finding, never a pass)."""
    import collections
    ctx = mp.get_context('spawn')
    pending = collections.deque((j, 0) for j in jobs)
    workers = [None] * nworkers

    def start():
        parent, child = ctx.Pipe()
        proc = ctx.Process(target=_serve, args=(child,), daemon=True)
        proc.start()
        return dict(proc=proc, conn=parent, job=None, t0=0)
    while pending or any(w and w['job'] for w in workers):
        for i in range(nworkers):
            w = workers[i]
            if w is None:
                w = workers[i] = start()
            if w['job'] is None and pending:
                job, tries = pending.popleft()
                w['job'], w['tries'], w['t0'] = job, tries, time.time()
                w['conn'].send(job)
            elif w['job'] is not None:
                if w['conn'].poll(0.05):
                    try:
                        yield w['conn'].recv()
                    except EOFError:
                        yield dict(params=w['job'][0], outcome='fail', battles=0, frames=0,
                                   failures=[dict(kind='error', detail='worker died', sig=signature('error', 'worker', 'worker died'))])
                        w['proc'].kill()
                        workers[i] = None
                        continue
                    w['job'] = None
                elif not w['proc'].is_alive() or time.time() - w['t0'] > timeout:
                    hung = w['proc'].is_alive()
                    w['proc'].kill()
                    job, tries = w['job'], w['tries']
                    workers[i] = None
                    if tries < 1:
                        pending.appendleft((job, tries + 1))
                    else:
                        p = job[0]
                        detail = 'no progress for %ds (%s)' % (timeout, 'hung' if hung else 'worker died')
                        yield dict(params=p, outcome='hang', battles=0, frames=0,
                                   failures=[dict(kind='hang', detail=detail, sig=signature('hang', p['stage'], p['backend'] + p['kind']))])
        time.sleep(0.01)
    for w in workers:
        if w:
            w['proc'].kill()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--count', type=int, default=100)
    ap.add_argument('--start', type=int, default=0, help='first scenario index (to resume or shard)')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--jobs', type=int, default=2)
    ap.add_argument('--out', required=True)
    ap.add_argument('--stages', default=None, help='comma list of ladder stages (default all)')
    ap.add_argument('--kinds', default=None, help='inject, walk (default: mostly inject, some walk)')
    ap.add_argument('--backend', default='pyboy', choices=['pyboy', 'sameboy'])
    ap.add_argument('--model', default='CGB-E', help='SameBoy model')
    ap.add_argument('--rom', default=None)
    ap.add_argument('--timeout', type=int, default=300, help='seconds before a scenario is declared hung and its worker killed')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    from qa.gb import ladder
    stages = a.stages.split(',') if a.stages else None
    kinds = a.kinds.split(',') if a.kinds else (['inject'] if a.backend == 'sameboy' else None)
    for st in (stages or [x[0] for x in ladder.STAGES]):                      # build checkpoints once, before forking
        build_stage_safely(st, a.rom, a.backend, a.model)
    log_path = os.path.join(a.out, 'results.jsonl')
    done = set()
    if os.path.exists(log_path):                                              # resume: skip indices already run
        for line in open(log_path):
            try:
                done.add(json.loads(line)['params']['index'])
            except Exception:
                pass
    jobs = [(make_params(a.seed, i, stages, kinds, a.backend), a.out, a.rom, a.model) for i in range(a.start, a.start + a.count) if i not in done]
    print('%d scenarios to run (%d already in the log)' % (len(jobs), len(done)), flush=True)
    t0 = time.time()
    n = 0
    with open(log_path, 'a') as log:
        for r in run_isolated(jobs, a.jobs, a.timeout):
            log.write(json.dumps(r, default=str) + '\n')
            log.flush()
            n += 1
            if n % 50 == 0:
                print('%d/%d scenarios, %ds' % (n, len(jobs), time.time() - t0), flush=True)
    return summarise(a.out, a)


def summarise(out, a=None):
    """Aggregate results.jsonl (all runs so far, not only this invocation) into summary.json."""
    results = [json.loads(line) for line in open(os.path.join(out, 'results.jsonl'))]
    by, sigs = {}, {}
    for r in results:
        by[r['outcome']] = by.get(r['outcome'], 0) + 1
        for f in r['failures']:
            sigs.setdefault(f['sig'], dict(f, count=0, first=r['params']))['count'] += 1
    completed = by.get('ok', 0) + by.get('fail', 0)
    species = {r['params']['species'] for r in results if r['battles'] and r['params'].get('kind') == 'inject'}
    summary = dict(attempted=len(results), completed=completed, outcomes=by, battles_executed=sum(r['battles'] for r in results),
                   skipped=by.get('skip', 0), not_started=by.get('no-battle', 0) + by.get('no-encounter', 0),
                   by_kind={k: sum(1 for r in results if r['params'].get('kind') == k and r['outcome'] in ('ok', 'fail')) for k in ('inject', 'walk')},
                   by_policy={p: sum(1 for r in results if r['params']['policy'] == p and r['outcome'] in ('ok', 'fail')) for p in ('fight', 'random', 'ko', 'swap', 'run', 'pack')},
                   by_status={str(st): sum(1 for r in results if r['params'].get('status') == st and r['outcome'] in ('ok', 'fail')) for st in STATUSES[2:]},
                   by_weather={str(w): sum(1 for r in results if r['params'].get('weather') == w and r['outcome'] in ('ok', 'fail')) for w in (None, 'WEATHER_RAIN', 'WEATHER_SUN', 'WEATHER_SANDSTORM', 'WEATHER_HAIL')},
                   distinct_species_fought=len(species), frames_played=sum(r['frames'] for r in results),
                   failures=sorted(sigs.values(), key=lambda f: -f['count']),
                   replay='python3 -m qa.gb.scenarios --seed SEED --start INDEX --count 1 --out DIR --jobs 1')
    json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=1, default=str)
    print(json.dumps({k: summary[k] for k in ('attempted', 'completed', 'battles_executed', 'skipped', 'not_started', 'outcomes')}), len(sigs), 'failure signatures')
    return 1 if sigs else 0


if __name__ == '__main__':
    sys.exit(main())
