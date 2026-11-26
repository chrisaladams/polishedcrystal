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
             'INTIMIDATE', 'PRESSURE', 'KEEN_EYE', 'RIVALRY', 'MOLD_BREAKER']
ATT_ITEMS = [None, 'CHOICE_BAND', 'CHOICE_SPECS', 'LIFE_ORB', 'LEFTOVERS', 'EXPERT_BELT',
             'MUSCLE_BAND', 'WISE_GLASSES', 'THICK_CLUB', 'LIGHT_BALL', 'CHOICE_SCARF',
             'CHARCOAL', 'MYSTIC_WATER', 'MAGNET', 'BLACK_BELT', 'SILK_SCARF', 'FAIRYFEATHER',
             'NEVERMELTICE', 'SOFT_SAND', 'PUNCHINGLOVE', 'METRONOME_I', 'SCOPE_LENS']
DEF_ITEMS = [None, 'ASSAULT_VEST', 'LEFTOVERS', 'EVIOLITE', 'METAL_POWDER']
# species whose items only work for them (UserValidBattleItem), picked more often
FORM_IDS = {'_plain': 1, '_alolan': 2, '_galarian': 3, '_hisuian': 4, '_paldean': 5}


def form_of(name):
    return next((v for k, v in FORM_IDS.items() if name and name.endswith(k)), 0)


ITEM_SPECIES = {'cubone': 'THICK_CLUB', 'marowak_plain': 'THICK_CLUB',
                'marowak_alolan': 'THICK_CLUB', 'pikachu': 'LIGHT_BALL'}
HP_TYPES = ['FIGHTING', 'FLYING', 'POISON', 'GROUND', 'ROCK', 'BUG', 'GHOST', 'STEEL',
            'FIRE', 'WATER', 'GRASS', 'ELECTRIC', 'PSYCHIC', 'ICE', 'DRAGON', 'DARK', 'FAIRY']
# moves whose damage depends on battle commands this harness doesn't replay
SKIP_EFFECTS = {'EFFECT_LEVEL_DAMAGE', 'EFFECT_SUPER_FANG', 'EFFECT_STATIC_DAMAGE',
                'EFFECT_COUNTER', 'EFFECT_GYRO_BALL', 'EFFECT_REVERSAL', 'EFFECT_RETURN',
                'EFFECT_MAGNITUDE', 'EFFECT_LOW_KICK', 'EFFECT_MULTI_HIT',
                'EFFECT_CONVERSION', 'EFFECT_FUTURE_SIGHT',
                'EFFECT_EXPLOSION', 'EFFECT_PURSUIT'}
SKIP_MOVES = {'AVALANCHE', 'PURSUIT', 'STRUGGLE'}
STATUS_BITS = {None: 0, 'psn': 1 << 3, 'brn': 1 << 4, 'frz': 1 << 5, 'par': 1 << 6,
               'tox': (1 << 3) | (1 << 7), 'slp': 3}
WEATHER_IDS = {None: 0, 'rain': 1, 'sun': 2, 'sand': 3, 'hail': 4}


def asm_for_build(text):
    """The source as this build assembles it: only the taken side of each
    `if DEF(FAITHFUL)` / `if !DEF(FAITHFUL)` block (LE_FAITHFUL=1: the
    faithful build), for tests that read generated data tables."""
    faithful = bool(os.environ.get('LE_FAITHFUL'))
    out, stack = [], []
    for line in text.split('\n'):
        code = line.split(';')[0].strip()
        if code in ('if DEF(FAITHFUL)', 'if !DEF(FAITHFUL)'):
            stack.append(faithful == (code == 'if DEF(FAITHFUL)'))
        elif code == 'else' and stack:
            stack[-1] = not stack[-1]
        elif code == 'endc' and stack:
            stack.pop()
        elif all(stack):
            out.append(line)
    return '\n'.join(out)


def rgbasm_values(names, files):
    """Evaluate constant names with rgbasm, as the build does."""
    with tempfile.NamedTemporaryFile('w', suffix='.asm', delete=False) as f:
        for n in names:
            f.write(f'IF DEF({n})\nPRINTLN "{n}={{d:{n}}}"\nENDC\n')
        path = f.name
    try:
        # (LE_FAITHFUL=1: the faithful build's values, for testing that ROM)
        flags = ['-DFAITHFUL'] if os.environ.get('LE_FAITHFUL') else []
        out = subprocess.run(['rgbasm', *flags, '-P', 'includes.asm', '-o', os.devnull, path],
                             cwd=ROOT, capture_output=True, text=True).stdout
    finally:
        os.unlink(path)
    return {k: int(v) for k, v in (l.split('=', 1) for l in out.splitlines() if '=' in l)}


class Side:
    def __init__(self, reflect=0, light_screen=0):
        self.reflect, self.light_screen = reflect, light_screen


class Mon:
    """Just enough of engine.Pmon for rom_damage."""
    def __init__(self, base, types, ability, item, status, hp, stage, side, mid=None,
                 gender=None):
        self.base, self.types, self.ability, self.item = base, types, ability, item
        self.status, self.maxhp, self.hp, self.stage, self.side = status, base['hp'], hp, stage, side
        self.flash_fire = False
        self.eviolite_ok = True
        self.id, self.gender = mid, gender
        self.metronome_count = 0


class PipelineOracle(StatOracle):
    def __init__(self):
        super().__init__()
        moves = json.load(open(os.path.join(HERE, 'data', 'moves.json')))
        self.moves = moves
        types = sorted({m['type'] for m in moves.values()})
        effects = sorted({m['effect'] for m in moves.values()})
        names = (list(moves) + types + HP_TYPES + effects + ABILITIES
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
        a_form, d_form = form_of(sc['names'][0]), form_of(sc['names'][1])
        w8('wEnemyMonForm', a_form)
        w8('wBattleMonForm', d_form)
        w8('wOTPartyMon1Form', a_form | (0x80 if att.gender == 'F' else 0))  # gender shares the byte
        w8('wPartyMon1Level', 50)
        w8('wCurBattleMon', 0)
        h.mem[h.addr('wPartyMon1')] = sc['dfn_sid']
        h.mem[h.addr('wPartyMon1') + (h.addr('wPartyMon1Form') - h.addr('wPartyMon1'))] = \
            d_form | (0x80 if dfn.gender == 'F' else 0)
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
        w8('wEnemyMetronomeCount', att.metronome_count)
        w8('wMoveHitState', 1 if sc['crit'] else 0)
        w8('hBattleTurn', 1)
        if att.ability in rom_damage.MOLD_BREAKERS:
            w8('wMoveState', 0x40)    # OPP_IGNOREABIL: set while a Mold Breaker's move runs
        w8('wEnemyMoveStructAnimation', self.ids[mv['id']])
        w8('wCurEnemyMove', self.ids[mv['id']])  # BATTLE_VARS_MOVE (contact checks)
        w8('wEnemyMoveStructEffect', self.ids[mv['effect']])
        w8('wEnemyMoveStructPower', mv['power'])
        w8('wEnemyMoveStructType', self.ids[sc.get('hp_type') or mv['type']])
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


def check_variation(o, rng, n):
    """Run the ROM's damagevariation n times on random damage values. The ROM
    picks its own roll, so each result must be rom_damage.vary(dmg, r) for some
    r in 0..15, and over many runs every roll should turn up."""
    h = o.h
    bad, seen = 0, [0] * 16
    for i in range(n):
        dmg = rng.choice([0, 1, 2, 3, 99, 100, 101, 999, 65535]) if i % 4 == 0 \
            else rng.randint(0, 2000)
        h.prepare()
        h.write16(h.addr('wCurDamage'), dmg)
        o._run('BattleCommand_damagevariation', max_frames=10)
        got = h.read16(h.addr('wCurDamage'))
        rolls = [r for r in range(16) if rom_damage.vary(dmg, r) == got]
        if not rolls:
            bad += 1
            print(f'  VARIATION MISMATCH: {dmg} -> rom {got}, port '
                  f'{sorted({rom_damage.vary(dmg, r) for r in range(16)})}')
        elif dmg >= 100 and len(rolls) == 1:
            seen[rolls[0]] += 1
    return bad, seen


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
    if rng.random() < 0.15:                 # a species with its own item
        an = rng.choice(sorted(ITEM_SPECIES))
        am = dict(pool)[an]
        asid = species_ids[rom_damage.species(type('M', (), {'id': an})())]
    if rng.random() < 0.08 and 'ditto' in dict(pool):
        dn, dm, dsid = 'ditto', dict(pool)['ditto'], species_ids['ditto']
    a_base, d_base = mon_stats(am['stats']), mon_stats(dm['stats'])
    status = lambda: rng.choice([None] * 4 + ['brn', 'psn', 'tox', 'par', 'slp'])
    a_item = rng.choice(ATT_ITEMS)
    d_item = rng.choice(DEF_ITEMS)
    a_hp = a_base['hp'] if rng.random() < 0.5 else rng.randint(1, a_base['hp'])
    d_hp = d_base['hp'] if rng.random() < 0.5 else rng.randint(1, d_base['hp'])
    if an in ITEM_SPECIES and rng.random() < 0.7:
        a_item = ITEM_SPECIES[an]
    if dn == 'ditto' and rng.random() < 0.7:
        d_item = 'METAL_POWDER'
    gender = lambda m: (None if m.get('female') is None
                        else ('F' if rng.random() < m['female'] else 'M'))
    att = Mon(a_base, am['types'], rng.choice(ABILITIES),
              a_item, status(), a_hp, stage(), Side(), mid=an, gender=gender(am))
    dfn = Mon(d_base, dm['types'], rng.choice(ABILITIES), d_item, status(), d_hp, stage(),
              Side(reflect, screen), mid=dn, gender=gender(dm))
    dfn.eviolite_ok = not dm.get('fully_evolved') and dn not in items.EVIOLITE_EXCLUDED
    if a_item == 'METRONOME_I':
        att.metronome_count = rng.randint(0, 5)
    mv = rng.choice(moves)
    hp_type = rng.choice(HP_TYPES) if mv['effect'] == 'EFFECT_HIDDEN_POWER' else None
    return {'hp_type': hp_type,'att': att, 'dfn': dfn, 'att_sid': asid, 'dfn_sid': dsid, 'move': mv,
            'weather': rng.choice([None, None, 'sun', 'rain', 'sand', 'hail']),
            'crit': rng.random() < 0.15, 'moved_second': rng.random() < 0.5,
            'names': (an, dn)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', type=int, nargs='?', default=3000)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--show', type=int, default=10, help='mismatches to print')
    ap.add_argument('--variation', type=int, default=2000,
                    help='damagevariation runs to check (0 to skip)')
    args = ap.parse_args()
    o = PipelineOracle()
    if args.variation:
        vbad, seen = check_variation(o, random.Random(args.seed), args.variation)
        print(f'damagevariation: {args.variation - vbad}/{args.variation} results are a '
              f'valid 85-100% roll; rolls seen (0..15): {seen}')
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
                                   crit=sc['crit'], roll=None, moved_second=sc['moved_second'],
                                   move_type=sc.get('hp_type'))
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
    return 0 if bad == 0 and not (args.variation and vbad) else 1


if __name__ == '__main__':
    sys.exit(main())
