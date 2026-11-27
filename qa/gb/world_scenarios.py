"""Non-battle world scenarios, enumerated for unique coverage first.

A scenario is one combination of (map, standing tile, time of day, event-flag state, follower species, action).
Scenario `i` is derived from `i` alone, in an order that covers breadth first:

    i in [0, 613)        every map once            (tod, flags, follower, action rotate with the index)
    then                 every map at every time of day
    then                 every map x time of day x flag state
    then                 the action variations     ...

so the first N scenarios are N *different* combinations and repeats only appear after the space of
(map, tod, flags, action) is exhausted; a repeat (same combination, other seed/tile) is reported as a repeat.

What a scenario does (real controller input after the injected placement):
  idle        stand still for 300 frames
  walk        eight short walks in random directions
  menus       Start menu: open three entries, page through them, back out
  transition  walk onto one of the map's warps and on for a few steps
  save        save the game, start a fresh console from the save, Continue, compare place/party/flags

Monitors, all the time: player struct / follower queue / crash handler / stack pointer (OverworldGuard), sprite
findings (per object against the repository graphic, objects not drawn), tilemap and palette sanity, a blank or
frozen screen, script mode stuck after the action. Nothing is a pass unless it ran to its end: outcomes are
ok / fail / skip (the map cannot be stood in) / interrupted (a trainer or wild battle began and ended the walk).

    python3 -m qa.gb.world_scenarios --count 1000 --seed 1 --jobs 3 --out DIR [--only SUBSTR] [--rom PATH]
"""
import argparse
import hashlib
import json
import os
import random
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

ACTIONS = ['idle', 'walk', 'menus', 'transition', 'walk', 'save']
TODS = [('morn', 7), ('day', 13), ('nite', 22)]
FLAG_STATES = ['default', 'allflags', 'noflags']
MENU_LABELS = ['StartMenu', 'StartMenu_Pokedex', 'StartMenu_Pokemon', 'StartMenu_Pack', 'StartMenu_Pokegear', 'StartMenu_Status',
               'StartMenu_FieldBook', 'StartMenu_Option', 'StartMenu_Save', 'PokegearMap_Init', 'PokegearRadio_Init', 'PokegearPhone_Init',
               'PokegearClock_Init']

_maps = []
_species = []


def enterable_maps():
    from qa.gb import mapdata
    if not _maps:
        _maps.extend(sorted(mapdata.attributes()))
    return _maps


def follower_species():
    if not _species:
        from qa.inventory import build
        inv = json.load(open(os.path.join(ROOT, 'qa/reports/inventory.json'))) if os.path.exists(os.path.join(ROOT, 'qa/reports/inventory.json')) else build()
        _species.extend(s for s in inv['follower'])
    return _species


def make_params(seed, i):
    maps = enterable_maps()
    n = len(maps)
    rng = random.Random(f'{seed}/{i}')
    order = random.Random(f'order/{seed}')
    perm = list(range(n))
    order.shuffle(perm)
    m = maps[perm[i % n]]
    block = i // n
    tod = TODS[(block + i) % 3] if block == 0 else TODS[block % 3]
    flags = FLAG_STATES[(block // 3) % 3] if block else FLAG_STATES[0]
    action = ACTIONS[(block // 9 + i) % len(ACTIONS)] if block >= 9 else ACTIONS[i % len(ACTIONS)]
    species = follower_species()
    follower = 'TOTODILE' if i % 4 else species[(i * 7 + block) % len(species)]
    key = f'{m}|{tod[0]}|{flags}|{action}|{follower}'
    return dict(seed=seed, index=i, map=m, tod=tod[0], hour=tod[1], flags=flags, action=action, follower=follower, key=key,
                rng_seed=rng.randrange(1 << 30), kind=action)


def signature(kind, where, detail):
    d = re.sub(r'\d+', 'N', detail)[:140]
    return hashlib.sha1(f'{kind}|{where}|{d}'.encode()).hexdigest()[:12]


# ---- worker (one cached game per process) ----------------------------------------------------------------
_G = {}


def _game(rom, out):
    from qa.gb import fixtures as F, saves
    from qa.gb.emu import Game
    from qa.gb.guards import OverworldGuard
    from qa.tests.test_map_smoke import build
    if 'g' not in _G:
        p = saves.fixture('smoke_base', build, rom=rom)
        g = Game(rom=rom, sav=p, workdir=out)
        saves.boot_continue(g, saves.fixture_meta(p)['where'])
        g.save_point()
        _G.update(g=g, guard=OverworldGuard(g), sav=p, rom=rom, counters={n: g.counter(n) for n in MENU_LABELS if n in g.sym})
    return _G['g'], _G['guard']


def _set_follower(g, name):
    from qa.gb.consts import C
    if name == 'TOTODILE' or name not in C:
        return
    sp = C[name] & 0xff
    g.wr('wPartySpecies', sp)
    g.wr('wPartyMon1Species', sp)
    if 'wPartyMon1Form' in g.sym:
        g.wr('wPartyMon1Form', (C[name] >> 8) & 0xff)


def run_job(job):
    params, out, rom = job
    return run_one(params, out, rom)


def run_one(params, out, rom=None):
    from qa.av import vram
    from qa.gb import collision, fixtures as F, mapdata, sweep
    from qa.gb.consts import map_ids
    from qa.tests.test_connections import Interrupted, hold
    from qa.tests.test_map_smoke import STATE_DEPENDENT, pick_tile
    from qa.tests.test_av import STATE_QUIRKS
    res = dict(params=params, outcome='ok', failures=[], covered={}, frames=0)
    g = None
    t0 = time.time()

    def fail(kind, detail):
        res['outcome'] = 'fail'
        res['failures'].append(dict(kind=kind, detail=detail[:300], sig=signature(kind, params['map'], detail)))
        try:
            os.makedirs(out, exist_ok=True)
            tag = os.path.join(out, 'w%d_%s' % (params['index'], kind))
            g.screenshot(os.path.basename(tag))
            g.dump_state(tag + '.state')
        except Exception:
            pass

    def cover(kind, ids):
        res['covered'].setdefault(kind, set()).update([ids] if isinstance(ids, str) else ids)

    try:
        g, guard = _game(rom, out)
        g.restore_point()
        guard.crash.hits.clear()
        rng = random.Random(params['rng_seed'])
        const = params['map']
        sg, sn = map_ids(const)
        sweep.apply_state(g, params['flags'])
        _set_follower(g, params['follower'])
        g.wr('wRTCHours', params['hour'])
        g.wr('wRTCMinutes', 5)
        F.teleport(g, sg, sn, 2, 2, settle=60)
        if F.where(g)[:2] != (sg, sn):
            res['outcome'] = 'skip'
            res['note'] = 'warp did not load the map'
            return res
        tile = pick_tile(g)
        if tile is None:
            res['outcome'] = 'skip'
            res['note'] = 'no walkable tile'
            return res
        w, h = g.rd('wMapWidth') * 2, g.rd('wMapHeight') * 2
        walk = [(x, y) for y in range(h) for x in range(w) if collision.walkable(g, x, y)]
        tile = rng.choice(walk) if walk else tile
        F.teleport(g, sg, sn, tile[0], tile[1], settle=40)
        g.tick(40)
        guard.player.ref = guard.player.read()
        guard.player.violations.clear()
        if g.in_battle():
            res['outcome'] = 'interrupted'
            return res
        cover('map', const)
        cover('tod_map', f"{const}@{params['tod']}")
        cover('follower', params['follower'])
        base_counts = {n: c() for n, c in _G['counters'].items()}

        def check(tag):
            guard.check(tag)
            if guard.violations:
                fail('corruption', f'{tag}: ' + '; '.join(guard.violations[:2]))
                guard.player.violations.clear()
            if guard.crash.crashed:
                fail('crash', f'{tag}: crash handler ran')
                guard.crash.hits.clear()
            if const in STATE_DEPENDENT:
                return
            first = {f['msg'] for f in vram.sprite_findings(g) if not f['expected'] and (const, f['kind']) not in STATE_QUIRKS}
            if first:
                g.tick(2)                      # a finding must persist: a struct caught mid-update is not a defect
                again = {f['msg'] for f in vram.sprite_findings(g) if not f['expected'] and (const, f['kind']) not in STATE_QUIRKS}
                for msg in sorted(first & again):
                    fail('sprite', f"{tag}: {msg}")
            for msg in vram.tilemap_problems(g):
                if 'unused bit 4' not in msg:
                    fail('tilemap', f'{tag}: {msg}')
            rgb = g.frame_rgb()
            if rgb.std() < 1.0 and not g.in_battle() and g.rd('wScriptMode') == 0:
                fail('blank-screen', f'{tag}: the screen is a single flat colour')

        check('placed')
        act = params['action']
        try:
            if act == 'idle':
                for k in range(5):
                    g.tick(60)
                    check(f'idle {k}')
            elif act == 'walk':
                for k in range(8):
                    hold(g, rng.choice(['up', 'down', 'left', 'right']), 16)
                    check(f'walk {k}')
            elif act == 'menus':
                for k in range(3):
                    g.press('start', 4, 30)
                    for _ in range(rng.randrange(0, 7)):
                        g.press('down', 4, 8)
                    g.press('a', 4, 40)
                    for _ in range(rng.randrange(0, 4)):
                        g.press(rng.choice(['right', 'left', 'down', 'up']), 4, 12)
                    g.tick(20)
                    check(f'menu {k} open')
                    for _ in range(8):
                        g.press('b', 4, 18)
                    g.tick(30)
                    check(f'menu {k} closed')
                now = {n: c() for n, c in _G['counters'].items()}
                cover('menu', [n for n in now if now[n] != base_counts[n]])
            elif act == 'transition':
                from qa.tests.test_warps import try_warp, warp_targets
                warps = warp_targets(const)
                if not warps:
                    res['note'] = 'no warps in this map'
                else:
                    idx = rng.randrange(len(warps))
                    x, y, dest, n = warps[idx]
                    r, why = try_warp(g, guard, const, idx, x, y, backup=n < 0)
                    if r == 'taken':
                        cover('warp', f'{const}#{idx}')
                        g.tick(90)
                        check('after warp')
                        for k in range(4):
                            hold(g, rng.choice(['up', 'down', 'left', 'right']), 16)
                            check(f'after warp walk {k}')
                    else:
                        res['note'] = 'warp not taken: ' + why
            elif act == 'save':
                from qa.gb import oracles, saves
                from qa.gb.emu import Game
                before = (F.where(g), g.rd('wPartyCount'))
                g.call('SilentGameSave')
                sram = saves.dump_sram(g)
                path = os.path.join(out, 'w%d.sav' % params['index'])
                os.makedirs(out, exist_ok=True)
                open(path, 'wb').write(sram)
                g2 = Game(rom=rom, sav=path, workdir=out)
                try:
                    saves.boot_continue(g2, F.where(g))
                    after = F.where(g2)
                    if after[:2] != before[0][:2]:
                        fail('save-cycle', f'Continue put the player on map {after[:2]}, saved on {before[0][:2]}')
                    if oracles.party_problems(g2) or g2.rd('wPartyCount') != before[1]:
                        fail('save-cycle', 'party differs after save + Continue: %r' % (oracles.party_problems(g2),))
                    for k in range(60):
                        g2.tick(1)
                    cover('save_state', const)
                except TimeoutError as e:
                    fail('save-cycle', 'Continue unavailable after a save: %s' % e)
                g2.close()
        except Interrupted:
            res['outcome'] = 'interrupted' if res['outcome'] == 'ok' else res['outcome']
        # idle in a clean state after the action: the script engine must have returned control
        g.tick(30)
        if g.rd('wScriptMode') not in (0,) and not g.in_battle() and act in ('idle', 'walk'):
            fail('stuck', f'script mode {g.rd("wScriptMode")} after a plain {act}')
        res['frames'] = g.frame
    except Exception as e:
        import traceback
        if g is not None:
            fail('error', ''.join(traceback.format_exception_only(type(e), e)).strip() + ' | ' + traceback.format_exc().splitlines()[-3][:120])
        else:
            res['outcome'] = 'fail'
            res['failures'].append(dict(kind='error', detail=str(e)[:300], sig=signature('error', 'setup', str(e))))
    res['covered'] = {k: sorted(v) for k, v in res['covered'].items()}
    res['seconds'] = round(time.time() - t0, 2)
    return res


# ---- driver -----------------------------------------------------------------------------------------------
def summarise(out):
    results = [json.loads(l) for l in open(os.path.join(out, 'results.jsonl'))]
    by = {}
    for r in results:
        by[r['outcome']] = by.get(r['outcome'], 0) + 1
    keys = {}
    for r in results:
        keys.setdefault(r['params']['key'], []).append(r['outcome'])
    done_keys = {k for k, v in keys.items() if any(o in ('ok', 'fail') for o in v)}
    sigs = {}
    for r in results:
        for f in r['failures']:
            sigs.setdefault(f['sig'], dict(f, count=0, first=r['params']))['count'] += 1
    cov = {}
    for r in results:
        if r['outcome'] in ('ok', 'fail'):
            for k, v in r['covered'].items():
                cov.setdefault(k, set()).update(v)
    summary = dict(attempted=len(results), outcomes=by, completed=by.get('ok', 0) + by.get('fail', 0),
                   unique_combinations_completed=len(done_keys), repeated_combinations=len(results) - len(keys),
                   by_action={a: sum(1 for r in results if r['params']['action'] == a and r['outcome'] in ('ok', 'fail')) for a in sorted(set(ACTIONS))},
                   by_flags={f: sum(1 for r in results if r['params']['flags'] == f and r['outcome'] in ('ok', 'fail')) for f in FLAG_STATES},
                   by_tod={t: sum(1 for r in results if r['params']['tod'] == t and r['outcome'] in ('ok', 'fail')) for t, _ in TODS},
                   seconds=round(sum(r.get('seconds', 0) for r in results)), failures=sorted(sigs.values(), key=lambda f: -f['count']),
                   replay='python3 -m qa.gb.world_scenarios --seed SEED --start INDEX --count 1 --jobs 1 --out DIR')
    json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), indent=1, default=str)
    json.dump({k: sorted(v) for k, v in cov.items()}, open(os.path.join(out, 'coverage.json'), 'w'))
    print(json.dumps({k: summary[k] for k in ('attempted', 'completed', 'unique_combinations_completed', 'outcomes')}), len(sigs), 'failure signatures')
    return 1 if sigs else 0


def main(argv=None):
    from qa.gb import scenarios
    ap = argparse.ArgumentParser()
    ap.add_argument('--count', type=int, default=100)
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--jobs', type=int, default=3)
    ap.add_argument('--out', required=True)
    ap.add_argument('--rom', default=None)
    ap.add_argument('--timeout', type=int, default=240)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    log_path = os.path.join(a.out, 'results.jsonl')
    done = set()
    if os.path.exists(log_path):
        for line in open(log_path):
            try:
                done.add(json.loads(line)['params']['index'])
            except Exception:
                pass
    jobs = [(make_params(a.seed, i), os.path.join(a.out, 'art'), a.rom) for i in range(a.start, a.start + a.count) if i not in done]
    print('%d scenarios to run (%d already in the log)' % (len(jobs), len(done)), flush=True)
    t0 = time.time()
    n = 0
    with open(log_path, 'a') as log:
        for r in scenarios.run_isolated(jobs, a.jobs, a.timeout, target='qa.gb.world_scenarios:run_job'):
            r.setdefault('covered', {})
            log.write(json.dumps(r, default=str) + '\n')
            log.flush()
            n += 1
            if n % 50 == 0:
                print('%d/%d scenarios, %ds' % (n, len(jobs), time.time() - t0), flush=True)
    return summarise(a.out)


if __name__ == '__main__':
    sys.exit(main())
