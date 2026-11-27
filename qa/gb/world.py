"""The world as a graph: maps are nodes; warps and map connections are edges.

Built from the repository's own map data (maps/*.asm, data/maps/attributes.asm), so it
follows the game as it changes. Edges whose use needs an HM, an item or a story flag are
not known statically: the navigator marks an edge blocked when walking it fails and routes
around it."""
from collections import deque

from . import mapdata

_cache = {}
LAST_MAP = 'LAST_MAP'


def _consts():
    if 'consts' not in _cache:
        attrs = mapdata.attributes()
        _cache['consts'] = attrs
        _cache['by_label'] = {m['label']: c for c, m in attrs.items()}
    return _cache['consts']


def warps(const):
    """[(x, y, dest_const, dest_index_1based)] for the map."""
    key = ('warps', const)
    if key not in _cache:
        attrs = _consts()
        _cache[key] = mapdata.parse_map(attrs[const]['label'])['warps'] if const in attrs else []
    return _cache[key]


def warp_arrival(dest, idx):
    """(x, y) where a warp to `dest`'s warp number idx puts the player, or None."""
    if dest == LAST_MAP or dest not in _consts():
        return None
    w = warps(dest)
    return (w[idx - 1][0], w[idx - 1][1]) if 0 < idx <= len(w) else None


def edges(const):
    """Outgoing edges of a map: ('warp', (x, y), dest, arrival) and ('conn', direction, dest, offset)."""
    out = []
    for x, y, dest, idx in warps(const):
        if dest in _consts():
            out.append(('warp', (x, y), dest, warp_arrival(dest, idx)))
    for d, _, c, off in _consts()[const]['connections']:
        if c not in _consts():
            continue                      # placeholder maps (FAKE_ROUTE_36) have no constants
        out.append(('conn', d, c, off))
    return out


def incoming(const):
    """[(source map, edge)] for every warp or connection that leads into `const`."""
    if 'incoming' not in _cache:
        table = {}
        for src in _consts():
            for e in edges(src):
                table.setdefault(e[2], []).append((src, e))
        _cache['incoming'] = table
    return _cache['incoming'].get(const, [])


def route(src, dst, blocked=frozenset()):
    """Shortest list of edges from map src to map dst, avoiding blocked (src, edge-index)."""
    if src == dst:
        return []
    prev, q = {src: None}, deque([src])
    while q:
        m = q.popleft()
        for i, e in enumerate(edges(m)):
            if (m, i) in blocked or e[2] in prev:
                continue
            prev[e[2]] = (m, i, e)
            if e[2] == dst:
                path, cur = [], dst
                while prev[cur]:
                    pm, pi, pe = prev[cur]
                    path.append((pm, pi, pe))
                    cur = pm
                return path[::-1]
            q.append(e[2])
    return None


def reachable(src, blocked=frozenset()):
    seen, q = {src}, deque([src])
    while q:
        m = q.popleft()
        for i, e in enumerate(edges(m)):
            if (m, i) in blocked or e[2] in seen:
                continue
            seen.add(e[2])
            q.append(e[2])
    return seen


def script_warps(const):
    """Destinations reached by `warp`/`warpfacing` script commands in the map's own scripts
    (cutscenes, ferries, story warps). Which state triggers them is not known statically."""
    import re
    key = ('swarps', const)
    if key not in _cache:
        attrs = _consts()
        out = []
        path = mapdata.map_file(attrs[const]['label']) if const in attrs else None
        if path:
            for line in open(path, encoding='utf-8'):
                m = re.match(r'\s+warp(?:facing)?\s+(?:\w+,\s*)?([A-Z][A-Z0-9_]+),\s*(-?\d+),\s*(-?\d+)', line)
                if m and m.group(1) in attrs:
                    out.append((m.group(1), int(m.group(2)), int(m.group(3))))
        _cache[key] = out
    return _cache[key]


def reachable_with_scripts(src, blocked=frozenset()):
    """Maps reachable by walking edges or by any script warp (an over-approximation)."""
    seen, q = {src}, deque([src])
    while q:
        m = q.popleft()
        nxt = [e[2] for i, e in enumerate(edges(m)) if (m, i) not in blocked] + [d for d, _, _ in script_warps(m)]
        for n in nxt:
            if n not in seen:
                seen.add(n)
                q.append(n)
    return seen
