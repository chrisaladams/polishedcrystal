#!/usr/bin/env python3
"""Ground truth for mechanics.can_status: calls the ROM's CanPoisonTarget /
CanBurnTarget / CanParalyzeTarget / CanSleepTarget / CanFreezeTarget
(CanStatusTarget) under PyBoy, reads the zero flag ("z = can"), and compares
with the port on random targets: types, abilities (incl. Mold Breaker on the
user), held items, an existing status, Safeguard, Substitute, weather, and
the three modes (move / no-Substitute / orb, with Corrosion).

Run: python3 meta_sim/oracle_status.py [N] [--seed S]
"""
import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mechanics                                                 # noqa: E402
from oracle_pipeline import PipelineOracle, rgbasm_values, WEATHER_IDS, STATUS_BITS  # noqa: E402

TYPES = ['NORMAL', 'POISON', 'STEEL', 'FIRE', 'ELECTRIC', 'ICE', 'GRASS', 'WATER', 'GROUND']
ABILITIES = [None, 'IMMUNITY', 'PASTEL_VEIL', 'WATER_VEIL', 'LIMBER', 'INSOMNIA',
             'VITAL_SPIRIT', 'MAGMA_ARMOR', 'LEAF_GUARD', 'CORROSION', 'INFILTRATOR',
             'MOLD_BREAKER']
ROUTINE = {'psn': 'CanPoisonTarget', 'brn': 'CanBurnTarget', 'par': 'CanParalyzeTarget',
           'slp': 'CanSleepTarget', 'frz': 'CanFreezeTarget'}
MODES = {'move': 0, 'nosub': 1, 'orb': 2}


class M:
    def __init__(self, types, ability, item, status, side=None):
        self.types, self.ability, self.item, self.status = types, ability, item, status
        self.side = side


class S:
    def __init__(self, safeguard):
        self.safeguard = safeguard


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', type=int, nargs='?', default=4000)
    ap.add_argument('--seed', type=int, default=1)
    args = ap.parse_args()
    o = PipelineOracle()
    h = o.h
    items = [None, 'LEFTOVERS'] + sorted(k for k, v in mechanics.ITEM_DATA.items()
                                         if (v.get('held') or '').startswith('HELD_PREVENT_'))
    ids = rgbasm_values(TYPES + [a for a in ABILITIES if a] + [i for i in items if i]
                        + ['GUARD_SAFEGUARD', 'SUBSTATUS_SUBSTITUTE', 'EFFECT_POISON',
                           'EFFECT_TOXIC', 'EFFECT_NORMAL_HIT', 'EFFECTIVE'], None)
    rng = random.Random(args.seed)
    ok = bad = 0
    for _ in range(args.n):
        st = rng.choice(list(ROUTINE))
        mode = rng.choice(list(MODES))
        types = rng.sample(TYPES, rng.choice([1, 2]))
        target = M(types, rng.choice(ABILITIES), rng.choice(items),
                   rng.choice([None] * 5 + ['par', 'brn']), S(rng.random() < 0.25))
        user = M(['NORMAL'], rng.choice(ABILITIES), None, None)
        sub = rng.random() < 0.25
        weather = rng.choice([None, None, 'sun', 'rain'])
        eff = rng.choice(['EFFECT_POISON', 'EFFECT_TOXIC', 'EFFECT_NORMAL_HIT'])
        move = {'effect': eff}
        h.prepare()
        for v in ('wEnemySubStatus1', 'wPlayerSubStatus1', 'wMoveState', 'wPlayerGuards',
                  'wEnemyGuards', 'wEnemyFutureSightCount', 'wPlayerFutureSightCount'):
            o.w8(v, 0)
        for i in range(5):
            h.mem[h.addr('wPlayerSubStatus1') + i] = 0
            h.mem[h.addr('wEnemySubStatus1') + i] = 0
        o.w8('hBattleTurn', 1)                         # the enemy statuses the player mon
        if user.ability == 'MOLD_BREAKER' and mode == 'move':
            o.w8('wMoveState', 0x40)   # OPP_IGNOREABIL: set while a Mold Breaker's move runs
        a = h.addr('wBattleMonType1')
        h.mem[a], h.mem[a + 1] = ids[types[0]], ids[types[-1]]
        o.w8('wPlayerAbility', ids[target.ability] if target.ability else 0)
        o.w8('wEnemyAbility', ids[user.ability] if user.ability else 0)
        o.w8('wBattleMonItem', ids[target.item] if target.item else 0)
        o.w8('wEnemyMonItem', 0)
        o.w8('wBattleMonStatus', STATUS_BITS[target.status])
        o.w16('wBattleMonHP', 50)
        o.w16('wEnemyMonHP', 50)
        if target.side.safeguard:
            o.w8('wPlayerGuards', ids['GUARD_SAFEGUARD'])
        if sub:
            h.mem[h.addr('wPlayerSubStatus4')] |= 1 << ids['SUBSTATUS_SUBSTITUTE']
        o.w8('wBattleWeather', WEATHER_IDS[weather])
        o.w8('wWeatherCount', 5 if weather else 0)
        o.w8('wTypeModifier', ids['EFFECTIVE'])
        o.w8('wEnemyMoveStructEffect', ids[eff])
        o._run(ROUTINE[st], bc=MODES[mode] << 8, max_frames=10)
        rom_can = bool(h.reg.F & 0x80)                 # z flag
        port = mechanics.can_status(target, st, user=user, source=mode, move=move,
                                    weather=weather, sub_blocked=sub)
        if rom_can == port:
            ok += 1
        else:
            bad += 1
            if bad <= 8:
                print(f'  MISMATCH rom {rom_can} port {port}: {st} mode {mode} target {types} '
                      f'{target.ability}/{target.item}/{target.status} safeguard '
                      f'{target.side.safeguard} sub {sub}; user {user.ability}; {eff}; {weather}')
    h.stop()
    print(f'{ok}/{ok + bad} status scenarios match the ROM exactly')
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
