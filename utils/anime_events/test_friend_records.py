#!/usr/bin/env python3
"""Check Friend Battle records (engine/link/friend_teams.asm) in the running
game (PyBoy), calling the routines directly (no cable: the link harness
checks a real battle's keeping).

- KeepFriendTeam packs the opponent's party (here the save's own, as a
  friend's) exactly as the record format says, eggs aside, PP Ups and hyper
  training included; the first two friends take a slot each, a third isn't
  kept, a rematch replaces that friend's own record, a Random Battle keeps
  nothing, and Unrestricted and Championship battles are kept with their
  rules;
- writing a record touches no byte outside its slot, and the record's marker
  stays cleared until the write is done (a power cut mid-write leaves an
  empty slot, never a wrong team);
- a record with any unusable field, even with a correct checksum, reads as
  an empty slot (FriendDeskFirst);
- LoadFriendTeam unpacks it so every Pokemon matches its original at level
  50: species, form, item, moves, PP (with PP Ups), DVs, personality, EVs,
  happiness, and the stats the game itself gives the original at level 50
  (BT_SetLevel), hyper training included, at full HP.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_friend_records.py SAVE.sav
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_wild_mons import Game, rgbasm_values  # noqa: E402

FRIENDS = {'A': ([0x80, 0x8d, 0x8d, 0x53, 0x53, 0x53, 0x53, 0x53], (0x11, 0x11)),   # "ANN"
           'B': ([0x81, 0x8e, 0x81, 0x53, 0x53, 0x53, 0x53, 0x53], (0x22, 0x22)),   # "BOB"
           'C': ([0x82, 0x88, 0x8d, 0x83, 0x88, 0x53, 0x53, 0x53], (0x33, 0x33))}   # "CINDI"


class Caller:
    """Run a game routine from DelayFrame's entry (where the game waits in
    the overworld): registers saved, its bank switched in, and both put back
    when it returns."""

    def __init__(self, g):
        self.g = g
        self.state = None
        g.pb.hook_register(*g.sym['DelayFrame'], self._hook, None)

    def _hook(self, _):
        g, rf = self.g, self.g.pb.register_file
        if self.state == 'armed':
            self.saved = (rf.A, rf.F, rf.B, rf.C, rf.D, rf.E, rf.HL)
            self.sp = rf.SP
            sp = rf.SP - 2
            g.m[sp], g.m[sp + 1] = rf.PC & 0xff, rf.PC >> 8
            rf.SP = sp
            self.bank = g.m[0xff87]  # hROMBank
            bank, addr = g.sym[self.label]
            g.m[0x2000] = bank
            g.m[0xff87] = bank
            for reg, value in self.regs.items():
                setattr(rf, reg, value)
            rf.PC = addr
            self.state = 'running'
        elif self.state == 'running' and rf.SP == self.sp:
            g.m[0x2000] = self.bank
            g.m[0xff87] = self.bank
            rf.A, rf.F, rf.B, rf.C, rf.D, rf.E, rf.HL = self.saved
            self.state = 'done'

    def call(self, label, **regs):
        self.label, self.regs, self.state = label, regs, 'armed'
        for _ in range(300):
            self.g.tick(2)
            if self.state == 'done':
                return True
        raise AssertionError(f'{label} did not return')


def main():
    save = open(sys.argv[1], 'rb').read()
    K = rgbasm_values(['FRIEND_TEAM_LENGTH', 'FRIENDMON_LENGTH', 'PARTYMON_STRUCT_LENGTH', 'PLAYER_NAME_LENGTH',
                       'MON_SPECIES', 'MON_FORM', 'MON_ITEM', 'MON_MOVES', 'MON_PP', 'MON_DVS', 'MON_PERSONALITY',
                       'MON_EVS', 'MON_HAPPINESS', 'MON_LEVEL', 'MON_HP', 'MON_MAXHP', 'MON_IS_EGG_F',
                       'NUM_STATS', 'LINK_RULE_STANDARD', 'LINK_RULE_RANDOM', 'LINK_RULE_RISING_STAR',
                       'LINK_RULE_UNRESTRICTED', 'LINK_RULE_WORLD', 'NUM_ITEMS', 'NUM_NATURES',
                       'EXTSPECIES_MASK'], None)
    L, N, R = K['PARTYMON_STRUCT_LENGTH'], K['PLAYER_NAME_LENGTH'], K['FRIEND_TEAM_LENGTH']
    g = Game(save)
    g.boot()
    call = Caller(g).call
    fails = []
    slots = (g.sym['sFriendTeam1'][1], g.sym['sFriendTeam2'][1])

    def check(cond, where, what):
        if not cond:
            fails.append((where, what))

    def sram(addr, n):
        return [g.m[0, addr + i] for i in range(n)]

    def set_sram(addr, data):
        for i, v in enumerate(data):
            g.m[0, addr + i] = v

    def party():
        """The save's party: (struct bytes, hyper training) for each Pokemon."""
        out = []
        for i in range(g.rd('wPartyCount')):
            b = g.addr('wPartyMon1') + i * L
            extra = g.addr('wPartyMonOTs') + i * (N + 3) + N
            out.append((bytes(g.m[1, b + k] for k in range(L)), g.m[1, extra]))
        return out

    def opponent(friend, rule, gender=0, mons=None):
        """Make the save's party (or `mons`) the link opponent's."""
        mons = party() if mons is None else mons
        name, tid = FRIENDS[friend]
        g.wr('wOTPartyCount', len(mons))
        for i, (struct, hyper) in enumerate(mons):
            for k, v in enumerate(struct):
                g.wr('wOTPartyMon1', v, i * L + k)
            g.wr('wOTPartyMonOTs', hyper, i * (N + 3) + N)
        for k, v in enumerate(name):
            g.wr('wOTPlayerName', v, k)
        g.wr('wOTPlayerID', tid[0])
        g.wr('wOTPlayerID', tid[1], 1)
        g.wr('wLinkBattleRules', rule)
        g.wr('wLinkOtherPlayerGender', gender)

    def pack(friend, rule, gender, mons):
        name, tid = FRIENDS[friend]
        mons = [(m, h) for m, h in mons if not m[K['MON_FORM']] & (1 << K['MON_IS_EGG_F'])]
        rec = [ord('F'), ord('B'), 0, rule, gender, *tid, *name, len(mons)]
        for m, hyper in mons:
            pp = 0
            for k in range(4):
                pp = (pp >> 2) | (m[K['MON_PP'] + k] & 0xc0)
            rec += [m[K['MON_SPECIES']], m[K['MON_FORM']], m[K['MON_ITEM']], *m[K['MON_MOVES']:K['MON_MOVES'] + 4],
                    pp, *m[K['MON_DVS']:K['MON_DVS'] + 3], m[K['MON_PERSONALITY']],
                    *m[K['MON_EVS']:K['MON_EVS'] + 6], m[K['MON_HAPPINESS']], hyper & 0xfc]
        return rec

    def kept(i):
        return sram(slots[i], R)

    def same_packing(record, expected):
        n = 16 + K['FRIENDMON_LENGTH'] * expected[15]
        return record[:2] == [ord('F'), ord('B')] and record[3:n] == expected[3:n] and \
            record[2] == (0x46 + sum(record[3:])) & 0xff

    mine = party()
    # give the first one some hyper training, so it's carried
    hyper_addr = g.addr('wPartyMonOTs') + N
    g.m[1, hyper_addr] = 0b10101101  # (hyper training's bits, with one of the two that aren't)
    mine = party()
    base = g.state()

    def clear_slots():
        for s in slots:
            set_sram(s, [0] * R)

    # packing, and the slots
    clear_slots()
    opponent('A', K['LINK_RULE_STANDARD'], 1)
    call('KeepFriendTeam')
    check(same_packing(kept(0), pack('A', K['LINK_RULE_STANDARD'], 1, mine)), 'pack',
          f'slot 1 is not the packed party: {bytes(kept(0)[:40]).hex()}')
    check(kept(1)[:2] != [ord('F'), ord('B')], 'slots', 'the first friend took both slots')
    opponent('B', K['LINK_RULE_UNRESTRICTED'])
    call('KeepFriendTeam')
    check(same_packing(kept(1), pack('B', K['LINK_RULE_UNRESTRICTED'], 0, mine)), 'slots',
          'the second friend (Unrestricted) is not in slot 2')
    before = (kept(0), kept(1))
    opponent('C', K['LINK_RULE_STANDARD'])
    call('KeepFriendTeam')
    check((kept(0), kept(1)) == before, 'slots', 'a third friend replaced a kept team')
    # a rematch with a changed team replaces that friend's own record
    changed = [(m, h) for m, h in mine[:3]]
    opponent('A', K['LINK_RULE_WORLD'], 1, changed)
    call('KeepFriendTeam')
    check(same_packing(kept(0), pack('A', K['LINK_RULE_WORLD'], 1, changed)), 'rematch',
          "the rematch (Championship) did not replace that friend's record")
    check(kept(1) == before[1], 'rematch', "the rematch touched the other friend's record")
    # Random Battles aren't kept
    clear_slots()
    opponent('A', K['LINK_RULE_RANDOM'])
    call('KeepFriendTeam')
    check(kept(0)[:2] != [ord('F'), ord('B')] and kept(1)[:2] != [ord('F'), ord('B')], 'random',
          'a Random Battle team was kept')

    # nothing outside the slot is written, and the marker stays cleared until
    # the record is whole
    for i in (0, 1):
        g.load(base)
        clear_slots()
        if i:
            opponent('A', K['LINK_RULE_STANDARD'])
            call('KeepFriendTeam')  # (slot 1 taken, so the next goes to slot 2)
        bank0 = sram(0xa000, 0x2000)
        markers = []
        hook = g.sym['PackFriendMon']
        g.pb.hook_register(*hook, lambda _, i=i: markers.append(tuple(sram(slots[i], 2))), None)
        opponent('B', K['LINK_RULE_STANDARD'])
        call('KeepFriendTeam')
        g.pb.hook_deregister(*hook)
        after = sram(0xa000, 0x2000)
        lo, hi = slots[i] - 0xa000, slots[i] - 0xa000 + R
        outside = [hex(0xa000 + k) for k in range(0x2000) if not lo <= k < hi and bank0[k] != after[k]]
        check(not outside, 'bounds', f'slot {i + 1}: bytes outside it changed: {outside[:6]}')
        check(markers and all(m == (0, 0) for m in markers), 'marker',
              f'slot {i + 1}: the marker was set while the record was written: {markers}')
        check(kept(i)[:2] == [ord('F'), ord('B')], 'marker', f'slot {i + 1}: not marked once written')

    # unusable fields read as an empty slot, even with a correct checksum
    def readable(record):
        record = list(record)
        record[2] = (0x46 + sum(record[3:])) & 0xff
        set_sram(slots[0], record)
        set_sram(slots[1], [0] * R)
        call('FriendDeskFirst')
        return g.m[g.sym['hScriptVar'][1]] != 0

    g.load(base)
    good = pack('A', K['LINK_RULE_STANDARD'], 0, mine)
    good += [0] * (R - len(good))
    check(readable(good), 'fields', 'a good record reads as empty')
    m0 = 16  # the first Pokemon
    for what, offset, value in (('Random rules', 3, K['LINK_RULE_RANDOM']), ('no such rules', 3, 9),
                                ('no such gender', 4, 7), ('no Pokemon', 15, 0), ('seven Pokemon', 15, 7),
                                ('species 0', m0, 0), ('species $ff', m0, 0xff),
                                ('an egg', m0 + 1, good[m0 + 1] | 1 << K['MON_IS_EGG_F']),
                                ('no such item', m0 + 2, K['NUM_ITEMS'] + 1), ('no first move', m0 + 3, 0),
                                ('no such nature', m0 + 11, (good[m0 + 11] & 0xe0) | K['NUM_NATURES'])):
        bad = list(good)
        bad[offset] = value
        check(not readable(bad), 'fields', f'{what}: read as a team')
    bad = list(good)
    bad[m0], bad[m0 + 1] = 0x30, good[m0 + 1] | K['EXTSPECIES_MASK']
    check(not readable(bad), 'fields', 'an extended species past the last: read as a team')
    rising = pack('A', K['LINK_RULE_RISING_STAR'], 0, mine[:2])
    check(not readable(rising + [0] * (R - len(rising))), 'fields', 'Rising Star with two: read as a team')
    rising = pack('A', K['LINK_RULE_RISING_STAR'], 0, mine[:3])
    check(readable(rising + [0] * (R - len(rising))), 'fields', 'Rising Star with three: read as empty')
    marked = list(good)
    marked[2] ^= 0xff
    set_sram(slots[0], marked)
    call('FriendDeskFirst')
    check(g.m[g.sym['hScriptVar'][1]] == 0, 'fields', 'a bad checksum: read as a team')

    # the round trip: unpacked at level 50, each matches the game's own
    # level 50 version of the original
    g.load(base)
    clear_slots()
    opponent('A', K['LINK_RULE_STANDARD'])
    call('KeepFriendTeam')
    g.wr('wFriendBattleSlot', 1)
    g.wr('wCupLevel', 50)
    call('LoadFriendTeam')
    g.wr('wFriendBattleSlot', 0)
    g.wr('wCupLevel', 0)
    ot = [bytes(g.m[1, g.addr('wOTPartyMon1') + i * L + k] for k in range(L)) for i in range(g.rd('wOTPartyCount'))]
    call('BT_SetLevel', A=50)  # (the player's party at level 50, as a cup makes it)
    ours = [m for m, _ in party()]
    check(len(ot) == len(ours), 'round trip', f'{len(ot)} unpacked, not {len(ours)}')
    stats = slice(K['MON_MAXHP'], K['MON_MAXHP'] + 2 * K['NUM_STATS'])
    for i, (o, m) in enumerate(zip(ot, ours)):
        for field, w in (('MON_SPECIES', 1), ('MON_FORM', 1), ('MON_ITEM', 1), ('MON_MOVES', 4), ('MON_DVS', 3),
                         ('MON_PERSONALITY', 1), ('MON_EVS', 6), ('MON_HAPPINESS', 1), ('MON_LEVEL', 1)):
            f = K[field]
            check(o[f:f + w] == m[f:f + w], 'round trip', f'#{i + 1} {field}: {o[f:f + w].hex()} not {m[f:f + w].hex()}')
        check(o[stats] == m[stats], 'round trip', f'#{i + 1} stats {o[stats].hex()} not {m[stats].hex()}'
              + (' (hyper trained)' if i == 0 else ''))
        check(o[K['MON_HP']:K['MON_HP'] + 2] == o[K['MON_MAXHP']:K['MON_MAXHP'] + 2], 'round trip',
              f'#{i + 1} not at full HP')
        pp = o[K['MON_PP']:K['MON_PP'] + 4]
        check([p & 0xc0 for p in pp] == [p & 0xc0 for p in m[K['MON_PP']:K['MON_PP'] + 4]]
              and all(p & 0x3f for p, mv in zip(pp, o[K['MON_MOVES']:K['MON_MOVES'] + 4]) if mv),
              'round trip', f'#{i + 1} PP {pp.hex()}')

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
