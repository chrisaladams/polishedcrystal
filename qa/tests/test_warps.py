"""Take every warp event of every map on foot and check where it leads.

For each `warp_event x, y, DEST, n` of a map: the player is placed on a walkable neighbour tile (INJECTED) and walks
onto the warp tile with real button input. The warp must

  * load the destination map named in the data (or, for LAST_MAP, return to a previous map),
  * put the player on the destination's n-th warp tile (the data says where the player arrives),
  * leave the object engine intact (player struct, follower queue, no crash handler),
  * leave no stuck state (script mode back to idle, the game loop still advancing).

A warp that could not be triggered from any neighbour (event-gated, blocked by an object or by a ledge) is counted
separately as NOT TAKEN and is not covered; it is never counted as passed. Coverage ids: `MAP#index`.
"""
import os

from qa.framework import qa_test
from qa.gb import collision, fixtures as F, mapdata
from qa.gb.consts import C, map_ids
from qa.gb.guards import OverworldGuard
from qa.gb.nav import map_const_of
from qa.tests.test_connections import Interrupted, hold
from qa.tests.test_map_smoke import build as build_base

PROVENANCE = 'walking onto each warp tile: gameplay input; party and the starting tile beside the warp: injected'
NEIGHBOURS = [('down', 0, 1), ('up', 0, -1), ('left', -1, 0), ('right', 1, 0)]   # direction pressed, offset of the start tile from the warp
LEAVE = {'down': 'up', 'up': 'down', 'left': 'right', 'right': 'left'}


def warp_targets(const):
    a = mapdata.attributes()[const]
    return mapdata.parse_map(a['label'])['warps']


def try_warp(g, guard, const, idx, x, y, backup=False):
    """Returns ('taken', map) / ('not-taken', why)."""
    sg, sn = map_ids(const)
    tried = []
    warp_tiles = {(w[0], w[1]) for w in warp_targets(const)}
    for direction, dx, dy in NEIGHBOURS:
        # the player stands on the neighbour tile on the side the warp is entered from, and walks *toward* the warp
        sx, sy = {'down': (x, y - 1), 'up': (x, y + 1), 'left': (x + 1, y), 'right': (x - 1, y)}[direction]
        if not (0 <= sx < g.rd('wMapWidth') * 2 and 0 <= sy < g.rd('wMapHeight') * 2):
            continue
        if not collision.walkable(g, sx, sy) and (sx, sy) not in warp_tiles:
            tried.append(f'{direction}: start tile blocked')
            continue
        F.teleport(g, sg, sn, sx, sy, settle=40)
        if F.where(g)[:2] != (sg, sn):
            tried.append(f'{direction}: map did not stay loaded')
            continue
        if backup:
            # warp -1 returns to the map the player came from; a real player has one (INJECTED: Olivine Port)
            bg, bn = map_ids('OLIVINE_PORT')
            g.wr('wBackupMapGroup', bg)
            g.wr('wBackupMapNumber', bn)
            g.wr('wBackupWarpNumber', 1)
        guard.player.ref = guard.player.read()
        guard.player.violations.clear()
        first = []

        def watch(game, first=first):                    # the position on the first frame in the new map, before any scene moves the player
            if not first and F.where(game)[:2] != (sg, sn):
                first.append(F.where(game))
        g.frame_hooks.append(watch)
        try:
            for _ in range(4):
                try:
                    hold(g, direction, 16)
                except Interrupted:
                    return 'not-taken', 'a battle started on the way'
                if F.where(g)[:2] != (sg, sn):
                    g.arrival = first[0] if first else F.where(g)
                    return 'taken', direction
        finally:
            g.frame_hooks.remove(watch)
        tried.append(f'{direction}: no warp')
    return 'not-taken', '; '.join(tried[:4]) or 'no usable neighbour tile'


def run_shard(ctx, shard, shards):
    g = ctx.boot('smoke_base', build_base)
    guard = OverworldGuard(g)
    g.save_point()
    consts = sorted(mapdata.attributes())[shard::shards]
    only = os.environ.get('QA_WARP_ONLY')
    if only:
        consts = [c for c in sorted(mapdata.attributes()) if only in c]
    limit = int(os.environ.get('QA_WARP_MAPS', '0')) or None
    if limit:
        consts = consts[:limit]
    taken = wrong = skipped = 0
    not_taken, problems, ambiguous = [], [], []
    total = 0
    for const in consts:
        warps = warp_targets(const)
        if not warps:
            continue
        for idx, (x, y, dest, n) in enumerate(warps):
            total += 1
            g.restore_point()
            guard.crash.hits.clear()
            try:
                sg, sn = map_ids(const)
                F.teleport(g, sg, sn, 2, 2, settle=80)           # load the map (INJECTED)
                if F.where(g)[:2] != (sg, sn):
                    skipped += 1
                    not_taken.append(f'{const}#{idx}: map did not load')
                    continue
                res, why = try_warp(g, guard, const, idx, x, y, backup=n < 0)
                if res != 'taken':
                    not_taken.append(f'{const}#{idx} -> {dest}: {why}')
                    continue
                g.tick(90)
                taken += 1
                n_amb = len(ambiguous)
                here = getattr(g, 'arrival', None) or F.where(g)
                now = F.where(g)
                if n < 0:
                    want_map = map_ids('OLIVINE_PORT')
                    if here[:2] != want_map:
                        wrong += 1
                        problems.append(f'{const}#{idx}: warp -1 led to map {here[:2]}, the backup map was Olivine Port')
                        continue
                elif dest != 'LAST_MAP':
                    want_map = map_ids(dest) if dest in mapdata.attributes() else None
                    if want_map is None:
                        wrong += 1
                        problems.append(f'{const}#{idx}: destination {dest} is not a map constant')
                        continue
                    if here[:2] != want_map:
                        arrived = map_const_of(*here[:2])
                        # redirects the game makes on purpose (Lavender Radio Tower becomes the Haunted one under an event flag)
                        if arrived and dest.startswith('LAV_RADIO_TOWER') and arrived.startswith('HAUNTED_RADIO_TOWER'):
                            ambiguous.append(f'{const}#{idx}: {dest} became {arrived} (event-driven map swap)')
                        elif any(map_ids(w[2]) == here[:2] for w in warp_targets(const) if w[2] in mapdata.attributes() and abs(w[0] - x) + abs(w[1] - y) <= 3 and w is not warp_targets(const)[idx]):
                            ambiguous.append(f'{const}#{idx}: crossed a neighbouring warp first and arrived at {arrived}')
                        else:
                            wrong += 1
                            problems.append(f'{const}#{idx}: led to map {here[:2]} ({arrived}), data says {dest}')
                            continue
                    else:
                        dw = warp_targets(dest)
                        if 1 <= n <= len(dw):
                            wx, wy = dw[n - 1][0], dw[n - 1][1]
                            # the player is placed on the warp tile and walks out of the door (one step): allow one tile
                            if abs(here[2] - wx) + abs(here[3] - wy) > 1:
                                wrong += 1
                                problems.append(f'{const}#{idx} -> {dest}#{n}: arrived at {(here[2], here[3])} on the first frame, the destination warp is at {(wx, wy)}')
                                continue
                guard.check(f'{const}#{idx}')
                if guard.violations:
                    problems.append(f'{const}#{idx}: ' + '; '.join(guard.violations[:2]))
                    guard.player.violations.clear()
                    continue
                if guard.crash.crashed:
                    problems.append(f'{const}#{idx}: crash handler ran')
                if len(ambiguous) == n_amb:                      # an ambiguous crossing exercised another warp: not counted for this one
                    ctx.cover('warp', f'{const}#{idx}')
            except Exception as e:
                problems.append(f'{const}#{idx}: {type(e).__name__}: {e}')
    for a_ in ambiguous:
        ctx.note('not a defect: ' + a_)
    ctx.note(f'shard {shard}/{shards}: {total} warps, {taken} taken on foot, {len(not_taken)} not taken, {wrong} wrong destination/arrival, {len(problems)} problems')
    for m in not_taken[:60]:
        ctx.note('not taken: ' + m)
    for p in problems:
        ctx.expect(False, p)
    ctx.expect(taken > 0, 'no warp in this shard could be taken (vacuous run)')
    if not_taken:
        ctx.uncover('map.warps', f'{len(not_taken)} of {total} warps in shard {shard} not taken')


def _make(i, n):
    @qa_test(suites=('map', 'full'), covers=('map.warps',), backends=('pyboy',), provenance=PROVENANCE, timeout=7200, name=f'test_warps.warps_{i}of{n}')
    def shard(ctx):
        run_shard(ctx, i, n)
    return shard


for _i in range(4):
    _make(_i, 4)
