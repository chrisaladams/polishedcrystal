"""Pragmatic 6v6 battle engine + heuristic AI for meta-tuning.

This is the "Option A" engine: a clean, uniform turn simulator built on the
same L50 data the 1v1 matrix uses. It is NOT a port of the ROM's trainer AI
(engine/battle/ai/*.asm, ~4400 lines) -- it is a consistent yardstick applied
identically to both sides so cross-mon comparison is fair.

Models the high-impact ~80% of mechanics and approximates the long tail:
  modelled : damage + STAB + type chart, stat stages, the major statuses
             (sleep/paralysis/burn/poison/toxic/freeze + confusion), on-hit
             secondary effects (status/flinch/recoil), self-stat setup moves,
             recovery, Leech Seed, entry hazards (Spikes/Toxic Spikes),
             priority, switching, and a heuristic move/switch AI. Sleep Clause
             is mirrored from the shipped game (toggle: SLEEP_CLAUSE).
  approxd.  : confusion as a flat self-hit chance; multi-hit as its average
             hit count; two-turn moves resolve in one turn; Explosion = big
             hit then user faints. Each mon commits to one ability and one
             item for the whole battle (see abilities.py/items.py) instead
             of switching among abilities per move like the 1v1 matrix does.
  ignored   : weather, screens, trapping, Perish Song, Transform/Sketch/
             Metronome, and most abilities/items beyond the modeled
             multiplier-style subset in abilities.py/items.py. (So Ditto/
             Wobbuffet/Smeargle and weather/screen teams are understated --
             documented.)

Damage uses a random roll (0.85-1.00) since this is Monte Carlo; crits off.
"""
import random

from stats import mon_stats
import abilities
import items

STAB = 1.5
CHOICE_ITEMS = {'CHOICE_BAND', 'CHOICE_SPECS', 'CHOICE_SCARF'}
SLEEP_CLAUSE = False         # shipped game dropped the Sleep Clause (sleep is
                             # unrestricted, 1-3 turns); mirror that here
MAX_TURNS = 300              # battle longer than this -> draw (anti-stall guard)

# ---- stat-stage multipliers (Gen table) --------------------------------------
def stage_mult(stage):
    stage = max(-6, min(6, stage))
    return (2 + stage) / 2 if stage >= 0 else 2 / (2 - stage)

# ---- self-boost moves: effect -> {stat: delta} -------------------------------
BOOST = {
    'EFFECT_ATTACK_UP_2':  {'atk': 2}, 'EFFECT_DEFENSE_UP_2': {'defe': 2},
    'EFFECT_SPEED_UP_2':   {'spe': 2}, 'EFFECT_SP_ATK_UP_2':  {'spa': 2},
    'EFFECT_SP_DEF_UP_2':  {'spd': 2}, 'EFFECT_DEFENSE_CURL': {'defe': 1},
    'EFFECT_DRAGON_DANCE': {'atk': 1, 'spe': 1},
    'EFFECT_BULK_UP':      {'atk': 1, 'defe': 1},
    'EFFECT_CALM_MIND':    {'spa': 1, 'spd': 1},
    'EFFECT_GROWTH':       {'atk': 1, 'spa': 1},
    'EFFECT_HONE_CLAWS':   {'atk': 1},
    'EFFECT_SHELL_SMASH':  {'atk': 2, 'spa': 2, 'spe': 2, 'defe': -1, 'spd': -1},
}
# opponent stat-drop status moves
DROP = {'EFFECT_SPEED_DOWN_2': {'spe': -2}, 'EFFECT_ATTACK_DOWN_2': {'atk': -2},
        'EFFECT_DEFENSE_DOWN_2': {'defe': -2}, 'EFFECT_ACCURACY_DOWN': {'acc': -1}}

# status-inflicting status moves: effect -> status key
INFLICT = {'EFFECT_SLEEP': 'slp', 'EFFECT_PARALYZE': 'par', 'EFFECT_TOXIC': 'tox',
           'EFFECT_POISON': 'psn', 'EFFECT_BURN': 'brn', 'EFFECT_CONFUSE': 'cnf'}
# on-hit secondary status: effect -> status key (applied at `chance`%)
ONHIT = {'EFFECT_BURN_HIT': 'brn', 'EFFECT_PARALYZE_HIT': 'par',
         'EFFECT_FREEZE_HIT': 'frz', 'EFFECT_POISON_HIT': 'psn'}
HEAL_EFFECTS = {'EFFECT_HEAL', 'EFFECT_HEALING_LIGHT', 'EFFECT_ROOST'}
RECOIL_EFFECTS = {'EFFECT_RECOIL_HIT', 'EFFECT_FLARE_BLITZ', 'EFFECT_CLOSE_COMBAT',
                  'EFFECT_JUMP_KICK', 'EFFECT_BRICK_BREAK'}  # close combat = self def/spd drop, approx as none
MULTI = {'EFFECT_MULTI_HIT': 3, 'EFFECT_DOUBLE_HIT': 2}


def type_mult(move_type, def_types, chart):
    m = 1.0
    for dt in def_types:
        m *= chart.get(f"{move_type}>{dt}", 1.0)
    return m


class Pmon:
    """Battle-time wrapper around a pokemon.json entry + a chosen moveset."""
    __slots__ = ('id', 'types', 'base', 'moves', 'ability', 'item', 'maxhp',
                 'hp', 'status', 'sleep', 'tox', 'stage', 'seeded', 'confused',
                 'fainted', 'locked_move')

    def __init__(self, mid, mon, moveset, ability=None, item=None):
        self.id = mid
        self.types = mon['types']
        self.base = mon['stats']           # already L50 stats dict
        self.moves = moveset               # list of move-name strings
        self.ability = ability             # one ability for the whole battle
        self.item = item                   # one held item for the whole battle
        self.maxhp = self.base['hp']
        self.hp = self.maxhp
        self.status = None                 # None/'par'/'brn'/'psn'/'tox'/'slp'/'frz'
        self.sleep = 0                     # remaining sleep turns
        self.tox = 0                       # toxic counter
        self.stage = dict(atk=0, defe=0, spa=0, spd=0, spe=0)
        self.seeded = False
        self.confused = 0
        self.fainted = False
        self.locked_move = None            # Choice-item move lock (index into self.moves)

    def stat(self, key, weather=None, ignore_stage=False):
        stage = 0 if ignore_stage else self.stage.get(key, 0)
        v = self.base[key] * stage_mult(stage)
        if key == 'spe':
            if self.status == 'par' and self.ability != 'QUICK_FEET':
                v *= 0.25
            if self.item == 'CHOICE_SCARF':
                v *= items.CHOICE_SCARF_SPEED_MULT
            v *= abilities.weather_speed_mult(self.ability, weather)
            if self.ability == 'QUICK_FEET' and self.status:
                v *= 1.5
        if key in ('defe', 'spd') and self.item == 'EVIOLITE':
            v *= items.EVIOLITE_DEF_MULT
        return v

    def reset_volatile(self):              # cleared on switch out
        self.stage = dict(atk=0, defe=0, spa=0, spd=0, spe=0)
        self.seeded = False
        self.confused = 0
        self.locked_move = None            # Choice lock releases on switch


class Side:
    def __init__(self, team):
        self.team = team                   # list[Pmon]
        self.active = 0
        self.spikes = 0                    # 0..3 layers
        self.tspikes = 0                   # 0..2 layers
        self.slept_by_foe = False          # sleep-clause bookkeeping

    @property
    def mon(self):
        return self.team[self.active]

    def alive_indices(self):
        return [i for i, m in enumerate(self.team) if not m.fainted]


# ---- damage ------------------------------------------------------------------
def type_eff(att, dfn, move, chart):
    """Type effectiveness for the effective move type, honouring Scrappy
    (Normal/Fighting hit Ghost) and defender ability immunities / Wonder Guard.
    Returns the multiplier (0.0 if the move can't connect)."""
    if abilities.defending_immune(dfn.ability, move):
        return 0.0
    mt = abilities.effective_type(att.ability, move)
    eff = 1.0
    for t in dfn.types:
        e = chart.get(f'{mt}>{t}', 1.0)
        if e == 0.0 and t == 'GHOST' and mt in ('NORMAL', 'FIGHTING') \
                and abilities.scrappy_hits_ghost(att.ability):
            e = 1.0
        eff *= e
    if abilities.wonder_guard_blocks(dfn.ability, eff):
        return 0.0
    return eff


def _sand_spdef(dfn, move, weather):
    """Rock-types get x1.5 Sp.Def in a sandstorm."""
    if weather == 'sand' and move['cat'] == 'SPECIAL' and 'ROCK' in dfn.types:
        return 1.5
    return 1.0


def survive_cap(dfn, dmg):
    """Sturdy / Focus Sash: a mon at full HP survives an otherwise-lethal hit
    with 1 HP. Focus Sash is single-use and is consumed on the save."""
    if dfn.hp < dfn.maxhp or dmg < dfn.hp:
        return dmg
    if dfn.ability == 'STURDY':
        return dfn.hp - 1
    if dfn.item == 'FOCUS_SASH':
        dfn.item = None
        return dfn.hp - 1
    return dmg


# ---- variable/fixed-power moves -----------------------------------------------
# moves.json stores these with power=1 (the ROM computes the real value at
# battle time). LEVEL_DAMAGE/SUPER_FANG bypass the stat formula entirely
# (fixed/fractional damage); the rest plug a computed power into the normal
# formula. Low Kick is approximated with a fixed mid power since this ROM's
# extracted data has no per-species weight to drive the real weight-class
# table -- documented limitation, not a faithful port.
def _fixed_damage(move, att, dfn):
    e = move['effect']
    if e == 'EFFECT_LEVEL_DAMAGE':
        return 50  # = attacker's level
    if e == 'EFFECT_SUPER_FANG':
        return max(1, dfn.hp // 2)
    return None


def effective_power(move, att, dfn):
    e = move['effect']
    if e == 'EFFECT_GYRO_BALL':
        return min(150, max(1, int(25 * dfn.stat('spe') / max(att.stat('spe'), 1)) + 1))
    if e == 'EFFECT_LOW_KICK':
        return 80
    if e == 'EFFECT_REVERSAL':
        frac = att.hp / att.maxhp
        if frac >= 0.6875: return 20
        if frac >= 0.3542: return 40
        if frac >= 0.2083: return 80
        if frac >= 0.1042: return 100
        if frac >= 0.0417: return 150
        return 200
    if e == 'EFFECT_RETURN':
        return 102  # max happiness, matching the uniform max-build baseline
    if e == 'EFFECT_MAGNITUDE':
        return 71   # average power across the magnitude 4-10 roll
    if e == 'EFFECT_CONDITIONAL_BOOST' and att.status not in (None, 'slp', 'frz'):
        return move['power'] * 2   # Facade
    return move['power']


def _damage_terms(att, dfn, move, chart, weather=None, moving_last=False):
    """Shared atk/def/STAB/multiplier setup for move_damage/expected_damage."""
    mt = abilities.effective_type(att.ability, move)
    eff = type_eff(att, dfn, move, chart)
    is_stab = abilities.gives_stab(att.ability, mt, att.types)
    amult = abilities.attacker_mult(att.ability, move, mt,
                                    statused=att.status is not None,
                                    hp_frac=att.hp / att.maxhp, weather=weather,
                                    moving_last=moving_last, eff=eff)
    ign_atk = dfn.ability == 'UNAWARE'      # defender ignores attacker's boosts
    ign_def = att.ability == 'UNAWARE'      # attacker ignores defender's boosts
    if move['cat'] == 'PHYSICAL':
        a = att.stat('atk', ignore_stage=ign_atk) * amult
        d = dfn.stat('defe', ignore_stage=ign_def)
        if att.status == 'brn' and att.ability != 'GUTS' and move['effect'] != 'EFFECT_CONDITIONAL_BOOST':
            a *= 0.5
        if att.item == 'CHOICE_BAND':
            a *= items.CHOICE_STAT_MULT
        if dfn.ability == 'MARVEL_SCALE' and dfn.status:
            d *= 1.5
    else:
        a = att.stat('spa', ignore_stage=ign_atk) * amult
        d = dfn.stat('spd', ignore_stage=ign_def)
        if att.item == 'CHOICE_SPECS':
            a *= items.CHOICE_STAT_MULT
    d *= _sand_spdef(dfn, move, weather)
    stab = abilities.stab_value(att.ability) if is_stab else 1.0
    dmg_mult = abilities.weather_dmg_mult(weather, mt)
    dmg_mult *= abilities.defender_mult(dfn.ability, move, mt, eff, dfn.hp / dfn.maxhp)
    if att.item == 'LIFE_ORB':
        dmg_mult *= items.LIFE_ORB_DMG_MULT
    return eff, a, d, stab, dmg_mult


def move_damage(att, dfn, move, chart, rng, weather=None, moving_last=False):
    """Expected/rolled damage for a damaging move att->dfn (0 if non-damaging/immune)."""
    if move['cat'] == 'STATUS' or move['power'] <= 0:
        return 0, 1.0
    eff = type_eff(att, dfn, move, chart)
    if eff == 0.0:
        return 0, 0.0
    hits = MULTI.get(move['effect'], 1)
    fixed = _fixed_damage(move, att, dfn)
    if fixed is not None:
        return int(fixed) * hits, eff
    power = effective_power(move, att, dfn)
    eff, a, d, stab, dmg_mult = _damage_terms(att, dfn, move, chart, weather, moving_last)
    base = ((((2 * 50) // 5 + 2) * power * a) // d) // 50 + 2
    roll = rng.uniform(0.85, 1.0)
    return int(base * stab * eff * dmg_mult * roll) * hits, eff


def expected_damage(att, dfn, move, chart, weather=None):
    """Deterministic average damage, for AI scoring (no RNG)."""
    if move['cat'] == 'STATUS' or move['power'] <= 0:
        return 0, type_eff(att, dfn, move, chart) if move['power'] else 1.0
    eff = type_eff(att, dfn, move, chart)
    if eff == 0.0:
        return 0, 0.0
    hits = MULTI.get(move['effect'], 1)
    acc = 1.0 if move['acc'] < 0 else move['acc'] / 100.0
    fixed = _fixed_damage(move, att, dfn)
    if fixed is not None:
        return int(fixed * acc) * hits, eff
    power = effective_power(move, att, dfn)
    eff, a, d, stab, dmg_mult = _damage_terms(att, dfn, move, chart, weather)
    base = ((((2 * 50) // 5 + 2) * power * a) // d) // 50 + 2
    return int(base * stab * eff * dmg_mult * 0.925) * hits * acc, eff


# ---- heuristic AI ------------------------------------------------------------
def _max_expected_damage(attacker, defender, moves, chart, weather):
    """Best expected damage `attacker` can deal `defender` with a damaging move."""
    best = 0.0
    for mv in attacker.moves:
        m = moves[mv]
        if m['cat'] == 'STATUS' or m['power'] <= 0:
            continue
        dmg, _ = expected_damage(attacker, defender, m, chart, weather)
        if dmg > best:
            best = dmg
    return best


def choose_move(side, foe, moves, chart, weather=None, rng=random):
    """Pick a move with a 1-ply look at the foe's likely response.

    A pure max-damage picker can't tell a fast revenge-killer (KOs before it's
    hit) from a frail flailer, or a durable waller (survives to status/heal/set
    up) from a mon that just dies. So we gate utility on survival: estimate
    whether the active will still be standing next turn, and only value
    setup/status/heal/hazards when it will. This stops the bot from dragging
    support and speed-control mons down to greedy-attacker behaviour."""
    att, dfn = side.mon, foe.mon
    if att.locked_move is not None:
        return att.locked_move

    best_dmg_i, best_dmg = 0, -1.0
    for i, mv in enumerate(att.moves):
        m = moves[mv]
        if m['cat'] == 'STATUS' or m['power'] <= 0:
            continue
        dmg, _ = expected_damage(att, dfn, m, chart, weather)
        if dmg > best_dmg:
            best_dmg, best_dmg_i = dmg, i
    if best_dmg < 0:
        best_dmg = 0.0

    foe_dmg = _max_expected_damage(dfn, att, moves, chart, weather)
    i_outspeed = att.stat('spe', weather) > dfn.stat('spe', weather)
    i_ko = best_dmg >= dfn.hp
    foe_ko = foe_dmg >= att.hp
    # "doomed": the foe is expected to faint me next turn whatever I do -- i.e.
    # it KOs me and I can't KO it first. No point setting up / statusing / healing.
    doomed = foe_ko and not (i_ko and i_outspeed)

    # If I can KO this turn, just do it (revenge-killing a faster glass cannon,
    # or trading up when I'm slower -- swinging is right either way).
    if i_ko:
        return best_dmg_i

    util = []                              # (priority_score, index)
    for i, mv in enumerate(att.moves):
        e = moves[mv]['effect']
        if e in HEAL_EFFECTS and att.hp < att.maxhp * 0.6 and not doomed:
            # heal more eagerly the lower I am, but only if it isn't futile
            util.append((3.0 + (att.maxhp - att.hp) / att.maxhp, i))
        elif e in BOOST and not doomed and foe_dmg < att.hp * 0.5:
            # set up only when I clearly survive; sweeping is better if I'm fast
            util.append((2.0 + (0.6 if i_outspeed else 0.0), i))
        elif e in INFLICT and dfn.status is None and not doomed:
            if INFLICT[e] == 'slp' and SLEEP_CLAUSE and foe.slept_by_foe:
                continue
            st = INFLICT[e]
            score = 1.5
            if st in ('slp', 'par') and not i_outspeed:
                score += 1.0      # neutralises a foe that would otherwise outrun me
            elif st in ('tox', 'psn', 'brn'):
                score += 0.4      # chip a bulky foe I can't break quickly
            util.append((score, i))
        elif (e == 'EFFECT_LEECH_SEED' and not dfn.seeded
              and 'GRASS' not in dfn.types and not doomed):
            util.append((1.6, i))
        elif e in ('EFFECT_SPIKES', 'EFFECT_TOXIC_SPIKES') and not doomed:
            util.append((1.2, i))

    if util:
        util.sort(reverse=True)
        score, idx = util[0]
        # a damaging move that takes a big chunk still competes with weak utility
        dmg_frac = best_dmg / max(dfn.hp, 1)
        if dmg_frac < 0.5 or score >= 2.8:
            if rng.random() < 0.85:        # a little noise so it isn't robotic
                return idx
    return best_dmg_i


def matchup_score(mon, foe, moves, chart):
    """How good is `mon` against active `foe`? offense - defense, for switching.
    Respects ability immunities both ways (e.g. a Levitate mon sees a Ground
    attacker as harmless and switches in; an attacker sees a Water move into a
    Water Absorb foe as worthless)."""
    off = 0.0
    for mv in mon.moves:
        m = moves[mv]
        if m['cat'] != 'STATUS' and m['power'] > 0:
            e = 0.0 if abilities.defending_immune(foe.ability, m) else type_mult(m['type'], foe.types, chart)
            off = max(off, e * (STAB if m['type'] in mon.types else 1.0))
    deff = 0.0
    for mv in foe.moves:
        m = moves[mv]
        if m['cat'] != 'STATUS' and m['power'] > 0:
            e = 0.0 if abilities.defending_immune(mon.ability, m) else type_mult(m['type'], mon.types, chart)
            deff = max(deff, e)
    return off - deff


def choose_switch(side, foe, moves, chart, forced, rng=random):
    """Pick a teammate index to send in. Returns index, or None to stay."""
    alive = [i for i in side.alive_indices() if forced or i != side.active]
    if not alive:
        return None
    # trapping abilities block a voluntary switch (a forced post-faint switch
    # still happens -- the trapped mon already fainted)
    if not forced and abilities.traps(foe.mon.ability, side.mon.types, side.mon.ability):
        return None
    best_i, best = None, -99.0
    for i in alive:
        s = matchup_score(side.team[i], foe.mon, moves, chart)
        if s > best:
            best, best_i = s, i
    if forced:
        return best_i
    # voluntary switch only when current matchup is clearly bad and a teammate is clearly better
    cur = matchup_score(side.mon, foe.mon, moves, chart)
    if best - cur >= 2.0 and cur < 0 and rng.random() < 0.5:
        return best_i
    return None


# ---- per-turn mechanics ------------------------------------------------------
def apply_switch(side, idx, chart, foe_side=None):
    # switch-out abilities act on the outgoing mon (only on a real switch)
    out = side.mon
    if idx != side.active and not out.fainted:
        if out.ability == 'REGENERATOR':
            out.hp = min(out.maxhp, out.hp + out.maxhp / 3)
        elif out.ability == 'NATURAL_CURE':
            out.status, out.sleep, out.tox = None, 0, 0
    out.reset_volatile()
    side.active = idx
    m = side.mon
    grounded = 'FLYING' not in m.types and m.ability != 'LEVITATE'
    # entry hazards (Magic Guard ignores the chip; airborne mons dodge Spikes)
    if side.spikes and grounded and m.ability != 'MAGIC_GUARD':
        m.hp -= m.maxhp * [0, 1/8, 1/6, 1/4][side.spikes]
    if side.tspikes and grounded:
        if 'POISON' in m.types:
            side.tspikes = 0               # absorbed
        elif 'STEEL' not in m.types and m.status is None:
            st = 'tox' if side.tspikes >= 2 else 'psn'
            if abilities.can_be_statused(m.ability, st):
                m.status = st
                if st == 'tox':
                    m.tox = 0
    if m.hp <= 0:
        m.fainted = True
        return
    if foe_side is not None and not foe_side.mon.fainted:
        on_switch_in(m, foe_side.mon)


def on_switch_in(m, foe):
    """Switch-in abilities: Intimidate (with Defiant/Competitive backlash and
    Clear Body-style prevention) and Download."""
    if m.ability == 'INTIMIDATE':
        if not abilities.prevents_drop(foe.ability, 'atk'):
            foe.stage['atk'] = max(-6, foe.stage['atk'] - 1)
        if foe.ability == 'DEFIANT':
            foe.stage['atk'] = min(6, foe.stage['atk'] + 2)
        elif foe.ability == 'COMPETITIVE':
            foe.stage['spa'] = min(6, foe.stage['spa'] + 2)
    elif m.ability == 'DOWNLOAD':
        if foe.stat('defe') <= foe.stat('spd'):
            m.stage['atk'] = min(6, m.stage['atk'] + 1)
        else:
            m.stage['spa'] = min(6, m.stage['spa'] + 1)


SAND_IMMUNE = {'ROCK', 'GROUND', 'STEEL'}


def end_of_turn(mon, foe_side, weather=None, rng=None):
    """Residual damage/heal + end-of-turn abilities. Returns False if mon faints.
    Magic Guard zeroes all indirect chip; Poison Heal turns poison into healing."""
    if mon.fainted:
        return False
    guard = mon.ability == 'MAGIC_GUARD'
    if mon.status in ('brn', 'psn'):
        if mon.ability == 'POISON_HEAL' and mon.status == 'psn':
            mon.hp = min(mon.maxhp, mon.hp + mon.maxhp / 8)
        elif not guard:
            mon.hp -= mon.maxhp / 8
    elif mon.status == 'tox':
        mon.tox += 1
        if mon.ability == 'POISON_HEAL':
            mon.hp = min(mon.maxhp, mon.hp + mon.maxhp / 8)
        elif not guard:
            mon.hp -= mon.maxhp * mon.tox / 16
    if mon.seeded and not mon.fainted and not guard:
        drain = min(mon.maxhp / 8, max(mon.hp, 0))
        mon.hp -= drain
    # weather residuals
    if weather == 'sand' and not guard and not (SAND_IMMUNE & set(mon.types)):
        mon.hp -= mon.maxhp / 16
    if weather == 'rain' and mon.ability in ('RAIN_DISH', 'DRY_SKIN'):
        mon.hp = min(mon.maxhp, mon.hp + mon.maxhp / 8 if mon.ability == 'DRY_SKIN'
                     else mon.hp + mon.maxhp / 16)
    if weather == 'hail' and mon.ability == 'ICE_BODY':
        mon.hp = min(mon.maxhp, mon.hp + mon.maxhp / 16)
    if weather == 'sun' and mon.ability in ('SOLAR_POWER', 'DRY_SKIN') and not guard:
        mon.hp -= mon.maxhp / 8
    # Speed Boost / Shed Skin
    if mon.ability == 'SPEED_BOOST':
        mon.stage['spe'] = min(6, mon.stage['spe'] + 1)
    if mon.ability == 'SHED_SKIN' and mon.status and rng and rng.random() < 1/3:
        mon.status, mon.sleep, mon.tox = None, 0, 0
    if mon.hp <= 0:
        mon.fainted = True
        return False
    if mon.item == 'LEFTOVERS' and mon.hp < mon.maxhp:
        mon.hp = min(mon.maxhp, mon.hp + mon.maxhp * items.LEFTOVERS_HEAL_FRAC)
    # self-status orbs: activate at end of turn if still unstatused (so the
    # status itself doesn't deal damage until the following end_of_turn)
    if mon.status is None:
        if mon.item == 'TOXIC_ORB' and abilities.can_be_statused(mon.ability, 'tox'):
            mon.status, mon.tox = 'tox', 0
        elif mon.item == 'FLAME_ORB' and abilities.can_be_statused(mon.ability, 'brn'):
            mon.status = 'brn'
    return True


def on_ko(att):
    """KO-triggered self-boost abilities."""
    a = att.ability
    if a in ('MOXIE', 'CHILLING_NEIGH'):
        att.stage['atk'] = min(6, att.stage['atk'] + 1)
    elif a in ('GRIM_NEIGH', 'SOUL_HEART'):
        att.stage['spa'] = min(6, att.stage['spa'] + 1)
    elif a == 'BEAST_BOOST':
        k = 'atk' if att.base['atk'] >= att.base['spa'] else 'spa'
        att.stage[k] = min(6, att.stage[k] + 1)


def on_hit(att, dfn, move, rng):
    """Contact-punish, on-hit status, and hit-reaction stat abilities."""
    contact = move.get('contact')
    if dfn.fainted:
        if dfn.ability == 'AFTERMATH' and contact and att.ability != 'MAGIC_GUARD':
            att.hp -= att.maxhp / 4
            if att.hp <= 0:
                att.fainted = True
        return
    da, mt = dfn.ability, move['type']
    if contact:
        if da in ('ROUGH_SKIN', 'IRON_BARBS') and att.ability != 'MAGIC_GUARD':
            att.hp -= att.maxhp / 8
            if att.hp <= 0:
                att.fainted = True
        elif att.status is None and rng.random() < 0.3:
            st = {'FLAME_BODY': 'brn', 'STATIC': 'par', 'POISON_POINT': 'psn'}.get(da)
            if da == 'EFFECT_SPORE':
                st = rng.choice(['par', 'psn'])
            if st and abilities.can_be_statused(att.ability, st):
                att.status = st
                if st == 'tox':
                    att.tox = 0
        if da in ('TANGLING_HAIR', 'GOOEY') and not abilities.prevents_drop(att.ability, 'spe'):
            att.stage['spe'] = max(-6, att.stage['spe'] - 1)
        if att.ability == 'POISON_TOUCH' and dfn.status is None and rng.random() < 0.3 \
                and abilities.can_be_statused(dfn.ability, 'psn'):
            dfn.status = 'psn'
    if da == 'JUSTIFIED' and mt == 'DARK':
        dfn.stage['atk'] = min(6, dfn.stage['atk'] + 1)
    elif da == 'RATTLED' and mt in ('BUG', 'DARK', 'GHOST'):
        dfn.stage['spe'] = min(6, dfn.stage['spe'] + 1)
    elif da == 'STAMINA':
        dfn.stage['defe'] = min(6, dfn.stage['defe'] + 1)
    elif da == 'WEAK_ARMOR' and move['cat'] == 'PHYSICAL':
        dfn.stage['defe'] = max(-6, dfn.stage['defe'] - 1)
        dfn.stage['spe'] = min(6, dfn.stage['spe'] + 2)
    elif da == 'WATER_COMPACTION' and mt == 'WATER':
        dfn.stage['defe'] = min(6, dfn.stage['defe'] + 2)


def perform(att_side, dfn_side, moves, chart, rng, weather=None, moving_last=False):
    """Execute the active mon's chosen action for att_side against dfn_side."""
    att, dfn = att_side.mon, dfn_side.mon

    # pre-move status gates
    if att.status == 'frz':
        if rng.random() < 0.2:
            att.status = None
        else:
            return
    if att.status == 'slp':
        att.sleep -= 1
        if att.sleep <= 0:
            att.status = None
        else:
            return
    if att.status == 'par' and rng.random() < 0.25:
        return
    if att.confused > 0:
        att.confused -= 1
        if rng.random() < 0.5:             # hurt self in confusion (approx)
            att.hp -= att.maxhp / 8
            if att.hp <= 0:
                att.fainted = True
            return

    idx = choose_move(att_side, dfn_side, moves, chart, weather, rng)
    mv = att.moves[idx]
    m = moves[mv]
    if att.item in CHOICE_ITEMS and m['cat'] != 'STATUS' and m['power'] > 0:
        att.locked_move = idx     # locks in on use, regardless of hit/miss

    # accuracy
    if m['acc'] >= 0 and rng.random() > m['acc'] / 100.0:
        return

    e = m['effect']
    if e == 'EFFECT_EXPLOSION':
        dmg, _ = move_damage(att, dfn, m, chart, rng, weather)
        dfn.hp -= survive_cap(dfn, dmg * 2)
        att.hp = 0
        att.fainted = True
        if dfn.hp <= 0:
            dfn.fainted = True
        return

    if m['cat'] != 'STATUS' and m['power'] > 0:
        dmg, eff = move_damage(att, dfn, m, chart, rng, weather, moving_last)
        pre_hp = dfn.hp
        dfn.hp -= survive_cap(dfn, dmg)
        if dfn.ability == 'BERSERK' and dfn.hp > 0 and pre_hp >= dfn.maxhp / 2 > dfn.hp:
            dfn.stage['spa'] = min(6, dfn.stage['spa'] + 1)
        if att.item == 'LIFE_ORB' and dmg > 0 and att.ability != 'MAGIC_GUARD':
            att.hp -= att.maxhp * items.LIFE_ORB_RECOIL_FRAC
            if att.hp <= 0:
                att.fainted = True
        if dfn.hp <= 0:
            dfn.fainted = True
            on_ko(att)
            on_hit(att, dfn, m, rng)       # Aftermath etc. on a contact KO
            return
        # on-hit secondary status (gated by the target's ability)
        if e in ONHIT and dfn.status is None and rng.random() < m['chance'] / 100.0:
            st = ONHIT[e]
            if st != 'slp' and abilities.can_be_statused(dfn.ability, st, weather):
                dfn.status = st
                if st == 'tox':
                    dfn.tox = 0
        if e in RECOIL_EFFECTS and att.ability not in ('ROCK_HEAD', 'MAGIC_GUARD'):
            att.hp -= dmg / 3
            if att.hp <= 0:
                att.fainted = True
        on_hit(att, dfn, m, rng)
        return

    # ---- status / utility moves ----
    if e in BOOST:
        for k, d in BOOST[e].items():
            delta = abilities.transform_self_change(att.ability, d)
            att.stage[k] = max(-6, min(6, att.stage.get(k, 0) + delta))
        return
    if e == 'EFFECT_BELLY_DRUM':
        att.stage['atk'] = -6 if att.ability == 'CONTRARY' else 6
        att.hp -= att.maxhp / 2
        if att.hp <= 0:
            att.fainted = True
        return
    if e in DROP:
        for k, d in DROP[e].items():
            if k not in dfn.stage or abilities.prevents_drop(dfn.ability, k):
                continue
            delta = -d if dfn.ability == 'CONTRARY' else (d * 2 if dfn.ability == 'SIMPLE' else d)
            dfn.stage[k] = max(-6, min(6, dfn.stage[k] + delta))
            if d < 0 and dfn.ability == 'DEFIANT':
                dfn.stage['atk'] = min(6, dfn.stage['atk'] + 2)
            elif d < 0 and dfn.ability == 'COMPETITIVE':
                dfn.stage['spa'] = min(6, dfn.stage['spa'] + 2)
        return
    if e in INFLICT and dfn.status is None:
        st = INFLICT[e]
        if st == 'slp':
            if SLEEP_CLAUSE and dfn_side.slept_by_foe:
                return
            if not abilities.can_be_statused(dfn.ability, 'slp', weather):
                return
            dfn.status = 'slp'
            dfn.sleep = rng.randint(1, 3)
            dfn_side.slept_by_foe = True
        elif st == 'cnf':
            if abilities.can_be_statused(dfn.ability, 'cnf'):
                dfn.confused = rng.randint(2, 4)
        elif abilities.can_be_statused(dfn.ability, st, weather):
            dfn.status = st
            if st == 'tox':
                dfn.tox = 0
            # Synchronize bounces the status back to the source
            if dfn.ability == 'SYNCHRONIZE' and st in ('psn', 'tox', 'par', 'brn') \
                    and att.status is None and abilities.can_be_statused(att.ability, st):
                att.status = st
                if st == 'tox':
                    att.tox = 0
        return
    if e in HEAL_EFFECTS:
        att.hp = min(att.maxhp, att.hp + att.maxhp / 2)
        return
    if e == 'EFFECT_LEECH_SEED':
        dfn.seeded = True
        return
    if e == 'EFFECT_SPIKES':
        dfn_side.spikes = min(3, dfn_side.spikes + 1)
        return
    if e == 'EFFECT_TOXIC_SPIKES':
        dfn_side.tspikes = min(2, dfn_side.tspikes + 1)
        return
    # unmodelled status move: no-op


def current_weather(a_side, b_side):
    """Weather is up while an un-fainted active mon holds a setter ability
    (modern 'ability weather': persists while its owner is on the field). If
    both sides set weather, the A-side's takes precedence -- a rare tie that
    barely affects aggregate stats."""
    for s in (a_side, b_side):
        if not s.mon.fainted:
            w = abilities.WEATHER_SETTERS.get(s.mon.ability)
            if w:
                return w
    return None


def run_battle(team_a, team_b, moves, chart, seed=None):
    """Run one 6v6. Returns 0 if side A wins, 1 if B, -1 on turn-limit draw."""
    rng = random.Random(seed)
    A, B = Side([Pmon(*t) for t in team_a]), Side([Pmon(*t) for t in team_b])
    apply_switch(A, 0, chart, B)
    apply_switch(B, 0, chart, A)

    for _ in range(MAX_TURNS):
        # ---- switching decisions (forced first if a side's active fainted) ----
        for s, foe in ((A, B), (B, A)):
            if s.mon.fainted:
                nxt = choose_switch(s, foe, moves, chart, forced=True, rng=rng)
                if nxt is not None:
                    apply_switch(s, nxt, chart, foe)
        if not A.alive_indices():
            return 1
        if not B.alive_indices():
            return 0
        for s, foe in ((A, B), (B, A)):
            if not s.mon.fainted:
                nxt = choose_switch(s, foe, moves, chart, forced=False, rng=rng)
                if nxt is not None:
                    apply_switch(s, nxt, chart, foe)

        weather = current_weather(A, B)

        # ---- order by (priority [+ ability bonus], speed) ----
        ia = choose_move(A, B, moves, chart, weather, rng)
        ib = choose_move(B, A, moves, chart, weather, rng)
        ma, mb = moves[A.mon.moves[ia]], moves[B.mon.moves[ib]]
        pa = ma['prio'] + abilities.priority_bonus(A.mon.ability, ma, A.mon.hp / A.mon.maxhp)
        pb = mb['prio'] + abilities.priority_bonus(B.mon.ability, mb, B.mon.hp / B.mon.maxhp)
        sa, sb = A.mon.stat('spe', weather), B.mon.stat('spe', weather)
        a_first = (pa, sa) > (pb, sb) or ((pa, sa) == (pb, sb) and rng.random() < 0.5)
        order = (A, B) if a_first else (B, A)

        for i, (s, foe) in enumerate((order, order[::-1])):
            if s.mon.fainted or foe.mon.fainted:
                continue
            perform(s, foe, moves, chart, rng, weather, moving_last=(i == 1))
        # ---- residuals (recompute weather: a faint may have removed the setter) ----
        weather = current_weather(A, B)
        for s, foe in ((A, B), (B, A)):
            end_of_turn(s.mon, foe, weather, rng)
        if not A.alive_indices():
            return 1
        if not B.alive_indices():
            return 0
    return -1
