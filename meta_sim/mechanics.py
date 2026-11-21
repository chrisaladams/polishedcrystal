"""Battle rules ported from the ROM, shared by engine.py.

Each helper names the routine it mirrors. The engine calls these instead of
open-coding the rules, so there is one place to check against the assembly.

  can_status        engine/battle/effect_commands.asm  CanStatusTarget
  status_move_immune                                    checkpowder / resettypematchup
  lower_stat / raise_stat   engine/battle/stats.asm     FarChangeStat (+ Defiant/Competitive)
  accuracy_hits     engine/battle/effect_commands.asm   BattleCommand_checkhit
"""
import json
import os

import rom_damage

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name):
    path = os.path.join(HERE, 'data', name)
    return json.load(open(path)) if os.path.exists(path) else {}


ABILITY_FLAGS = _load('abilities.json')     # data/abilities/flags.asm
ITEM_DATA = _load('items.json')             # data/items/attributes.asm
MOLD_BREAKERS = rom_damage.MOLD_BREAKERS


def held(mon):
    """The held-item effect constant (HELD_*) of mon's item, or None."""
    return (ITEM_DATA.get(mon.item) or {}).get('held') if mon.item else None


def item_param(mon):
    return (ITEM_DATA.get(mon.item) or {}).get('param') if mon.item else None


def nibble_fraction(param):
    """Item params like $ba are a MultiplyAndDivide pair: $ba = 11/10."""
    v = int(param.replace('$', '0x'), 16) if isinstance(param, str) else int(param)
    return v >> 4, v & 0xF


def ignorable(ability):
    return 'IGNORABLE' in ABILITY_FLAGS.get(ability, [])


def seen_ability(user, target):
    """_GetIgnorableAbility: target's ability as the user's move sees it
    (Mold Breaker / Teravolt / Turboblaze ignore IGNORABLE abilities)."""
    if user is not None and user.ability in MOLD_BREAKERS and ignorable(target.ability):
        return None
    return target.ability


# ---- status -------------------------------------------------------------------
STATUS_TYPES = {'psn': ('POISON', 'STEEL'), 'tox': ('POISON', 'STEEL'), 'brn': ('FIRE',),
                'par': ('ELECTRIC',), 'frz': ('ICE',), 'slp': ()}
STATUS_ABILITY = {'slp': 'INSOMNIA', 'psn': 'IMMUNITY', 'tox': 'IMMUNITY',
                  'brn': 'WATER_VEIL', 'par': 'LIMBER', 'frz': 'MAGMA_ARMOR'}
ABILITY_ALIAS = {'VITAL_SPIRIT': 'INSOMNIA', 'PASTEL_VEIL': 'IMMUNITY'}
STATUS_ITEM = {'slp': 'HELD_PREVENT_SLEEP', 'psn': 'HELD_PREVENT_POISON',
               'tox': 'HELD_PREVENT_POISON', 'brn': 'HELD_PREVENT_BURN',
               'par': 'HELD_PREVENT_PARALYZE', 'frz': 'HELD_PREVENT_FREEZE'}
POISON_STATUS_EFFECTS = {'EFFECT_POISON', 'EFFECT_TOXIC'}


def can_status(target, st, *, user=None, source='move', move=None, weather=None,
               sub_blocked=False):
    """CanStatusTarget. source: 'move' (a move: Substitute and Safeguard
    apply), 'nosub' (Toxic Spikes, contact abilities, Synchronize: Safeguard
    applies, Substitute doesn't) or 'orb' (Toxic/Flame Orb: neither applies,
    and the holder's own Corrosion lets it poison itself)."""
    if target.status is not None:
        return False
    if st == 'frz' and weather == 'sun':
        return False                                  # harsh sunlight prevents freeze
    if st in ('psn', 'tox'):
        if source == 'orb' and target.ability == 'CORROSION':
            return True
        if (source == 'move' and move is not None and user is not None
                and move['effect'] in POISON_STATUS_EFFECTS and user.ability == 'CORROSION'):
            return True                               # Corrosion bypasses all but status
    if set(target.types) & set(STATUS_TYPES[st]):
        return False
    if held(target) == STATUS_ITEM[st]:
        return False
    if source != 'orb':
        side = target.side
        if side is not None and getattr(side, 'safeguard', 0) and \
                not (user is not None and user.ability == 'INFILTRATOR'):
            return False
    if source == 'move' and sub_blocked and not (user is not None and user.ability == 'INFILTRATOR'):
        return False                                  # CheckSubstituteOpp (Infiltrator bypasses)
    ab = seen_ability(user, target) if source == 'move' else target.ability
    ab = ABILITY_ALIAS.get(ab, ab)
    if ab == STATUS_ABILITY[st]:
        return False
    if ab == 'LEAF_GUARD' and weather == 'sun':
        return False
    return True


def can_confuse(target, *, user=None, sub_blocked=False, safeguard_applies=True):
    """BattleCommand_confuse / confusetarget."""
    if target.confused:
        return False
    if held(target) == 'HELD_PREVENT_CONFUSE':
        return False
    if seen_ability(user, target) == 'OWN_TEMPO':
        return False
    if safeguard_applies and target.side is not None and getattr(target.side, 'safeguard', 0) \
            and not (user is not None and user.ability == 'INFILTRATOR'):
        return False
    return not (sub_blocked and not (user is not None and user.ability == 'INFILTRATOR'))


def sub_blocks(user, target, move):
    """CheckSubstituteOpp: the target's Substitute is in the way, unless the
    user has Infiltrator or the move is a sound move."""
    return (target.sub_hp > 0 and user.ability != 'INFILTRATOR'
            and not (move is not None and move.get('sound')))


def status_move_immune(user, target, move, chart, type_mult):
    """BattleCommand_checkpowder (+ resettypematchup): Thunder Wave, Toxic and
    powder moves fail on a type immunity (Ground vs Thunder Wave, Steel vs
    Toxic, Grass vs powder); Corrosion's Toxic ignores it. Other status moves
    ignore the type chart. Returns True if the move can't affect the target."""
    mid = move.get('id')
    script = move.get('script', ())
    checks_type = (mid == 'THUNDER_WAVE' or 'resettypematchup' in script
                   or (mid == 'TOXIC' and user.ability != 'CORROSION')
                   or (move.get('powder') and not (mid == 'POISONPOWDER'
                                                   and user.ability == 'CORROSION')))
    if move.get('powder') and ('GRASS' in target.types
                               or seen_ability(user, target) == 'OVERCOAT'
                               or held(target) == 'HELD_SAFETY_GOGGLES'):
        return True
    if checks_type and type_mult(move['type'], target, chart) == 0:
        return True
    return False


# ---- stat stages ----------------------------------------------------------------
STAT_KEYS = ('atk', 'defe', 'spa', 'spd', 'spe', 'acc', 'eva')


def _apply(mon, stat, n):
    old = mon.stage.get(stat, 0)
    new = max(-6, min(6, old + n))
    mon.stage[stat] = new
    return new != old


def raise_stat(mon, stat, n):
    """A self stat change (forceraisestat / forcelowerstat on the user).
    Contrary inverts it. Returns True if the stage moved."""
    if mon.ability == 'CONTRARY':
        n = -n
    return _apply(mon, stat, n)


DROP_BLOCK = {'HYPER_CUTTER': 'atk', 'BIG_PECKS': 'defe', 'KEEN_EYE': 'acc',
              'ILLUMINATE': 'acc', 'MINDS_EYE': 'acc'}


def change_opp_stat(target, stat, delta, *, user=None, sub_blocked=False):
    """FarChangeStat with STAT_TARGET (a move changing the foe's stats).
    Contrary flips the direction first; a drop then runs into Substitute,
    Clear Body / White Smoke, Hyper Cutter / Big Pecks / Keen Eye-style
    single-stat guards and Clear Amulet, and a drop that lands sets off the
    target's Defiant (+2 Atk) or Competitive (+2 Sp. Atk). Returns True if the
    stage moved."""
    ab = seen_ability(user, target)
    if ab == 'CONTRARY':
        delta = -delta
    if sub_blocked:
        return False
    if delta < 0:
        if ab in ('CLEAR_BODY', 'WHITE_SMOKE') or DROP_BLOCK.get(ab) == stat:
            return False
        if held(target) == 'HELD_CLEAR_AMULET':
            return False
    if not _apply(target, stat, delta):
        return False
    if delta < 0 and not target.fainted:
        if target.ability == 'DEFIANT':
            _apply(target, 'atk', 2)
        elif target.ability == 'COMPETITIVE':
            _apply(target, 'spa', 2)
    return True


def lower_stat(target, stat, n, *, user=None, sub_blocked=False):
    """A move lowering the foe's stat by n stages (see change_opp_stat)."""
    return change_opp_stat(target, stat, -n, user=user, sub_blocked=sub_blocked)


# ---- accuracy -----------------------------------------------------------------
FLY_HITTERS = {'GUST', 'THUNDER', 'HURRICANE', 'TWISTER'}
DIG_HITTERS = {'EARTHQUAKE', 'MAGNITUDE'}
ALWAYS_HIT_EFFECTS = {'EFFECT_ALWAYS_HIT', 'EFFECT_ROAR', 'EFFECT_COUNTER'}
LINK_EVASION_CAP = 2          # link battles cap the target's evasion boost at +2


def acc_fraction(level):
    """DoStatChangeMod + $11 for accuracy level 1..13 (7 = neutral):
    -1 = 3/4 ... -6 = 3/9, +1 = 4/3 ... +6 = 9/3."""
    return (level - 4, 3) if level >= 7 else (3, 10 - level)


def accuracy_hits(att, dfn, move, rng, *, weather=None, target_moved_first=False,
                  pursuit_switch=False, link=True):
    """BattleCommand_checkhit from the accuracy checks on: returns True if the
    move hits. The caller has already handled Protect, Dream Eater and moves
    that need no accuracy roll (scripts without checkhit)."""
    mid, eff = move.get('id'), move['effect']
    if pursuit_switch and eff == 'EFFECT_PURSUIT':
        return True
    if mid == 'TOXIC' and 'POISON' in att.types:
        return True
    if att.ability == 'NO_GUARD' or seen_ability(att, dfn) == 'NO_GUARD':
        return True
    semi = getattr(dfn, 'semi_inv', None)
    if semi == 'fly' and mid not in FLY_HITTERS:
        return False
    if semi == 'dig' and mid not in DIG_HITTERS:
        return False
    if weather == 'rain' and mid in ('THUNDER', 'HURRICANE'):
        return True
    if weather == 'hail' and mid == 'BLIZZARD':
        return True
    if getattr(dfn, 'minimized', False) and mid in ('BODY_SLAM', 'STOMP'):
        return True
    if eff in ALWAYS_HIT_EFFECTS or mid == 'STRUGGLE':
        return True

    acc = move['acc']
    if acc < 0:
        acc = 255
    if eff == 'EFFECT_THUNDER':                       # BattleCommand_thunderaccuracy
        if weather == 'rain':
            acc = 100
        elif weather == 'sun':
            acc = 50
    target_ab = seen_ability(att, dfn)
    if target_ab == 'WONDER_SKIN' and move['cat'] == 'STATUS':
        acc = 50

    a = 7 + att.stage.get('acc', 0)
    c = 7 + dfn.stage.get('eva', 0)
    if link and c > 7 + LINK_EVASION_CAP:
        c = 7 + LINK_EVASION_CAP
    if att.ability == 'UNAWARE':
        c = 7
    elif (getattr(dfn, 'identified', False)
          or att.ability in ('KEEN_EYE', 'ILLUMINATE', 'MINDS_EYE')) and c > 7:
        c = 7
    if target_ab == 'UNAWARE':
        a = 7
    level = max(0, min(12, 6 + a - c)) + 1
    num, den = acc_fraction(level)
    v = acc * num // den

    # ApplyAccuracyAbilities
    if att.ability == 'COMPOUND_EYES':
        v = v * 13 // 10
    elif att.ability == 'HUSTLE' and move['cat'] == 'PHYSICAL':
        v = v * 4 // 5
    if target_ab == 'TANGLED_FEET' and dfn.confused:
        v = v // 2
    elif target_ab == 'SAND_VEIL' and weather == 'sand':
        v = v * 4 // 5
    elif target_ab == 'SNOW_CLOAK' and weather == 'hail':
        v = v * 4 // 5
    # items
    h = held(att)
    if h == 'HELD_ACCURACY_BOOST' or (h == 'HELD_ZOOM_LENS' and target_moved_first):
        n, d = nibble_fraction(item_param(att))
        v = v * n // d
    if held(dfn) == 'HELD_BRIGHTPOWDER':
        n, d = nibble_fraction(item_param(dfn))
        v = v * n // d
    if v >= 256:
        return True
    return rng.randrange(100) < v


# ---- Hidden Power -----------------------------------------------------------------
TYPE_ORDER = ['NORMAL', 'FIGHTING', 'FLYING', 'POISON', 'GROUND', 'ROCK', 'BUG', 'GHOST',
              'STEEL', 'FIRE', 'WATER', 'GRASS', 'ELECTRIC', 'PSYCHIC', 'ICE', 'DRAGON',
              'DARK', 'FAIRY']                       # constants/type_constants.asm
DV_STATS = ('hp', 'atk', 'defe', 'spe', 'spa', 'spd')   # bit order a..f in GetHiddenPowerType


def hidden_power_type(dvs):
    """GetHiddenPowerType (non-faithful): dvs = {stat: 0..15}. Each DV's low
    bit makes one bit of %fedcba (HP, Atk, Def, Spe, Sp.Atk, Sp.Def); 63 is
    Fairy, otherwise Fighting + (bits >> 2)."""
    b = sum((dvs[k] & 1) << i for i, k in enumerate(DV_STATS))
    return 'FAIRY' if b == 63 else TYPE_ORDER[(b >> 2) + 1]


def dvs_for_hidden_power(ptype):
    """Highest DVs (15, or 14 where a bit must be 0) that give Hidden Power
    type ptype. HP and Atk always stay 15."""
    if ptype == 'FAIRY':
        return {k: 15 for k in DV_STATS}
    t = TYPE_ORDER.index(ptype) - 1                 # 0..15
    b = (t << 2) | 3
    if b == 63:                                     # Dark: 63 is Fairy, so HP DV 14
        b = 62
    return {k: 15 if (b >> i) & 1 else 14 for i, k in enumerate(DV_STATS)}


# ---- speed ----------------------------------------------------------------------
WEATHER_SPEED_ABILITY = {'SWIFT_SWIM': 'rain', 'CHLOROPHYLL': 'sun', 'SAND_RUSH': 'sand',
                         'SLUSH_RUSH': 'hail'}


def speed(mon, weather=None):
    """GetSpeed (engine/battle/core.asm): stat stage, paralysis halving
    (not with Quick Feet), ApplySpeedAbilities (Unburden, weather doublers,
    Quick Feet x1.5 while statused), then Quick Powder (Ditto) x2 / Iron Ball
    x0.5 / Choice Scarf x1.5, all integer MultiplyAndDivide; capped at $ffff."""
    v = mon.base['spe']
    if mon.fainted:
        return v
    num, den = rom_damage.stage_fraction(7 + mon.stage.get('spe', 0))
    v = v * num // den
    ab = mon.ability
    if mon.status == 'par' and ab != 'QUICK_FEET':
        v //= 2
    if ab == 'UNBURDEN' and getattr(mon, 'unburden', False):
        v *= 2
    elif WEATHER_SPEED_ABILITY.get(ab) and WEATHER_SPEED_ABILITY[ab] == weather:
        v *= 2
    elif ab == 'QUICK_FEET' and mon.status is not None:
        v = v * 3 // 2
    h, param = rom_damage.held_effect(mon)
    if h == 'HELD_QUICK_POWDER':
        if rom_damage.valid_item(mon, mon.item):
            v *= 2
    elif h == 'HELD_IRON_BALL':
        v //= 2
    elif h == 'HELD_CHOICE' and param == 'SPEED':
        v = v * 3 // 2
    return min(v, 0xFFFF)


# ---- turn order -------------------------------------------------------------------
def move_priority(mon, move):
    """GetMovePriority: the move's priority, +1 for Prankster status moves."""
    p = move.get('prio', 0)
    if mon.ability == 'PRANKSTER' and move['cat'] == 'STATUS':
        p += 1
    return p


def _item_priority(mon, move, rng):
    """CheckMoveSpeed's per-side bonus: +1 if Quick Draw (30%, attacking moves),
    Quick Claw (param%) or Custap Berry (at a pinch, eaten) lets it go first,
    -1 for Lagging Tail. Returns (bonus, custap_eaten)."""
    if mon.ability == 'QUICK_DRAW' and move['cat'] != 'STATUS' and rng.randrange(100) < 30:
        return 1, False
    foe = mon.side.foe.mon if mon.side is not None and mon.side.foe is not None else None
    unnerved = foe is not None and not foe.fainted and foe.ability == 'UNNERVE'
    h, param = rom_damage.held_effect(mon)
    if h == 'HELD_QUICK_CLAW':
        return (1 if rng.randrange(100) < int(param) else 0), False
    if h == 'HELD_CUSTAP_BERRY' and not unnerved:
        pinch = mon.hp <= mon.maxhp // (2 if mon.ability == 'GLUTTONY' else 4)
        return (1, True) if pinch else (0, False)
    if h == 'HELD_LAGGING_TAIL':
        return -1, False
    return 0, False


def a_moves_first(a, b, a_move, b_move, rng, *, trick_room=False, weather_a=None,
                  weather_b=None):
    """DetermineMoveOrder: priority, then the item/ability bonuses, then GetSpeed
    (Trick Room reverses it), ties at random."""
    pa, pb = move_priority(a, a_move), move_priority(b, b_move)
    if pa != pb:
        return pa > pb
    ba, ca = _item_priority(a, a_move, rng)
    bb, cb = _item_priority(b, b_move, rng)
    for mon, eaten in ((a, ca), (b, cb)):
        if eaten:
            mon.item = None
            if mon.ability == 'UNBURDEN':
                mon.unburden = True
    if ba != bb:
        return ba > bb
    sa, sb = speed(a, weather_a), speed(b, weather_b)
    if sa == sb:
        return rng.randrange(2) == 0
    return (sa < sb) if trick_room else (sa > sb)
