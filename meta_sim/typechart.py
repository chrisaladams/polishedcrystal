"""Shared type-effectiveness lookup for both calc.py (1v1) and engine.py (6v6)."""

STAB = 1.5


_CACHE = {}


def type_mult(move_type, def_types, chart):
    # cached: the hottest call in a battle (one chart per run, so the key
    # leaves the chart out; a different chart object clears the cache)
    key = (move_type, def_types[0], def_types[-1] if len(def_types) > 1 else None)
    if _CACHE.get('chart') is not chart:
        _CACHE.clear()
        _CACHE['chart'] = chart
    m = _CACHE.get(key)
    if m is None:
        m = 1.0
        for dt in def_types:
            m *= chart.get(f"{move_type}>{dt}", 1.0)
        _CACHE[key] = m
    return m
