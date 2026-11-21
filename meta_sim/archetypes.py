"""Playstyles ("archetypes") and playstyle-specific builds for the meta test.

A mon is judged on every playstyle it can genuinely play, each with a set and
item built for that job, instead of on one generic set. A wall gets recovery
and status instead of four attacks; a special attacker never wastes a slot on
Swords Dance; a support carries its utility moves.

Eligibility is decided from the mon's L50 stats (against the pool's own
percentiles, so it keeps working after a rebalance) and from what it can learn.

A Build is (mon id, playstyle, moveset, ability, item). build_pool_builds()
returns every build for the pool.
"""
from dataclasses import dataclass, field

import os
import json
import abilities
import items
from engine import BOOST, HEAL_EFFECTS, INFLICT, RECHARGE_EFFECTS
from teams import _setup_score, est_power, pick_moveset, STATUS_PRIORITY

# ---- playstyles ----------------------------------------------------------------
PHYSICAL = 'physical attacker'
SPECIAL = 'special attacker'
MIXED = 'mixed attacker'
SETUP = 'setup sweeper'
REVENGE = 'revenge killer'
PHYS_WALL = 'physical wall'
SPEC_WALL = 'special wall'
TANK = 'bulky tank'
SUPPORT = 'support'
HAZARDS = 'hazard setter'
CLERIC = 'cleric'
PIVOT = 'pivot'
WEATHER_SETTER = 'weather setter'
WEATHER_SWEEPER = 'weather sweeper'
BATON = 'baton passer'
TRICK_ROOM = 'trick room setter'
TRAPPER = 'trapper'

PLAYSTYLES = [PHYSICAL, SPECIAL, MIXED, SETUP, REVENGE, WEATHER_SWEEPER, BATON,
              PHYS_WALL, SPEC_WALL, TANK, SUPPORT, HAZARDS, CLERIC, PIVOT,
              WEATHER_SETTER, TRICK_ROOM, TRAPPER]

# Team-slot families used by the balanced team builder and the swap test.
FAMILY = {PHYSICAL: 'offense', SPECIAL: 'offense', MIXED: 'offense',
          SETUP: 'speed', REVENGE: 'speed',
          PHYS_WALL: 'defense', SPEC_WALL: 'defense', TANK: 'defense',
          SUPPORT: 'utility', HAZARDS: 'utility', CLERIC: 'utility', PIVOT: 'utility',
          WEATHER_SWEEPER: 'offense', BATON: 'speed', WEATHER_SETTER: 'utility',
          TRICK_ROOM: 'utility', TRAPPER: 'utility'}

# Metrics that show whether a mon is doing its job, per playstyle.
JOB_METRICS = {
    PHYSICAL: ['dmg_dealt', 'kos'], SPECIAL: ['dmg_dealt', 'kos'], MIXED: ['dmg_dealt', 'kos'],
    SETUP: ['dmg_dealt', 'kos'], REVENGE: ['kos', 'dmg_dealt'],
    PHYS_WALL: ['dmg_taken', 'turns_active', 'heal_done'],
    SPEC_WALL: ['dmg_taken', 'turns_active', 'heal_done'],
    TANK: ['dmg_taken', 'dmg_dealt', 'turns_active'],
    SUPPORT: ['status_infl', 'screens_set', 'stat_drops', 'phazes'],
    HAZARDS: ['hazards_set', 'status_infl'],
    CLERIC: ['cures', 'heal_done'],
    PIVOT: ['pivots', 'dmg_dealt'],
    WEATHER_SETTER: ['weather_set', 'dmg_dealt'],
    WEATHER_SWEEPER: ['dmg_dealt', 'kos'],
    BATON: ['passes', 'subs_made'],
    TRICK_ROOM: ['trick_rooms', 'dmg_dealt'],
    TRAPPER: ['traps', 'perish_kos', 'kos'],
}

# Weather: the moves and abilities that set it, and what each weather boosts.
WEATHER_MOVE = {'sun': 'EFFECT_SUNNY_DAY', 'rain': 'EFFECT_RAIN_DANCE',
                'sand': 'EFFECT_SANDSTORM', 'hail': 'EFFECT_HAIL'}
WEATHER_SETTING = {'DROUGHT': 'sun', 'DRIZZLE': 'rain', 'SAND_STREAM': 'sand',
                   'SNOW_WARNING': 'hail'}
WEATHER_ABUSE = {'SWIFT_SWIM': 'rain', 'CHLOROPHYLL': 'sun', 'SAND_RUSH': 'sand',
                 'SLUSH_RUSH': 'hail', 'SOLAR_POWER': 'sun', 'SAND_FORCE': 'sand'}
WEATHER_TYPES = {'sun': {'FIRE'}, 'rain': {'WATER'}, 'sand': {'ROCK', 'GROUND', 'STEEL'},
                 'hail': {'ICE'}}
WEATHER_SURE_HIT = {'rain': {'THUNDER', 'HURRICANE'}, 'hail': {'BLIZZARD'},
                    'sun': {'SOLAR_BEAM'}}
WEATHER_ROCK = {'sun': 'HEAT_ROCK', 'rain': 'DAMP_ROCK', 'sand': 'SMOOTH_ROCK',
                'hail': 'ICY_ROCK'}

STATUS_MOVES = set(INFLICT) - {'EFFECT_CONFUSE'}
RECOVERY = HEAL_EFFECTS
HAZARD_MOVES = {'EFFECT_SPIKES', 'EFFECT_TOXIC_SPIKES'}
SCREENS = {'EFFECT_REFLECT', 'EFFECT_LIGHT_SCREEN'}
SUPPORT_TOOLS = SCREENS | {'EFFECT_ENCORE', 'EFFECT_HAZE', 'EFFECT_ROAR', 'EFFECT_PAIN_SPLIT',
                           'EFFECT_LEECH_SEED', 'EFFECT_KNOCK_OFF', 'EFFECT_RAPID_SPIN'}
PIVOT_MOVES = {'EFFECT_SWITCH_HIT'}
PRIORITY_EFFECTS = {'EFFECT_PRIORITY_HIT', 'EFFECT_SUCKER_PUNCH'}
NEVER = {'EFFECT_EXPLOSION', 'EFFECT_COUNTER', 'EFFECT_HYPER_BEAM'}   # self-KO / unmodelled / recharge
SUPPORT_ORDER = ['EFFECT_REFLECT', 'EFFECT_LIGHT_SCREEN', 'EFFECT_ENCORE', 'EFFECT_KNOCK_OFF',
                 'EFFECT_ROAR', 'EFFECT_HAZE', 'EFFECT_LEECH_SEED', 'EFFECT_PAIN_SPLIT',
                 'EFFECT_RAPID_SPIN']


@dataclass
class Build:
    mid: str
    style: str
    moves: list
    ability: str
    item: str
    mon: dict = field(repr=False)
    weather: str = None                    # weather this build sets or relies on
    hp_type: str = None                    # Hidden Power type (DV-based), if it runs it

    @property
    def key(self):
        return f'{self.mid}|{self.style}'

    def as_team_entry(self):
        """The tuple engine.Pmon expects."""
        return (self.mid, self.mon, list(self.moves), self.ability, self.item, self.hp_type)


def percentiles(pool):
    def pct(vals, q):
        vals = sorted(vals)
        return vals[min(len(vals) - 1, int(len(vals) * q))]
    stats = [m['stats'] for m in pool.values()]
    out = {}
    for k in ('hp', 'atk', 'defe', 'spa', 'spd', 'spe'):
        for q in (50, 60, 75):
            out[f'{k}{q}'] = pct([s[k] for s in stats], q / 100)
    for q in (50, 60, 75):
        out[f'pbulk{q}'] = pct([s['hp'] * s['defe'] for s in stats], q / 100)
        out[f'sbulk{q}'] = pct([s['hp'] * s['spd'] for s in stats], q / 100)
    return out


def _attacks(mon, moves, cat=None, n=4, exclude=(), prefer_priority=False):
    """Best attacking moves: strongest STAB first, then type coverage."""
    s = mon['stats']
    def score(mv):
        m = moves[mv]
        stat = s['atk'] if m['cat'] == 'PHYSICAL' else s['spa']
        stab = 1.5 if m['type'] in mon['types'] else 1.0
        acc = 1.0 if m['acc'] < 0 else m['acc'] / 100
        pri = 1.4 if prefer_priority and m['prio'] > 0 else 1.0
        slow = 0.5 if m['effect'] in ('EFFECT_FLY', 'EFFECT_SOLAR_BEAM', 'EFFECT_FUTURE_SIGHT',
                                      'EFFECT_DREAM_EATER') else 1.0
        return est_power(m) * stab * acc * stat * pri * slow
    cands = [mv for mv in mon['_pool'] if moves[mv]['cat'] != 'STATUS'
             and est_power(moves[mv]) > 0 and moves[mv]['effect'] not in NEVER
             and mv not in exclude and (cat is None or moves[mv]['cat'] == cat)]
    cands.sort(key=score, reverse=True)
    chosen, types = [], set()
    if prefer_priority:
        pri = [mv for mv in cands if moves[mv]['prio'] > 0]
        if pri:
            chosen.append(pri[0]); types.add(moves[pri[0]]['type'])
    for mv in cands:                       # STABs first
        t = moves[mv]['type']
        if len(chosen) >= n:
            break
        if t in mon['types'] and t not in types:
            chosen.append(mv); types.add(t)
    for mv in cands:                       # then coverage
        t = moves[mv]['type']
        if len(chosen) >= n:
            break
        if mv not in chosen and t not in types:
            chosen.append(mv); types.add(t)
    for mv in cands:                       # then anything strong
        if len(chosen) >= n:
            break
        if mv not in chosen:
            chosen.append(mv)
    return chosen


def _best_of(mon, moves, effects, key=None):
    cands = [mv for mv in mon['_pool'] if moves[mv]['effect'] in effects]
    if not cands:
        return None
    return max(cands, key=key or (lambda mv: (moves[mv]['acc'], moves[mv]['pp'])))


def _status_move(mon, moves):
    return _best_of(mon, moves, STATUS_MOVES, key=lambda mv: (
        STATUS_PRIORITY.get(moves[mv]['effect'], 0), moves[mv]['acc']))


def _setup_move(mon, moves, phys):
    cands = [(_setup_score(moves[mv]['effect'], phys), mv) for mv in mon['_pool']
             if moves[mv]['effect'] in BOOST or moves[mv]['effect'] in ('EFFECT_BELLY_DRUM',)]
    if phys and any(moves[mv]['effect'] == 'EFFECT_CURSE' for mv in mon['_pool']) \
            and 'GHOST' not in mon['types']:
        cands.append((1.5, next(mv for mv in mon['_pool'] if moves[mv]['effect'] == 'EFFECT_CURSE')))
    cands = [c for c in cands if c[0] > 0]
    return max(cands)[1] if cands else None


def _fill(moveset, mon, moves, cat=None):
    for mv in _attacks(mon, moves, cat, n=4, exclude=moveset):
        if len(moveset) >= 4:
            break
        if mv not in moveset:
            moveset.append(mv)
    if len(moveset) < 4:                   # no real attacks: Counter / Mirror Coat
        for mv in ('COUNTER', 'MIRROR_COAT'):
            if mv in mon['_pool'] and mv not in moveset and len(moveset) < 4:
                moveset.append(mv)
    return moveset[:4]


def _weather_attacks(mon, moves, w, n=4, cat=None):
    """Attacks for a weather team: weather-boosted and sure-hit moves first."""
    boosted = WEATHER_TYPES[w]
    sure = WEATHER_SURE_HIT.get(w, set())
    pool = [mv for mv in _attacks(mon, moves, cat, n=12)]
    first = [mv for mv in pool if mv in sure or moves[mv]['type'] in boosted][:2]
    return _fill(first, mon, moves, cat)[:n]


def _item(style, mid, mon, ability):
    if items.eviolite_eligible(mid, mon):
        return 'EVIOLITE'
    if ability in items.ORB_FOR_ABILITY:
        return items.ORB_FOR_ABILITY[ability]
    s = mon['stats']
    if style == WEATHER_SWEEPER:
        return 'LIFE_ORB'
    if style == PHYSICAL:
        return 'CHOICE_BAND'
    if style == SPECIAL:
        return 'CHOICE_SPECS'
    if style == REVENGE:
        return 'CHOICE_SCARF'
    if style in (MIXED, SETUP):
        bulk = s['hp'] + (s['defe'] + s['spd']) // 2
        return 'FOCUS_SASH' if style == SETUP and bulk < items.FOCUS_SASH_BULK_THRESHOLD \
            else 'LIFE_ORB'
    return 'LEFTOVERS'


SUPPORT_CORE = SCREENS | {'EFFECT_ENCORE', 'EFFECT_HAZE', 'EFFECT_PAIN_SPLIT',
                          'EFFECT_LEECH_SEED'}   # tools that make a mon a support


def builds_for(mid, mon, moves, P):
    """Every playstyle build this mon qualifies for."""
    s = mon['stats']
    pool = mon['_pool']
    effects = {moves[mv]['effect'] for mv in pool}
    phys = s['atk'] >= s['spa']
    off = max(s['atk'], s['spa'])
    out = []

    def n_attacks(cat):
        return len([mv for mv in _attacks(mon, moves, cat, n=4) if est_power(moves[mv]) >= 60])

    if s['atk'] >= P['atk60'] and s['atk'] >= s['spa'] * 0.9 and n_attacks('PHYSICAL') >= 2:
        out.append((PHYSICAL, _attacks(mon, moves, 'PHYSICAL') or _attacks(mon, moves)))
    if s['spa'] >= P['spa60'] and s['spa'] >= s['atk'] * 0.9 and n_attacks('SPECIAL') >= 2:
        out.append((SPECIAL, _attacks(mon, moves, 'SPECIAL') or _attacks(mon, moves)))
    if (s['atk'] >= P['atk60'] and s['spa'] >= P['spa60']
            and n_attacks('PHYSICAL') >= 2 and n_attacks('SPECIAL') >= 2):
        out.append((MIXED, _attacks(mon, moves, 'PHYSICAL', n=2)
                    + _attacks(mon, moves, 'SPECIAL', n=2)))
    setup = _setup_move(mon, moves, phys)
    if setup and off >= P['atk50' if phys else 'spa50'] and (
            s['spe'] >= P['spe50'] or s['hp'] * min(s['defe'], s['spd']) >= P['pbulk50']):
        out.append((SETUP, _fill([setup], mon, moves, 'PHYSICAL' if phys else 'SPECIAL')))
    has_priority = any(moves[mv]['prio'] > 0 and est_power(moves[mv]) >= 40
                       and moves[mv]['cat'] != 'STATUS' for mv in pool)
    if off >= P['atk50' if phys else 'spa50'] and (
            s['spe'] >= P['spe75'] or (has_priority and off >= P['atk60' if phys else 'spa60'])):
        out.append((REVENGE, _attacks(mon, moves, prefer_priority=True)))

    recovery = _best_of(mon, moves, RECOVERY)
    status = _status_move(mon, moves)
    sleep_talk = _best_of(mon, moves, {'EFFECT_SLEEP_TALK'})
    def wall_set(cat=None):
        ms = [m for m in (recovery, status) if m]
        if recovery == 'REST' and sleep_talk:
            ms.insert(1, sleep_talk)       # RestTalk
        return _fill(ms, mon, moves) if len(ms) else None
    pb, sb = s['hp'] * s['defe'] / P['pbulk75'], s['hp'] * s['spd'] / P['sbulk75']
    if max(pb, sb) >= 1 and (recovery or status):  # one wall build, on its stronger side
        out.append((PHYS_WALL if pb >= sb else SPEC_WALL, wall_set()))
    if (s['hp'] * s['defe'] >= P['pbulk60'] and s['hp'] * s['spd'] >= P['sbulk60']
            and off >= P['atk50' if phys else 'spa50']):
        ms = [recovery] if recovery else []
        out.append((TANK, _fill(ms, mon, moves, 'PHYSICAL' if phys else 'SPECIAL')))

    tools = [e for e in SUPPORT_ORDER if e in effects]
    core = [e for e in tools if e in SUPPORT_CORE]
    sturdy_or_fast = (s['hp'] * min(s['defe'], s['spd']) >= P['pbulk50']
                      or s['spe'] >= P['spe75'])
    if core and (status or len(core) >= 2) and sturdy_or_fast:
        ms = [status] if status else []
        for e in core + [t for t in tools if t not in core]:
            if len(ms) >= 3:
                break
            mv = _best_of(mon, moves, {e})
            if mv not in ms:
                ms.append(mv)
        out.append((SUPPORT, _fill(ms, mon, moves)))
    hz = _best_of(mon, moves, HAZARD_MOVES, key=lambda mv: moves[mv]['effect'] == 'EFFECT_SPIKES')
    if hz:
        ms = [hz] + [m for m in (_best_of(mon, moves, HAZARD_MOVES - {moves[hz]['effect']}),
                                 status or recovery) if m]
        out.append((HAZARDS, _fill(ms[:3], mon, moves)))
    bell = _best_of(mon, moves, {'EFFECT_HEAL_BELL'})
    if bell:
        out.append((CLERIC, _fill([bell] + ([recovery] if recovery else []), mon, moves)))
    piv = _best_of(mon, moves, PIVOT_MOVES)
    if piv or (s['hp'] * min(s['defe'], s['spd']) >= P['pbulk50']
               and 'REGENERATOR' in (mon.get('abilities') or [])):
        out.append((PIVOT, _fill([piv] if piv else [], mon, moves)))

    abil = mon.get('abilities') or []
    forced = {}                            # style -> (ability, weather)
    # weather setter: a weather ability, or a weather move it benefits from
    setters = [WEATHER_SETTING[a] for a in abil if a in WEATHER_SETTING]
    for w in ('rain', 'sun', 'sand', 'hail'):
        if setters:
            break
        if WEATHER_MOVE[w] in effects and (set(mon['types']) & WEATHER_TYPES[w]) and (
                s['hp'] * min(s['defe'], s['spd']) >= P['pbulk50'] or s['spe'] >= P['spe60']):
            setters = [w]
    if setters:
        w = setters[0]
        ms = [] if any(WEATHER_SETTING.get(a) == w for a in abil) else \
            [_best_of(mon, moves, {WEATHER_MOVE[w]})]
        ms += [m for m in ((recovery if recovery != 'REST' else None) or status,) if m]
        out.append((WEATHER_SETTER, ms + [m for m in _weather_attacks(mon, moves, w)
                                          if m not in ms]))
        forced[WEATHER_SETTER] = (next((a for a in abil if WEATHER_SETTING.get(a) == w), None), w)
    # weather sweeper: an ability that only pays off in weather
    abusers = [a for a in abil if a in WEATHER_ABUSE]
    if abusers and off >= P['atk50' if phys else 'spa50']:
        a = abusers[0]
        w = WEATHER_ABUSE[a]
        out.append((WEATHER_SWEEPER, _weather_attacks(mon, moves, w,
                                                      cat='PHYSICAL' if phys else 'SPECIAL')))
        forced[WEATHER_SWEEPER] = (a, w)
    # Baton Passer: set up (behind a Substitute) and pass it on
    bp = _best_of(mon, moves, {'EFFECT_BATON_PASS'})
    any_setup = _setup_move(mon, moves, phys) or _setup_move(mon, moves, not phys) or \
        _best_of(mon, moves, {'EFFECT_SPEED_UP_2'})
    if bp and any_setup and (s['spe'] >= P['spe50'] or s['hp'] * min(s['defe'], s['spd']) >= P['pbulk50']):
        sub = _best_of(mon, moves, {'EFFECT_SUBSTITUTE'})
        out.append((BATON, _fill([m for m in (any_setup, sub, bp) if m], mon, moves)))
    # Trick Room setter: slow, and can survive to set it
    tr = _best_of(mon, moves, {'EFFECT_TRICK_ROOM'})
    if tr and s['spe'] <= P['spe50']:
        out.append((TRICK_ROOM, _fill([tr] + ([recovery] if recovery else []), mon, moves)))
    # trapper: a trapping ability or Mean Look, with something to do to the trapped foe
    trap_ab = next((a for a in abil if a in ('SHADOW_TAG', 'ARENA_TRAP', 'MAGNET_PULL')), None)
    mean_look = _best_of(mon, moves, {'EFFECT_MEAN_LOOK'})
    if trap_ab or mean_look:
        perish = _best_of(mon, moves, {'EFFECT_PERISH_SONG'})
        protect = _best_of(mon, moves, {'EFFECT_PROTECT'})
        ms = [] if trap_ab else [mean_look]
        if perish and (trap_ab or mean_look):
            ms += [perish, protect]
        elif status:
            ms += [status]
        out.append((TRAPPER, _fill([m for m in ms if m], mon, moves)))
        forced[TRAPPER] = (trap_ab, None)

    if not out:                            # every mon gets at least one build
        out.append((PHYSICAL if phys else SPECIAL,
                    _attacks(mon, moves, 'PHYSICAL' if phys else 'SPECIAL') or _attacks(mon, moves)))

    builds = []
    for style, moveset in out:
        moveset = ([m for m in moveset if m][:4] or _attacks(mon, moves)
                   or pick_moveset(mid, mon, moves, None, mon['_role']))
        ability = abilities.pick_ability(mon.get('abilities'), s)
        if style == PIVOT and 'REGENERATOR' in (mon.get('abilities') or []):
            ability = 'REGENERATOR'
        weather = None
        if style in forced:
            fa, weather = forced[style]
            ability = fa or ability
        item = _item(style, mid, mon, ability)
        if style == WEATHER_SETTER and item == 'LEFTOVERS':
            item = WEATHER_ROCK[weather]   # 8 turns of weather
        if item in ('CHOICE_BAND', 'CHOICE_SPECS', 'CHOICE_SCARF') and len(moveset) == 4:
            trick = _best_of(mon, moves, {'EFFECT_TRICK'})
            if trick and trick not in moveset:
                moveset = moveset[:3] + [trick]   # Trick the choice item onto a wall
        if style == SUPPORT and item == 'LEFTOVERS' and sum(
                moves[m]['effect'] in SCREENS for m in moveset) == 2:
            item = 'LIGHT_CLAY'            # dual screens: 8 turns each
        builds.append(Build(mid, style, moveset, ability, item, mon, weather))
    return builds


BEST_SETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'best_sets.json')


def build_pool_builds(pool, moves, sets_path='default'):
    """Every build in the pool. Sets found by optimize.py (data/best_sets.json)
    replace the heuristic moves / item / ability / Hidden Power type."""
    P = percentiles(pool)
    out = []
    for mid in sorted(pool):
        out.extend(builds_for(mid, pool[mid], moves, P))
    if sets_path == 'default':
        sets_path = BEST_SETS              # read at call time, so optimize.py can turn it off
    if sets_path and os.path.exists(sets_path):
        best = json.load(open(sets_path))
        for b in out:
            o = best.get(b.key)
            if o and all(mv in moves for mv in o['moves']):
                b.moves, b.item, b.ability = list(o['moves']), o['item'], o['ability']
                b.hp_type = o.get('hp_type')
    return out
