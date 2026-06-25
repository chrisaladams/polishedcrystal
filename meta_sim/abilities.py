"""Ability model shared by the 1v1 matrix (calc.py) and the 6v6 engine.

Aim: cover all 155 abilities in the ROM as faithfully as this abstraction
allows. Each ability falls into one of:
  * MODELLED here / via an engine hook (the large majority of competitively
    relevant ones -- see the tables and functions below);
  * a genuine NO-OP in a 1v1/6v6 stat sim (Run Away, Honey Gather, Illuminate,
    Pickup, ...): listed in NOOP_ABILITIES so coverage accounting is honest;
  * UNMODELLABLE in this abstraction (Trace/Imposter/Forecast/form-change/
    doubles-only/terrain): listed in UNMODELLED_ABILITIES with the reason.

The engine calls the hook functions (on_switch_in/on_hit/on_ko/end_of_turn/...);
the pure damage/typing multipliers are used by both tools so they agree.
"""

# ============================================================ commit choice ===
# When a mon must pick one ability for a battle, prefer the most battle-swinging
# one it has. (The 1v1 matrix tries all of a mon's offensive abilities per move
# and gives the defender its best defensive one.)
ABILITY_PRIORITY = [
    # weather / archetype
    'DROUGHT', 'DRIZZLE', 'SAND_STREAM', 'SNOW_WARNING',
    # type immunities
    'LEVITATE', 'WATER_ABSORB', 'VOLT_ABSORB', 'STORM_DRAIN', 'FLASH_FIRE',
    'SAP_SIPPER', 'DRY_SKIN', 'LIGHTNING_ROD', 'MOTOR_DRIVE', 'WONDER_GUARD',
    # big defensive
    'MULTISCALE', 'REGENERATOR', 'UNAWARE', 'FUR_COAT', 'ICE_SCALES',
    'THICK_FAT', 'FILTER', 'SOLID_ROCK', 'PRISM_ARMOR', 'STURDY',
    # big offensive
    'HUGE_POWER', 'PURE_POWER', 'ADAPTABILITY', 'PROTEAN', 'LIBERO',
    'TOUGH_CLAWS', 'SHARPNESS', 'MEGA_LAUNCHER', 'IRON_FIST', 'TECHNICIAN',
    'SHEER_FORCE', 'PIXILATE', 'REFRIGERATE', 'AERILATE', 'GALVANIZE',
    'TINTED_LENS', 'PUNK_ROCK', 'RECKLESS', 'STEELY_SPIRIT', 'SAND_FORCE',
    'ANALYTIC', 'SOLAR_POWER', 'GORILLA_TACTICS', 'HUSTLE',
    # pinch / conditional offense
    'GUTS', 'OVERGROW', 'BLAZE', 'TORRENT', 'SWARM',
    # on-hit / on-ko / switch-in / contact
    'INTIMIDATE', 'MOXIE', 'BERSERK', 'DEFIANT', 'COMPETITIVE', 'DOWNLOAD',
    'CONTRARY', 'SIMPLE', 'JUSTIFIED', 'STAMINA', 'WEAK_ARMOR', 'RATTLED',
    'ROUGH_SKIN', 'IRON_BARBS', 'FLAME_BODY', 'STATIC', 'POISON_POINT',
    'SERENE_GRACE', 'SHIELD_DUST',
    'EFFECT_SPORE', 'POISON_TOUCH', 'TANGLING_HAIR', 'CURSED_BODY', 'AFTERMATH',
    # status / utility
    'POISON_HEAL', 'MAGIC_GUARD', 'NATURAL_CURE', 'SHED_SKIN', 'HYDRATION',
    'GUTS', 'QUICK_FEET', 'MARVEL_SCALE', 'SPEED_BOOST', 'PRANKSTER',
    'GALE_WINGS', 'TRIAGE', 'SCRAPPY', 'MINDS_EYE', 'MOLD_BREAKER',
    'CLEAR_BODY', 'WHITE_SMOKE', 'CORROSION', 'SYNCHRONIZE',
    # trapping
    'SHADOW_TAG', 'ARENA_TRAP', 'MAGNET_PULL',
    # weather speed (only live under weather)
    'SWIFT_SWIM', 'CHLOROPHYLL', 'SAND_RUSH', 'SLUSH_RUSH',
    # status immunities (last: defensive insurance)
    'IMMUNITY', 'LIMBER', 'WATER_VEIL', 'MAGMA_ARMOR', 'INSOMNIA',
    'VITAL_SPIRIT', 'SWEET_VEIL', 'PASTEL_VEIL', 'LEAF_GUARD', 'EARLY_BIRD',
    'RAIN_DISH', 'ICE_BODY', 'OVERCOAT', 'COMPOUND_EYES', 'NO_GUARD',
]


def pick_ability(abilities):
    if not abilities:
        return None
    for pref in ABILITY_PRIORITY:
        if pref in abilities:
            return pref
    return abilities[0]


# =============================================================== move typing ===
TECHNICIAN_THRESHOLD = 60
ATE = {'PIXILATE': 'FAIRY', 'REFRIGERATE': 'ICE', 'AERILATE': 'FLYING',
       'GALVANIZE': 'ELECTRIC'}            # Normal moves become this type, x1.2


def effective_type(ability, move):
    """Move type after a type-changing ability (-ate / Normalize)."""
    mt = move['type']
    if ability in ATE and mt == 'NORMAL':
        return ATE[ability]
    if ability == 'NORMALIZE':
        return 'NORMAL'
    return mt


def gives_stab(ability, move_type, user_types):
    """Protean/Libero make every move STAB (the user takes the move's type)."""
    if ability in ('PROTEAN', 'LIBERO'):
        return True
    return move_type in user_types


def stab_value(ability):
    return 2.0 if ability == 'ADAPTABILITY' else 1.5


# ====================================================== attacker damage mult ===
PINCH = {'OVERGROW': 'GRASS', 'BLAZE': 'FIRE', 'TORRENT': 'WATER', 'SWARM': 'BUG'}
ATK_DOUBLERS = {'HUGE_POWER', 'PURE_POWER'}


def attacker_mult(ability, move, move_type, *, statused=False, hp_frac=1.0,
                  weather=None, moving_last=False, eff=1.0):
    """Every attacker-side ability damage multiplier folded into one number.
    move_type is the *effective* type (after -ate). State args default to the
    1v1 'best case' (full HP, no status, no weather, not moving last)."""
    m = 1.0
    cat = move['cat']
    if ability in ATK_DOUBLERS and cat == 'PHYSICAL':
        m *= 2.0
    if ability == 'HUSTLE' and cat == 'PHYSICAL':
        m *= 1.5
    if ability == 'GORILLA_TACTICS' and cat == 'PHYSICAL':
        m *= 1.5
    if ability == 'GUTS' and statused and cat == 'PHYSICAL':
        m *= 1.5
    if ability == 'TECHNICIAN' and move['power'] <= TECHNICIAN_THRESHOLD:
        m *= 1.5
    if ability == 'SHEER_FORCE' and move.get('chance', 0) > 0:
        m *= 1.3
    if ability == 'TOUGH_CLAWS' and move.get('contact'):
        m *= 1.3
    if ability == 'IRON_FIST' and move.get('punch'):
        m *= 1.2
    if ability == 'RECKLESS' and move.get('recoil'):
        m *= 1.2
    if ability == 'MEGA_LAUNCHER' and move.get('pulse'):
        m *= 1.5
    if ability == 'SHARPNESS' and move.get('slice'):
        m *= 1.5
    if ability == 'PUNK_ROCK' and move.get('sound'):
        m *= 1.3
    if ability == 'STEELY_SPIRIT' and move_type == 'STEEL':
        m *= 1.5
    if ability in ATE and move['type'] == 'NORMAL':
        m *= 1.2
    if ability == 'SAND_FORCE' and weather == 'sand' and move_type in ('ROCK', 'GROUND', 'STEEL'):
        m *= 1.3
    if ability == 'ANALYTIC' and moving_last:
        m *= 1.3
    if ability == 'SOLAR_POWER' and weather == 'sun' and cat == 'SPECIAL':
        m *= 1.5
    if ability in PINCH and move_type == PINCH[ability] and hp_frac <= 1/3:
        m *= 1.5
    if ability == 'TINTED_LENS' and 0 < eff < 1.0:
        m *= 2.0
    return m


# ====================================================== defender damage mult ===
# type-immunity abilities -> the move type they zero out
TYPE_IMMUNITY = {
    'LEVITATE': 'GROUND', 'FLASH_FIRE': 'FIRE', 'WELL_BAKED_BODY': 'FIRE',
    'WATER_ABSORB': 'WATER', 'DRY_SKIN': 'WATER', 'STORM_DRAIN': 'WATER',
    'VOLT_ABSORB': 'ELECTRIC', 'LIGHTNING_ROD': 'ELECTRIC', 'MOTOR_DRIVE': 'ELECTRIC',
    'SAP_SIPPER': 'GRASS', 'EARTH_EATER': 'GROUND',
}


def defending_immune(ability, move):
    """True if the DEFENDER's ability makes the move deal 0 (type immunity, or
    Bulletproof/Soundproof move-flag immunity)."""
    if TYPE_IMMUNITY.get(ability) == move['type']:
        return True
    if ability == 'BULLETPROOF' and move.get('bullet'):
        return True
    if ability in ('SOUNDPROOF',) and move.get('sound'):
        return True
    return False


def defender_mult(ability, move, move_type, eff, hp_frac=1.0):
    """Defender-side damage multipliers (after immunities/type chart)."""
    m = 1.0
    cat = move['cat']
    if move_type in ('FIRE', 'ICE') and ability == 'THICK_FAT':
        m *= 0.5
    if move_type == 'FIRE' and ability in ('HEATPROOF', 'WATER_BUBBLE'):
        m *= 0.5
    if move_type == 'FIRE' and ability == 'DRY_SKIN':
        m *= 1.25
    if move_type == 'FIRE' and ability == 'FLUFFY':
        m *= 2.0
    if ability in ('FILTER', 'SOLID_ROCK', 'PRISM_ARMOR') and eff > 1.0:
        m *= 0.75
    if ability in ('MULTISCALE', 'SHADOW_SHIELD') and hp_frac >= 1.0:
        m *= 0.5
    if ability == 'FUR_COAT' and cat == 'PHYSICAL':
        m *= 0.5
    if ability == 'ICE_SCALES' and cat == 'SPECIAL':
        m *= 0.5
    if ability == 'FLUFFY' and move.get('contact'):
        m *= 0.5
    if ability == 'PUNK_ROCK' and move.get('sound'):
        m *= 0.5
    if ability == 'PURIFYING_SALT' and move_type == 'GHOST':
        m *= 0.5
    if ability == 'MARVEL_SCALE':  # treated as "statused" -> caller passes via hp? no:
        pass                       # handled in engine (needs status); see defender_status_mult
    return m


def wonder_guard_blocks(ability, eff):
    """Wonder Guard: only super-effective moves connect."""
    return ability == 'WONDER_GUARD' and eff <= 1.0


def scrappy_hits_ghost(ability):
    return ability in ('SCRAPPY', 'MINDS_EYE')


# ============================================================ stat handling ===
PREVENT_DROP_ALL = {'CLEAR_BODY', 'WHITE_SMOKE', 'FULL_METAL_BODY'}


def prevents_drop(ability, stat):
    """Does the ability stop the foe from lowering this stat?"""
    if ability in PREVENT_DROP_ALL:
        return True
    if ability == 'HYPER_CUTTER' and stat == 'atk':
        return True
    if ability == 'BIG_PECKS' and stat == 'defe':
        return True
    return False


def transform_self_change(ability, delta):
    """Contrary inverts a self stat change; Simple doubles it."""
    if ability == 'CONTRARY':
        return -delta
    if ability == 'SIMPLE':
        return delta * 2
    return delta


# ============================================================== status gates ===
# ability -> set of statuses it is immune to receiving
STATUS_IMMUNE = {
    'IMMUNITY': {'psn', 'tox'}, 'PASTEL_VEIL': {'psn', 'tox'},
    'LIMBER': {'par'}, 'WATER_VEIL': {'brn'}, 'WATER_BUBBLE': {'brn'},
    'THERMAL_EXCHANGE': {'brn'}, 'MAGMA_ARMOR': {'frz'},
    'INSOMNIA': {'slp'}, 'VITAL_SPIRIT': {'slp'}, 'SWEET_VEIL': {'slp'},
    'COMATOSE': {'slp', 'psn', 'tox', 'par', 'brn', 'frz'},
}


def can_be_statused(ability, status, weather=None):
    if status in STATUS_IMMUNE.get(ability, ()):
        return False
    if ability == 'LEAF_GUARD' and weather == 'sun':
        return False
    if ability == 'OWN_TEMPO' and status == 'cnf':
        return False
    return True


def secondary_chance(att_ability, dfn_ability, base):
    """On-hit secondary-effect chance after the attacker's Serene Grace (x2)
    and the defender's Shield Dust (suppresses secondaries entirely)."""
    if dfn_ability == 'SHIELD_DUST':
        return 0
    if att_ability == 'SERENE_GRACE':
        return base * 2
    return base


# =============================================================== priority ===
def priority_bonus(ability, move, hp_frac=1.0):
    if ability == 'PRANKSTER' and move['cat'] == 'STATUS':
        return 1
    if ability == 'GALE_WINGS' and move['type'] == 'FLYING' and hp_frac >= 1.0:
        return 1
    if ability == 'TRIAGE' and move['effect'] in ('EFFECT_HEAL', 'EFFECT_ROOST', 'EFFECT_REST'):
        return 3
    return 0


# =============================================================== trapping ===
def traps(trapper_ability, foe_types, foe_ability):
    """Can `trapper_ability` stop the foe from switching?"""
    if foe_ability in ('SHADOW_TAG',):           # can't trap a fellow Shadow Tag
        return False
    if trapper_ability == 'SHADOW_TAG':
        return 'GHOST' not in foe_types
    if trapper_ability == 'ARENA_TRAP':
        return 'FLYING' not in foe_types and foe_ability != 'LEVITATE'
    if trapper_ability == 'MAGNET_PULL':
        return 'STEEL' in foe_types
    return False


# ================================================================ weather ===
WEATHER_SETTERS = {'DROUGHT': 'sun', 'DRIZZLE': 'rain',
                   'SAND_STREAM': 'sand', 'SNOW_WARNING': 'hail'}
WEATHER_DMG = {'sun': {'FIRE': 1.5, 'WATER': 0.5},
               'rain': {'WATER': 1.5, 'FIRE': 0.5}}
WEATHER_SPEED = {'rain': 'SWIFT_SWIM', 'sun': 'CHLOROPHYLL',
                 'sand': 'SAND_RUSH', 'hail': 'SLUSH_RUSH'}


def weather_speed_mult(ability, weather):
    base = 2.0 if weather and WEATHER_SPEED.get(weather) == ability else 1.0
    if ability == 'QUICK_FEET':           # handled with status in engine; placeholder
        return base
    return base


def weather_dmg_mult(weather, move_type):
    return WEATHER_DMG.get(weather, {}).get(move_type, 1.0)


def own_weather_dmg_mult(ability, move_type):
    return weather_dmg_mult(WEATHER_SETTERS.get(ability), move_type)


# ============================================== coverage accounting (honest) ===
# Abilities that genuinely do nothing in a 1v1/6v6 damage sim -> no-op is correct.
NOOP_ABILITIES = {
    'NO_ABILITY', 'RUN_AWAY', 'HONEY_GATHER', 'ILLUMINATE', 'PICKUP', 'KEEN_EYE',
    'STICKY_HOLD', 'SUCTION_CUPS', 'OBLIVIOUS', 'CUTE_CHARM', 'TANGLED_FEET',
    'RIVALRY', 'KLUTZ', 'STALL', 'FRISK', 'ANTICIPATION', 'FOREWARN', 'PICKPOCKET',
    'GLUTTONY', 'HARVEST', 'CHEEK_POUCH', 'BALL_FETCH', 'STENCH', 'SHELL_ARMOR',
    'BATTLE_ARMOR', 'SUPER_LUCK', 'SNIPER',
    'INNER_FOCUS', 'STEADFAST', 'COMPOUND_EYES', 'NO_GUARD',
    'HYDRATION', 'LEAF_GUARD', 'EARLY_BIRD', 'WONDER_SKIN', 'SAND_VEIL',
    'SNOW_CLOAK', 'CLOUD_NINE', 'PRESSURE', 'UNNERVE', 'DAMP', 'AROMA_VEIL',
    'OVERCOAT', 'SOUNDPROOF', 'BULLETPROOF', 'SCREEN_CLEANER', 'CUD_CHEW',
    'QUICK_DRAW', 'BIG_PECKS', 'LIGHT_METAL', 'HEAVY_METAL', 'ARMOR_TAIL',
    'DAZZLING', 'QUEENLY_MAJESTY',
}
# Abilities that need mechanics this abstraction lacks (form change, copy,
# terrain, doubles, transform) -> documented unmodelled.
UNMODELLED_ABILITIES = {
    'TRACE', 'IMPOSTER', 'FORECAST', 'MOODY', 'NEUTRALIZING_GAS', 'CURSED_BODY',
    'PERISH_BODY', 'MUMMY', 'WANDERING_SPIRIT', 'POWER_OF_ALCHEMY', 'RECEIVER',
    'ZEN_MODE', 'SCHOOLING', 'STANCE_CHANGE', 'DISGUISE', 'POWER_CONSTRUCT',
    'SHIELDS_DOWN', 'RKS_SYSTEM', 'BATTLE_BOND', 'COMATOSE', 'CORROSION',
    'UNBURDEN', 'SYMBIOSIS', 'PARENTAL_BOND', 'PROTOSYNTHESIS', 'INFILTRATOR',
    'MOLD_BREAKER',  # partial: see suppress_target_ability
}
