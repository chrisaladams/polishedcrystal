#!/usr/bin/env python3
"""Ground truth for whole battle turns: plays real link-battle turns in the
ROM under PyBoy and compares what happens with engine.py's turn.

The other oracles check one routine each (stats, damage, accuracy, Speed,
status immunities). This one checks everything a turn does at once: move
order, every move effect, abilities, items, secondary effects, end-of-turn
damage and healing, fainting. It is the check that catches whatever the
engine leaves out or gets wrong between those routines.

How it drives the ROM:
- One emulator, no cable. The ROM is patched in memory (a copy, not the
  built file) so that the battle menu, the move menu and the link exchange
  each stop in a `jr -2` loop. When one is reached, this script writes the
  choice (our move, the opponent's move slot) and returns from the routine.
- Both teams are built with the game's own TryAddMonToParty, FillPP and
  UpdatePkmnStats, given the scenario's moves, item, ability, perfect DVs and
  a neutral nature; the opponent's team is copied to the OT party and the
  battle is started with StartBattle in link mode (wLinkMode =
  LINK_COLOSSEUM), exactly as the Cable Club starts it.
- In a link battle every random number comes from wLinkBattleRNs. The state
  at the first menu is saved; each sample reloads it, writes fresh random
  numbers, plays the turn and reads the result.

The engine plays the same turn many times with different seeds, from the
same start (the stats, genders and abilities are read back from the ROM, so
only the turn itself is compared), and the two distributions are compared:
who moved first, each side's HP, fainting, status and stat stages.

Run from the repository root after `make`:
    python3 meta_sim/oracle_turn.py [--scenarios 40] [--samples 150] [--seed 1]
"""
import argparse
import collections
import io
import json
import math
import os
import random
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'test'))
sys.path.insert(0, HERE)

from rom_harness import find_build, load_symbols                 # noqa: E402
from oracle_pipeline import rgbasm_values                         # noqa: E402

# the routines that stop in a loop for the script, and the loop StartBattle
# returns into (4 free bytes at the end of bank 0: jr -2; ei; ret)
STOPS = ['BattleMenu', 'MoveSelectionScreen', 'LinkBattleSendReceiveAction',
         'GetPlayerSwitchTarget']
# after each loop, how the routine returns: BattleMenu with carry clear
# (`and a`), the move menu with z set (`xor a`), the others plainly
STUBS = {'BattleMenu': b'\xa7\xc9', 'MoveSelectionScreen': b'\xaf\xc9',
         'LinkBattleSendReceiveAction': b'\xc9\x00'}
# GetPlayerSwitchTarget's stub, `ld a, [wPlayerSwitchTarget]; ret`, is built
# once the address is known
FREE = 0x3ffc
OPTIONS1 = 0x03 | 0x0c | 0x20       # instant text, autoscroll on A/B, no scroll; no animations
STATUS_NAMES = {0: None, 1 << 3: 'psn', 1 << 4: 'brn', 1 << 5: 'frz', 1 << 6: 'par'}
STAT_KEYS = ['atk', 'defe', 'spe', 'spa', 'spd', 'acc', 'eva']
PARTY_STATS = ['hp', 'atk', 'defe', 'spe', 'spa', 'spd']          # party struct order


class Rom:
    """One Game Boy, stopped at the battle menu, ready to play turns."""

    def __init__(self, rom=None):
        from pyboy import PyBoy
        if rom is None:
            rom, symp = find_build(ROOT)
        else:
            symp = rom[:-4] + '.sym'
        self.sym = load_symbols(symp)
        data = bytearray(open(rom, 'rb').read())
        for name in STOPS:
            bank, addr = self.sym[name]
            off = bank * 0x4000 + addr - 0x4000 if bank else addr
            if name == 'GetPlayerSwitchTarget':
                t = self.sym['wPlayerSwitchTarget'][1]
                stub = bytes([0xfa, t & 0xff, t >> 8, 0xc9])
            else:
                stub = STUBS[name]
            data[off:off + 2 + len(stub)] = b'\x18\xfe' + stub
        data[FREE:FREE + 4] = b'\x18\xfe\xfb\xc9'
        self.tmp = tempfile.mkdtemp()
        path = os.path.join(self.tmp, 'game.gbc')
        open(path, 'wb').write(data)
        self.pb = PyBoy(path, window='null', sound_emulated=False)
        self.pb.set_emulation_speed(0)
        self.mem, self.reg = self.pb.memory, self.pb.register_file
        for _ in range(900):
            self.pb.tick(1, False)
        self.ie = self.mem[0xffff]
        self.sp0 = self.reg.SP
        # Every frame, look at where VBlank interrupted the game. A frame
        # always ends inside the VBlank handler, so PC can't be polled; and a
        # hook on a loop would run on every pass. If the game is waiting in
        # one of the loops, answer it and point the interrupt's return
        # address past the loop, at the routine's return stub.
        self.hit = None
        self.plan = None
        self.loops = {}
        for name in STOPS:
            bank, addr = self.sym[name]
            self.loops[addr] = (bank, name)
        self.loops[FREE] = (0, 'end')
        self.pb.hook_register(0, 0x40, self._vblank, None)
        base = self.a('wPartyMon1')
        self.stride = self.a('wPartyMon2') - base
        self.field = {f: self.a('wPartyMon1' + f) - base for f in
                      ('Species', 'Item', 'Moves', 'PP', 'EVs', 'DVs', 'Personality',
                       'Form', 'Level', 'HP', 'MaxHP', 'Stats')}
        self.boot = io.BytesIO()
        self.pb.save_state(self.boot)

    # ---- memory
    def a(self, name):
        return self.sym[name][1]

    def w(self, name, v, k=0):
        a = self.a(name) + k
        if 0xd000 <= a < 0xe000:
            self.mem[1, a] = v & 0xff
        else:
            self.mem[a] = v & 0xff

    def r(self, name, k=0):
        a = self.a(name) + k
        return self.mem[1, a] if 0xd000 <= a < 0xe000 else self.mem[a]

    def r16(self, name, k=0):
        return self.r(name, k) << 8 | self.r(name, k + 1)

    def call(self, name, frames=120, **regs):
        """Run a routine to its ret, interrupts off, on a scratch stack."""
        bank, entry = self.sym[name]
        m, reg = self.mem, self.reg
        m[0xff70] = 1
        m[0xffff] = 0
        m[0xff0f] = 0
        m[0x2000] = bank
        m[0xff87] = bank
        reg.SP = self.sp0 - 2
        m[reg.SP], m[reg.SP + 1] = FREE & 0xff, FREE >> 8
        for k, v in regs.items():
            if k == 'hl':
                reg.HL = v
            else:
                setattr(reg, k[0].upper(), v >> 8)
                setattr(reg, k[1].upper(), v & 0xff)
        reg.PC = entry
        for _ in range(frames):
            self.pb.tick(1, False)
            if reg.PC in (FREE, FREE + 1):
                return
        raise RuntimeError(f'{name} did not return (PC={reg.PC:04x})')

    # ---- teams
    def add_mon(self, mon, ids):
        """Add a set to the player's party with the game's own code."""
        sp, form = ids['species'][mon['id']]
        self.w('wCurPartySpecies', sp)
        self.w('wCurForm', form)
        self.w('wCurPartyLevel', 50)
        self.w('wMonType', 0)
        self.call('TryAddMonToParty')
        i = self.r('wPartyCount') - 1
        o = self.a('wPartyMon1') + i * self.stride
        f = self.field
        for j in range(4):
            self.mem[1, o + f['Moves'] + j] = ids['move'][mon['moves'][j]] if j < len(mon['moves']) else 0
        self.mem[1, o + f['Item']] = ids['item'].get(mon['item'], 0)
        pers = self.mem[1, o + f['Personality']] & 0x80          # keep shininess
        self.mem[1, o + f['Personality']] = pers | ids['slot'][mon['slot']]  # HARDY = 0
        for j in range(3):
            self.mem[1, o + f['DVs'] + j] = 0xff
        for j in range(6):
            self.mem[1, o + f['EVs'] + j] = 84                    # 504 in all: under the 510 cap
        self.w('wCurPartyMon', i)
        self.call('FillPP', hl=o + f['Moves'], de=o + f['PP'])
        self.call('UpdatePkmnStats')
        for j in range(2):
            self.mem[1, o + f['HP'] + j] = self.mem[1, o + f['MaxHP'] + j]

    def start(self, mine, theirs, ids):
        """Build both teams and play up to the first battle menu."""
        self.pb.load_state(io.BytesIO(self.boot.getvalue()))
        self.ids = ids
        self.w('wInitialOptions2', ids['EVS_OPT_MODERN'])
        n = self.a('wPartyMonNicknamesEnd') - self.a('wPartyMons')
        self.w('wPartyCount', 0)
        for mon in theirs:
            self.add_mon(mon, ids)
        ot = [self.mem[1, self.a('wPartyMons') + k] for k in range(n)]
        self.w('wPartyCount', 0)
        for mon in mine:
            self.add_mon(mon, ids)
        for k in range(n):
            self.mem[1, self.a('wOTPartyMons') + k] = ot[k]
        self.w('wOTPartyCount', len(theirs))
        self.w('wLinkMode', ids['LINK_COLOSSEUM'])
        self.mem[0xffcb] = 2                                      # internal clock
        self.w('wOtherTrainerClass', ids['CAL'])
        self.w('wBattleType', 0)
        self.w('wOptions1', OPTIONS1)
        for k in range(10):
            self.w('wLinkBattleRNs', random.randrange(0xfd), k)
        self.w('wLinkBattleRNCount', 0)
        # StartBattle, with interrupts on (via `ei; ret`), returning to the end loop
        bank, entry = self.sym['StartBattle']
        m, reg = self.mem, self.reg
        sp = self.sp0 - 4
        m[sp], m[sp + 1] = entry & 0xff, entry >> 8
        m[sp + 2], m[sp + 3] = FREE & 0xff, FREE >> 8
        reg.SP = sp
        m[0x2000] = bank
        m[0xff87] = bank
        m[0xff70] = 1
        m[0xffff] = self.ie
        reg.PC = FREE + 2
        where = self.run()
        if where != 'BattleMenu':
            raise RuntimeError(f'battle did not reach the menu ({where})')
        self.turn_start = io.BytesIO()
        self.pb.save_state(self.turn_start)

    def _vblank(self, _):
        m = self.mem
        sp = self.reg.SP
        pc = m[sp] | m[sp + 1] << 8
        loop = self.loops.get(pc)
        if not loop or (pc >= 0x4000 and m[0xff87] != loop[0]) or self.hit:
            return
        name = loop[1]
        plan = self.plan
        if plan is None:
            self.hit = name
            return
        if name == 'BattleMenu':
            if plan['menu']:                    # back at the menu: the turn is over
                plan['snaps'].append(self.snapshot())
                plan['t'] += 1
                plan['menu'] = plan['sent'] = False
            if plan['t'] >= len(plan['choices']) or plan['fainted'] or plan['out']:
                self.hit = name
                return
            plan['menu'] = True
            self.w('wBattlePlayerAction', 0)
        elif name == 'MoveSelectionScreen':
            mine = plan['choices'][plan['t']][0]
            self.w('wCurMoveNum', mine)
            self.w('wCurPlayerMove', self.r('wBattleMonMoves', mine))
        elif name == 'LinkBattleSendReceiveAction' and not plan['sent']:
            plan['sent'] = True
            self.w('wBattleAction', plan['choices'][plan['t']][1])
        elif name == 'LinkBattleSendReceiveAction':
            # the opponent replacing a fainted Pokemon: its second one
            self.w('wBattleAction', self.ids['BATTLEACTION_SWITCH1'] + 1)
            plan['fainted'] = True
        elif name == 'GetPlayerSwitchTarget':
            # we replace ours with our second one (and if both fainted, the
            # opponent's choice comes from this same exchange)
            self.w('wCurPartyMon', 1)
            self.w('wPlayerSwitchTarget', 2)
            self.w('wBattleAction', self.ids['BATTLEACTION_SWITCH1'] + 1)
            plan['fainted'] = True
        else:
            if name == 'end':                   # the battle is over: someone fainted
                plan['snaps'].append(self.snapshot())
            self.hit = name
            return
        pc += 2                                 # the return stub
        m[sp], m[sp + 1] = pc & 0xff, pc >> 8

    def run(self, frames=8000):
        self.hit = None
        for f in range(frames):
            if f % 4 == 0:                  # tap A: text boxes wait for a new press
                if f % 8:
                    self.pb.button_release('a')
                else:
                    self.pb.button_press('a')
            self.pb.tick(1, False)
            if self.hit:
                return self.hit
        return None

    def read_side(self, prefix, stat_prefix):
        status = self.r(prefix + 'Status')
        st = 'slp' if status & 7 else 'tox' if status & 0x80 else STATUS_NAMES.get(status & 0x78)
        return {'hp': self.r16(prefix + 'HP'), 'maxhp': self.r16(prefix + 'MaxHP'),
                'status': st, 'stages': [self.r(stat_prefix, k) - 7 for k in range(7)]}

    def info(self):
        """Stats, ability and gender of both active mons, as the battle has them."""
        out = {}
        for side, pfx in (('me', 'wBattleMon'), ('foe', 'wEnemyMon')):
            st = {k: self.r16(pfx + 'MaxHP') if k == 'hp' else None for k in PARTY_STATS}
            for k, nm in (('atk', 'Attack'), ('defe', 'Defense'), ('spe', 'Speed'),
                          ('spa', 'SpAtk'), ('spd', 'SpDef')):
                st[k] = self.r16(pfx + nm)
            out[side] = {'stats': st, 'gender': self.r(pfx + 'Gender') >> 7}
        out['me']['ability'] = self.r('wPlayerAbility')
        out['foe']['ability'] = self.r('wEnemyAbility')
        return out

    def snapshot(self):
        """Both lead Pokemon (once one has been replaced, it's fainted)."""
        out = {'first': self.r('wEnemyGoesFirst') == 0}
        for side, cur, pfx, stages, party in (
                ('me', 'wCurBattleMon', 'wBattleMon', 'wPlayerStatLevels', 'wPartyMon1'),
                ('foe', 'wCurOTMon', 'wEnemyMon', 'wEnemyStatLevels', 'wOTPartyMon1')):
            if self.r(cur) == 0:
                out[side] = self.read_side(pfx, stages)
            else:                               # fainted, or forced out
                status = self.r(party + 'Status')
                st = 'slp' if status & 7 else 'tox' if status & 0x80 else STATUS_NAMES.get(status & 0x78)
                out[side] = {'hp': self.r16(party + 'HP'), 'maxhp': self.r16(party + 'MaxHP'),
                             'status': st, 'stages': [0] * 7}
                self.plan['out'] = True
        return out

    def play(self, choices, rns, count):
        """From the saved first menu, play a turn for each (our move slot,
        their move slot) in choices; return the state after each turn (fewer
        if the battle ends)."""
        self.pb.load_state(io.BytesIO(self.turn_start.getvalue()))
        for k in range(10):
            self.w('wLinkBattleRNs', rns[k], k)
        self.w('wLinkBattleRNCount', count)
        self.plan = {'choices': choices, 't': 0, 'menu': False, 'sent': False, 'snaps': [],
                     'fainted': False, 'out': False}
        where = self.run(frames=4000 * len(choices))
        snaps = self.plan['snaps']
        self.plan = None
        if where is None:
            raise RuntimeError('the turn did not finish')
        return snaps


def load_ids(mons, moves, items):
    """Constant values for every species/form, move, item and the rest."""
    from make_random_sets import species_and_form
    sf = {mid: species_and_form(mid) for mid in mons}
    names = sorted({n for s, f in sf.values() for n in (s, f)} | set(moves) | set(items)
                   | {a for m in mons.values() for a in m['abilities']}
                   | {'ABILITY_1', 'ABILITY_2', 'HIDDEN_ABILITY', 'LINK_COLOSSEUM', 'CAL',
                      'EVS_OPT_MODERN', 'BATTLEACTION_SWITCH1'})
    v = rgbasm_values(names, None)
    ids = {k: v[k] for k in ('LINK_COLOSSEUM', 'CAL', 'EVS_OPT_MODERN', 'BATTLEACTION_SWITCH1')}
    ids['species'] = {}
    for mid, (s, f) in sf.items():
        if s in v and f in v:
            ids['species'][mid] = (v[s] & 0xff, (v[s] >> 8) << 5 | v[f])
    ids['move'] = {m: v[m] for m in moves if m in v}
    ids['item'] = {i: v[i] for i in items if i in v}
    ids['slot'] = {k: v[k] for k in ('ABILITY_1', 'ABILITY_2', 'HIDDEN_ABILITY')}
    ids['ability_name'] = {v[a]: a for m in mons.values() for a in m['abilities'] if a in v}
    return ids


SLOTS = ['ABILITY_1', 'ABILITY_2', 'HIDDEN_ABILITY']
# a second Pokemon on each side, so a faint doesn't end the battle (the ROM
# skips the end of the turn when it does)
BENCH = {'id': 'snorlax', 'moves': ['TACKLE'], 'item': None, 'ability': 'THICK_FAT',
         'slot': 'ABILITY_2', 'key': 'bench'}


def load_data():
    d = os.path.join(HERE, 'data')
    return {n: json.load(open(os.path.join(d, n + '.json')))
            for n in ('pokemon', 'moves', 'items', 'typechart', 'best_sets')}


def scenario_sets(data, ids, rng, n):
    """n random pairs of optimised sets the ROM can build."""
    pool = []
    for key, st in sorted(data['best_sets'].items()):
        mid = key.split('|')[0]
        mon = data['pokemon'].get(mid)
        if (not mon or mid not in ids['species'] or 'HIDDEN_POWER' in st['moves']
                or any(m not in ids['move'] for m in st['moves'])
                or (st['item'] and st['item'] not in ids['item'])):
            continue
        ab = mon['abilities']
        slot = SLOTS[ab.index(st['ability'])] if st['ability'] in ab else 'ABILITY_1'
        pool.append({'id': mid, 'moves': st['moves'], 'item': st['item'], 'ability': st['ability'],
                     'slot': slot, 'key': key})
    return [tuple(rng.sample(pool, 2)) for _ in range(n)]


def sim_play(a, b, info, choices, data, seed):
    """engine.py's version of Rom.play, from the same stats, abilities and genders."""
    import engine
    rng = random.Random(seed)
    random.seed(seed)                       # a few engine paths use the module RNG
    field = engine.Field()
    mons = []
    for st, inf in ((a, info['me']), (b, info['foe'])):
        mon = data['pokemon'][st['id']]
        p = engine.Pmon(st['id'], mon, list(st['moves']), inf['ability'], st['item'])
        p.base = dict(inf['stats'])
        p.maxhp = p.hp = inf['stats']['hp']
        p.gender = None if mon.get('female') is None else ('F' if inf['gender'] else 'M')
        mons.append(p)
    bench = [engine.Pmon(BENCH['id'], data['pokemon'][BENCH['id']], list(BENCH['moves']),
                         BENCH['ability'], None) for _ in range(2)]
    A, B = engine.Side([mons[0], bench[0]], field), engine.Side([mons[1], bench[1]], field)
    A.foe, B.foe = B, A
    engine.apply_switch(B, 0, A, data['typechart'])   # the ROM sends out the opponent first
    engine.apply_switch(A, 0, B, data['typechart'])
    snaps = []
    for ia, ib in choices:
        if mons[0].fainted or mons[1].fainted or A.mon is not mons[0] or B.mon is not mons[1]:
            break                           # a lead fainted or was forced out
        A.mon.turns_active += 1
        B.mon.turns_active += 1
        first = engine.resolve_turn(A, B, field, ia, ib, data['moves'], data['typechart'], rng)
        field.trick_room = max(0, field.trick_room - 1)
        if field.weather:
            field.weather_turns -= 1
            if field.weather_turns <= 0:
                field.weather = None
        snaps.append({'me': sim_side(mons[0]), 'foe': sim_side(mons[1]), 'first': first})
    return snaps


def sim_side(p):
    return {'hp': 0 if p.fainted else max(0, math.floor(p.hp)), 'maxhp': p.maxhp,
            'status': None if p.fainted else p.status,
            'stages': [p.stage.get(k, 0) for k in STAT_KEYS]}


def features(snaps, turns):
    """One sample as numbers, per turn; a finished battle keeps its last state."""
    out = []
    last = snaps[-1] if snaps else None
    for t in range(turns):
        s = snaps[t] if t < len(snaps) else last
        f = {}
        for side in ('me', 'foe'):
            d = s[side]
            f[f'{side} HP'] = d['hp'] / d['maxhp']
            f[f'{side} fainted'] = float(d['hp'] == 0)
            for st in ('par', 'brn', 'psn', 'tox', 'slp', 'frz'):
                f[f'{side} {st}'] = float(d['status'] == st and d['hp'] > 0)
            for k, v in zip(STAT_KEYS, d['stages']):
                f[f'{side} {k} stage'] = float(v) if d['hp'] > 0 else 0.0
        f['we moved first'] = float(s['first']) if t < len(snaps) else None
        out.append(f)
    return out


def compare(rom_samples, sim_samples, turns):
    """Differences that are both clear (over 4 standard errors) and big enough to matter."""
    found = []
    for t in range(turns):
        for k in rom_samples[0][t]:
            xs = [s[t][k] for s in rom_samples if s[t][k] is not None]
            ys = [s[t][k] for s in sim_samples if s[t][k] is not None]
            if len(xs) < 10 or len(ys) < 10:
                continue
            mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
            vx = sum((x - mx) ** 2 for x in xs) / (len(xs) - 1)
            vy = sum((y - my) ** 2 for y in ys) / (len(ys) - 1)
            se = math.sqrt(vx / len(xs) + vy / len(ys))
            floor = 0.25 if 'stage' in k else 0.04 if 'HP' in k else 0.08
            if abs(mx - my) > max(4 * se, floor) or (se == 0 and abs(mx - my) > 1e-9):
                found.append((t + 1, k, mx, my))
    return found


def run_scenario(args):
    a, b, choices, samples, seed = args
    data = load_data()
    ids = load_ids(data['pokemon'], data['moves'], data['items'])
    rom = _ROM.get('rom') or _ROM.setdefault('rom', Rom())
    rng = random.Random(seed)
    rom.start([a, BENCH], [b, BENCH], ids)
    info = rom.info()
    for side in ('me', 'foe'):
        info[side]['ability'] = ids['ability_name'].get(info[side]['ability'], '?')
    results = []
    for pair in choices:
        seq = [pair] * TURNS
        rom_s, sim_s = [], []
        for n in range(samples):
            rns = [rng.randrange(0xfd) for _ in range(10)]
            rom_s.append(features(rom.play(seq, rns, rng.randrange(9)), TURNS))
            sim_s.append(features(sim_play(a, b, info, seq, data, rng.randrange(1 << 30)), TURNS))
        results.append((pair, compare(rom_s, sim_s, TURNS)))
    return a, b, info, results


_ROM = {}
TURNS = 3


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--scenarios', type=int, default=24)
    ap.add_argument('--samples', type=int, default=120)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--workers', type=int, default=os.cpu_count() or 1)
    args = ap.parse_args()
    data = load_data()
    ids = load_ids(data['pokemon'], data['moves'], data['items'])
    rng = random.Random(args.seed)
    jobs = []
    for a, b in scenario_sets(data, ids, rng, args.scenarios):
        choices = [(rng.randrange(len(a['moves'])), rng.randrange(len(b['moves']))) for _ in range(2)]
        jobs.append((a, b, choices, args.samples, rng.randrange(1 << 30)))
    import multiprocessing
    clean = 0
    with multiprocessing.Pool(args.workers) as pool:
        for a, b, info, results in pool.imap_unordered(run_scenario, jobs):
            for (i, j), found in results:
                head = (f"{a['key']} {a['moves'][i]} vs {b['key']} {b['moves'][j]} "
                        f"(abilities {info['me']['ability']}/{info['foe']['ability']})")
                if a['ability'] != info['me']['ability'] or b['ability'] != info['foe']['ability']:
                    head += f" [set abilities {a['ability']}/{b['ability']}]"
                if not found:
                    clean += 1
                    print(f'ok    {head}', flush=True)
                    continue
                print(f'DIFF  {head}', flush=True)
                for t, k, x, y in found:
                    print(f'        turn {t}: {k}: ROM {x:.3f}, engine {y:.3f}', flush=True)
    print(f'\n{clean}/{2 * len(jobs)} matchups agree')


if __name__ == '__main__':
    sys.exit(main())
