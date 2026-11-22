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
import rom_damage  # noqa: E402
from engine import Pmon, Side, perform, end_of_turn  # noqa: E402

MOVES = json.load(open(os.path.join(HERE, 'data', 'moves.json')))
CHART = json.load(open(os.path.join(HERE, 'data', 'typechart.json')))


def mon(types=('NORMAL',), stats=None, moves=('TACKLE',), ability=None, item=None, mid='x'):
    s = dict(hp=300, atk=150, defe=150, spa=150, spd=150, spe=100)
    s.update(stats or {})
    return Pmon(mid, {'types': list(types), 'stats': s}, list(moves), ability, item)


def duel(a, b, a2=None, b2=None):
    field = engine.Field()
    A = Side([a] + ([a2] if a2 else []), field)
    B = Side([b] + ([b2] if b2 else []), field)
    A.foe, B.foe = B, A
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
        b.pp = [99]                         # PP is tracked now; keep it topped up
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


def test_weather_moves_and_damage():
    a = mon(types=('WATER',), moves=('RAIN_DANCE', 'SURF', 'THUNDER'), item='DAMP_ROCK')
    b = mon(stats={'hp': 999})
    A, B = duel(a, b)
    act(A, B, 'SURF', random.Random(4))
    dry = b.maxhp - b.hp
    b.hp = b.maxhp
    act(A, B, 'RAIN_DANCE')
    assert A.field.weather == 'rain' and A.field.weather_turns == engine.WEATHER_ROCK_TURNS
    act(A, B, 'SURF', random.Random(4))
    assert abs((b.maxhp - b.hp) / dry - 1.5) < 0.05
    hits = 0
    for seed in range(200):                 # Thunder never misses in rain
        b.hp = b.maxhp
        act(A, B, 'THUNDER', random.Random(seed))
        hits += b.hp < b.maxhp
    assert hits == 200


def test_weather_ability_speed_and_chip():
    t = mon(types=('ROCK',), ability='SAND_STREAM', moves=('TACKLE',))
    k = mon(ability='SWIFT_SWIM', mid='k')
    A, B = duel(t, k)
    engine.apply_switch(A, 0, B, CHART)
    assert A.field.weather == 'sand'
    k.hp = k.maxhp
    end_of_turn(k, A)
    assert k.hp == k.maxhp - k.maxhp // 16    # floored, like GetSixteenthMaxHP
    t.hp = t.maxhp
    end_of_turn(t, B)
    assert t.hp == t.maxhp                  # Rock types don't take sand damage
    base = k.stat('spe')
    A.field.weather = 'rain'
    assert k.stat('spe') == base * 2


def test_cloud_nine_suppresses_weather():
    a = mon(types=('FIRE',), moves=('FLAMETHROWER',))
    b = mon(ability='CLOUD_NINE', stats={'hp': 999})
    A, B = duel(a, b)
    A.field.weather, A.field.weather_turns = 'sun', 5
    assert engine.weather_of(a) is None


def test_substitute_absorbs_and_blocks_status():
    a = mon(moves=('SUBSTITUTE',))
    b = mon(moves=('TACKLE', 'TOXIC'))
    A, B = duel(a, b)
    act(A, B, 'SUBSTITUTE')
    assert a.hp == a.maxhp * 3 / 4 and a.sub_hp == a.maxhp / 4
    act(B, A, 'TOXIC')
    assert a.status is None
    hp = a.hp
    act(B, A, 'TACKLE')
    assert a.hp == hp and a.sub_hp < a.maxhp / 4


def test_baton_pass_passes_boosts():
    a = mon(moves=('BATON_PASS',))
    a2 = mon(mid='a2')
    b = mon()
    A, B = duel(a, b, a2=a2)
    a.stage['atk'], a.sub_hp = 2, 40
    act(A, B, 'BATON_PASS')
    assert A.mon is a2 and a2.stage['atk'] == 2 and a2.sub_hp == 40 and a.passes == 1


def test_trick_swaps_items_and_locks():
    a = mon(types=('PSYCHIC',), moves=('TRICK',), item='CHOICE_SCARF')
    b = mon(moves=('TOXIC', 'TACKLE'), item='LEFTOVERS')
    A, B = duel(a, b)
    act(A, B, 'TRICK')
    assert (a.item, b.item) == ('LEFTOVERS', 'CHOICE_SCARF')
    act(B, A, 'TOXIC')
    assert b.locked_move == 0               # now stuck using Toxic


def test_trick_room_and_turn_order():
    a = mon(moves=('TRICK_ROOM',))
    b = mon()
    A, B = duel(a, b)
    act(A, B, 'TRICK_ROOM')
    assert A.field.trick_room == engine.TRICK_ROOM_TURNS and a.trick_rooms == 1
    act(A, B, 'TRICK_ROOM')
    assert A.field.trick_room == 0          # using it again ends it


def test_rest_and_sleep_talk():
    a = mon(moves=('REST', 'SLEEP_TALK', 'TACKLE'))
    a.hp = 10
    b = mon()
    A, B = duel(a, b)
    act(A, B, 'REST')
    assert a.hp == a.maxhp and a.status == 'slp' and a.sleep == engine.REST_SLEEP_TURNS + 1
    assert engine.choose_move(A, B, MOVES, CHART) == 1
    act(A, B, 'SLEEP_TALK', random.Random(0))
    assert b.hp < b.maxhp                   # Sleep Talk called Tackle


def test_mean_look_traps_but_not_ghosts():
    a = mon(moves=('MEAN_LOOK',))
    b, b2 = mon(mid='b'), mon(mid='b2')
    A, B = duel(a, b, b2=b2)
    act(A, B, 'MEAN_LOOK')
    assert engine.is_trapped(B, A)
    g = mon(types=('GHOST',), mid='g')
    A, B = duel(a, g, b2=b2)
    act(A, B, 'MEAN_LOOK')
    assert not engine.is_trapped(B, A)


def test_shadow_tag_and_arena_trap():
    t = mon(ability='SHADOW_TAG')
    b = mon()
    A, B = duel(t, b)
    assert engine.is_trapped(B, A)
    d = mon(types=('GROUND',), ability='ARENA_TRAP')
    f = mon(types=('FLYING',))
    A, B = duel(d, f)
    assert not engine.is_trapped(B, A)      # airborne mons escape Arena Trap


def test_binding_chips_and_expires():
    a = mon(types=('FIRE',), moves=('FIRE_SPIN',), item='BINDING_BAND')
    b = mon(stats={'hp': 999})
    A, B = duel(a, b)
    act(A, B, 'FIRE_SPIN', random.Random(0))   # seed 0 hits (Fire Spin is 90%)
    assert b.bound in engine.BIND_TURNS and engine.is_trapped(B, A)
    hp = b.hp
    end_of_turn(b, A)
    assert hp - b.hp == b.maxhp // 6           # floored, like GetSixthMaxHP


def test_perish_song_faints():
    a = mon(moves=('PERISH_SONG',))
    b = mon()
    A, B = duel(a, b)
    act(A, B, 'PERISH_SONG')
    for _ in range(engine.PERISH_COUNT):
        end_of_turn(b, A)
    assert b.hp <= 0 and a.perish_kos == 1


def test_counter_returns_double():
    w = mon(types=('PSYCHIC',), moves=('COUNTER', 'MIRROR_COAT'), stats={'hp': 999})
    b = mon(moves=('TACKLE',))
    A, B = duel(w, b)
    act(B, A, 'TACKLE')
    taken = w.maxhp - w.hp
    act(A, B, 'COUNTER')
    assert b.maxhp - b.hp == 2 * taken
    hp = b.hp
    act(A, B, 'MIRROR_COAT')                # took no special damage: fails
    assert b.hp == hp


def test_pursuit_double_power():
    a = mon(types=('DARK',), moves=('PURSUIT',))
    b1, b2 = mon(stats={'hp': 999}, mid='b1'), mon(stats={'hp': 999}, mid='b2')
    A, B = duel(a, b1)
    perform(A, B, MOVES, CHART, random.Random(1), idx=0)
    single = b1.maxhp - b1.hp
    A, B = duel(a, b2)
    perform(A, B, MOVES, CHART, random.Random(1), idx=0, pursuit_switch=True)
    assert abs((b2.maxhp - b2.hp) - 2 * single) <= 1


def test_sun_healing_and_growth():
    a = mon(types=('GRASS',), moves=('HEALINGLIGHT', 'GROWTH'))
    b = mon()
    A, B = duel(a, b)
    A.field.weather, A.field.weather_turns = 'sun', 5
    a.hp = 1
    act(A, B, 'HEALINGLIGHT')
    assert abs(a.hp - (1 + a.maxhp * 2 / 3)) < 1e-6
    act(A, B, 'GROWTH')
    assert a.stage['atk'] == 2 and a.stage['spa'] == 2


def test_two_turn_moves_charge():
    a = mon(types=('GRASS',), moves=('SOLAR_BEAM', 'FLY'))
    b = mon(stats={'hp': 999}, moves=('TACKLE',))
    A, B = duel(a, b)
    act(A, B, 'SOLAR_BEAM')
    assert b.hp == b.maxhp and a.charging == 0
    act(A, B, 'SOLAR_BEAM')
    assert b.hp < b.maxhp and a.charging is None
    A.field.weather, A.field.weather_turns = 'sun', 5
    hp = b.hp
    act(A, B, 'SOLAR_BEAM')                 # no charge turn in sun
    assert b.hp < hp
    act(A, B, 'FLY')
    assert a.semi_inv
    hp = a.hp
    act(B, A, 'TACKLE')
    assert a.hp == hp                       # can't be hit in the air


def test_dream_eater_needs_sleep_and_drains():
    a = mon(types=('PSYCHIC',), moves=('DREAM_EATER',))
    a.hp = 100
    b = mon()
    A, B = duel(a, b)
    act(A, B, 'DREAM_EATER')
    assert b.hp == b.maxhp
    b.status, b.sleep = 'slp', 3
    act(A, B, 'DREAM_EATER')
    assert b.hp < b.maxhp and a.hp > 100


def test_future_sight_lands_two_turns_later():
    a = mon(types=('PSYCHIC',), moves=('FUTURE_SIGHT',))
    b = mon(stats={'hp': 999})
    A, B = duel(a, b)
    act(A, B, 'FUTURE_SIGHT')
    for _ in range(engine.FUTURE_SIGHT_TICKS - 1):
        engine.land_future_sight(B, MOVES, CHART, random.Random(0))
        assert b.hp == b.maxhp
    engine.land_future_sight(B, MOVES, CHART, random.Random(0))
    assert b.hp < b.maxhp and a.dmg_dealt > 0


def test_static_damage_and_jump_kick_crash():
    a = mon(types=('DRAGON',), moves=('DRAGON_RAGE',))
    b = mon()
    A, B = duel(a, b)
    act(A, B, 'DRAGON_RAGE')
    assert b.maxhp - b.hp == 40
    k = mon(types=('FIGHTING',), moves=('HI_JUMP_KICK',))
    g = mon(types=('GHOST',))
    A, B = duel(k, g)
    for seed in range(20):                  # find a seed that misses (90% accuracy)
        k.hp, k.pp = k.maxhp, [99]
        act(A, B, 'HI_JUMP_KICK', random.Random(seed))
        if k.hp < k.maxhp:
            break
    assert k.hp == k.maxhp / 2 or k.hp == k.maxhp


class Seq(random.Random):
    """A Random whose randrange/random return scripted values first."""
    def __init__(self, ranges=(), floats=()):
        super().__init__(0)
        self.ranges, self.floats = list(ranges), list(floats)

    def randrange(self, *a):
        return self.ranges.pop(0) if self.ranges else super().randrange(*a)

    def random(self):
        return self.floats.pop(0) if self.floats else super().random()


def test_damage_matches_rom_formula():
    # 150 Atk vs 150 Def, 40-power Tackle, L50, no STAB, neutral, top roll:
    # ((2*50/5+2) * 40 * 150 / 150) / 50 + 2 = 19
    a, b = mon(types=('FIRE',)), mon(stats={'hp': 999})
    dmg, eff, _ = engine.move_damage(a, b, MOVES['TACKLE'], CHART, Seq(ranges=[1, 15]))
    assert (dmg, eff) == (19, 1.0), (dmg, eff)
    dmg, _, _ = engine.move_damage(a, b, MOVES['TACKLE'], CHART, Seq(ranges=[1, 0]))
    assert dmg == 19 * 85 // 100            # bottom roll


def test_crits_ignore_screens_and_boost():
    a, b = mon(types=('FIRE',)), mon(stats={'hp': 999})
    A, B = duel(a, b)
    B.reflect = 5
    crit, _, n = engine.move_damage(a, b, MOVES['TACKLE'], CHART, Seq(ranges=[0, 15]))
    plain, _, _ = engine.move_damage(a, b, MOVES['TACKLE'], CHART, Seq(ranges=[1, 15]))
    assert n == 1 and crit > 2 * plain      # 1.5x and Reflect skipped
    # crit stage 3+ always crits; Battle Armor never does
    a.focus_energy, a.item = True, 'SCOPE_LENS'
    assert rom_damage.crit_stage(a, MOVES['TACKLE']) == 3
    assert rom_damage.roll_crit(a, b, MOVES['TACKLE'], random.Random(0))
    b.ability = 'BATTLE_ARMOR'
    assert not rom_damage.roll_crit(a, b, MOVES['TACKLE'], random.Random(0))


def test_confusion_self_hit():
    a, b = mon(moves=('TACKLE',)), mon(stats={'hp': 999})
    A, B = duel(a, b)
    a.confused = 3
    act(A, B, 'TACKLE', Seq(ranges=[0]))    # 1/3 roll hits itself
    assert a.maxhp - a.hp == rom_damage.confusion_damage(a) and b.hp == b.maxhp
    assert a.confused == 2
    a.confused = 1
    hp = a.hp
    act(A, B, 'TACKLE', Seq(ranges=[0]))    # count runs out: snaps out and attacks
    assert a.confused == 0 and a.hp == hp and b.hp < b.maxhp


def test_flinch_only_when_moving_first():
    a = mon(types=('DARK',), moves=('BITE',))
    b = mon(stats={'hp': 999}, moves=('TACKLE',))
    A, B = duel(a, b)
    act(A, B, 'BITE', Seq(floats=[0.0] * 5))
    assert b.flinched and a.flinches == 1
    act(B, A, 'TACKLE')
    assert a.hp == a.maxhp and not b.flinched
    b.flinched = False
    act(A, B, 'BITE', Seq(floats=[0.0] * 5), foe_moved=True)
    assert not b.flinched                   # target already moved
    b.ability = 'INNER_FOCUS'
    act(A, B, 'BITE', Seq(floats=[0.0] * 5))
    act(B, A, 'TACKLE')
    assert a.hp < a.maxhp                   # Inner Focus ignores the flinch


def test_explosion_not_doubled_and_solar_beam_not_halved():
    a = mon(moves=('EXPLOSION',))
    b = mon(stats={'hp': 9999})
    A, B = duel(a, b)
    act(A, B, 'EXPLOSION', Seq(ranges=[0, 1, 15]))     # accuracy roll, crit roll, damage roll
    want, _ = rom_damage.damage(a, b, MOVES['EXPLOSION'], CHART, power=250, roll=15)
    assert b.maxhp - b.hp == want
    g = mon(types=('GRASS',))
    A, B = duel(g, mon())
    A.field.weather, A.field.weather_turns = 'rain', 5
    rain, _ = engine.expected_damage(g, B.mon, MOVES['SOLAR_BEAM'], CHART)
    A.field.weather = None
    clear, _ = engine.expected_damage(g, B.mon, MOVES['SOLAR_BEAM'], CHART)
    assert rain == clear



# ---- step 1: mechanics ported from the ROM -------------------------------------
import mechanics  # noqa: E402


def test_status_type_immunities():
    for move, types, ok in (('TOXIC', ('STEEL',), False), ('TOXIC', ('POISON',), False),
                            ('THUNDER_WAVE', ('GROUND',), False), ('THUNDER_WAVE', ('ELECTRIC',), False),
                            ('WILL_O_WISP', ('FIRE',), False), ('TOXIC', ('NORMAL',), True)):
        if move not in MOVES:
            continue
        a, b = mon(moves=(move,)), mon(types=types)
        A, B = duel(a, b)
        act(A, B, move, Seq(ranges=[0] * 4))
        assert (b.status is not None) == ok, (move, types, b.status)
    a, b = mon(moves=('TOXIC',), ability='CORROSION'), mon(types=('STEEL',))
    A, B = duel(a, b)
    act(A, B, 'TOXIC', Seq(ranges=[0] * 4))
    assert b.status == 'tox'                # Corrosion poisons Steel types


def test_paralysis_halves_speed():
    a = mon(stats={'spe': 200})
    assert mechanics.speed(a) == 200
    a.status = 'par'
    assert mechanics.speed(a) == 100        # GetSpeed: x1/2, not 1/4
    a.ability = 'QUICK_FEET'
    assert mechanics.speed(a) == 300


def test_sleep_lasts_one_to_three_turns():
    lengths = set()
    for seed in range(60):
        a, b = mon(moves=('HYPNOSIS', 'TACKLE')), mon(moves=('TACKLE',))
        A, B = duel(a, b)
        b.status, b.sleep = 'slp', random.Random(seed).randint(2, 4)
        turns = 0
        while b.status == 'slp':
            act(B, A, 'TACKLE')
            turns += 1
        lengths.add(turns - 1)              # the last call is the waking turn
    assert lengths == {1, 2, 3}, lengths


def test_accuracy_and_evasion_stages():
    a, b = mon(moves=('TACKLE',)), mon()
    A, B = duel(a, b)
    m = MOVES['TACKLE']
    def rate():
        rng = random.Random(1)
        return sum(mechanics.accuracy_hits(a, b, m, rng) for _ in range(4000)) / 4000
    assert rate() == 1.0
    b.stage['eva'] = 1
    assert abs(rate() - 0.75) < 0.03        # +1 evasion = 3/4
    b.stage['eva'] = 6
    assert abs(rate() - 0.60) < 0.03        # link battles cap it at +2 (3/5)
    a.ability = 'KEEN_EYE'
    assert rate() == 1.0                    # Keen Eye ignores evasion boosts


def test_double_team_and_minimize():
    a = mon(moves=('DOUBLE_TEAM', 'MINIMIZE'))
    A, B = duel(a, mon())
    act(A, B, 'DOUBLE_TEAM')
    assert a.stage['eva'] == 1
    act(A, B, 'MINIMIZE')
    assert a.stage['eva'] == 3 and a.minimized


def test_secondary_status_moves():
    for move, st in (('BODY_SLAM', 'par'), ('THUNDER', 'par')):
        a, b = mon(types=('FIRE',), moves=(move,)), mon(stats={'hp': 999})
        A, B = duel(a, b)
        act(A, B, move, Seq(ranges=[0, 23, 15, 0]))   # hit, no crit, top roll, effect roll
        assert b.status == st, (move, b.status)
    a, b = mon(moves=('DYNAMICPUNCH',)), mon(stats={'hp': 999})
    A, B = duel(a, b)
    act(A, B, 'DYNAMICPUNCH', Seq(ranges=[0, 23, 15, 0]))
    assert b.confused


def test_endure_and_destiny_bond():
    a, b = mon(stats={'atk': 400}, moves=('TACKLE',)), mon(stats={'hp': 20}, moves=('ENDURE',))
    A, B = duel(a, b)
    act(B, A, 'ENDURE', random.Random(0))
    act(A, B, 'TACKLE')
    assert b.hp == 1 and not b.fainted
    c = mon(stats={'hp': 20}, moves=('DESTINY_BOND',))
    A, B = duel(a, c)
    act(B, A, 'DESTINY_BOND')
    act(A, B, 'TACKLE')
    assert c.fainted and a.fainted          # took the attacker down with it


def test_attract_needs_opposite_genders():
    a, b = mon(moves=('ATTRACT',)), mon()
    A, B = duel(a, b)
    a.gender, b.gender = 'M', 'M'
    act(A, B, 'ATTRACT')
    assert b.infatuated is None
    b.gender = 'F'
    act(A, B, 'ATTRACT')
    assert b.infatuated is a
    b.ability = 'OBLIVIOUS'
    b.infatuated = None
    act(A, B, 'ATTRACT')
    assert b.infatuated is None


def test_disable_and_pp():
    a, b = mon(moves=('DISABLE',)), mon(moves=('TACKLE', 'SCRATCH'))
    A, B = duel(a, b)
    act(B, A, 'TACKLE')
    act(A, B, 'DISABLE')
    assert b.disabled == 0
    assert engine.choose_move(B, A, MOVES, CHART) == 1
    b.pp = [0, 0]
    assert engine.choose_move(B, A, MOVES, CHART) == -1   # Struggle
    hp = b.hp
    perform(B, A, MOVES, CHART, random.Random(0), idx=-1)
    assert b.hp == hp - b.maxhp // 4        # Struggle recoil: 1/4 max HP


def test_hidden_power_type():
    a = mon(types=('NORMAL',), moves=('HIDDEN_POWER',))
    g = mon(types=('GRASS',), stats={'hp': 999})
    fire = engine.Pmon('x', {'types': ['NORMAL'], 'stats': dict(a.base)}, ['HIDDEN_POWER'],
                       hp_type='FIRE')
    d1, e1, _ = engine.move_damage(a, g, MOVES['HIDDEN_POWER'], CHART, Seq(ranges=[23, 15]))
    d2, e2, _ = engine.move_damage(fire, g, MOVES['HIDDEN_POWER'], CHART, Seq(ranges=[23, 15]),
                                   move_type='FIRE')
    assert e2 == 2.0 and d2 > d1


def test_sitrus_berry_and_intimidate():
    a, b = mon(stats={'atk': 300}, moves=('TACKLE',)), mon(item='SITRUS_BERRY')
    A, B = duel(a, b)
    b.hp = b.maxhp // 2 + 5
    act(A, B, 'TACKLE')
    assert b.item is None and b.berry_eaten == 'SITRUS_BERRY'
    i, t = mon(ability='INTIMIDATE', mid='i'), mon(ability='INNER_FOCUS', mid='t')
    A, B = duel(t, mon(mid='z'), b2=i)
    engine.apply_switch(B, 1, A, CHART)
    assert t.stage['atk'] == 0              # Inner Focus resists Intimidate
    d = mon(ability='DEFIANT', mid='d')
    A, B = duel(d, mon(mid='z2'), b2=mon(ability='INTIMIDATE', mid='i2'))
    engine.apply_switch(B, 1, A, CHART)
    assert d.stage['atk'] == 1              # -1, then Defiant +2


def test_explosion_misses_but_user_faints_and_damp():
    a = mon(moves=('EXPLOSION',))
    g = mon(types=('GHOST',))
    A, B = duel(a, g)
    act(A, B, 'EXPLOSION', Seq(ranges=[0, 23, 15]))
    assert a.fainted and g.hp == g.maxhp    # immune target, but the user still faints
    a2, dmp = mon(moves=('EXPLOSION',)), mon(ability='DAMP')
    A, B = duel(a2, dmp)
    act(A, B, 'EXPLOSION', Seq(ranges=[0, 23, 15]))
    assert not a2.fainted and dmp.hp == dmp.maxhp


def test_contact_punishers_and_weak_armor():
    a, b = mon(moves=('TACKLE',)), mon(item='ROCKY_HELMET', stats={'hp': 999})
    A, B = duel(a, b)
    act(A, B, 'TACKLE')
    assert a.maxhp - a.hp == a.maxhp // 6
    w = mon(ability='WEAK_ARMOR', stats={'hp': 999})
    A, B = duel(mon(moves=('TACKLE',)), w)
    act(A, B, 'TACKLE')
    assert w.stage['defe'] == -1 and w.stage['spe'] == 2


def test_magic_bounce_reflects_toxic():
    a, b = mon(moves=('TOXIC',)), mon(ability='MAGIC_BOUNCE')
    A, B = duel(a, b)
    act(A, B, 'TOXIC', Seq(ranges=[0] * 4))
    assert b.status is None and a.status == 'tox'


def test_lead_intimidate_survives_the_other_lead_entering():
    # both leads come out at the start; the second one sent out must keep
    # the first one's Intimidate drop (the turn oracle caught it being wiped)
    a, b = mon(ability='INTIMIDATE'), mon()
    A, B = duel(a, b)
    engine.apply_switch(A, 0, B, CHART)
    engine.apply_switch(B, 0, A, CHART)
    assert b.stage['atk'] == -1
    c, d = mon(), mon(ability='INTIMIDATE')
    C, D = duel(c, d)
    engine.apply_switch(C, 0, D, CHART)
    engine.apply_switch(D, 0, C, CHART)
    assert c.stage['atk'] == -1


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
