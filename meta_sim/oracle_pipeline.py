#!/usr/bin/env python3
"""Ground truth for the battle engine's damage: rom_damage.py vs the ROM.

For each random scenario this sets up a real battle in WRAM (attacker as the
enemy mon, defender as the player's: species, L50 stats, types, ability, held
item, status, HP, stat stages, weather, screens, crit flag, the move struct)
and runs the game's own BattleCommand_damagestats -> damagecalc -> stab ->
conditionalboost under PyBoy, then compares wCurDamage with rom_damage.damage()
for the same scenario (unrolled, i.e. before damagevariation, which is a
plain integer formula checked separately).

Scenarios mix damage-relevant abilities and items, burns and other statuses,
all stat stages, the four weathers, Reflect / Light Screen, crits, low HP
(pinch abilities) and full HP (Multiscale), Eviolite on unevolved mons.

Usage (from the repo root, after `make`):
  python3 meta_sim/oracle_pipeline.py            # 3000 scenarios
  python3 meta_sim/oracle_pipeline.py 20000 --seed 5
"""
import argparse
import json
import os
import random
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from oracle import StatOracle, load_species_ids          # noqa: E402
from stats import mon_stats                                # noqa: E402
import items                                               # noqa: E402
import rom_damage                                          # noqa: E402

ABILITIES = ['TECHNICIAN', 'HUGE_POWER', 'HUSTLE', 'OVERGROW', 'BLAZE', 'TORRENT', 'SWARM',
             'SHEER_FORCE', 'ANALYTIC', 'SOLAR_POWER', 'IRON_FIST', 'TOUGH_CLAWS',
             'MEGA_LAUNCHER', 'SAND_FORCE', 'RECKLESS', 'GUTS', 'PIXILATE', 'GALVANIZE',
             'SHARPNESS', 'ADAPTABILITY', 'TINTED_LENS', 'SNIPER', 'SCRAPPY',
             'MULTISCALE', 'MARVEL_SCALE', 'THICK_FAT', 'DRY_SKIN', 'FUR_COAT', 'FLUFFY',
             'SOLID_ROCK', 'FILTER', 'UNAWARE', 'INFILTRATOR',
             'INTIMIDATE', 'PRESSURE', 'KEEN_EYE']
ATT_ITEMS = [None, 'CHOICE_BAND', 'CHOICE_SPECS', 'LIFE_ORB', 'LEFTOVERS', 'EXPERT_BELT',
             'MUSCLE_BAND', 'WISE_GLASSES']
DEF_ITEMS = [None, 'ASSAULT_VEST', 'LEFTOVERS', 'EVIOLITE']
# moves whose damage depends on battle commands this harness doesn't replay
SKIP_EFFECTS = {'EFFECT_LEVEL_DAMAGE', 'EFFECT_SUPER_FANG', 'EFFECT_STATIC_DAMAGE',
                'EFFECT_COUNTER', 'EFFECT_GYRO_BALL', 'EFFECT_REVERSAL', 'EFFECT_RETURN',
                'EFFECT_MAGNITUDE', 'EFFECT_LOW_KICK', 'EFFECT_MULTI_HIT', 'EFFECT_PSYSTRIKE',
                'EFFECT_CONVERSION', 'EFFECT_FUTURE_SIGHT', 'EFFECT_HIDDEN_POWER',
                'EFFECT_EXPLOSION', 'EFFECT_PURSUIT'}
SKIP_MOVES = {'AVALANCHE', 'PURSUIT', 'STRUGGLE'}
STATUS_BITS = {None: 0, 'psn': 1 << 3, 'brn': 1 << 4, 'frz': 1 << 5, 'par': 1 << 6,
               'tox': (1 << 3) | (1 << 7), 'slp': 3}
WEATHER_IDS = {None: 0, 'rain': 1, 'sun': 2, 'sand': 3, 'hail': 4}


def rgbasm_values(names, files):
    """Evaluate constant names with rgbasm, as the build does."""
    with tempfile.NamedTemporaryFile('w', suffix='.asm', delete=False) as f:
        for n in names:
            f.write(f'IF DEF({n})\nPRINTLN "{n}={{d:{n}}}"\nENDC\n')
        path = f.name
    try:
        out = subprocess.run(['rgbasm', '-P', 'includes.asm', '-o', os.devnull, path],
                             cwd=ROOT, capture_output=True, text=True).stdout
    finally:
        os.unlink(path)
    return {k: int(v) for k, v in (l.split('=', 1) for l in out.splitlines() if '=' in l)}


class Side:
    def __init__(self, reflect=0, light_screen=0):
        self.reflect, self.light_screen = reflect, light_screen


class Mon:
    """Just enough of engine.Pmon for rom_damage."""
    def __init__(self, base, types, ability, item, status, hp, stage, side):
        self.base, self.types, self.ability, self.item = base, types, ability, item
        self.status, self.maxhp, self.hp, self.stage, self.side = status, base['hp'], hp, stage, side
        self.flash_fire = False
        self.eviolite_ok = True


class PipelineOracle(StatOracle):
    def __init__(self):
        super().__init__()
        moves = json.load(open(os.path.join(HERE, 'data', 'moves.json')))
        self.moves = moves
        types = sorted({m['type'] for m in moves.values()})
        effects = sorted({m['effect'] for m in moves.values()})
        names = (list(moves) + types + effects + ABILITIES
                 + [i for i in ATT_ITEMS + DEF_ITEMS if i])
        self.ids = rgbasm_values(names, None)
        missing = [n for n in ABILITIES + [i for i in ATT_ITEMS + DEF_ITEMS if i]
                   if n not in self.ids]
        if missing:
            raise SystemExit(f'constants not found: {missing}')

    def w16(self, name, v):
        self.h.write16(self.h.addr(name), v)

    def w8(self, name, v):
        self.h.mem[self.h.addr(name)] = v & 0xFF

    def setup_mon(self, prefix, sid, mon, types, ability, item, status, hp):
        w8, w16, ids = self.w8, self.w16, self.ids
        w8(f'{prefix}Species', sid)
        w8(f'{prefix}Form', 0)
        w8(f'{prefix}Item', ids[item] if item else 0)
        w8(f'{prefix}Level', 50)
        w8(f'{prefix}Status', STATUS_BITS[status])
        w16(f'{prefix}HP', hp)
        w16(f'{prefix}MaxHP', mon.base['hp'])
        for k, name in (('atk', 'Attack'), ('defe', 'Defense'), ('spe', 'Speed'),
                        ('spa', 'SpAtk'), ('spd', 'SpDef')):
            w16(f'{prefix}{name}', mon.base[k])
        a = self.h.addr(f'{prefix}Type1')
        self.h.mem[a] = ids[types[0]]
        self.h.mem[a + 1] = ids[types[-1]]
        w8(f'{prefix}Ability', ids[ability])
        # battle vars read the live ability from wEnemyAbility/wPlayerAbility
        w8('wEnemyAbility' if prefix == 'wEnemyMon' else 'wPlayerAbility', ids[ability])

    def rom(self, sc):
        """Run the ROM's damage commands for scenario sc; returns wCurDamage."""
        h, w8 = self.h, self.w8
        h.prepare()
        att, dfn, mv = sc['att'], sc['dfn'], sc['move']
        for name in ('wEnemySubStatus1', 'wEnemySubStatus2', 'wEnemySubStatus3',
                     'wEnemySubStatus4', 'wPlayerSubStatus1', 'wEnemyFutureSightCount',
                     'wPlayerFutureSightCount', 'wAttackMissed', 'wBattleType', 'wMoveState'):
            w8(name, 0)
        for i in range(4):
            h.mem[h.addr('wPlayerSubStatus1') + i] = 0
            h.mem[h.addr('wEnemySubStatus1') + i] = 0
        self.setup_mon('wEnemyMon', sc['att_sid'], att, att.types, att.ability, att.item,
                       att.status, att.hp)
        self.setup_mon('wBattleMon', sc['dfn_sid'], dfn, dfn.types, dfn.ability, dfn.item,
                       dfn.status, dfn.hp)
        # party structs: the attacker's level comes from its party record
        # (TrueUserPartyAttr), and Eviolite's evolution check reads the defender's
        w8('wCurOTMon', 0)
        w8('wOTPartyMon1Species', sc['att_sid'])
        w8('wOTPartyMon1Item', self.ids[att.item] if att.item else 0)
        w8('wOTPartyMon1Level', 50)
        w8('wOTPartyMon1Form', 0)
        w8('wPartyMon1Level', 50)
        w8('wCurBattleMon', 0)
        h.mem[h.addr('wPartyMon1')] = sc['dfn_sid']
        h.mem[h.addr('wPartyMon1') + (h.addr('wPartyMon1Form') - h.addr('wPartyMon1'))] = 0
        h.mem[h.addr('wPartyMon1') + 1] = self.ids[dfn.item] if dfn.item else 0
        order = ['atk', 'defe', 'spe', 'spa', 'spd']
        for i in range(7):
            h.mem[h.addr('wEnemyStatLevels') + i] = 7
            h.mem[h.addr('wPlayerStatLevels') + i] = 7
        for i, k in enumerate(order):
            h.mem[h.addr('wEnemyStatLevels') + i] = att.stage[k] + 7
            h.mem[h.addr('wPlayerStatLevels') + i] = dfn.stage[k] + 7
        w8('wBattleWeather', WEATHER_IDS[sc['weather']])
        w8('wWeatherCount', 5 if sc['weather'] else 0)
        w8('wPlayerScreens', (5 if dfn.side.reflect else 0) | ((5 << 4) if dfn.side.light_screen else 0))
        w8('wEnemyGoesFirst', 0 if sc['moved_second'] else 1)
        w8('wMoveHitState', 1 if sc['crit'] else 0)
        w8('hBattleTurn', 1)
        w8('wEnemyMoveStructAnimation', self.ids[mv['id']])
        w8('wCurEnemyMove', self.ids[mv['id']])  # BATTLE_VARS_MOVE (contact checks)
        w8('wEnemyMoveStructEffect', self.ids[mv['effect']])
        w8('wEnemyMoveStructPower', mv['power'])
        w8('wEnemyMoveStructType', self.ids[mv['type']])
        w8('wEnemyMoveStructAccuracy', 100)
        w8('wEnemyMoveStructEffectChance', mv['chance'])
        w8('wEnemyMoveStructCategory', {'PHYSICAL': 0, 'SPECIAL': 1}[mv['cat']])

        self._run('BattleCommand_damagestats', max_frames=10)
        b, c, d, e = h.reg.B, h.reg.C, h.reg.D, h.reg.E
        self._run('BattleCommand_damagecalc', bc=(b << 8) | c, de=(d << 8) | e, max_frames=10)
        calc = h.read16(h.addr('wCurDamage'))
        self._run('BattleCommand_stab', max_frames=10)
        self.trace = {'atk': b, 'def': c, 'power': d, 'level': e, 'after_calc': calc,
                      'after_stab': h.read16(h.addr('wCurDamage')),
                      'matchup': h.mem[h.addr('wTypeMatchup')]}
        if h.mem[h.addr('wAttackMissed')]:
            return 0
        self._run('BattleCommand_conditionalboost', max_frames=10)
        return h.read16(h.addr('wCurDamage'))


def scenario(rng, pool, species_ids, moves, chart_types):
    def pick():
        while True:
            name, m = rng.choice(pool)
            sid = species_ids.get(name)
            if sid and sid <= 254:
                return name, sid, m
    stage = lambda: {k: (rng.randint(-6, 6) if rng.random() < 0.4 else 0)
                     for k in ('atk', 'defe', 'spa', 'spd', 'spe')}
    reflect, screen = rng.random() < 0.2, rng.random() < 0.2
    (an, asid, am), (dn, dsid, dm) = pick(), pick()
    a_base, d_base = mon_stats(am['stats']), mon_stats(dm['stats'])
    status = lambda: rng.choice([None] * 4 + ['brn', 'psn', 'tox', 'par', 'slp'])
    a_item = rng.choice(ATT_ITEMS)
    d_item = rng.choice(DEF_ITEMS)
    a_hp = a_base['hp'] if rng.random() < 0.5 else rng.randint(1, a_base['hp'])
    d_hp = d_base['hp'] if rng.random() < 0.5 else rng.randint(1, d_base['hp'])
    att = Mon(a_base, am['types'], rng.choice(ABILITIES),
              a_item, status(), a_hp, stage(), Side())
    dfn = Mon(d_base, dm['types'], rng.choice(ABILITIES), d_item, status(), d_hp, stage(),
              Side(reflect, screen))
    dfn.eviolite_ok = not dm.get('fully_evolved') and dn not in items.EVIOLITE_EXCLUDED
    mv = rng.choice(moves)
    return {'att': att, 'dfn': dfn, 'att_sid': asid, 'dfn_sid': dsid, 'move': mv,
            'weather': rng.choice([None, None, 'sun', 'rain', 'sand', 'hail']),
            'crit': rng.random() < 0.15, 'moved_second': rng.random() < 0.5,
            'names': (an, dn)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', type=int, nargs='?', default=3000)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--show', type=int, default=10, help='mismatches to print')
    args = ap.parse_args()
    o = PipelineOracle()
    mons = json.load(open(os.path.join(HERE, 'data', 'pokemon.json')))
    chart = json.load(open(os.path.join(HERE, 'data', 'typechart.json')))
    pool = [(k, v) for k, v in mons.items() if 'stats' in v and v.get('abilities')]
    species_ids = load_species_ids()
    moves = [m for m in o.moves.values() if m['cat'] != 'STATUS' and m['power'] > 1
             and m['effect'] not in SKIP_EFFECTS and m['id'] not in SKIP_MOVES]
    rng = random.Random(args.seed)
    ok = bad = 0
    shown = 0
    for _ in range(args.n):
        sc = scenario(rng, pool, species_ids, moves, None)
        want = o.rom(sc)
        got, _ = rom_damage.damage(sc['att'], sc['dfn'], sc['move'], chart,
                                   power=sc['move']['power'], weather=sc['weather'],
                                   crit=sc['crit'], roll=None, moved_second=sc['moved_second'])
        if got == want:
            ok += 1
        else:
            bad += 1
            if shown < args.show:
                shown += 1
                a, d = sc['att'], sc['dfn']
                print(f"  MISMATCH rom={want} port={got}: {sc['names'][0]} ({a.ability}, {a.item}, "
                      f"{a.status}, hp {a.hp}/{a.maxhp}, stages {a.stage}) uses {sc['move']['id']} "
                      f"on {sc['names'][1]} ({d.ability}, {d.item}, {d.status}, hp {d.hp}/{d.maxhp}, "
                      f"stages {d.stage}, reflect {d.side.reflect}, screen {d.side.light_screen}); "
                      f"weather {sc['weather']}, crit {sc['crit']}, moved_second {sc['moved_second']}")
    o.h.stop()
    print(f'{ok}/{ok + bad} scenarios match the ROM exactly ({100 * ok / (ok + bad):.2f}%)')
    return 0 if bad == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
