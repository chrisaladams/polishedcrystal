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
TRADE_CENTER = (20, 2)
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
        self.noise_desk = False
        self.setup_errors = 0
        self.rules = 'normal'
        self.rules_chosen = False
        self.party_size = None
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
        # optionally give every party Pokemon the same moves just before the
        # party is sent (the real party comes back from the save afterwards)
        self.force_moves = None
        bank, addr = sym['Link_PrepPartyData_Gen2']
        self.pb.hook_register(bank, addr, self._on_prep_party, None)
        # --unplug-desk N,FRAMES (side A): unplug the cable just as the Nth
        # byte of the Championship session's exchanges starts, for FRAMES
        # frames (the session's commit boundaries are byte positions)
        self.desk_unplug = (0, 0)
        self.desk_bytes = None
        self.pb.hook_register(*sym['Special_WorldLinkSession'], self._on_world_session, None)
        self.pb.hook_register(*sym['Serial_ExchangeByte'], self._on_serial_byte, None)
        # LINKTEST_TRACE=Label,Label: log each time these run
        for label in filter(None, os.environ.get('LINKTEST_TRACE', '').split(',')):
            if label in sym:
                self.pb.hook_register(*sym[label], lambda _, label=label: self.say(
                    f'    (trace) {label}' + (f' (session byte {self.desk_bytes})' if self.desk_bytes is not None else '')), None)

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
                self.rd('wBattleMode') or (self.noise_setup and self.where() == COLOSSEUM)
                or (self.noise_desk and self.rules_chosen)):
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
        if self.rules == 'world':
            # Championship rules are for players past Red
            sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
            from test_wild_mons import rgbasm_values
            n = rgbasm_values(['EVENT_GOT_MYSTICTICKET_FROM_RED'], None)['EVENT_GOT_MYSTICTICKET_FROM_RED']
            a = self.sym['wEventFlags'][1] + n // 8
            self.mem[1, a] = self.mem[1, a] | 1 << (n % 8)
        if getattr(self, 'boot_day', None) is not None:
            # a different clock on this Game Boy
            self.mem[1, self.sym['wRTCDayLo'][1]] = self.boot_day
            self.say(f'    (test) clock set to day {self.boot_day}')
        if getattr(self, 'last_rules', None) is not None:
            # (test) the rules this cartridge's last link battle used
            self.mem[self.sym['wLinkBattleRules'][1]] = RULES.index(self.last_rules)
            self.say(f'    (test) last battle rules: {self.last_rules}')
        if self.where() != POKECENTER_2F or getattr(self, 'trade', False):
            # warp to the link room, in front of the battle desk (the trade
            # desk with --trade)
            desk_x = 5 if getattr(self, 'trade', False) else 9
            for n, v in (('wMapGroup', 20), ('wMapNumber', 1), ('wXCoord', desk_x), ('wYCoord', 3),
                         ('wDefaultSpawnpoint', 255), ('wMapStatus', 1)):
                a = self.sym[n][1]
                if 0xd000 <= a < 0xe000:
                    self.mem[1, a] = v
                else:
                    self.mem[a] = v
            self.mem[0xff92] = 0xf1        # hMapEntryMethod = MAPSETUP_WARP
            self.tick(600)
        if getattr(self, 'trade', False):
            # (test) the trade desk turns away Pokemon carrying mail: no held
            # items, in memory only
            stride = self.sym['wPartyMon2'][1] - self.sym['wPartyMon1'][1]
            item = self.sym['wPartyMon1Item'][1]
            for i in range(self.rd('wPartyCount')):
                self.mem[1, item + i * stride] = 0
        if self.party_size is not None:
            assert self.party_size <= self.rd('wPartyCount'), 'save has too few Pokémon for the fixture'
            self.mem[1, self.sym['wPartyCount'][1]] = self.party_size
        self.say(f'booted at {self.where()} party {self.rd("wPartyCount")}')
        self.party_before = self.party_ids()

    def _on_prep_party(self, _):
        if not self.force_moves:
            return
        base = self.sym['wPartyMon1'][1]
        stride = self.sym['wPartyMon2'][1] - base
        mv = self.sym['wPartyMon1Moves'][1] - base
        pp = self.sym['wPartyMon1PP'][1] - base
        for i in range(self.rd('wPartyCount')):
            for j, m in enumerate(self.force_moves):
                self.mem[1, base + i * stride + mv + j] = m
                self.mem[1, base + i * stride + pp + j] = 10
        self.say(f'    (test) forced moves {self.force_moves} on the party')

    def _on_world_session(self, _):
        if self.desk_unplug[0]:
            self.desk_bytes = 0

    def _on_serial_byte(self, _):
        if self.desk_bytes is None:
            return
        self.desk_bytes += 1
        if self.desk_bytes == self.desk_unplug[0]:
            self.desk_bytes = None
            self.cable.mm[126] = 1
            self.unplug_wait, self.unplug_left = 0, self.desk_unplug[1]
            self.say(f'    (test) cable unplugged at session byte {self.desk_unplug[0]} '
                     f'for {self.desk_unplug[1]} frames')

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

    def unplug_world_at(self, exchange):
        remaining = exchange

        def unplug(_):
            nonlocal remaining
            remaining -= 1
            if not remaining:
                self.cable.mm[126] = 1
                self.say(f'    (test) cable unplugged at Championship exchange {exchange}')

        self.pb.hook_register(*self.sym['WorldLinkSwap'], unplug, None)

    def dump_sram(self, sav):
        """Write this cartridge's battery RAM (and the input save's clock bytes)
        to out/<name>.sav, for the next session."""
        ram = bytes(self.mem[bank, 0xa000 + i] for bank in range(4) for i in range(0x2000))
        tail = open(sav, 'rb').read()[len(ram):]
        with open(os.path.join(self.out, f'{self.name}.sav'), 'wb') as f:
            f.write(ram + tail)

    def friend_report(self):
        """The teams this side kept for Friend Battles (sFriendTeam1 and 2,
        in SRAM bank 0), and its own party, to check against the other's."""
        teams = []
        for label in ('sFriendTeam1', 'sFriendTeam2'):
            if label not in self.sym:
                return {}
            a = self.sym[label][1]
            teams.append(bytes(self.mem[0, a + i] for i in range(FRIEND_TEAM_LENGTH)))
        n = self.rd('wPartyCount')
        stride = self.sym['wPartyMon2'][1] - self.sym['wPartyMon1'][1]
        base = self.sym['wPartyMon1'][1]
        form = self.sym['wPartyMon1Form'][1] - base
        mons = [(self.mem[1, base + i * stride], self.mem[1, base + i * stride + form])
                for i in range(n) if not self.mem[1, base + i * stride + form] & 0x40]  # (eggs aside)
        level = self.sym['wPartyMon1Level'][1] - base
        levels = {self.mem[1, base + i * stride + level] for i in range(n)}
        name = bytes(self.rd('wPlayerName', i) for i in range(8))
        return {'teams': teams, 'mons': mons, 'name': name, 'levels': levels}

    def party_ids(self):
        n = self.rd('wPartyCount')
        stride = self.sym['wPartyMon2'][1] - self.sym['wPartyMon1'][1]
        base = self.sym['wPartyMon1'][1]
        form = self.sym['wPartyMon1Form'][1] - base
        level = self.sym['wPartyMon1Level'][1] - base
        mons = [(self.mem[1, base + i * stride], self.mem[1, base + i * stride + form],
                 self.mem[1, base + i * stride + level])
                for i in range(n)]
        dex = sum(bin(self.rd('wPokedexCaught', k)).count('1') for k in range(32))
        return {'mons': mons, 'dex': dex}

    def snapshot(self):
        return {'mestat': [self.rd('wBattleMonStatus')] + [self.rd('wPlayerStatLevels', k) for k in range(7)],
                'foestat': [self.rd('wEnemyMonStatus')] + [self.rd('wEnemyStatLevels', k) for k in range(7)],
                'clock': self.rd('hSerialConnectionStatus'),
                'rn': self.rd('wLinkBattleRNCount'),
                'me': (self.rd('wBattleMonSpecies'), self.rd16('wBattleMonHP')),
                'foe': (self.rd('wEnemyMonSpecies'), self.rd16('wEnemyMonHP')),
                'levels': (self.rd('wBattleMonLevel'), self.rd('wEnemyMonLevel')),
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
                if 'Link error! Trying' in text and not getattr(self, '_in_retry', False):
                    self._in_retry = True
                    self.setup_retries = getattr(self, 'setup_retries', 0) + 1
                    n = 26
                    snd = bytes(self.rd('wLinkCheckSend', k) for k in range(n)).hex(' ')
                    rcv = bytes(self.rd('wLinkCheckRecv', k) for k in range(n)).hex(' ')
                    self.say(f'    retry: sent hash {self.rd("wLinkSentPartyHash"):02x}'
                             f'{self.rd("wLinkSentPartyHash", 1):02x} send [{snd}] recv [{rcv}]')
                elif 'Trying' not in text:
                    self._in_retry = False
                setup_error = 'battle data' in text
                if setup_error and 'wLinkCheckSend' in self.sym:
                    n = 26
                    snd = bytes(self.rd('wLinkCheckSend', k) for k in range(n)).hex(' ')
                    rcv = bytes(self.rd('wLinkCheckRecv', k) for k in range(n)).hex(' ')
                    self.say(f'    sent hash {self.rd("wLinkSentPartyHash"):02x}{self.rd("wLinkSentPartyHash", 1):02x}'
                             f' send [{snd}] recv [{rcv}] failed {self.rd("wLinkSetupFailed")}')
                if 'out of' in text and 'sync' in text:
                    recv = [self.rd('wLinkExchangeReceived', k) for k in range(3)]
                    self.say(f'*** the games stopped the battle: out of sync. fingerprint '
                             f'{self.rd("wLinkBattleFingerprint"):02x} received {recv} '
                             f'desynced {self.rd("wLinkBattleDesynced")} action {self.rd("wBattleAction")} '
                             f'enemy switch target {self.rd("wEnemySwitchTarget")} '
                             f'OT party {self.rd("wOTPartyCount")} {self.snapshot()}')
                    return 'stopped: out of sync'
                if setup_error:
                    self.setup_errors += 1
                    seated = False        # back in the Colosseum: sit down again
                if 'different rules' in text:
                    return 'rejected: different rules'
                if 'the same build' in text:
                    return 'rejected: different build'
                if "didn't" in text and 'go through' in text:
                    # (the desk's checks got a garbled or missed exchange:
                    # it offers to try again, and the default A says yes)
                    self.say('    (desk: the link did not go through; trying again)')
                if 'three eligible' in text:
                    return 'rejected: illegal Rising Star party'
                # the linked World Championship's sessions that end at the desk
                for words, outcome in (('are in a World', 'registered'), ('You heard how', 'synced'),
                                       ('someone else', 'other brackets'), ('interrupted', 'interrupted')):
                    if (self.rules == 'world' or getattr(self, 'trade', False)) and words in joined:
                        if 'wWorldLinkReceive' in self.sym:
                            n = 2 + 2 * 20 + 4
                            self.say('    received ' + bytes(self.rd('wWorldLinkReceive', k)
                                                         for k in range(n)).hex(' '))
                            self.say('    sent     ' + bytes(self.rd('wWorldLinkSend', k)
                                                         for k in range(n)).hex(' '))
                        for _ in range(12):
                            self.press('a', 30)
                            if not self.rd('wScriptRunning'):
                                break
                        self.tick(200)
                        if outcome == 'interrupted' and (self.where() != POKECENTER_2F
                                or self.rd('wScriptRunning') or self.rd('wLinkMode')
                                or self.rd('hSerialConnectionStatus') != 0xff):
                            return 'desk: interruption did not restore control'
                        return 'desk: ' + outcome
            in_battle = self.rd('wBattleMode') != 0
            here = self.where()
            if getattr(self, 'trade', False) and here == TRADE_CENTER:
                self.tick(200)
                self.shot('trade_center')
                return 'in the Trade Center'
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
                elif any(w in joined for w in ('prevents usage', 'no PP left', 'disabled!')) and 'no more' not in joined:
                    # the game refused that move (an item, Disable, no PP...):
                    # back to the Fight menu, where the next move is chosen
                    self.say('    (move refused: choosing another)')
                    for _ in range(3):
                        self.press('b', 20)
                elif 'Use next' in joined:
                    self.press('a', 40)
                elif 'Choose a' in joined or 'Which' in joined and in_battle:
                    target = self.next_healthy()
                    if target is None:
                        self.press('b', 20)
                        continue
                    # the party menu cursor wraps around: move it until the
                    # game says it's on the target
                    for _ in range(12):
                        if self.rd('wMenuCursorY') == target + 1:
                            break
                        self.press('down', 6)
                    self.press('a', 30)
                    self.press('a', 30)   # "Switch" on the submenu
                    self.say(f'--- switch to party slot {target}')
                else:
                    self.press('a', 12)
                continue
            if state == 'battle':
                self.tick(400)                # the game reloads the real party
                self.shot('after')
                after = self.party_ids()
                same = after == self.party_before
                self.say(f'battle over; real party back: {same} {self.party_before} -> {after}')
                return f'battle over, real party back: {same}'
            if 'Random teams' in joined and not self.rules_chosen:
                self.rules_chosen = True
                for _ in range(RULES.index(self.rules)):
                    self.press('down', 10)
                self.press('a', 30)
                self.say(f'--- chose {self.rules} rules')
                continue
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
        rf = self.pb.register_file
        # where it was: the ROM bank (hROMBank) and the return addresses on
        # the stack, for finding which routine it was stuck in
        bank = self.mem[self.sym['hROMBank'][1]] if 'hROMBank' in self.sym else '?'
        stack = ' '.join(f'{self.mem[rf.SP + 2 * k] | self.mem[rf.SP + 2 * k + 1] << 8:04x}' for k in range(12))
        self.say(f'    (timeout) PC {rf.PC:04x} ROM bank {bank} SP {rf.SP:04x} stack {stack}'
                 f' serial status {self.mem[self.sym["hSerialConnectionStatus"][1]]:02x}'
                 f' IE {self.mem[0xffff]:02x} timeout frames {self.mem[self.sym["wLinkTimeoutFrames"][1]]:02x}'
                 f'{self.mem[self.sym["wLinkTimeoutFrames"][1] + 1]:02x}')
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
           desync_at=0, shot_every=5, unplug=(0, 0, 0), rules='normal', force_moves=None,
           party_size=None, expect_rejection=False, noise_desk=False, day=None, trade=False, last_rules=None,
           world_unplug=None, unplug_desk=(0, 0)):
    try:
        s = Side(name, rom, sav, load_sym(symp), cable, slot, out, corrupt, seed, noise_setup)
        s.trade = trade
        s.last_rules = last_rules
        s.noise_desk = noise_desk
        if day is not None:
            s.boot_day = day
        s.desync_at = desync_at
        s.shot_every = shot_every
        s.unplug_at, s.unplug_delay, s.unplug_frames = unplug
        s.desk_unplug = unplug_desk
        s.rules = rules
        s.party_size = party_size
        if force_moves:
            s.force_moves = force_moves
        if world_unplug is not None:
            s.unplug_world_at(world_unplug)
        result = s.run(turns, time.time() + seconds)
        # (a session that ends at the desk doesn't stop the other side early)
        if not (expect_rejection and result.startswith('rejected:')) and not result.startswith('desk:') \
                and not result.startswith('in the Trade Center'):
            cable.mm[127] = 1
        s.tick(120)
        s.dump_sram(sav)
        q.put((name, f'{result} ({getattr(s, "setup_retries", 0)} swap retries, '
                     f'{s.setup_errors} setup errors)', s.exchanges, cable.flips(slot), s.friend_report()))
        s.pb.stop(save=False)
    except Exception as e:                       # noqa: BLE001
        cable.mm[127] = 1
        import traceback
        q.put((name, 'error: ' + traceback.format_exc(), [], 0, {}))


FRIEND_TEAM_LENGTH = 16 + 20 * 6  # (constants/serial_constants.asm)
RULES = ('normal', 'random', 'rising', 'unrestricted', 'world')  # the desk's menu, in wire ID order


def compare(ta, tb):
    """Check the records of each action exchange agree, mirrored."""
    problems = []
    for i, (a, b) in enumerate(zip(ta, tb)):
        if a['me'] != b['foe'] or a['foe'] != b['me']:
            problems.append(f'exchange {i + 1}: A sees me {a["me"]} foe {a["foe"]}, '
                            f'B sees me {b["me"]} foe {b["foe"]}')
        elif a.get('mestat') != b.get('foestat') or a.get('foestat') != b.get('mestat'):
            problems.append(f'exchange {i + 1}: status/stat changes differ: A me {a["mestat"]} '
                            f'foe {a["foestat"]}, B me {b["mestat"]} foe {b["foestat"]}')
        elif a.get('rn') != b.get('rn'):
            problems.append(f'exchange {i + 1}: random number position differs: A {a["rn"]} B {b["rn"]}')
        elif a['levels'] != b['levels'][::-1]:
            problems.append(f'exchange {i + 1}: active levels differ: A {a["levels"]}, B {b["levels"]}')
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
    ap.add_argument('--force-moves', default='',
                    help='comma-separated move constants every party Pokemon gets before the swap')
    ap.add_argument('--rules', default='normal', help='rules each side picks at the desk: '
                    'normal, random, rising, unrestricted, or A,B (e.g. rising,unrestricted)')
    ap.add_argument('--party-size', type=int, choices=range(1, 7),
                    help='limit both test parties before visiting the desk, using only the in-memory save')
    ap.add_argument('--expect-rejection', choices=('mismatch', 'build', 'rising-party'),
                    help='both desks should refuse the match for this reason')
    ap.add_argument('--unplug', default='',
                    help='AT,DELAY,FRAMES: at action exchange AT (side A), wait DELAY frames, '
                         'then unplug the cable for FRAMES frames')
    desk_cut = ap.add_mutually_exclusive_group()
    desk_cut.add_argument('--world-unplug', type=int, choices=(1, 2),
                          help='disconnect at the start of this Championship desk exchange')
    desk_cut.add_argument('--unplug-desk', default='',
                          help='N,FRAMES: unplug the cable as byte N of the Championship session starts '
                               '(counted on side A), for FRAMES frames')
    ap.add_argument('--desync-at', type=int, default=0,
                    help="change side B's HP at this action exchange, to test desync detection")
    ap.add_argument('--noise-setup', action='store_true',
                    help='start the noise on entering the Colosseum, before the parties are swapped')
    ap.add_argument('--noise-desk', action='store_true',
                    help="start side B's noise at the battle desk (the Championship's exchange)")
    ap.add_argument('--day-b', type=int, default=None, help="set side B's clock to this day")
    ap.add_argument('--trade', action='store_true',
                    help='go to the trade desk instead: both should reach the Trade Center')
    ap.add_argument('--last-rules', default=None,
                    help="each cartridge's last battle rules (as --rules: one, or A,B), set at boot")
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--out', default='linktest_out')
    args = ap.parse_args()
    formats = args.rules.split(',')
    if len(formats) not in (1, 2) or any(rule not in RULES for rule in formats):
        ap.error('invalid battle format')
    last_rules = args.last_rules.split(',') if args.last_rules else [None]
    if len(last_rules) not in (1, 2) or any(r is not None and r not in RULES for r in last_rules):
        ap.error('invalid --last-rules')
    if args.world_unplug and (any(rule != 'world' for rule in formats) or args.trade or args.unplug):
        ap.error('--world-unplug needs Championship rules on both sides and no other unplug')
    os.makedirs(args.out, exist_ok=True)
    force_ids = None
    if args.force_moves:
        sys.path.insert(0, os.path.join(ROOT, 'meta_sim'))
        from oracle_pipeline import rgbasm_values
        names = args.force_moves.split(',')
        ids = rgbasm_values(names, None)
        force_ids = [ids[n] for n in names]
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
                                            else (0, 0, 0),
                                            (formats * 2)[slot], force_ids, args.party_size, bool(args.expect_rejection),
                                            args.noise_desk and slot == 1, args.day_b if slot else None,
                                            args.trade, (last_rules * 2)[slot],
                                            args.world_unplug if not slot else None,
                                            tuple(map(int, args.unplug_desk.split(','))) if args.unplug_desk
                                            and not slot else (0, 0)))
        p.start()
        ctx_procs.append(p)
    res = {}
    friends = {}
    for _ in ctx_procs:
        name, result, turns, flips, friend = q.get(timeout=args.seconds + 120)
        res[name] = (result, turns, flips)
        friends[name] = friend
    for p in ctx_procs:
        p.join(timeout=30)
    for name in 'AB':
        print(f'{name}: {res[name][0]} after {len(res[name][1])} action exchanges, '
              f'{res[name][2]} bits flipped')
    if args.expect_rejection:
        reasons = {'mismatch': 'different rules', 'build': 'different build',
                   'rising-party': 'illegal Rising Star party'}
        wanted = 'rejected: ' + reasons[args.expect_rejection]
        if all(res[name][0].startswith(wanted) and not res[name][1] for name in 'AB'):
            return 0
        print(f'Expected both desks to report {wanted}.')
        return 1
    if args.trade:
        if all(res[name][0].startswith('in the Trade Center') for name in 'AB'):
            return 0
        print('Expected both sides to reach the Trade Center.')
        return 1
    if args.world_unplug:
        if all(res[name][0].startswith('desk: interrupted') and not res[name][1] for name in 'AB'):
            return 0
        print('Expected both desks to report an interruption before any battle.')
        return 1
    if all(res[name][0].startswith('desk:') for name in 'AB'):
        # a Championship session that ended at the desk: the caller checks it
        return 0
    problems = compare(res['A'][1], res['B'][1])
    n = min(len(res['A'][1]), len(res['B'][1]))
    if not n:
        problems.append('No action exchange completed on both sides.')
    elif not args.rom_b:
        expected_level = {'rising': 30, 'unrestricted': None}.get(formats[0], 50)
        expected_size = {'rising': 3, 'random': 6, 'world': 6}.get(formats[0])
        for name, other in (('A', 'B'), ('B', 'A')):
            for exchange in res[name][1]:
                if expected_level is None:  # (Unrestricted: each at its own level)
                    mine, theirs = exchange['levels']
                    if friends[name] and friends[other] and (
                            mine not in friends[name]['levels'] or theirs not in friends[other]['levels']):
                        problems.append(f'Side {name} battled at levels {exchange["levels"]}, not their own '
                                        f'({sorted(friends[name]["levels"])} and {sorted(friends[other]["levels"])}).')
                        break
                elif exchange['levels'] != (expected_level, expected_level):
                    problems.append(f'Side {name} did not battle at level {expected_level}.')
                    break
                if expected_size and any(len(exchange[key]) != expected_size for key in ('party', 'otparty')):
                    problems.append(f'Side {name} did not enter with {expected_size} Pokémon per party.')
                    break
    # Friend Battles: after a finished battle, each side keeps the other's team
    # (not a Random Battle's generated one)
    for name, other in (('A', 'B'), ('B', 'A')):
        if not res[name][0].startswith('battle over') or not friends[name] or args.rom_b:
            continue
        kept = [team for team in friends[name]['teams'] if team[:2] == b'FB']
        if formats[0] == 'random':
            if kept:
                problems.append(f'Side {name} kept a Random Battle team.')
            continue
        theirs = friends[other]
        match = [team for team in kept if team[7:15] == theirs['name']]
        if len(match) != 1:
            problems.append(f'Side {name} kept {len(match)} teams for {other}.')
            continue
        team = match[0]
        if sum(team[3:]) + 0x46 & 0xff != team[2]:
            problems.append(f'Side {name} kept a team with a bad checksum.')
        if team[3] != RULES.index(formats[0]):
            problems.append(f'Side {name} kept the wrong rules: {team[3]}.')
        mons = [(team[16 + 20 * i], team[17 + 20 * i]) for i in range(team[15])]
        sent = theirs['mons'][:args.party_size] if args.party_size else theirs['mons']
        if mons != sent:
            problems.append(f'Side {name} kept {mons}, not {other}\'s {sent}.')
    sync_stops = []
    for name in 'AB':
        result = res[name][0]
        if result.startswith(('error:', 'timeout', 'battle over, real party back: False')):
            problems.append(f'Side {name} did not finish successfully.')
        if result.startswith('stopped: out of sync'):
            sync_stops.append(name)
    if args.desync_at and not sync_stops:
        problems.append('The injected desync did not stop the battle.')
    if sync_stops and not (args.corrupt or args.unplug or args.desync_at):
        problems.append(f'Unexpected sync stop on side {", ".join(sync_stops)}.')
    if problems:
        print('\n'.join(problems[:10]))
        return 1
    print(f'In sync at all {n} action exchanges both sides made.')
    return 0


if __name__ == '__main__':
    mp.set_start_method('fork')
    sys.exit(main())
