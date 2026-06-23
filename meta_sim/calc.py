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
    def_abilities = defender.get('abilities') or [None]
    # defender's best-case defensive ability: immune (Levitate/Bulletproof/...) -> 0
    if any(ab and abilities.defending_immune(ab, move) for ab in def_abilities):
        return 0
    mt = abilities.effective_type(atk_ability, move)        # -ate / Normalize
    eff = type_mult(mt, defender['types'], chart)
    if abilities.scrappy_hits_ghost(atk_ability) and mt in ('NORMAL', 'FIGHTING') \
            and 'GHOST' in defender['types']:
        eff = type_mult(mt, [t for t in defender['types'] if t != 'GHOST'], chart)
    if any(ab == 'WONDER_GUARD' for ab in def_abilities) and eff <= 1.0:
        return 0
    if eff == 0.0:
        return 0
    # best-case attacker state: own weather up if it's a setter
    weather = abilities.WEATHER_SETTERS.get(atk_ability)
    amult = abilities.attacker_mult(atk_ability, move, mt, weather=weather, eff=eff)
    if move['cat'] == 'PHYSICAL':
        a, d = attacker['stats']['atk'] * amult, defender['stats']['defe']
    else:
        a, d = attacker['stats']['spa'] * amult, defender['stats']['spd']
    base = ((( (2 * LEVEL) // 5 + 2) * move['power'] * a) // d) // 50 + 2
    is_stab = abilities.gives_stab(atk_ability, mt, attacker['types'])
    stab = abilities.stab_value(atk_ability) if is_stab else 1.0
    # defender's best-case damage reduction (Thick Fat/Filter/Multiscale/...)
    dmult = min((abilities.defender_mult(ab, move, mt, eff, 1.0) for ab in def_abilities), default=1.0)
    dmg = base * stab * eff * dmult * abilities.weather_dmg_mult(weather, mt) * ROLL
    return int(dmg)

def best_move(attacker, defender, moves, learnset, chart):
    """Pick attacker's highest-average-damage legal move vs defender, trying
    each of the attacker's abilities (best case, matching the uniform max-build
    philosophy); the defender gets its best-case defensive ability per move.
    Returns (move_name, damage, type_effectiveness) or (None, 0, 0)."""
    best = (None, 0, 0.0)
    atk_abilities = attacker.get('abilities') or [None]
    for mv in learnset:
        m = moves[mv]
        for ab in set(atk_abilities):
            dmg = damage(attacker, defender, m, chart, atk_ability=ab)
            if dmg > best[1]:
                best = (mv, dmg, type_mult(m['type'], defender['types'], chart))
    return best

def hits_to_ko(dmg, hp):
    """Number of hits of `dmg` to drop `hp`. inf if no damage."""
    if dmg <= 0:
        return float('inf')
    return -(-hp // dmg)  # ceil
