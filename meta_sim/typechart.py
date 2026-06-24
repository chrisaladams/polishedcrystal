"""Shared type-effectiveness lookup for both calc.py (1v1) and engine.py (6v6)."""

STAB = 1.5


def type_mult(move_type, def_types, chart):
    m = 1.0
    for dt in def_types:
        m *= chart.get(f"{move_type}>{dt}", 1.0)
    return m
