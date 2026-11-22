#!/usr/bin/env python3
"""Link two emulated Game Boys with a virtual cable and play a link battle.

Each side boots its save, talks to the Pokemon Center 2F battle desk, saves,
walks to its seat in the Colosseum and fights: every turn it picks the next
move in rotation and, when a Pokemon faints, sends in the next healthy one.

At the start of every turn each side records what it believes the battle is
(both active Pokemon and their HP). The two records must agree, mirrored
(one side's "player" is the other side's "enemy"); if they ever differ the
battle has desynced, which this tool reports.

The cable is PyBoy's shared-memory serial link (one process per Game Boy).
--corrupt N flips one bit in roughly 1 of every N bytes received by side B
during the battle, to test how the game copes with a noisy cable.

Run from the repository root after `make`:

  python3 utils/linktest/linktest.py A.sav B.sav [--turns 30] [--out DIR]
"""
import argparse
import ctypes
import json
import mmap
import multiprocessing as mp
import os
import random
import re
import shutil
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
POKECENTER_2F = (20, 1)
COLOSSEUM = (20, 3)


def load_sym(path):
    sym = {}
    for line in open(path):
        p = line.split()
        if len(p) == 2 and ':' in p[0]:
            b, a = p[0].split(':')
            sym.setdefault(p[1], (int(b, 16), int(a, 16)))
    return sym


def load_charmap():
    ch = {0x7f: ' '}
    for line in open(os.path.join(ROOT, 'constants/charmap.asm')):
        m = re.match(r'\s*charmap\s+"(.)",\s*\$([0-9a-fA-F]+)', line)
        if m:
            ch.setdefault(int(m.group(2), 16), m.group(1))
    return ch


class Cable:
    """The shared block the lockstep cable lives in (see pyboy_link)."""

    def __init__(self):
        self.mm = mmap.mmap(-1, 128)
        self.address = ctypes.addressof(ctypes.c_char.from_buffer(self.mm))
        self.mm[12] = self.mm[64 + 12] = 1          # both sides alive

    def end(self, slot):
        return type('End', (), {'address': self.address, 'slot': slot})()

    def set_noise(self, slot, n, seed=1):
        o = 64 * slot
        self.mm[o + 14:o + 16] = int(n).to_bytes(2, 'little')
        self.mm[o + 16:o + 20] = int(seed).to_bytes(4, 'little')

    def flips(self, slot):
        return int.from_bytes(self.mm[64 * slot + 20:64 * slot + 24], 'little')


class Side:
    """One Game Boy and the scripted player holding it."""

    def __init__(self, name, rom, sav, sym, cable, slot, out, corrupt, seed, noise_setup=False):
        from pyboy import PyBoy
        self.name, self.sym, self.out = name, sym, out
        self.ch = load_charmap()
        gbc = os.path.join(out, f'{name}.gbc')
        shutil.copy(rom, gbc)
        self.cable, self.slot = cable, slot
        self.pb = PyBoy(gbc, window='null', ram_file=open(sav, 'rb'),
                        serial_shared_memory=cable.end(slot), serial_interrupt_based=True)
        self.pb.set_emulation_speed(0)
        self.mem = self.pb.memory
        self.log = open(os.path.join(out, f'{name}.log'), 'w')
        self.turns = []
        self.corrupt = corrupt
        self.rng = random.Random(seed)
        self.noisy = False
        self.noise_setup = noise_setup
        self.setup_errors = 0
        self.desync_at = 0
        self.shot_every = 5
        self.unplug_at = self.unplug_delay = self.unplug_frames = 0
        self.unplug_wait = self.unplug_left = 0
        # record the battle every time the game starts an action exchange
        # (each turn, and when a fainted Pokemon is replaced): both games
        # make the same exchanges, so these records line up exactly
        self.exchanges = []
        bank, addr = sym['LinkBattleSendReceiveAction']
        self.pb.hook_register(bank, addr, self._on_exchange, None)

    # ---- memory helpers
    def rd(self, name, k=0):
        a = self.sym[name][1] + k
        return self.mem[1, a] if 0xd000 <= a < 0xe000 else self.mem[a]

    def rd16(self, name):
        return self.rd(name) << 8 | self.rd(name, 1)

    def screen(self, r0=0, r1=18):
        t = self.sym['wTilemap'][1]
        return [''.join(self.ch.get(self.mem[t + r * 20 + c], '?') for c in range(20))
                for r in range(r0, r1)]

    def where(self):
        return (self.rd('wMapGroup'), self.rd('wMapNumber'))

    # ---- input
    def tick(self, n=1):
        for _ in range(n):
            self.pb.tick(1, False)
            if self.unplug_wait:
                self.unplug_wait -= 1
                if not self.unplug_wait:
                    self.cable.mm[126] = 1
                    self.say(f'    (test) cable unplugged for {self.unplug_frames} frames')
            elif self.unplug_left:
                self.unplug_left -= 1
                if not self.unplug_left:
                    self.cable.mm[126] = 0
                    self.say('    (test) cable plugged back in')
        if self.corrupt and not self.noisy and (
                self.rd('wBattleMode') or (self.noise_setup and self.where() == COLOSSEUM)):
            # line noise on what this side receives, from the battle on
            # (or from entering the Colosseum, to hit the pre-battle data swap)
            self.cable.set_noise(self.slot, self.corrupt, self.rng.randrange(1 << 30))
            self.noisy = True

    def press(self, b, wait=20):
        self.pb.button_press(b)
        self.tick(4)
        self.pb.button_release(b)
        self.tick(wait)

    def shot(self, tag):
        self.pb.tick(1, True)
        self.pb.screen.image.convert('RGB').save(os.path.join(self.out, f'{self.name}_{tag}.png'))

    def say(self, msg):
        self.log.write(msg + '\n')
        self.log.flush()

    # ---- the script
    def boot(self):
        self.tick(900)
        for b in ('start', 'start', 'a', 'a', 'a'):
            self.press(b, 200)
        for _ in range(4):
            self.press('b', 30)
        self.tick(60)
        if self.where() != POKECENTER_2F:
            # warp to the link room, in front of the battle desk
            for n, v in (('wMapGroup', 20), ('wMapNumber', 1), ('wXCoord', 9), ('wYCoord', 3),
                         ('wDefaultSpawnpoint', 255), ('wMapStatus', 1)):
                a = self.sym[n][1]
                if 0xd000 <= a < 0xe000:
                    self.mem[1, a] = v
                else:
                    self.mem[a] = v
            self.mem[0xff92] = 0xf1        # hMapEntryMethod = MAPSETUP_WARP
            self.tick(600)
        self.say(f'booted at {self.where()} party {self.rd("wPartyCount")}')

    def _on_exchange(self, _):
        self.exchanges.append(self.snapshot())
        if self.unplug_at and len(self.exchanges) == self.unplug_at:
            self.unplug_wait = self.unplug_delay + 1
            self.unplug_left = self.unplug_frames
        if self.desync_at and len(self.exchanges) == self.desync_at:
            # knock one HP off our active Pokemon, a split that no byte on
            # the cable explains: the per-turn fingerprint must catch it
            a = self.sym['wBattleMonHP'][1] + 1
            self.mem[a] = (self.mem[a] - 1) & 0xff
            self.say(f'    (test) changed our HP at exchange {self.desync_at}')

    def snapshot(self):
        return {'clock': self.rd('hSerialConnectionStatus'),
                'rn': self.rd('wLinkBattleRNCount'),
                'me': (self.rd('wBattleMonSpecies'), self.rd16('wBattleMonHP')),
                'foe': (self.rd('wEnemyMonSpecies'), self.rd16('wEnemyMonHP')),
                'party': [self.party_hp(i) for i in range(self.rd('wPartyCount'))],
                'otparty': [self.ot_hp(i) for i in range(self.rd('wOTPartyCount'))]}

    def party_hp(self, i):
        base = self.sym['wPartyMon1HP'][1] + i * (self.sym['wPartyMon2'][1] - self.sym['wPartyMon1'][1])
        return self.mem[1, base] << 8 | self.mem[1, base + 1]

    def ot_hp(self, i):
        base = self.sym['wOTPartyMon1HP'][1] + i * (self.sym['wOTPartyMon2'][1] - self.sym['wOTPartyMon1'][1])
        return self.mem[1, base] << 8 | self.mem[1, base + 1]

    def next_healthy(self):
        cur = self.rd('wCurPartyMon')
        for i in range(self.rd('wPartyCount')):
            if self.party_hp(i) > 0 and i != self.rd('wCurBattleMon'):
                return i
        return None

    def run(self, max_turns, deadline):
        self.boot()
        last_text = ''
        slot = {}
        talked = False
        seated = False
        state = 'desk'
        while time.time() < deadline:
            if self.cable.mm[127]:
                self.say('the other side has finished')
                return 'partner finished'
            scr = self.screen()
            joined = '\n'.join(scr)
            text = ' / '.join(s.strip('│┃ ') for s in scr[9:17] if s.strip('│┃ '))
            if text and text != last_text:
                self.say('  ' + text)
                last_text = text
                if 'Trying' in text and 'again' in text and text != getattr(self, '_last_retry', ''):
                    self.setup_retries = getattr(self, 'setup_retries', 0) + 1
                    self._last_retry = text
                setup_error = 'battle data' in text
                if setup_error and 'wLinkCheckSend' in self.sym:
                    n = 26
                    snd = bytes(self.rd('wLinkCheckSend', k) for k in range(n)).hex(' ')
                    rcv = bytes(self.rd('wLinkCheckRecv', k) for k in range(n)).hex(' ')
                    self.say(f'    sent hash {self.rd("wLinkSentPartyHash"):02x}{self.rd("wLinkSentPartyHash", 1):02x}'
                             f' send [{snd}] recv [{rcv}] failed {self.rd("wLinkSetupFailed")}')
                if 'out of' in text and 'sync' in text:
                    self.say('*** the games stopped the battle: out of sync')
                    return 'stopped: out of sync'
                if setup_error:
                    self.setup_errors += 1
                    seated = False        # back in the Colosseum: sit down again
            in_battle = self.rd('wBattleMode') != 0
            here = self.where()
            if in_battle:
                state = 'battle'
                if 'Fight' in joined and 'Run' in joined:
                    if len(self.turns) >= max_turns:
                        self.say('turn limit reached')
                        return 'turn limit'
                    snap = self.snapshot()
                    self.turns.append(snap)
                    if len(self.turns) % self.shot_every == 1 % self.shot_every:
                        self.shot(f'turn{len(self.turns)}')
                    cur = self.rd('wCurBattleMon')
                    nmoves = max(1, sum(1 for j in range(4) if self.rd('wBattleMonMoves', j)))
                    k = slot.get(cur, 0) % nmoves
                    slot[cur] = k + 1
                    self.say(f'--- turn {len(self.turns)}: {json.dumps(snap)} move slot {k}')
                    self.press('up', 4); self.press('left', 4); self.press('a', 30)
                    for _ in range(4):
                        self.press('up', 6)
                    for _ in range(k):
                        self.press('down', 6)
                    self.press('a', 30)
                elif 'Use next' in joined:
                    self.press('a', 40)
                elif 'Choose a' in joined or 'Which' in joined and in_battle:
                    target = self.next_healthy()
                    if target is None:
                        self.press('b', 20)
                        continue
                    for _ in range(6):
                        self.press('up', 6)
                    for _ in range(target):
                        self.press('down', 6)
                    self.press('a', 30)
                    self.press('a', 30)   # "Switch" on the submenu
                    self.say(f'--- switch to party slot {target}')
                else:
                    self.press('a', 12)
                continue
            if state == 'battle':
                self.shot('after')
                self.say('battle over')
                return 'battle over'
            if here == POKECENTER_2F and not talked:
                if self.slot:
                    self.tick(150)        # people never talk to the desk on the same frame
                self.press('up', 30)
                self.press('a', 60)
                talked = True
                continue
            if here == COLOSSEUM and not seated:
                self.shot('colosseum')
                self.seat()
                seated = True
                continue
            self.press('a', 20)
        self.shot('timeout')
        return 'timeout'

    def seat(self):
        """Walk to the free seat at the table and press A."""
        self.tick(120)
        x, y = self.rd('wXCoord'), self.rd('wYCoord')
        self.say(f'in colosseum at {x},{y}')
        # the table is at x=4..5, y=4. The friend stands on one side
        # (Special_CableClubCheckWhichChris): the external-clock player sits
        # on the right facing left, the clock player on the left facing right
        seat_x, face = (6, 'left') if self.rd('hSerialConnectionStatus') == 1 else (3, 'right')
        for _ in range(8):
            if self.rd('wYCoord') > 4:
                self.press('up', 16)
        for _ in range(6):
            x = self.rd('wXCoord')
            if x < seat_x:
                self.press('right', 16)
            elif x > seat_x:
                self.press('left', 16)
        for _ in range(4):
            if self.rd('wYCoord') > 4:
                self.press('up', 16)
        self.press(face, 16)
        self.say(f'seated at {self.rd("wXCoord")},{self.rd("wYCoord")} facing {face}')
        self.press('a', 60)


def worker(name, rom, sav, symp, cable, slot, out, turns, seconds, corrupt, seed, q, noise_setup,
           desync_at=0, shot_every=5, unplug=(0, 0, 0)):
    try:
        s = Side(name, rom, sav, load_sym(symp), cable, slot, out, corrupt, seed, noise_setup)
        s.desync_at = desync_at
        s.shot_every = shot_every
        s.unplug_at, s.unplug_delay, s.unplug_frames = unplug
        result = s.run(turns, time.time() + seconds)
        cable.mm[127] = 1
        q.put((name, f'{result} ({getattr(s, "setup_retries", 0)} swap retries, '
                     f'{s.setup_errors} setup errors)', s.exchanges, cable.flips(slot)))
        s.pb.stop(save=False)
    except Exception as e:                       # noqa: BLE001
        cable.mm[127] = 1
        import traceback
        q.put((name, 'error: ' + traceback.format_exc(), [], 0))


def compare(ta, tb):
    """Check the records of each action exchange agree, mirrored."""
    problems = []
    for i, (a, b) in enumerate(zip(ta, tb)):
        if a['me'] != b['foe'] or a['foe'] != b['me']:
            problems.append(f'exchange {i + 1}: A sees me {a["me"]} foe {a["foe"]}, '
                            f'B sees me {b["me"]} foe {b["foe"]}')
        elif a['party'] != b['otparty'] or a['otparty'] != b['party']:
            problems.append(f'exchange {i + 1}: party HP differs: A {a["party"]}/{a["otparty"]}, '
                            f'B {b["party"]}/{b["otparty"]}')
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('save_a')
    ap.add_argument('save_b')
    ap.add_argument('--rom', default=os.path.join(ROOT, 'polishedcrystal-3.2.3.gbc'))
    ap.add_argument('--rom-b', default=None, help='a different ROM for side B')
    ap.add_argument('--turns', type=int, default=30)
    ap.add_argument('--seconds', type=int, default=900)
    ap.add_argument('--corrupt', type=int, default=0)
    ap.add_argument('--shot-every', type=int, default=5, help='screenshot every N turns')
    ap.add_argument('--unplug', default='',
                    help='AT,DELAY,FRAMES: at action exchange AT (side A), wait DELAY frames, '
                         'then unplug the cable for FRAMES frames')
    ap.add_argument('--desync-at', type=int, default=0,
                    help="change side B's HP at this action exchange, to test desync detection")
    ap.add_argument('--noise-setup', action='store_true',
                    help='start the noise on entering the Colosseum, before the parties are swapped')
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', default='linktest_out')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    symp = args.rom[:-4] + '.sym'
    cable = Cable()
    q = mp.Queue()
    ctx_procs = []
    for slot, (name, sav, rom, corrupt) in enumerate((
            ('A', args.save_a, args.rom, 0),
            ('B', args.save_b, args.rom_b or args.rom, args.corrupt))):
        p = mp.Process(target=worker, args=(name, rom, sav, rom[:-4] + '.sym', cable, slot,
                                            args.out, args.turns, args.seconds, corrupt,
                                            args.seed + slot, q, args.noise_setup,
                                            args.desync_at if slot else 0, args.shot_every,
                                            tuple(map(int, args.unplug.split(','))) if args.unplug and not slot
                                            else (0, 0, 0)))
        p.start()
        ctx_procs.append(p)
    res = {}
    for _ in ctx_procs:
        name, result, turns, flips = q.get(timeout=args.seconds + 120)
        res[name] = (result, turns, flips)
    for p in ctx_procs:
        p.join(timeout=30)
    for name in 'AB':
        print(f'{name}: {res[name][0]} after {len(res[name][1])} action exchanges, '
              f'{res[name][2]} bits flipped')
    problems = compare(res['A'][1], res['B'][1])
    n = min(len(res['A'][1]), len(res['B'][1]))
    print('\n'.join(problems[:10]) if problems else f'in sync at all {n} action exchanges both sides made')
    return 1 if problems else 0


if __name__ == '__main__':
    mp.set_start_method('fork')
    sys.exit(main())
