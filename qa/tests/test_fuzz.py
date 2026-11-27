"""Seeded random-input fuzzing from several overworld starting points.

Buttons are pressed at random for QA_FUZZ_FRAMES frames (default 6000) per start. Wild
battles, trainer sight lines, menus and scripts are entered as the dice allow. Watched
throughout: ROM crash handlers, CPU hard locks, the player's object struct, the follower
queue and the stack pointer. On SameBoy a write watchpoint on the player's identity
bytes names the routine that corrupts them. A failure prints the seed and writes the
input log so it can be replayed.
"""
import json
import os

from qa.framework import qa_test
from qa.gb import fixtures as F
from qa.gb.consts import C, map_ids
from qa.gb.guards import OverworldGuard
from qa.tests.test_map_smoke import build, hard_locked, pick_tile

PROVENANCE = 'random button input from injected starting positions (seeded)'
STARTS = ['NEW_BARK_TOWN', 'ROUTE_29', 'GOLDENROD_CITY', 'ROUTE_43', 'LAKE_OF_RAGE', 'ILEX_FOREST', 'NATIONAL_PARK',
          'ECRUTEAK_CITY', 'ROUTE_36', 'CERULEAN_CAPE']
WEIGHTS = (('up', 6), ('down', 6), ('left', 6), ('right', 6), ('a', 3), ('b', 2), ('start', 0.4), ('select', 0.2))


def fuzz(ctx, g, start, frames):
    rng = ctx.rng
    guard = OverworldGuard(g)
    names, weights = zip(*WEIGHTS)
    sg, sn = map_ids(start)
    F.teleport(g, sg, sn, 2, 2, settle=60)
    tile = pick_tile(g)
    if tile is None:
        return None
    F.teleport(g, sg, sn, tile[0], tile[1], settle=90)
    log, battles, maps = [], 0, {F.where(g)[:2]}
    watched = []
    if hasattr(g, 'write_watch'):
        base = g.sym['wPlayerStruct'][1]
        from qa.gb.guards import PLAYER_SPRITES
        valid = {C.get(n) for n in PLAYER_SPRITES}

        def on_write(game, addr, old, new, pc):
            idx = addr - base
            if idx == 0 and new in valid:
                return
            if idx in (1, 2) and new == old:
                return
            watched.append(f'write {new:#04x} over {old:#04x} at wPlayerStruct+{idx} by {game.where(pc)}')
        g.write_watch(base, base + 3, on_write, wram_bank=1)
    used = 0
    while used < frames:
        # a mix of purposeful walking (long directional holds that cross tiles) and button mashing
        if rng.random() < 0.7:
            b = rng.choice(('up', 'down', 'left', 'right'))
            hold = rng.choice((16, 32, 48, 64))
        else:
            b = rng.choices(names, weights)[0]
            hold = rng.choice((2, 4, 8))
        log.append((g.frame, b, hold))
        g.hold(b, hold)
        g.tick(rng.choice((2, 6, 12)))
        used += hold + 8
        if g.in_battle():
            battles += 1
        maps.add(F.where(g)[:2])
        if len(log) % 20 == 0:
            guard.check(f'{start} frame {g.frame}')
            if hard_locked(g):
                guard.player.violations.append(f'{start}: CPU hard lock at {g.where()}')
        if guard.violations or watched:
            break
    problems = list(guard.violations) + watched
    return dict(start=start, log=log, battles=battles, maps=len(maps), problems=problems)


def run(ctx):
    frames = int(os.environ.get('QA_FUZZ_FRAMES', '6000'))
    starts = STARTS[:int(os.environ.get('QA_FUZZ_STARTS', len(STARTS)))]
    total_b = 0
    for start in starts:
        g = ctx.boot('smoke_base', build)
        r = fuzz(ctx, g, start, frames)
        if r is None:
            ctx.note(f'{start}: no walkable tile')
            continue
        total_b += r['battles']
        ctx.note(f'{start}: {frames} frames, {len(r["log"])} inputs, {r["battles"]} battle frames, {r["maps"]} maps seen')
        if r['problems']:
            path = os.path.join(ctx.out, f'fuzz_{start}_seed{ctx.seed}.json')
            json.dump({'seed': ctx.seed, 'start': start, 'inputs': r['log']}, open(path, 'w'))
            ctx.artifacts.append(path)
            ctx.snapshot(g, f'fuzz_{start}')
            for p in r['problems'][:4]:
                ctx.expect(False, f'seed {ctx.seed}, start {start}: {p}')
    ctx.note(f'{total_b} frames spent in battle across all starts')


@qa_test(suites=('general', 'full'), covers=('stress.fuzz', 'hw.memory_guard', 'follower'),
         backends=('pyboy', 'sameboy'), provenance=PROVENANCE, timeout=3000)
def random_input_fuzz(ctx):
    run(ctx)
