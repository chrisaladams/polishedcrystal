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
SLEEP_CLAUSE = True          # mirror the shipped Sleep Clause
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

    def stat(self, key, weather=None):
        v = self.base[key] * stage_mult(self.stage.get(key, 0))
        if key == 'spe':
            if self.status == 'par':
                v *= 0.25
            if self.item == 'CHOICE_SCARF':
                v *= items.CHOICE_SCARF_SPEED_MULT
            v *= abilities.weather_speed_mult(self.ability, weather)
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
def eff_mult(move, dfn, chart):
    """Type effectiveness including the defender's ability (Levitate-style
    immunity -> 0, Thick Fat-style halving -> 0.5)."""
    return (type_mult(move['type'], dfn.types, chart)
            * abilities.defending_type_mult(dfn.ability, move['type']))


def _sand_spdef(dfn, move, weather):
    """Rock-types get x1.5 Sp.Def in a sandstorm."""
    if weather == 'sand' and move['cat'] == 'SPECIAL' and 'ROCK' in dfn.types:
        return 1.5
    return 1.0


def _damage_terms(att, dfn, move, chart, weather=None):
    """Shared atk/def/STAB/multiplier setup for move_damage/expected_damage."""
    eff = eff_mult(move, dfn, chart)
    is_stab = move['type'] in att.types
    atk_mult, dmg_mult = abilities.offense_multipliers(att.ability, move, is_stab)
    if move['cat'] == 'PHYSICAL':
        a, d = att.stat('atk') * atk_mult, dfn.stat('defe')
        if att.status == 'brn':
            a *= 0.5
        if att.item == 'CHOICE_BAND':
            a *= items.CHOICE_STAT_MULT
    else:
        a, d = att.stat('spa') * atk_mult, dfn.stat('spd')
        if att.item == 'CHOICE_SPECS':
            a *= items.CHOICE_STAT_MULT
    d *= _sand_spdef(dfn, move, weather)
    stab = abilities.stab_mult(att.ability, is_stab)
    dmg_mult *= abilities.weather_dmg_mult(weather, move['type'])
    if att.item == 'LIFE_ORB':
        dmg_mult *= items.LIFE_ORB_DMG_MULT
    return eff, a, d, stab, dmg_mult


def move_damage(att, dfn, move, chart, rng, weather=None):
    """Expected/rolled damage for a damaging move att->dfn (0 if non-damaging/immune)."""
    if move['cat'] == 'STATUS' or move['power'] <= 0:
        return 0, 1.0
    eff = eff_mult(move, dfn, chart)
    if eff == 0.0:
        return 0, 0.0
    eff, a, d, stab, dmg_mult = _damage_terms(att, dfn, move, chart, weather)
    base = ((((2 * 50) // 5 + 2) * move['power'] * a) // d) // 50 + 2
    roll = rng.uniform(0.85, 1.0)
    hits = MULTI.get(move['effect'], 1)
    return int(base * stab * eff * dmg_mult * roll) * hits, eff


def expected_damage(att, dfn, move, chart, weather=None):
    """Deterministic average damage, for AI scoring (no RNG)."""
    if move['cat'] == 'STATUS' or move['power'] <= 0:
        return 0, eff_mult(move, dfn, chart) if move['power'] else 1.0
    eff = eff_mult(move, dfn, chart)
    if eff == 0.0:
        return 0, 0.0
    eff, a, d, stab, dmg_mult = _damage_terms(att, dfn, move, chart, weather)
    base = ((((2 * 50) // 5 + 2) * move['power'] * a) // d) // 50 + 2
    hits = MULTI.get(move['effect'], 1)
    acc = 1.0 if move['acc'] < 0 else move['acc'] / 100.0
    return int(base * stab * eff * dmg_mult * 0.925) * hits * acc, eff


# ---- heuristic AI ------------------------------------------------------------
def choose_move(side, foe, moves, chart, weather=None):
    """Return the index into att.moves the heuristic AI plays this turn."""
    att, dfn = side.mon, foe.mon
    if att.locked_move is not None:
        return att.locked_move
    best_dmg_i, best_dmg = 0, -1.0
    util = []                              # (priority_score, index)
    for i, mv in enumerate(att.moves):
        m = moves[mv]
        dmg, eff = expected_damage(att, dfn, m, chart, weather)
        if dmg > best_dmg:
            best_dmg, best_dmg_i = dmg, i
        e = m['effect']
        # ---- utility scoring (only if it doesn't already KO) ----
        if e in HEAL_EFFECTS and att.hp < att.maxhp * 0.55:
            util.append((3.0, i))
        elif e in BOOST and att.hp > att.maxhp * 0.6:
            # set up only when reasonably safe (foe unlikely to OHKO)
            util.append((2.0, i))
        elif e in INFLICT and dfn.status is None:
            # status the foe -- great for walls; require it to be allowed
            if not (INFLICT[e] == 'slp' and SLEEP_CLAUSE and foe.slept_by_foe):
                util.append((1.5, i))
        elif e == 'EFFECT_LEECH_SEED' and not dfn.seeded and 'GRASS' not in dfn.types:
            util.append((1.4, i))
        elif e in ('EFFECT_SPIKES', 'EFFECT_TOXIC_SPIKES'):
            util.append((1.2, i))

    # If best damaging move OHKOs, just attack.
    if best_dmg >= dfn.hp:
        return best_dmg_i
    # Otherwise weigh utility vs chip damage.
    if util:
        util.sort(reverse=True)
        score, idx = util[0]
        # damage worth a chunk of the foe still competes with weak utility
        dmg_frac = best_dmg / max(dfn.hp, 1)
        if dmg_frac < 0.45 or score >= 2.5:
            # randomise a little so setup/status isn't robotic
            if random.random() < 0.8:
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
            off = max(off, type_mult(m['type'], foe.types, chart) *
                      abilities.defending_type_mult(foe.ability, m['type']) *
                      (STAB if m['type'] in mon.types else 1.0))
    deff = 0.0
    for mv in foe.moves:
        m = moves[mv]
        if m['cat'] != 'STATUS' and m['power'] > 0:
            deff = max(deff, type_mult(m['type'], mon.types, chart) *
                       abilities.defending_type_mult(mon.ability, m['type']))
    return off - deff


def choose_switch(side, foe, moves, chart, forced):
    """Pick a teammate index to send in. Returns index, or None to stay."""
    alive = [i for i in side.alive_indices() if forced or i != side.active]
    if not alive:
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
    if best - cur >= 2.0 and cur < 0 and random.random() < 0.5:
        return best_i
    return None


# ---- per-turn mechanics ------------------------------------------------------
def apply_switch(side, idx, chart, foe_side=None):
    side.mon.reset_volatile()
    side.active = idx
    m = side.mon
    # entry hazards
    if side.spikes and 'FLYING' not in m.types:
        m.hp -= m.maxhp * [0, 1/8, 1/6, 1/4][side.spikes]
    if side.tspikes and 'FLYING' not in m.types:
        if 'POISON' in m.types:
            side.tspikes = 0               # absorbed
        elif 'STEEL' not in m.types and m.status is None:
            m.status = 'tox' if side.tspikes >= 2 else 'psn'
    if m.hp <= 0:
        m.fainted = True
        return
    # Intimidate: drop the opposing active mon's Attack one stage on switch-in
    if m.ability == 'INTIMIDATE' and foe_side is not None and not foe_side.mon.fainted:
        f = foe_side.mon
        f.stage['atk'] = max(-6, f.stage['atk'] - 1)


SAND_IMMUNE = {'ROCK', 'GROUND', 'STEEL'}


def end_of_turn(mon, foe_side, weather=None):
    """Residual damage/heal. Returns False if mon faints."""
    if mon.fainted:
        return False
    if mon.status == 'brn' or mon.status == 'psn':
        mon.hp -= mon.maxhp / 8
    elif mon.status == 'tox':
        mon.tox += 1
        mon.hp -= mon.maxhp * mon.tox / 16
    if mon.seeded and not mon.fainted:
        drain = min(mon.maxhp / 8, max(mon.hp, 0))
        mon.hp -= drain
    if weather == 'sand' and not (SAND_IMMUNE & set(mon.types)):
        mon.hp -= mon.maxhp / 16
    if mon.hp <= 0:
        mon.fainted = True
        return False
    if mon.item == 'LEFTOVERS' and mon.hp < mon.maxhp:
        mon.hp = min(mon.maxhp, mon.hp + mon.maxhp * items.LEFTOVERS_HEAL_FRAC)
    return True


def perform(att_side, dfn_side, moves, chart, rng, weather=None):
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

    idx = choose_move(att_side, dfn_side, moves, chart, weather)
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
        dfn.hp -= dmg * 2
        att.hp = 0
        att.fainted = True
        if dfn.hp <= 0:
            dfn.fainted = True
        return

    if m['cat'] != 'STATUS' and m['power'] > 0:
        dmg, eff = move_damage(att, dfn, m, chart, rng, weather)
        dfn.hp -= dmg
        if att.item == 'LIFE_ORB' and dmg > 0:
            att.hp -= att.maxhp * items.LIFE_ORB_RECOIL_FRAC
            if att.hp <= 0:
                att.fainted = True
        if dfn.hp <= 0:
            dfn.fainted = True
            return
        # on-hit secondaries
        if e in ONHIT and dfn.status is None and rng.random() < m['chance'] / 100.0:
            st = ONHIT[e]
            if not (st == 'slp'):          # on-hit sleep doesn't exist; guard anyway
                dfn.status = st
                if st == 'tox':
                    dfn.tox = 0
        if e == 'EFFECT_FLINCH_HIT' and rng.random() < m['chance'] / 100.0:
            pass                            # flinch handled by turn order in battle loop (approx: ignore)
        if e in RECOIL_EFFECTS:
            att.hp -= dmg / 3
            if att.hp <= 0:
                att.fainted = True
        return

    # ---- status / utility moves ----
    if e in BOOST:
        for k, d in BOOST[e].items():
            att.stage[k] = max(-6, min(6, att.stage.get(k, 0) + d))
        if e == 'EFFECT_SHELL_SMASH':
            pass
        return
    if e == 'EFFECT_BELLY_DRUM':
        att.stage['atk'] = 6
        att.hp -= att.maxhp / 2
        if att.hp <= 0:
            att.fainted = True
        return
    if e in DROP:
        for k, d in DROP[e].items():
            if k in dfn.stage:
                dfn.stage[k] = max(-6, min(6, dfn.stage[k] + d))
        return
    if e in INFLICT and dfn.status is None:
        st = INFLICT[e]
        if st == 'slp':
            if SLEEP_CLAUSE and dfn_side.slept_by_foe:
                return
            dfn.status = 'slp'
            dfn.sleep = rng.randint(1, 3)
            dfn_side.slept_by_foe = True
        elif st == 'cnf':
            dfn.confused = rng.randint(2, 4)
        else:
            dfn.status = st
            if st == 'tox':
                dfn.tox = 0
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
                nxt = choose_switch(s, foe, moves, chart, forced=True)
                if nxt is not None:
                    apply_switch(s, nxt, chart, foe)
        if not A.alive_indices():
            return 1
        if not B.alive_indices():
            return 0
        for s, foe in ((A, B), (B, A)):
            if not s.mon.fainted:
                nxt = choose_switch(s, foe, moves, chart, forced=False)
                if nxt is not None:
                    apply_switch(s, nxt, chart, foe)

        weather = current_weather(A, B)

        # ---- order by (priority of chosen move, speed) ----
        ia = choose_move(A, B, moves, chart, weather)
        ib = choose_move(B, A, moves, chart, weather)
        pa, pb = moves[A.mon.moves[ia]]['prio'], moves[B.mon.moves[ib]]['prio']
        sa, sb = A.mon.stat('spe', weather), B.mon.stat('spe', weather)
        a_first = (pa, sa) > (pb, sb) or ((pa, sa) == (pb, sb) and rng.random() < 0.5)
        order = (A, B) if a_first else (B, A)

        for s, foe in (order, order[::-1]):
            if s.mon.fainted or foe.mon.fainted:
                continue
            perform(s, foe, moves, chart, rng, weather)
        # ---- residuals (recompute weather: a faint may have removed the setter) ----
        weather = current_weather(A, B)
        for s, foe in ((A, B), (B, A)):
            end_of_turn(s.mon, foe, weather)
        if not A.alive_indices():
            return 1
        if not B.alive_indices():
            return 0
    return -1
