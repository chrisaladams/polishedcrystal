"""Damage calculation and 1v1 best-move selection.

Standard Gen damage formula (physical/special split is per-move in this ROM):
    base = floor(floor(floor(2*L/5 + 2) * Power * A / D) / 50) + 2
    dmg  = base * STAB * type_effectiveness
STAB = 1.5; type effectiveness = product over the defender's types from the chart.
Crits off, weather/items/abilities-beyond-multipliers off, damage roll = 0.925
(the average of the 0.85-1.00 spread, applied as a flat factor).

This is a first-order signal for raw stat/typing/movepool tuning, NOT a full
battle: it ignores switching, status over time, hazards, and most item/ability
effects. Documented in meta_sim/matrix.py output.
"""
from stats import LEVEL

STAB = 1.5
ROLL = 0.925  # average damage roll

def type_mult(move_type, def_types, chart):
    m = 1.0
    for dt in def_types:
        m *= chart.get(f"{move_type}>{dt}", 1.0)
    return m

def damage(attacker, defender, move, chart):
    """Return average damage (int) move does from attacker to defender.
    attacker/defender: dicts with 'stats' (L50) and 'types'. move: moves.json entry.
    Returns 0 for status moves or zero-power / immune moves."""
    if move['cat'] == 'STATUS' or move['power'] <= 0:
        return 0
    eff = type_mult(move['type'], defender['types'], chart)
    if eff == 0.0:
        return 0
    if move['cat'] == 'PHYSICAL':
        a, d = attacker['stats']['atk'], defender['stats']['defe']
    else:
        a, d = attacker['stats']['spa'], defender['stats']['spd']
    base = ((( (2 * LEVEL) // 5 + 2) * move['power'] * a) // d) // 50 + 2
    stab = STAB if move['type'] in attacker['types'] else 1.0
    return int(base * stab * eff * ROLL)

def best_move(attacker, defender, moves, learnset, chart):
    """Pick attacker's highest-average-damage legal move vs defender.
    Returns (move_name, damage, type_effectiveness) or (None, 0, 0)."""
    best = (None, 0, 0.0)
    for mv in learnset:
        m = moves[mv]
        dmg = damage(attacker, defender, m, chart)
        if dmg > best[1]:
            best = (mv, dmg, type_mult(m['type'], defender['types'], chart))
    return best

def hits_to_ko(dmg, hp):
    """Number of hits of `dmg` to drop `hp`. inf if no damage."""
    if dmg <= 0:
        return float('inf')
    return -(-hp // dmg)  # ceil
