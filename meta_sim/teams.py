"""Moveset selection + team building for the 6v6 sim.

Two builders, so we can diff them (the user's "Both, compare"):
  random    : random legal 6-mon teams. Unbiased; undersells synergy/support
              mons that only shine with a role around them.
  role      : classify each mon by stats into a role (sweeper/wall/pivot/lead),
              then fill a balanced template with type diversity. Surfaces the
              support/stall mons the 1v1 matrix and random teams understate.

Movesets are chosen by the same role-aware heuristic in both builders, so the
only variable between the two runs is *team composition*.
"""
import random

from engine import (BOOST, HEAL_EFFECTS, INFLICT, type_mult)
import abilities
import items

# role-relevant utility effect buckets
SETUP = set(BOOST) | {'EFFECT_BELLY_DRUM'}
STATUS = set(INFLICT)
HAZARD = {'EFFECT_SPIKES', 'EFFECT_TOXIC_SPIKES'}
SUPPORT = HEAL_EFFECTS | {'EFFECT_LEECH_SEED'}


def _damaging(mon, moves):
    out = []
    for mv in mon_pool(mon):
        m = moves.get(mv)
        if m and m['cat'] != 'STATUS' and m['power'] > 0:
            out.append(mv)
    return out


def mon_pool(mon):
    return mon.get('_pool', [])


def classify(mon):
    """Assign a coarse role from L50 max-build stats.

    Thresholds are calibrated to this pool's distribution (offense med 157 /
    p75 167, bulk med 326 / p75 344, speed med 137 / p75 152):
      sweeper : fast + hits hard            (off >= 160 and spe >= 150)
      tank    : hits hard but slow/bulky    (off >= 160, not fast)
      wall    : bulky + low offense         (bulk >= 340 and off < 158)
      pivot   : everything else (balanced)
    """
    s = mon['stats']
    off = max(s['atk'], s['spa'])
    bulk = s['hp'] + (s['defe'] + s['spd']) // 2
    speed = s['spe']
    if off >= 160 and speed >= 150:
        return 'sweeper'
    if off >= 160:
        return 'tank'
    if bulk >= 340 and off < 158:
        return 'wall'
    return 'pivot'


def pick_moveset(mid, mon, moves, chart, role):
    """Choose up to 4 moves: strong STAB + coverage damage, plus role utility."""
    pool = mon_pool(mon)
    phys_bias = mon['stats']['atk'] >= mon['stats']['spa']

    # rank damaging moves by power, category fit, and STAB
    def dmg_key(mv):
        m = moves[mv]
        cat_fit = 1.15 if (m['cat'] == 'PHYSICAL') == phys_bias else 1.0
        stab = 1.5 if m['type'] in mon['types'] else 1.0
        return m['power'] * cat_fit * stab

    dmg = sorted((mv for mv in pool if moves[mv]['cat'] != 'STATUS'
                  and moves[mv]['power'] > 0), key=dmg_key, reverse=True)

    chosen, seen_types = [], set()
    # best STAB hitter first, then coverage (distinct types)
    for mv in dmg:
        t = moves[mv]['type']
        is_stab = t in mon['types']
        if is_stab and not any(moves[c]['type'] == t for c in chosen):
            chosen.append(mv); seen_types.add(t)
        if len(chosen) >= 2:
            break
    for mv in dmg:
        if mv in chosen:
            continue
        t = moves[mv]['type']
        if t not in seen_types:
            chosen.append(mv); seen_types.add(t)
        if len(chosen) >= 3:
            break

    # role utility slot(s)
    def first(eff_set):
        return next((mv for mv in pool if moves[mv]['effect'] in eff_set), None)

    utils = []
    if role in ('sweeper', 'tank'):
        u = first(SETUP)
        if u: utils.append(u)
    if role == 'wall':
        for bucket in (HEAL_EFFECTS, STATUS, {'EFFECT_LEECH_SEED'}):
            u = first(bucket)
            if u and u not in utils:
                utils.append(u)
    if role == 'pivot':
        u = first(STATUS) or first(HAZARD)
        if u: utils.append(u)

    for u in utils:
        if u not in chosen and len(chosen) < 4:
            chosen.append(u)
    # backfill to 4 with remaining damage
    for mv in dmg:
        if len(chosen) >= 4:
            break
        if mv not in chosen:
            chosen.append(mv)
    return chosen[:4] if chosen else (dmg[:1] or pool[:1])


def build_pool(mons, learnsets, args):
    """Filter the species pool and attach movepools + roles."""
    from stats import mon_stats
    pool = {}
    for mid, m in mons.items():
        if 'stats' not in m or 'types' not in m:
            continue
        if not args.include_unevolved and not m.get('fully_evolved'):
            continue
        if not args.include_legendary and m.get('legendary'):
            continue
        if not learnsets.get(mid):
            continue
        m = dict(m)
        m['stats'] = mon_stats(m['stats'])
        m['_pool'] = learnsets[mid]
        m['_role'] = classify(m)
        pool[mid] = m
    return pool


def make_mon(mid, pool, moves, chart):
    """Return (mid, mon, moveset, ability, item) tuple ready for engine.Pmon."""
    m = pool[mid]
    ability = abilities.pick_ability(m.get('abilities'))
    item = items.pick_item(mid, m, m['_role'])
    return (mid, m, pick_moveset(mid, m, moves, chart, m['_role']), ability, item)


def random_team(ids, pool, moves, chart, rng):
    pick = rng.sample(ids, 6)
    return [make_mon(mid, pool, moves, chart) for mid in pick]


# role template: a balanced 6 covering every role so each is represented in
# proportion to the pool (sweeper 18 / tank 58 / pivot 70 / wall 28). Without a
# 'tank' slot the 58 tank-role mons would never be drafted -> zero-sample noise.
ROLE_TEMPLATE = ['sweeper', 'tank', 'tank', 'pivot', 'pivot', 'wall']


def role_team(ids, pool, moves, chart, rng):
    by_role = {'sweeper': [], 'tank': [], 'pivot': [], 'wall': []}
    for mid in ids:
        by_role[pool[mid]['_role']].append(mid)
    chosen, used_types = [], set()
    for want in ROLE_TEMPLATE:
        cands = by_role[want] or (by_role['tank'] if want == 'sweeper' else [])
        cands = [c for c in cands if c not in chosen]
        if not cands:
            cands = [c for c in ids if c not in chosen]
        # prefer type diversity
        rng.shuffle(cands)
        cands.sort(key=lambda c: len(set(pool[c]['types']) & used_types))
        mid = cands[0]
        chosen.append(mid)
        used_types |= set(pool[mid]['types'])
    return [make_mon(mid, pool, moves, chart) for mid in chosen]
