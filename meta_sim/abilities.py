"""Shared ability constants/helpers for both the 1v1 matrix (calc.py) and the
6v6 engine (engine.py), so the two tools agree on what's modeled.

Multiplier-style abilities only -- no Levitate immunity, Intimidate,
Sturdy, trapping, Regenerator, etc. Those need event hooks (switch-in,
on-faint) the engines don't have yet.
"""

TECHNICIAN_THRESHOLD = 60
ADAPTABILITY_STAB = 2.0
ATK_DOUBLERS = {'HUGE_POWER', 'PURE_POWER'}
WEATHER_OWN_BOOST = {
    'DROUGHT': {'FIRE': 1.5, 'WATER': 0.5},
    'DRIZZLE': {'WATER': 1.5, 'FIRE': 0.5},
}

# Preference order when a mon must commit to one ability for a whole 6v6
# battle (the 1v1 matrix instead tries all of a mon's abilities and keeps
# the best per move). Offensive multiplier abilities first; anything else
# falls back to whichever ability is listed first on the species.
OFFENSE_PRIORITY = ['ADAPTABILITY', 'HUGE_POWER', 'PURE_POWER', 'TECHNICIAN',
                     'SHEER_FORCE', 'DROUGHT', 'DRIZZLE', 'SAND_STREAM']


def pick_ability(abilities):
    """Pick one ability for a mon to use for an entire 6v6 battle: prefer a
    modeled offensive ability if the species has one, else its first
    (regular) ability."""
    if not abilities:
        return None
    for pref in OFFENSE_PRIORITY:
        if pref in abilities:
            return pref
    return abilities[0]


def offense_multipliers(ability, move, is_stab):
    """Return (atk_mult, dmg_mult) for an attacker's `ability` using `move`.
    atk_mult applies to the raw Attack/Sp.Atk stat; dmg_mult applies to the
    final damage number (STAB override is folded into dmg_mult by the
    caller choosing the right STAB constant, this just covers the rest)."""
    atk_mult = 2.0 if (ability in ATK_DOUBLERS and move['cat'] == 'PHYSICAL') else 1.0
    dmg_mult = 1.0
    if ability == 'TECHNICIAN' and move['power'] <= TECHNICIAN_THRESHOLD:
        dmg_mult *= 1.5
    if ability == 'SHEER_FORCE' and move.get('chance', 0) > 0:
        dmg_mult *= 1.3
    boost = WEATHER_OWN_BOOST.get(ability, {}).get(move['type'])
    if boost:
        dmg_mult *= boost
    return atk_mult, dmg_mult


def stab_mult(ability, is_stab):
    if not is_stab:
        return 1.0
    return ADAPTABILITY_STAB if ability == 'ADAPTABILITY' else 1.5


def defending_sand_mult(defender_abilities, defender_types, move):
    """Sp.Def x1.5 for a Rock-type defender whose own Sand Stream keeps
    sand up indefinitely in this static model."""
    if move['cat'] != 'SPECIAL':
        return 1.0
    if 'SAND_STREAM' not in (defender_abilities or []):
        return 1.0
    if 'ROCK' not in defender_types:
        return 1.0
    return 1.5
