#!/usr/bin/env python3
"""Ground truth for mechanics.speed: runs the ROM's GetSpeed under PyBoy on
random scenarios (stat stage, paralysis, Quick Feet, Unburden, weather Speed
abilities, Choice Scarf, Iron Ball, Quick Powder on Ditto) and compares.

Run: python3 meta_sim/oracle_speed.py [N] [--seed S]
"""
import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mechanics                                                 # noqa: E402
from oracle_pipeline import PipelineOracle, rgbasm_values, WEATHER_IDS, STATUS_BITS  # noqa: E402
from oracle import load_species_ids                              # noqa: E402

ABILITIES = [None, 'QUICK_FEET', 'UNBURDEN', 'SWIFT_SWIM', 'CHLOROPHYLL', 'SAND_RUSH',
             'SLUSH_RUSH']
ITEMS = [None, 'CHOICE_SCARF', 'IRON_BALL', 'QUICK_POWDER', 'LEFTOVERS']


class M:
    def __init__(self, sid_name, spe, stage, status, ability, item, unburden):
        self.id, self.base, self.stage = sid_name, {'spe': spe}, {'spe': stage}
        self.status, self.ability, self.item, self.unburden = status, ability, item, unburden
        self.fainted = False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', type=int, nargs='?', default=3000)
    ap.add_argument('--seed', type=int, default=1)
    args = ap.parse_args()
    o = PipelineOracle()
    h = o.h
    ids = rgbasm_values([a for a in ABILITIES if a] + [i for i in ITEMS if i]
                        + ['SUBSTATUS_UNBURDEN'], None)
    sids = load_species_ids()
    rng = random.Random(args.seed)
    ok = bad = 0
    for _ in range(args.n):
        name = 'ditto' if rng.random() < 0.2 else rng.choice(['pikachu', 'snorlax', 'jolteon'])
        mon = M(name, rng.randint(5, 400), rng.choice([0, 0] + list(range(-6, 7))),
                rng.choice([None, None, 'par', 'brn', 'psn', 'slp']), rng.choice(ABILITIES),
                rng.choice(ITEMS), rng.random() < 0.5)
        weather = rng.choice([None, 'sun', 'rain', 'sand', 'hail'])
        h.prepare()
        for v in ('wEnemySubStatus1', 'wPlayerSubStatus1', 'wMoveState',
                  'wEnemyFutureSightCount', 'wPlayerFutureSightCount', 'wPlayerAbility'):
            o.w8(v, 0)
        if mon.ability == 'UNBURDEN' and mon.unburden:
            h.mem[h.addr('wEnemySubStatus1')] |= 1 << ids['SUBSTATUS_UNBURDEN']
        o.w8('hBattleTurn', 1)
        o.w8('wEnemyMonSpecies', sids[name])
        o.w8('wEnemyMonForm', 0)
        o.w16('wEnemyMonSpeed', mon.base['spe'])
        o.w16('wEnemyMonHP', 50)
        o.w8('wEnemyMonStatus', STATUS_BITS[mon.status])
        o.w8('wEnemyAbility', ids[mon.ability] if mon.ability else 0)
        o.w8('wEnemyMonItem', ids[mon.item] if mon.item else 0)
        h.mem[h.addr('wEnemySpeLevel')] = 7 + mon.stage['spe']
        o.w8('wBattleWeather', WEATHER_IDS[weather])
        o.w8('wWeatherCount', 5 if weather else 0)
        o._run('GetSpeed', max_frames=10)
        got = (h.reg.B << 8) | h.reg.C
        want = mechanics.speed(mon, weather)
        if got == want:
            ok += 1
        else:
            bad += 1
            if bad <= 8:
                print(f'  MISMATCH rom {got} port {want}: {vars(mon)} weather {weather}')
    h.stop()
    print(f'{ok}/{ok + bad} speed scenarios match the ROM exactly')
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
