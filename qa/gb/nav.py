"""Game-aware navigation with real controller input.

Reads the running game (map, position, collision, object positions) from RAM using the
.sym file, plans with BFS over tiles and over the world graph (qa/gb/world.py), and
walks by pressing buttons. Nothing here moves the player by writing memory: it is
gameplay input. Every press is logged so a run can be replayed exactly.

Interruptions are handled the way a player would: dialogue is advanced, battles are
played by a simple policy, and a script that never returns control is reported as a
softlock instead of hanging.
"""
from collections import deque

from . import collision, mapdata, world
from .consts import C, values

DIRS = {'up': (0, -1), 'down': (0, 1), 'left': (-1, 0), 'right': (1, 0)}
OPP = {'up': 'down', 'down': 'up', 'left': 'right', 'right': 'left'}
FACING = {'up': 0x0c, 'down': 0x00, 'left': 0x04, 'right': 0x08}   # OBJECT_FACING values

_ids = {}


def map_const_of(group, number):
    """(group, number) -> map constant name."""
    if not _ids:
        names = []
        for c in mapdata.attributes():
            names += ['GROUP_' + c, 'MAP_' + c]
        v = values(names)
        for c in mapdata.attributes():
            if 'GROUP_' + c in v:
                _ids[(v['GROUP_' + c], v['MAP_' + c])] = c
    return _ids.get((group, number))


class Softlock(Exception):
    """The game stopped giving control back (or stopped running)."""


class Stuck(Exception):
    """Navigation could not make progress."""


class Navigator:
    def __init__(self, g, battle=None, seed=1):
        import random
        self.g = g
        self.log = []                 # (frame, button, frames): the replayable input record
        self.rng = random.Random(seed)
        self.battle_policy = battle   # callable(nav) used when a battle starts; default: autoplay
        self.blocked_edges = set()
        self.events = []              # notable things that happened, in order
        self.battles = 0
        self.steps = 0
        self.stats = {'dialogues': 0, 'battles': 0, 'blackouts': 0, 'softlocks': 0}

    # ---- input
    def press(self, button, hold=4, wait=6):
        self.log.append((self.g.frame, button, hold))
        self.g.press(button, hold, wait)

    def hold(self, button, frames):
        self.log.append((self.g.frame, button, frames))
        self.g.hold(button, frames)

    # ---- reading the game
    def pos(self):
        g = self.g
        return (g.rd('wMapGroup'), g.rd('wMapNumber'), g.rd('wXCoord'), g.rd('wYCoord'))

    def here(self):
        gr, nr, x, y = self.pos()
        return map_const_of(gr, nr), (x, y)

    def ready(self):
        """The player is walking around: no script, text, menu or battle."""
        g = self.g
        return (g.rd('wScriptMode') == 0 and g.rd('wScriptRunning') == 0 and g.read(0xff9c) == 0
                and not g.in_battle() and g.rd('wMapStatus') == 2)

    def objects(self):
        """Tiles occupied by non-player objects: {(x, y): sprite}."""
        g = self.g
        base = g.sym['wPlayerStruct'][1]
        stride = g.sym['wObject1Struct'][1] - base
        out = {}
        follower = C['FOLLOWER_OBJECT']
        for i in range(1, C['NUM_OBJECT_STRUCTS']):
            a = base + i * stride
            sprite = g.read(a, 1)
            if not sprite or g.read(a + 1, 1) == follower:
                continue
            mx, my = g.read(a + 16, 1), g.read(a + 17, 1)
            if mx < 4 or my < 4:
                continue
            out[(mx - 4, my - 4)] = sprite
        return out

    # ---- interruptions
    def screen_hash(self):
        import zlib
        return zlib.crc32(self.g.dump(self.g.sym['wTilemap'][1], 360))

    def settle(self, max_frames=9000, answer='a'):
        """Hand control back: advance dialogue, play battles, until the player can walk.

        Presses `answer` (A, like a player) and watches the screen. If the screen stops
        changing it tries B, then each direction with A (menus, prompts, name entry), and
        only after max_frames reports a softlock."""
        g = self.g
        start = g.frame
        last, same = None, 0
        order = [answer, 'b', 'down', 'a', 'up', 'a', 'start']
        k = 0
        while not self.ready():
            if g.frame - start > max_frames:
                self.stats['softlocks'] += 1
                shot = g.screenshot('softlock_%d' % g.frame)
                raise Softlock('[%s] ' % shot + 'no control after %d frames at %s (script mode %d, running %d, battle %d)' % (
                    max_frames, self.here(), g.rd('wScriptMode'), g.rd('wScriptRunning'), g.rd('wBattleMode')))
            if g.in_battle():
                self.play_battle()
                last, same = None, 0
                continue
            h = self.screen_hash()
            same = same + 1 if h == last else 0
            last = h
            key = answer
            if same >= 6:                 # nothing changing: try something else, once
                k += 1
                same = 0
                key = order[k % len(order)]
            self.press(key, 4, 16)
            self.stats['dialogues'] += 1
        g.tick(4)

    def play_battle(self, max_frames=36000):
        from .autobattle import play
        self.stats['battles'] += 1
        play(self, max_frames)

    # ---- movement
    def step(self, direction):
        """One tile in `direction`. Returns 'moved', 'turned', 'map' (map changed) or 'blocked'."""
        before = self.pos()
        after = before
        for attempt in range(2):        # the first press toward a new direction only turns the player
            self.hold(direction, 16)
            self.g.tick(2)
            if not self.ready():
                self.settle()
            after = self.pos()
            if after != before:
                break
        self.steps += 1
        if after[:2] != before[:2]:
            return 'map'
        if after[2:] != before[2:]:
            return 'moved'
        return 'blocked'

    def passable(self, x, y, warp_tiles, goal):
        c = collision.tile_collision(self.g, x, y)
        if c is None:
            return False
        if (x, y) == goal:
            return True
        if (x, y) in warp_tiles:
            return False
        return c in collision.PASSABLE

    def bfs(self, goals, extra_blocked=()):
        """Shortest list of directions from the player to any tile in goals, or None.
        Objects are walls at first; if that leaves no path they are treated as passable
        (they move: wandering NPCs and visible wild Pokemon) and the walk waits for them."""
        path = self._bfs(goals, extra_blocked, True)
        if path is None:
            path = self._bfs(goals, extra_blocked, False)
        return path

    def _bfs(self, goals, extra_blocked, objects_block):
        g = self.g
        _, (sx, sy) = self.here()
        const = self.here()[0]
        warp_tiles = {(w[0], w[1]) for w in world.warps(const)} if const else set()
        blocked = (set(self.objects()) if objects_block else set()) | set(extra_blocked)
        goals = set(goals)
        prev, q = {(sx, sy): None}, deque([(sx, sy)])
        while q:
            cur = q.popleft()
            if cur in goals:
                path = []
                while prev[cur]:
                    cur, d = prev[cur]
                    path.append(d)
                return path[::-1]
            for d, (dx, dy) in DIRS.items():
                n = (cur[0] + dx, cur[1] + dy)
                if n in prev or n in blocked and n not in goals:
                    continue
                if not self.passable(n[0], n[1], warp_tiles, n if n in goals else None):
                    continue
                prev[n] = (cur, d)
                q.append(n)
        return None

    def walk_path(self, path):
        """Follow a list of directions, re-checking each step. Returns False if it was
        interrupted by a map change (the caller decides what that means)."""
        for d in path:
            r = self.step(d)
            if r == 'map':
                return False
            if r == 'blocked':
                # an NPC moved into the way, or the tile was not what we thought: let the caller replan
                self.g.tick(20)
                return None
        return True

    def goto_tile(self, goals, max_replans=40):
        """Walk to the nearest of the goal tiles (in the current map)."""
        start_map = self.here()[0]
        for _ in range(max_replans):
            if not self.ready():
                self.settle()
            if self.here()[1] in set(goals) and self.here()[0] == start_map:
                return True
            path = self.bfs(goals)
            if path is None:
                return False
            r = self.walk_path(path)
            if r is False:
                return False
            if r is True:
                return self.here()[1] in set(goals) or self.here()[0] != start_map
        return False

    def face(self, direction):
        """Turn to face a direction without moving (press toward a blocked tile)."""
        self.hold(direction, 4)
        self.g.tick(8)

    # ---- the world graph
    def take_edge(self, edge):
        """Walk across one world-graph edge from the current map. Returns the new map const or None."""
        kind = edge[0]
        const, _ = self.here()
        g = self.g
        self.why = []
        if kind == 'warp':
            (wx, wy) = edge[1]
            cand = []
            for d, (dx, dy) in DIRS.items():
                n = (wx - dx, wy - dy)                  # the tile we step from, moving in direction d
                cand.append((n, d))
            for n, d in cand:
                if not self.goto_tile({n}):
                    if self.here()[0] != const:
                        return self.here()[0]
                    self.why.append(f'no path to {n} (collision {collision.tile_collision(g, *n)})')
                    continue
                if self.here()[0] != const:
                    return self.here()[0]
                if self.here()[1] != n:
                    self.why.append(f'stopped at {self.here()[1]} not {n}')
                    continue
                for _ in range(3):          # carpets and stairs fire on a further step in the same direction
                    r = self.step(d)
                    if self.here()[0] != const:
                        return self.here()[0]
                self.why.append(f'stepped {d} from {n}: {r}, still at {self.here()[1]}')
            return None
        # connection: stand on an edge tile that is walkable on both sides and walk out
        direction, dst, offset = edge[1], edge[2], edge[3]
        w, h = g.rd('wMapWidth') * 2, g.rd('wMapHeight') * 2
        wd, hd = (2 * v for v in mapdata.dims(dst))
        tiles = []
        if direction in ('north', 'south'):
            for x in range(w):
                if 0 <= x - 2 * offset < wd:
                    e, i = (0, 1) if direction == 'north' else (h - 1, h - 2)
                    if collision.walkable(g, x, e, edge=True) and collision.walkable(g, x, i):
                        tiles.append(((x, i), (x, e)))
        else:
            for y in range(h):
                if 0 <= y - 2 * offset < hd:
                    e, i = (0, 1) if direction == 'west' else (w - 1, w - 2)
                    if collision.walkable(g, e, y, edge=True) and collision.walkable(g, i, y):
                        tiles.append(((i, y), (e, y)))
        d = {'north': 'up', 'south': 'down', 'west': 'left', 'east': 'right'}[direction]
        _, (px, py) = self.here()
        tiles.sort(key=lambda t: abs(t[0][0] - px) + abs(t[0][1] - py))
        for inner, edge_tile in tiles[:6]:
            if not self.goto_tile({inner}):
                if self.here()[0] != const:
                    return self.here()[0]
                continue
            for _ in range(4):
                self.step(d)
                if self.here()[0] != const:
                    return self.here()[0]
        return None

    def goto_map(self, dst, max_hops=80):
        """Walk to map `dst` along the world graph, learning which edges fail."""
        for _ in range(max_hops):
            const, _p = self.here()
            if const == dst:
                return True
            r = world.route(const, dst, self.blocked_edges)
            if not r:
                raise Stuck('no route from %s to %s (blocked: %d edges)' % (const, dst, len(self.blocked_edges)))
            m, i, e = r[0]
            got = self.take_edge(e)
            if got is None:
                self.blocked_edges.add((m, i))
                shot = self.g.screenshot('blocked_%s_%d' % (m, i))
                self.g.dump_state(shot[:-4] + '.state')
                self.events.append(('blocked-edge', m, e[:3], list(self.why)[:4], shot))
        raise Stuck('too many hops going to ' + dst)
