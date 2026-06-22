"""Damage calculation and 1v1 best-move selection.

Standard Gen damage formula (physical/special split is per-move in this ROM):
    base = floor(floor(floor(2*L/5 + 2) * Power * A / D) / 50) + 2
    dmg  = base * STAB * type_effectiveness
STAB = 1.5; type effectiveness = product over the defender's types from the chart.
Crits off, items off, damage roll = 0.925 (the average of the 0.85-1.00 spread,
applied as a flat factor).

ABILITY MODELING (multiplier-style only, no abilities-beyond-damage like
Levitate immunity or Intimidate): each attacker is evaluated under all of its
own abilities (regular x2 + hidden) and the best move+ability combo wins,
mirroring the existing "every mon at a max build" philosophy elsewhere in this
tool. Modeled abilities:
  Huge Power / Pure Power   atk x2 on physical moves
  Adaptability               STAB 2.0 instead of 1.5
  Technician                 x1.5 on moves with power <= 60
  Sheer Force                x1.3 on moves with a secondary-effect chance > 0
  Drought / Drizzle          x1.5 own Fire/Water moves, x0.5 the opposing type
On the defending side, only Sand Stream's self-sand Rock-type Sp.Def boost
(x1.5 vs special moves) is modeled, since it's a named, frequently-cited case
(Tyranitar) and doesn't require choosing among abilities.
Not modeled: Guts/Quick Feet (need status), type-changing abilities
(Aerilate/Pixilate/Refrigerate), held items, weather chip damage over time.
This is still a first-order signal for raw stat/typing/movepool/ability
tuning, NOT a full battle: it ignores switching, status over time, hazards,
and most item effects. Documented in meta_sim/matrix.py output.
"""
from stats import LEVEL
import abilities

STAB = 1.5
ROLL = 0.925  # average damage roll

def type_mult(move_type, def_types, chart):
    m = 1.0
    for dt in def_types:
        m *= chart.get(f"{move_type}>{dt}", 1.0)
    return m

def damage(attacker, defender, move, chart, atk_ability=None):
    """Return average damage (int) move does from attacker to defender.
    attacker/defender: dicts with 'stats' (L50) and 'types'. move: moves.json
    entry. atk_ability: one ability name to apply for this calculation (the
    caller tries each of the attacker's abilities and keeps the best result).
    Returns 0 for status moves or zero-power / immune moves."""
    if move['cat'] == 'STATUS' or move['power'] <= 0:
        return 0
    eff = type_mult(move['type'], defender['types'], chart)
    if eff == 0.0:
        return 0
    is_stab = move['type'] in attacker['types']
    atk_mult, dmg_mult = abilities.offense_multipliers(atk_ability, move, is_stab)
    if move['cat'] == 'PHYSICAL':
        a, d = attacker['stats']['atk'] * atk_mult, defender['stats']['defe']
    else:
        a, d = attacker['stats']['spa'] * atk_mult, defender['stats']['spd']
    base = ((( (2 * LEVEL) // 5 + 2) * move['power'] * a) // d) // 50 + 2
    stab = abilities.stab_mult(atk_ability, is_stab)
    dmg = base * stab * eff * dmg_mult * ROLL
    return int(dmg)

def best_move(attacker, defender, moves, learnset, chart):
    """Pick attacker's highest-average-damage legal move vs defender, trying
    each of the attacker's abilities (best case, matching the uniform max-
    build philosophy) and applying the defender's own Sand Stream Sp.Def
    boost if applicable.
    Returns (move_name, damage, type_effectiveness) or (None, 0, 0)."""
    best = (None, 0, 0.0)
    atk_abilities = attacker.get('abilities') or [None]
    for mv in learnset:
        m = moves[mv]
        sand = abilities.defending_sand_mult(defender.get('abilities'), defender['types'], m)
        for ab in set(atk_abilities):
            dmg = damage(attacker, defender, m, chart, atk_ability=ab)
            if sand != 1.0:
                dmg = int(dmg / sand)
            if dmg > best[1]:
                best = (mv, dmg, type_mult(m['type'], defender['types'], chart))
    return best

def hits_to_ko(dmg, hp):
    """Number of hits of `dmg` to drop `hp`. inf if no damage."""
    if dmg <= 0:
        return float('inf')
    return -(-hp // dmg)  # ceil
