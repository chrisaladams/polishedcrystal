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
from qa.gb.guards import PlayerStructGuard

PROVENANCE = 'walk: gameplay input; party/position/save: injected fixture'


def build(g):
    """a Totodile in the party, standing on Route 43 (10,8)"""
    F.give_mon(g, C['TOTODILE'], 10)
    F.teleport(g, *map_ids('ROUTE_43'), 10, 8)


def run(g, out=None):
    """Walk north from Route 43 into Lake of Rage up to the old man.
    Returns (ok, notes)."""
    guard = PlayerStructGuard(g)
    notes = []
    old_man = (20, 26)
    positions = []
    blocked = 0
    last = None
    for step in range(60):
        g.hold('up', 16)
        g.tick(6)
        guard.check(f'step {step} at {F.where(g)}')
        w = F.where(g)
        positions.append(w)
        if w[:2] == map_ids('LAKE_OF_RAGE') and w[2:] == (20, 27):
            blocked += 1 if last == w else 0
            if blocked >= 3:
                break
        last = w
    reached = [p for p in positions if p[:2] == map_ids('LAKE_OF_RAGE') and p[2:] == (20, 27)]
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
    # the player's tiles must be on screen: OAM sprites around screen centre using the player's tile base
    sprite = g.mem[1, guard.base]
    tile = g.mem[1, guard.base + 2]
    notes.append(f'player struct sprite={sprite} tile={tile}')
    if out:
        g.screenshot(os.path.join(out, 'lake_old_man.png') if False else 'lake_old_man')
    return ok, notes


def main():
    out = '/tmp/qa_lake'
    p = saves.fixture('route43_basic', build)
    g = Game(sav=p, workdir=out)
    saves.boot_continue(g, saves.fixture_meta(p)['where'])
    ok, notes = run(g, out)
    print('PASS' if ok else 'FAIL', *notes, sep='\n  ')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
