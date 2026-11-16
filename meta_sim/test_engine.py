#!/usr/bin/env python3
"""Scripted checks for engine.py's move mechanics.

Each test builds a tiny 1v1 or 2v2 with fixed moves and drives perform()
directly, so it checks one mechanic at a time without battle randomness.
Run: python3 meta_sim/test_engine.py
"""
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import engine  # noqa: E402
from engine import Pmon, Side, perform, end_of_turn  # noqa: E402

MOVES = json.load(open(os.path.join(HERE, 'data', 'moves.json')))
CHART = json.load(open(os.path.join(HERE, 'data', 'typechart.json')))


def mon(types=('NORMAL',), stats=None, moves=('TACKLE',), ability=None, item=None, mid='x'):
    s = dict(hp=300, atk=150, defe=150, spa=150, spd=150, spe=100)
    s.update(stats or {})
    return Pmon(mid, {'types': list(types), 'stats': s}, list(moves), ability, item)


def duel(a, b, a2=None, b2=None):
    A = Side([a] + ([a2] if a2 else []))
    B = Side([b] + ([b2] if b2 else []))
    return A, B


def act(A, B, move, rng=None, foe_move=None, foe_moved=False):
    perform(A, B, MOVES, CHART, rng or random.Random(1), idx=A.mon.moves.index(move),
            foe_move=foe_move, foe_moved=foe_moved)


def test_screens_halve_damage():
    a, b = mon(moves=('TACKLE',)), mon(moves=('REFLECT', 'LIGHT_SCREEN'))
    A, B = duel(a, b)
    act(A, B, 'TACKLE', random.Random(5))
    plain = b.dmg_taken
    b.hp, b.dmg_taken = b.maxhp, 0.0
    act(B, A, 'REFLECT')
    assert B.reflect == engine.SCREEN_TURNS and b.screens_set == 1
    act(A, B, 'TACKLE', random.Random(5))
    assert abs(b.dmg_taken - plain * engine.SCREEN_DAMAGE_MULT) < 0.02, (plain, b.dmg_taken)


def test_protect_blocks_then_decays():
    a, b = mon(moves=('TACKLE',)), mon(moves=('PROTECT',))
    A, B = duel(a, b)
    act(B, A, 'PROTECT', random.Random(0))
    assert b.protected
    act(A, B, 'TACKLE')
    assert b.hp == b.maxhp
    b.protected = False
    hits = 0
    for seed in range(300):
        b.protect_count = 1
        act(B, A, 'PROTECT', random.Random(seed))
        hits += b.protected
        b.protected = False
    assert 70 < hits < 130, hits             # ~1/3 on the second consecutive use


def test_sucker_punch_needs_an_attack():
    a, b = mon(types=('DARK',), moves=('SUCKER_PUNCH',)), mon(moves=('TACKLE', 'SWORDS_DANCE'))
    A, B = duel(a, b)
    act(A, B, 'SUCKER_PUNCH', foe_move='SWORDS_DANCE')
    assert b.hp == b.maxhp
    act(A, B, 'SUCKER_PUNCH', foe_move='TACKLE')
    assert b.hp < b.maxhp


def test_drain_heals_half():
    a = mon(types=('GRASS',), moves=('GIGA_DRAIN',))
    a.hp = 100
    b = mon()
    A, B = duel(a, b)
    act(A, B, 'GIGA_DRAIN')
    dealt = b.maxhp - b.hp
    assert abs((a.hp - 100) - dealt / 2) < 1e-6


def test_knock_off_removes_item_and_boosts():
    a = mon(types=('DARK',), moves=('KNOCK_OFF',))
    b1, b2 = mon(item='LEFTOVERS'), mon()
    A, B = duel(a, b1)
    act(A, B, 'KNOCK_OFF', random.Random(3))
    with_item = b1.maxhp - b1.hp
    assert b1.item is None
    A, B = duel(a, b2)
    act(A, B, 'KNOCK_OFF', random.Random(3))
    assert with_item > (b2.maxhp - b2.hp) * 1.3


def test_rapid_spin_clears_hazards():
    a, b = mon(moves=('RAPID_SPIN',)), mon()
    A, B = duel(a, b)
    A.spikes, A.tspikes, a.seeded = 2, 1, True
    act(A, B, 'RAPID_SPIN')
    assert (A.spikes, A.tspikes, a.seeded, a.hazards_cleared) == (0, 0, False, 1)


def test_u_turn_pivots_to_best_matchup():
    a = mon(types=('BUG',), moves=('U_TURN',))
    a2 = mon(types=('FIRE',), moves=('FLAMETHROWER',), mid='fire')
    b = mon(types=('GRASS',), moves=('TACKLE',))
    A, B = duel(a, b, a2=a2)
    act(A, B, 'U_TURN')
    assert A.mon is a2 and a.pivots == 1 and A.switched


def test_roar_forces_a_switch_and_hazards_hit():
    a = mon(moves=('ROAR',))
    b, b2 = mon(mid='b'), mon(mid='b2')
    A, B = duel(a, b, b2=b2)
    B.spikes = 1
    act(A, B, 'ROAR')
    assert B.mon is b2 and a.phazes == 1 and b2.hp < b2.maxhp


def test_heal_bell_cures_team():
    a, a2, b = mon(moves=('HEAL_BELL',)), mon(mid='a2'), mon()
    a.status, a2.status = 'psn', 'par'
    A, B = duel(a, b, a2=a2)
    act(A, B, 'HEAL_BELL')
    assert a.status is None and a2.status is None and a.cures == 2


def test_haze_and_encore_and_pain_split():
    a, b = mon(moves=('HAZE', 'ENCORE', 'PAIN_SPLIT')), mon(moves=('SWORDS_DANCE', 'TACKLE'))
    A, B = duel(a, b)
    b.stage['atk'] = 4
    act(A, B, 'HAZE')
    assert b.stage['atk'] == 0 and a.stat_drops == 4
    b.last_move = 0
    act(A, B, 'ENCORE')
    assert b.encore == engine.ENCORE_TURNS
    assert engine.choose_move(B, A, MOVES, CHART) == 0
    a.hp = 50
    act(A, B, 'PAIN_SPLIT')
    assert a.hp == b.hp == (50 + 300) / 2


def test_curse_both_ways():
    a = mon(moves=('CURSE',))
    g = mon(types=('GHOST',), moves=('CURSE',), mid='g')
    b = mon()
    A, B = duel(a, b)
    act(A, B, 'CURSE')
    assert (a.stage['atk'], a.stage['defe'], a.stage['spe']) == (1, 1, -1)
    A, B = duel(g, b)
    act(A, B, 'CURSE')
    assert g.hp == g.maxhp / 2 and b.cursed
    end_of_turn(b, A)
    assert b.hp == b.maxhp * 3 / 4


def test_close_combat_drops_own_defences():
    a, b = mon(types=('FIGHTING',), moves=('CLOSE_COMBAT',)), mon(stats={'hp': 999})
    A, B = duel(a, b)
    act(A, B, 'CLOSE_COMBAT')
    assert (a.stage['defe'], a.stage['spd']) == (-1, -1)


def test_icy_wind_always_lowers_speed():
    a, b = mon(types=('ICE',), moves=('ICY_WIND',)), mon(stats={'hp': 999})
    A, B = duel(a, b)
    act(A, B, 'ICY_WIND', random.Random(0))
    assert b.stage['spe'] == -1 and a.stat_drops == 1


def test_battle_reports_detail():
    team = [('x', {'types': ['NORMAL'], 'stats': dict(hp=300, atk=150, defe=150, spa=150,
                                                       spd=150, spe=100)},
             ['TACKLE', 'REFLECT'], None, 'LEFTOVERS')]
    res, ca, cb = engine.run_battle(team, team, MOVES, CHART, seed=1, detail=True)
    assert res in (0, 1, -1) and set(engine.STAT_KEYS) <= set(ca[0])
    assert ca[0]['turns_active'] > 0 and ca[0]['dmg_taken'] > 0


if __name__ == '__main__':
    failed = 0
    for name, fn in list(globals().items()):
        if name.startswith('test_'):
            try:
                fn()
                print(f'  ok   {name}')
            except AssertionError as e:
                failed += 1
                print(f'  FAIL {name}: {e}')
    print('all passed' if not failed else f'{failed} failed')
    sys.exit(1 if failed else 0)
