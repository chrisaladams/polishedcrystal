"""Damage, computed the way the ROM computes it.

A step-for-step port of the move script's damage commands, with the same
integer arithmetic and the same order of operations:

  critical      engine/battle/effect_commands.asm  BattleCommand_critical
  damagestats   ... BattleCommand_damagestats (stats, screens, Eviolite,
                    weather Def/Sp.Def boosts, TruncateHL_BC)
  damagecalc    ... BattleCommand_damagecalc (DamagePass1-4, stat stages via
                    DoStatChangeMod, ApplyDamageAbilities, burn, Flash Fire,
                    crit, held items)
  stab          ... BattleCommand_stab (type matchup byte, STAB, weather,
                    Tinted Lens / Filter / Solid Rock, Expert Belt)
  damagevariation  85-100% as damage * (85..100) / 100
  conditionalboost Facade / Hex / Venoshock / Acrobatics / Avalanche /
                    Pursuit double, Knock Off +50%

Every modifier is MultiplyAndDivide (home/math.asm): multiply by x, then
integer-divide by y. hMultiplicand and hQuotient are 3 bytes, so values are
held in 24 bits between steps. oracle_pipeline.py checks this module against
the real routines running under PyBoy.
"""

import json as _json
import os as _os

_ITEMS_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'data', 'items.json')
ITEM_DATA = _json.load(open(_ITEMS_PATH)) if _os.path.exists(_ITEMS_PATH) else {}


def held_effect(mon):
    """(HELD_* effect, parameter) of mon's item, from data/items/attributes.asm."""
    d = ITEM_DATA.get(mon.item) if mon.item else None
    return (d['held'], d['param']) if d else (None, None)


def makes_contact(att, move):
    """_CheckContactMove: Protective Pads, or Punching Glove on a punching
    move, stop a contact move from counting as contact."""
    if not move.get('contact'):
        return False
    h = held_effect(att)[0]
    if h == 'HELD_PROTECTIVE_PADS' or (h == 'HELD_PUNCHING_GLOVE' and move.get('punch')):
        return False
    return True


M24 = 0xFFFFFF
L50 = 50

# Category-gated attacker modifiers (ApplyPhysical/SpecialAttackDamageMod).
CRIT_MOVE_STAGE = 1
CRIT_CHANCE = {0: 1, 1: 3, 2: 12}          # out of 24 (data/battle/critical_hit_chances.asm)
CONDITIONAL_DOUBLE = {'FACADE', 'HEX', 'VENOSHOCK', 'ACROBATICS', 'AVALANCHE', 'PURSUIT'}
PINCH = {'OVERGROW': 'GRASS', 'BLAZE': 'FIRE', 'TORRENT': 'WATER', 'SWARM': 'BUG'}
ATE = {'PIXILATE': 'FAIRY', 'GALVANIZE': 'ELECTRIC'}
MOLD_BREAKERS = {'MOLD_BREAKER', 'TERAVOLT', 'TURBOBLAZE'}
# data/abilities/type_nullification_abilities.asm, plus Levitate (CheckAirborne)
TYPE_NULLIFY = {'VOLT_ABSORB': 'ELECTRIC', 'LIGHTNING_ROD': 'ELECTRIC',
                'MOTOR_DRIVE': 'ELECTRIC', 'DRY_SKIN': 'WATER', 'WATER_ABSORB': 'WATER',
                'FLASH_FIRE': 'FIRE', 'SAP_SIPPER': 'GRASS', 'LEVITATE': 'GROUND'}


# UserValidBattleItem's .ValidBattleItemTable: species-locked items
VALID_ITEM_SPECIES = {'LIGHT_BALL': ('pikachu',), 'LEEK': ('farfetch_d', 'sirfetch_d'),
                      'LUCKY_PUNCH': ('chansey',), 'QUICK_POWDER': ('ditto',),
                      'THICK_CLUB': ('cubone', 'marowak')}
FORM_SUFFIX = ('_plain', '_alolan', '_galarian', '_hisuian', '_paldean', '_armored')


def species(mon):
    sid = getattr(mon, 'id', None) or ''
    for suf in FORM_SUFFIX:
        if sid.endswith(suf):
            return sid[:-len(suf)]
    if sid.startswith('tauros_paldean'):
        return 'tauros'
    return sid


def valid_item(mon, item):
    return mon.item == item and species(mon) in VALID_ITEM_SPECIES.get(item, ())


def eviolite(mon):
    """UnevolvedEviolite: the holder must be able to evolve and not be on the
    fork's EvioliteExcludedSpecies list (mon.eviolite_ok carries both)."""
    return mon.item == 'EVIOLITE' and getattr(mon, 'eviolite_ok', True)


def mul(v, k):
    """Multiply: 3-byte multiplicand times a 1-byte multiplier."""
    return (v & M24) * k


def mad(v, num, den):
    """MultiplyAndDivide ($xy): v * x / y, kept to the 3-byte quotient."""
    return ((v & M24) * num // den) & M24


def stage_fraction(level):
    """DoStatChangeMod: stat level 1..13 (7 = neutral) -> (num, den)."""
    if level >= 7:
        return level - 5, 2
    return 2, 9 - level


def truncate(atk, dfn):
    """TruncateHL_BC: halve both 16-bit values until each fits in a byte."""
    while (atk >> 8) | (dfn >> 8):
        dfn = max(dfn >> 1, 1)
        atk = max(atk >> 1, 1)
    return atk & 0xFF, dfn & 0xFF


def type_byte(move_type, defender_types, chart, scrappy=False):
    """wTypeMatchup: $10 = neutral, doubled / halved (rounding down) / zeroed
    per defending type."""
    m = 0x10
    for t in defender_types:
        f = chart.get(f'{move_type}>{t}', 1.0)
        if f == 0 and scrappy and t == 'GHOST' and move_type in ('NORMAL', 'FIGHTING'):
            continue
        if f == 0:
            return 0
        if f > 1:
            m *= 2
        elif f < 1:
            m >>= 1
    return m


def crit_stage(att, move):
    c = 0
    if valid_item(att, 'LEEK') or valid_item(att, 'LUCKY_PUNCH'):
        c += 2
    if getattr(att, 'focus_energy', False):
        c += 2
    if move.get('high_crit'):
        c += 1
    if held_effect(att)[0] == 'HELD_CRITICAL_UP':        # Scope Lens / Razor Claw
        c += 1
    if att.ability == 'SUPER_LUCK':
        c += 1
    return c


def roll_crit(att, dfn, move, rng):
    if move['power'] <= 0 or (dfn.ability in ('BATTLE_ARMOR', 'SHELL_ARMOR')
                              and att.ability not in MOLD_BREAKERS):
        return False
    c = crit_stage(att, move)
    if c >= 3:
        return True
    return rng.randrange(24) < CRIT_CHANCE[c]


def damage(att, dfn, move, chart, *, power, weather=None, crit=False, roll=None,
           moved_second=False, damaged_this_turn=False, pursuit_switch=False,
           ground_immune=False, absorbed=False, flag_immune=False, trace=None,
           move_type=None, rollout_doublings=0, post_doublings=0, parental_second=False):
    """One hit's damage and the raw type matchup byte (0 = immune).

    att / dfn are engine.Pmon (raw L50 stats in .base, stages in .stage).
    power: the move's base power after variable-power effects.
    roll: 0..15 for 85..100%, or None for the unrolled (100%) damage.
    """
    # move_type: Hidden Power's DV-based type (hiddenpower runs before damagestats)
    move_type = move_type or move['type']
    if att.ability in ATE and move_type == 'NORMAL':
        move_type = ATE[att.ability]                    # Pixilate / Galvanize
    # Scrappy / Mind's Eye, or a Foresight-identified target: Normal and
    # Fighting moves hit Ghosts
    scrappy = att.ability in ('SCRAPPY', 'MINDS_EYE') or getattr(dfn, 'identified', False)
    raw = type_byte(move_type, dfn.types, chart, scrappy)
    if ground_immune or absorbed or flag_immune:
        raw = 0
    if att.ability not in MOLD_BREAKERS and TYPE_NULLIFY.get(dfn.ability) == move_type:
        raw = 0                                         # CheckNullificationAbilities
    if raw == 0 or power <= 0:
        return 0, raw
    physical = move['cat'] == 'PHYSICAL'
    psystrike = move['effect'] == 'EFFECT_PSYSTRIKE'   # Sp. Atk vs Defense
    defender_ab = None if att.ability in MOLD_BREAKERS else dfn.ability
    screens_up = (dfn.side is not None and not crit and att.ability != 'INFILTRATOR'
                  and move['effect'] != 'EFFECT_BRICK_BREAK')

    # ---- damagestats
    if physical or psystrike:
        d = dfn.base['defe']
        if weather == 'hail' and 'ICE' in dfn.types:
            d += d >> 1                                  # HailDefenseBoost
        if species(dfn) == 'ditto' and dfn.item == 'METAL_POWDER':
            d += d >> 1                                  # DittoMetalPowder
        if eviolite(dfn):
            d += d >> 1                                  # UnevolvedEviolite
    if physical:
        a = att.base['atk']
        if screens_up and dfn.side.reflect:
            d = (d << 1) & 0xFFFF
        if valid_item(att, 'THICK_CLUB') or valid_item(att, 'LIGHT_BALL'):
            a = (a << 1) & 0xFFFF                        # ThickClubOrLightBallBoost
    elif psystrike:
        a = att.base['spa']
        if screens_up and dfn.side.light_screen:
            d = (d << 1) & 0xFFFF
        if valid_item(att, 'LIGHT_BALL'):
            a = (a << 1) & 0xFFFF
    else:
        d = dfn.base['spd']
        if weather == 'sand' and 'ROCK' in dfn.types:
            d += d >> 1                                  # SandstormSpDefBoost
        if eviolite(dfn):
            d += d >> 1
        a = att.base['spa']
        if screens_up and dfn.side.light_screen:
            d = (d << 1) & 0xFFFF
        if valid_item(att, 'LIGHT_BALL'):
            a = (a << 1) & 0xFFFF                        # LightBallBoost
    a, d = truncate(a, d)
    d = d or 1

    # ---- damagecalc
    v = (2 * L50) // 5 + 2                               # DamagePass1
    v = mul(v, power)                                    # DamagePass2
    v = mul(v, a)
    akey, dkey = ('atk', 'defe') if physical else (('spa', 'defe') if psystrike else ('spa', 'spd'))
    if dfn.ability != 'UNAWARE' or att.ability in MOLD_BREAKERS:
        level = att.stage[akey] + 7
        if not (crit and level < 7):
            v = mad(v, *stage_fraction(level))
    if att.ability != 'UNAWARE':
        level = dfn.stage[dkey] + 7
        if not (crit and level >= 7):
            v = mad(v, *stage_fraction(14 - level))

    # ApplyDamageAbilities: the attacker's, then the defender's
    ab = att.ability
    if ab == 'TECHNICIAN' and power <= 60:
        v = mad(v, 3, 2)
    elif ab == 'HUGE_POWER' and physical:
        v = mad(v, 2, 1)
    elif ab in ('HUSTLE', 'GORILLA_TACTICS') and physical:
        v = mad(v, 3, 2)
    elif ab in PINCH and move_type == PINCH[ab] and att.hp <= att.maxhp // 3:
        v = mad(v, 3, 2)
    elif ab == 'STEELY_SPIRIT' and move_type == 'STEEL':
        v = mad(v, 3, 2)
    elif ab == 'RIVALRY' and getattr(att, 'gender', None) and getattr(dfn, 'gender', None):
        v = mad(v, 5, 4) if att.gender == dfn.gender else mad(v, 3, 4)
    elif ab == 'SHEER_FORCE' and move.get('secondary', move.get('chance', 0) > 0):
        v = mad(v, 13, 10)
    elif ab == 'ANALYTIC' and moved_second:
        v = mad(v, 13, 10)
    elif ab == 'SOLAR_POWER' and weather == 'sun' and not physical:
        v = mad(v, 3, 2)
    elif ab == 'IRON_FIST' and move.get('punch'):
        v = mad(v, 6, 5)
    elif ab == 'TOUGH_CLAWS' and makes_contact(att, move):
        v = mad(v, 13, 10)
    elif ab == 'MEGA_LAUNCHER' and move.get('pulse'):
        v = mad(v, 3, 2)
    elif ab == 'SHARPNESS' and move.get('slice'):
        v = mad(v, 3, 2)
    elif ab == 'SAND_FORCE' and weather == 'sand' and move_type in ('GROUND', 'ROCK', 'STEEL'):
        v = mad(v, 13, 10)
    elif ab == 'RECKLESS' and move['effect'] in ('EFFECT_RECOIL_HIT', 'EFFECT_JUMP_KICK'):
        v = mad(v, 6, 5)
    elif ab == 'GUTS' and att.status is not None and physical:
        v = mad(v, 3, 2)
    elif ab in ATE and move['type'] == 'NORMAL':
        v = mad(v, 6, 5)
    db = defender_ab
    if db == 'MULTISCALE' and dfn.hp >= dfn.maxhp:
        v = mad(v, 1, 2)
    elif db == 'MARVEL_SCALE' and dfn.status is not None and (physical or psystrike):
        v = mad(v, 2, 3)
    elif db == 'THICK_FAT' and move_type in ('FIRE', 'ICE'):
        v = mad(v, 1, 2)
    elif db == 'DRY_SKIN' and move_type == 'FIRE':
        v = mad(v, 5, 4)
    elif db == 'FUR_COAT' and (physical or psystrike):   # ApplyPhysicalDefenseDamageMod
        v = mad(v, 1, 2)
    elif db == 'FLUFFY':
        if move_type == 'FIRE':
            v = mad(v, 2, 1)
        if makes_contact(att, move):
            v = mad(v, 1, 2)

    if att.status == 'brn' and physical and move.get('id') != 'FACADE' and ab != 'GUTS':
        v = mad(v, 1, 2)
    if getattr(att, 'flash_fire', False) and move_type == 'FIRE':
        v = mad(v, 3, 2)
    if crit:
        v = mad(v, 9, 4) if ab == 'SNIPER' else mad(v, 3, 2)
    # item boosts (damagecalc .Item boosts): one held effect per item
    item = att.item
    h, param = held_effect(att)
    if h == 'HELD_TYPE_BOOST' and move_type == param:
        v = mad(v, 6, 5)
    elif h == 'HELD_CATEGORY_BOOST' and move['cat'] == param:   # Muscle Band / Wise Glasses
        v = mad(v, 11, 10)
    elif h == 'HELD_CHOICE' and (param == 'ATTACK' and physical
                                 or param == 'SP_ATTACK' and not physical):
        v = mad(v, 3, 2)
    elif h == 'HELD_METRONOME':
        v = mad(v, 5 + min(getattr(att, 'metronome_count', 0), 5), 5)   # +20% per repeat, max 5
    elif h == 'HELD_PUNCHING_GLOVE' and move.get('punch'):
        v = mad(v, 11, 10)
    elif h == 'HELD_LIFE_ORB':
        v = mad(v, 13, 10)
    if held_effect(dfn)[0] == 'HELD_ASSAULT_VEST' and not physical and not psystrike:   # ...SpecialDefense...
        v = mad(v, 2, 3)

    v = (v // d) & M24                                   # DamagePass3
    v = (v // 50) & M24
    dmg = min(v + 2, 0xFFFF)                             # DamagePass4
    if trace is not None:
        trace.update(atk=a, defe=d, after_calc=dmg)

    # ---- stab
    m = raw
    if move_type in att.types:
        m = m * 2 if ab == 'ADAPTABILITY' else m + (m >> 1)
    if weather == 'sun':
        if move_type == 'FIRE':
            m += m >> 1
        elif move_type == 'WATER':
            m >>= 1
    elif weather == 'rain':
        if move_type == 'WATER':
            m += m >> 1
        elif move_type == 'FIRE':
            m >>= 1
    v = dmg * m
    if parental_second:                                  # Parental Bond's 2nd hit: x1/4
        v = mad(v, 1, 4)
    if ab == 'TINTED_LENS' and raw < 0x10:
        v = mad(v, 2, 1)
    if defender_ab in ('SOLID_ROCK', 'FILTER') and raw > 0x10:
        v = mad(v, 3, 4)
    if h == 'HELD_EXPERT_BELT' and raw >= 0x11:
        v = mad(v, 6, 5)
    v //= 0x10
    dmg = min(v, 0xFFFF) or 1
    if trace is not None:
        trace.update(matchup=m, raw=raw, after_stab=dmg)

    # ---- rolloutpower (Rollout: doubles per consecutive hit, once more if curled)
    for _ in range(rollout_doublings):
        dmg = min(dmg * 2, 0xFFFF)

    # ---- damagevariation
    if roll is not None:
        dmg = vary(dmg, roll)

    # ---- doubleminimizedamage / doubleflyingdamage / doubleundergrounddamage
    for _ in range(post_doublings):
        dmg = min(dmg * 2, 0xFFFF)

    # ---- conditionalboost
    mid = move.get('id')
    double = ((mid == 'FACADE' and att.status in ('brn', 'psn', 'tox', 'par'))
              or (mid == 'HEX' and dfn.status is not None)
              or (mid == 'VENOSHOCK' and dfn.status in ('psn', 'tox'))
              or (mid == 'ACROBATICS' and not att.item)
              or (mid == 'AVALANCHE' and damaged_this_turn)
              or (mid == 'PURSUIT' and pursuit_switch))
    if double:
        dmg = min(dmg * 2, 0xFFFF)
    if mid == 'KNOCK_OFF' and dfn.item and dfn.ability != 'STICKY_HOLD':
        dmg = (dmg + (dmg >> 1)) & 0xFFFF
    return dmg, raw


def vary(dmg, roll):
    """BattleCommand_damagevariation: damage * (85 + roll) / 100 for roll
    0..15 (BattleRandomRange 16), leaving 0 and 1 alone."""
    if dmg < 2:
        return dmg
    return (dmg * (85 + roll) // 100) & 0xFFFF


def confusion_damage(mon):
    """HitSelfInConfusion + ConfusedDamageCalc: a typeless 40-power physical
    hit with the mon's own Attack and Defense and stat stages; no STAB, type,
    crit, burn or random roll."""
    a, d = truncate(mon.base['atk'], mon.base['defe'])
    d = d or 1
    v = mul(mul((2 * L50) // 5 + 2, 40), a)
    v = mad(v, *stage_fraction(mon.stage['atk'] + 7))
    v = mad(v, *stage_fraction(14 - (mon.stage['defe'] + 7)))
    v = (v // d) & M24
    v = (v // 50) & M24
    return min(v + 2, 0xFFFF)
