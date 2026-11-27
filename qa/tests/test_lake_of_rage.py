"""Regression: Lake of Rage hardware report 1 (player vanishes / freezes walking up to the old man).

Root cause (confirmed): walking in over the Route 43 -> Lake of Rage map
connection kept the follower's follow link alive while no follower object
existed on the new map (Lake of Rage has 19 object events, which CanHaveFollower
refused). Every step queued into wFollowMovementQueue (5 bytes) with nobody
consuming it; entries 6-8 overwrote wPlayerStruct's Sprite, MapObjectIndex and
SpriteTile with 13 (the 'step up' movement byte), so the player was drawn from
garbage tiles and then ignored input.

Provenance: Route 43 position, party and the save are INJECTED (fixture); the
walk itself is genuine button input across the real map connection.
"""
import os
import sys

from qa.gb import fixtures as F, saves
from qa.gb.consts import C, map_ids
from qa.gb.emu import Game
from qa.framework import qa_test
from qa.gb.guards import PlayerStructGuard

PROVENANCE = 'walk: gameplay input; party/position/save: injected fixture'


def build(g):
    """a Totodile in the party, standing on Route 43 (10,8)"""
    F.give_mon(g, C['TOTODILE'], 10)
    F.teleport(g, *map_ids('ROUTE_43'), 10, 8)


def run(g):
    """Walk north from Route 43 into Lake of Rage up to the old man.
    Returns (ok, notes)."""
    guard = PlayerStructGuard(g)
    notes = []
    positions = []
    blocked = 0
    last = None
    lake = map_ids('LAKE_OF_RAGE')
    for step in range(60):
        g.hold('up', 16)
        g.tick(6)
        guard.check(f'step {step} at {F.where(g)}')
        w = F.where(g)
        positions.append(w)
        if w[:2] == lake and w[2:] == (20, 27):
            blocked += 1 if last == w else 0
            if blocked >= 3:
                break
        last = w
    reached = [p for p in positions if p[:2] == lake and p[2:] == (20, 27)]
    ok = True
    if guard.violations:
        ok = False
        notes += guard.violations[:5]
    if not reached:
        ok = False
        notes.append('never reached the old man at (20,27): last %r' % (positions[-1],))
    if reached and blocked < 3:
        ok = False
        notes.append('player was not stopped by the old man (walked through or past him)')
    notes.append('player struct sprite=%d tile=%d' % (g.read(guard.base, 1), g.read(guard.base + 2, 1)))
    return ok, notes


@qa_test(suites=('regression', 'map', 'full'), covers=('map.connections', 'follower', 'sprites.player'),
         backends=('pyboy', 'sameboy'), provenance=PROVENANCE)
def lake_of_rage_approach(ctx):
    g = ctx.boot('route43_basic', build)
    ok, notes = run(g)
    for n in notes:
        ctx.note(n)
    ctx.expect(ok, '; '.join(notes))
    ctx.screenshot(g, 'lake_old_man')
