"""Shared ability constants/helpers for both the 1v1 matrix (calc.py) and the
6v6 engine (engine.py), so the two tools agree on what's modeled.

Models the high-impact, frequently-cited subset:
  offense   : Huge/Pure Power, Adaptability, Technician, Sheer Force.
  defense   : type-immunity abilities (Levitate/Flash Fire/Water+Volt Absorb/
              Sap Sipper/Lightning Rod/Motor Drive/Dry Skin) and damage-halvers
              (Thick Fat). Applied to the defender in both tools.
  switch-in : Intimidate (-1 foe Atk). 6v6 engine only (1v1 has no switch).
  weather   : Drought/Drizzle/Sand Stream/Snow Warning set weather while their
              owner is active; weather scales Fire/Water damage, boosts Rock
              Sp.Def in sand, doubles Swift Swim/Chlorophyll/Sand/Slush Rush
              speed, and chips non-Rock/Ground/Steel in sand. 6v6 engine only;
              the 1v1 matrix instead gives a weather-setter its own best-case
              boost (weather assumed up).
Still out: Sturdy, Regenerator, Magic Guard/Bounce, trapping, type-changing
(-ate) abilities, Unaware, Speed Boost.
"""

TECHNICIAN_THRESHOLD = 60
ADAPTABILITY_STAB = 2.0
ATK_DOUBLERS = {'HUGE_POWER', 'PURE_POWER'}

# --- defender-side type interactions -----------------------------------------
# type-immunity abilities -> the move type they zero out
TYPE_IMMUNITY = {
    'LEVITATE': 'GROUND',
    'FLASH_FIRE': 'FIRE',
    'WATER_ABSORB': 'WATER', 'DRY_SKIN': 'WATER', 'STORM_DRAIN': 'WATER',
    'VOLT_ABSORB': 'ELECTRIC', 'LIGHTNING_ROD': 'ELECTRIC', 'MOTOR_DRIVE': 'ELECTRIC',
    'SAP_SIPPER': 'GRASS',
}
# damage-halving defensive abilities -> the move types they halve
TYPE_RESIST = {
    'THICK_FAT': {'FIRE', 'ICE'},
    'HEATPROOF': {'FIRE'},
    'WATER_BUBBLE': {'FIRE'},
}

# --- weather -----------------------------------------------------------------
WEATHER_SETTERS = {'DROUGHT': 'sun', 'DRIZZLE': 'rain',
                   'SAND_STREAM': 'sand', 'SNOW_WARNING': 'hail'}
# move-type damage scaling under weather
WEATHER_DMG = {'sun': {'FIRE': 1.5, 'WATER': 0.5},
               'rain': {'WATER': 1.5, 'FIRE': 0.5}}
# speed-doubling abilities by weather
WEATHER_SPEED = {'rain': 'SWIFT_SWIM', 'sun': 'CHLOROPHYLL',
                 'sand': 'SAND_RUSH', 'hail': 'SLUSH_RUSH'}

# Preference order when a mon must commit to one ability for a whole 6v6 battle
# (the 1v1 matrix instead tries all of a mon's offensive abilities per move, and
# always gives the defender its best defensive one). Ordered by how much the
# ability swings a game: archetype-defining weather and matchup-flipping
# immunities first, then offensive multipliers, then the rest.
ABILITY_PRIORITY = [
    'DROUGHT', 'DRIZZLE', 'SAND_STREAM', 'SNOW_WARNING',
    'LEVITATE', 'WATER_ABSORB', 'VOLT_ABSORB', 'FLASH_FIRE', 'SAP_SIPPER',
    'DRY_SKIN', 'LIGHTNING_ROD', 'MOTOR_DRIVE',
    'REGENERATOR', 'STURDY',
    'HUGE_POWER', 'PURE_POWER', 'ADAPTABILITY', 'TOUGH_CLAWS',
    'INTIMIDATE', 'THICK_FAT', 'NATURAL_CURE',
    'TECHNICIAN', 'SHEER_FORCE',
    'SWIFT_SWIM', 'CHLOROPHYLL', 'SAND_RUSH', 'SLUSH_RUSH',
]


def pick_ability(abilities):
    """Pick one ability for a mon to use for an entire 6v6 battle: the most
    battle-swinging modeled ability the species has (see ABILITY_PRIORITY),
    else its first (regular) ability."""
    if not abilities:
        return None
    for pref in ABILITY_PRIORITY:
        if pref in abilities:
            return pref
    return abilities[0]


def defending_type_mult(ability, move_type):
    """Effectiveness multiplier the DEFENDER's `ability` applies to an incoming
    move: 0.0 for a type immunity, 0.5 for a damage-halver (Thick Fat), else
    1.0. One committed ability (the 6v6 case)."""
    if TYPE_IMMUNITY.get(ability) == move_type:
        return 0.0
    if move_type in TYPE_RESIST.get(ability, ()):
        return 0.5
    return 1.0


def best_defending_type_mult(abilities, move_type):
    """1v1 'best case': a defender that could run any of its abilities gets the
    most favorable (lowest) multiplier across them."""
    if not abilities:
        return 1.0
    return min(defending_type_mult(a, move_type) for a in abilities)


def weather_speed_mult(ability, weather):
    """x2 speed if `ability` is the weather's speed-booster, else x1."""
    return 2.0 if weather and WEATHER_SPEED.get(weather) == ability else 1.0


def weather_dmg_mult(weather, move_type):
    """Fire/Water damage scaling under sun/rain (x1 otherwise)."""
    return WEATHER_DMG.get(weather, {}).get(move_type, 1.0)


def own_weather_dmg_mult(ability, move_type):
    """1v1 best-case: a weather-setter's own Fire/Water move gets the weather
    boost (weather assumed always up for the setter)."""
    return weather_dmg_mult(WEATHER_SETTERS.get(ability), move_type)


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
    if ability == 'TOUGH_CLAWS' and move.get('contact'):
        dmg_mult *= 1.3
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
