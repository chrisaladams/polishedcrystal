#!/usr/bin/env python3
"""Ground truth for mechanics.accuracy_hits: runs the ROM's
BattleCommand_checkhit under PyBoy and compares it with the port.

In a link battle BattleRandom reads the shared wLinkBattleRNs buffer, so the
accuracy roll can be set exactly. For each random scenario the port gives a
threshold v (the move hits when the 0-99 roll is below v); the ROM is run with
the roll at v-1 (must hit) and at v (must miss), which pins v down exactly.

Run: python3 meta_sim/oracle_accuracy.py [N] [--seed S]
"""
import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import mechanics                                         # noqa: E402
from oracle_pipeline import PipelineOracle, rgbasm_values, WEATHER_IDS   # noqa: E402

ABILITIES = [None, 'COMPOUND_EYES', 'HUSTLE', 'NO_GUARD', 'KEEN_EYE', 'UNAWARE',
             'TANGLED_FEET', 'SAND_VEIL', 'SNOW_CLOAK', 'WONDER_SKIN', 'ILLUMINATE', 'MINDS_EYE']
ITEMS = [None, 'WIDE_LENS', 'ZOOM_LENS', 'BRIGHTPOWDER']


class M:
    """Just enough of a Pmon for mechanics.accuracy_hits."""
    def __init__(self, ability, item, acc, eva, confused=False, identified=False):
        self.ability, self.item = ability, item
        self.stage = {'acc': acc, 'eva': eva}
        self.types = ['NORMAL']
        self.confused, self.identified = confused, identified
        self.semi_inv, self.minimized = None, False


class AccuracyOracle(PipelineOracle):
    def __init__(self):
        super().__init__()
        self.ids.update(rgbasm_values([a for a in ABILITIES if a] + [i for i in ITEMS if i]
                                      + ['LINK_COLOSSEUM', 'EFFECTIVE'], None))

    def rom_hits(self, sc, roll):
        h, w8, ids = self.h, self.w8, self.ids
        h.prepare()
        att, dfn, mv = sc['att'], sc['dfn'], sc['move']
        for name in ('wEnemySubStatus1', 'wPlayerSubStatus1', 'wMoveState', 'wAttackMissed',
                     'wEnemyFutureSightCount', 'wPlayerFutureSightCount', 'wPlayerGuards',
                     'wEnemyGuards'):
            w8(name, 0)
        for i in range(5):
            h.mem[h.addr('wPlayerSubStatus1') + i] = 0
            h.mem[h.addr('wEnemySubStatus1') + i] = 0
        if dfn.confused:
            h.mem[h.addr('wPlayerSubStatus3')] |= 0x80      # SUBSTATUS_CONFUSED (bit 7)
        if dfn.identified:
            h.mem[h.addr('wPlayerSubStatus1')] |= 1 << self.bit('SUBSTATUS_IDENTIFIED')
        w8('wEnemyAbility', ids[att.ability] if att.ability else 0)
        w8('wPlayerAbility', ids[dfn.ability] if dfn.ability else 0)
        for prefix, mon in (('wEnemyMon', att), ('wBattleMon', dfn)):
            w8(f'{prefix}Item', ids[mon.item] if mon.item else 0)
            w8(f'{prefix}Species', 1)
            w8(f'{prefix}Form', 0)
            w8(f'{prefix}Status', 0)
            self.w16(f'{prefix}HP', 100)
        w8('wOTPartyMon1Item', ids[att.item] if att.item else 0)
        w8('wCurOTMon', 0)
        w8('wCurBattleMon', 0)
        for i in range(7):
            h.mem[h.addr('wEnemyStatLevels') + i] = 7
            h.mem[h.addr('wPlayerStatLevels') + i] = 7
        h.mem[h.addr('wEnemyAccLevel')] = 7 + att.stage['acc']
        h.mem[h.addr('wPlayerEvaLevel')] = 7 + dfn.stage['eva']
        w8('wBattleWeather', WEATHER_IDS[sc['weather']])
        w8('wWeatherCount', 5 if sc['weather'] else 0)
        w8('wEnemyGoesFirst', 0 if sc['target_first'] else 1)
        w8('hBattleTurn', 1)
        w8('wTypeModifier', ids['EFFECTIVE'])
        w8('wCurEnemyMove', ids[mv['id']])
        w8('wEnemyMoveStructAnimation', ids[mv['id']])
        w8('wEnemyMoveStructEffect', ids[mv['effect']])
        w8('wEnemyMoveStructPower', mv['power'])
        w8('wEnemyMoveStructType', ids[mv['type']])
        w8('wEnemyMoveStructAccuracy', mv['acc'] & 0xFF)
        w8('wEnemyMoveStructCategory', {'PHYSICAL': 0, 'SPECIAL': 1, 'STATUS': 2}[mv['cat']])
        w8('wLinkMode', ids['LINK_COLOSSEUM'])
        w8('wLinkBattleRNCount', 0)
        for i in range(10):
            h.mem[h.addr('wLinkBattleRNs') + i] = roll
        if mv['effect'] == 'EFFECT_THUNDER':
            self._run('BattleCommand_thunderaccuracy', max_frames=10)
        self._run('BattleCommand_checkhit', max_frames=20)
        return h.mem[h.addr('wAttackMissed')] == 0

    def bit(self, name):
        if not hasattr(self, '_bits'):
            self._bits = {}
        if name not in self._bits:
            self._bits[name] = rgbasm_values([name], None)[name]
        return self._bits[name]


def port_threshold(sc):
    """The smallest roll that misses, by asking the port with a fixed roll."""
    class Fixed:
        def __init__(self, r):
            self.r = r

        def randrange(self, n):
            return self.r
    for r in range(100):
        if not mechanics.accuracy_hits(sc['att'], sc['dfn'], sc['move'], Fixed(r),
                                       weather=sc['weather'],
                                       target_moved_first=sc['target_first']):
            return r
    return 100


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', type=int, nargs='?', default=2000)
    ap.add_argument('--seed', type=int, default=1)
    args = ap.parse_args()
    o = AccuracyOracle()
    rng = random.Random(args.seed)
    moves = [m for m in o.moves.values() if 'checkhit' in m.get('script', ())
             and m['effect'] not in ('EFFECT_OHKO', 'EFFECT_DREAM_EATER') and m['id'] in o.ids]
    ok = bad = 0
    for _ in range(args.n):
        stage = lambda: rng.choice([0, 0, 0] + list(range(-6, 7)))
        att = M(rng.choice(ABILITIES), rng.choice(ITEMS), stage(), 0)
        dfn = M(rng.choice(ABILITIES), rng.choice(ITEMS), 0, stage(),
                confused=rng.random() < 0.2, identified=rng.random() < 0.15)
        sc = {'att': att, 'dfn': dfn, 'move': rng.choice(moves),
              'weather': rng.choice([None, None, 'sun', 'rain', 'sand', 'hail']),
              'target_first': rng.random() < 0.5}
        v = port_threshold(sc)
        good = True
        if v > 0:
            good &= o.rom_hits(sc, v - 1)
        if v < 100:
            good &= not o.rom_hits(sc, v)
        if good:
            ok += 1
        else:
            bad += 1
            if bad <= 8:
                print(f"  MISMATCH port threshold {v}: {sc['move']['id']} acc {sc['move']['acc']}, "
                      f"att {att.ability}/{att.item} acc{att.stage['acc']:+d}, "
                      f"dfn {dfn.ability}/{dfn.item} eva{dfn.stage['eva']:+d} conf {dfn.confused} "
                      f"id {dfn.identified}, weather {sc['weather']}, target first {sc['target_first']}")
    o.h.stop()
    print(f'{ok}/{ok + bad} accuracy scenarios match the ROM exactly')
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
