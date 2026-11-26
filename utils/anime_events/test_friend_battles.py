#!/usr/bin/env python3
"""Check Friend Battles in the running game (PyBoy), from a save.

A friend's team is written to the cartridge as KeepFriendTeam keeps it after
a link battle (utils/linktest/linktest.py checks that part over a virtual
cable), here from the save's own party, under a made-up friend's name:

- with no team kept, the Cable Club's third receptionist explains, and no
  battle starts; a slot of leftover bytes (a bad checksum) counts as empty;
- with one kept, "Battle" brings out your whole party at level 50 against
  the friend (their class from their gender, their name) with that team:
  species, forms, items, moves and PP Ups, DVs, personality, EVs, at level
  50 and full HP; afterwards your party is back as it was, healed, and
  nothing is left set;
- a Rising Star team battles three of yours, at level 30;
- "Look" shows the team, then each one in the summary screen (Down to the
  next) at its rule's level, leaving nothing set up for a battle; "Next" goes to the other kept team, "Remove"
  empties the slot and leaves the link records alone.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_friend_battles.py SAVE.sav
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_wild_mons import Game, rgbasm_values  # noqa: E402

FRIEND = [0x85, 0x91, 0x88, 0x84, 0x8d, 0x83, 0x53, 0x53]  # "FRIEND@@"
OTHER = [0x82, 0x80, 0x8b, 0x53, 0x53, 0x53, 0x53, 0x53]   # "CAL@"


def main():
    save = open(sys.argv[1], 'rb').read()
    names = ['FRIEND_TEAM_LENGTH', 'FRIENDMON_LENGTH', 'FRIEND_TEAM_HEADER_LENGTH', 'PARTYMON_STRUCT_LENGTH',
             'MON_SPECIES', 'MON_FORM', 'MON_ITEM', 'MON_MOVES', 'MON_PP', 'MON_DVS', 'MON_PERSONALITY',
             'MON_EVS', 'MON_HAPPINESS', 'MON_LEVEL', 'MON_HP', 'MON_MAXHP', 'MON_STATUS', 'MON_IS_EGG_F',
             'LINK_RULE_STANDARD', 'LINK_RULE_RISING_STAR', 'CAL', 'CARRIE', 'PLAYER_FEMALE',
             'GROUP_POKECENTER_2F', 'MAP_POKECENTER_2F', 'NUM_MOVES']
    K = rgbasm_values(names, None)
    L = K['PARTYMON_STRUCT_LENGTH']
    g = Game(save)
    g.boot()
    fails = []
    slots = (g.sym['sFriendTeam1'][1], g.sym['sFriendTeam2'][1])

    def party_mon(i):
        b = g.addr('wPartyMon1') + i * L
        return bytes(g.m[1, b + k] for k in range(L))

    def pack(mons, rule, gender, name, tid=(0x12, 0x34)):
        rec = [ord('F'), ord('B'), 0, rule, gender, *tid, *name, len(mons)]
        for m in mons:
            pp = 0
            for k in range(K['NUM_MOVES']):
                pp = (pp >> 2) | (m[K['MON_PP'] + k] & 0xc0)
            rec += [m[K['MON_SPECIES']], m[K['MON_FORM']], m[K['MON_ITEM']],
                    *m[K['MON_MOVES']:K['MON_MOVES'] + 4], pp, *m[K['MON_DVS']:K['MON_DVS'] + 3],
                    m[K['MON_PERSONALITY']], *m[K['MON_EVS']:K['MON_EVS'] + 6], m[K['MON_HAPPINESS']], 0]
        rec += [0] * (K['FRIEND_TEAM_LENGTH'] - len(rec))
        rec[2] = (0x46 + sum(rec[3:])) & 0xff
        return rec

    def write_slot(i, rec):
        for k, v in enumerate(rec):
            g.m[0, slots[i] + k] = v

    def read_slot(i):
        return [g.m[0, slots[i] + k] for k in range(K['FRIEND_TEAM_LENGTH'])]

    def party_block():
        a = g.addr('wPartyCount')
        return bytes(g.m[1, a + i] for i in range(g.addr('wPartyMonNicknamesEnd') - a))

    def talk():
        g.warp(K['GROUP_POKECENTER_2F'], K['MAP_POKECENTER_2F'], 13, 4)
        g.tick(30)
        g.face('up')
        g.tick(10)

    def until_battle(presses=20):
        for _ in range(presses):
            g.press('a', 40)
            if g.rd('wBattleMode'):
                return True
        for _ in range(200):
            if g.rd('wBattleMode'):
                return True
            g.tick(2)
        return False

    def win():
        g.tick(300)
        for i in range(600):
            if i < 20:
                for k in range(g.rd('wOTPartyCount')):
                    g.wr('wOTPartyMon1HP', 0, k * L)
                    g.wr('wOTPartyMon1HP', 0, k * L + 1)
                g.wr('wEnemyMonHP', 0)
                g.wr('wEnemyMonHP', 1, 1)
                g.wr('wBattleMonHP', 3)
                g.wr('wBattleMonHP', 0xe7, 1)
                g.wr('wEnemyMonSpeed', 0)
                g.wr('wEnemyMonSpeed', 1, 1)
            g.press('a', 20)
            if not g.rd('wBattleMode'):
                break

    def settle():
        for _ in range(120):
            g.tick(30)
            g.press('b', 10)
            if not g.rd('wScriptRunning') and not g.rd('wBattleMode'):
                g.tick(60)
                if not g.rd('wScriptRunning'):
                    return

    n = g.rd('wPartyCount')
    mine = [party_mon(i) for i in range(n)]
    mine = [m for m in mine if not m[K['MON_FORM']] & (1 << K['MON_IS_EGG_F'])]
    base = g.state()
    before = party_block()
    records = bytes(g.m[0, g.sym['sLinkBattleStats'][1] + i] for i in range(64))

    # nothing kept (and leftover bytes): no battle
    for leftover in (False, True):
        g.load(base)
        write_slot(0, [0] * K['FRIEND_TEAM_LENGTH'])
        bad = pack(mine, K['LINK_RULE_STANDARD'], 0, FRIEND)
        bad[2] ^= 1
        write_slot(1, bad if leftover else [0xff] * K['FRIEND_TEAM_LENGTH'])
        talk()
        if until_battle(10):
            fails.append(('empty', f'a battle started (leftover bytes: {leftover})'))
        settle()

    # a Standard team, in the second slot: battle it
    g.load(base)
    write_slot(0, [0] * K['FRIEND_TEAM_LENGTH'])
    write_slot(1, pack(mine, K['LINK_RULE_STANDARD'], K['PLAYER_FEMALE'], FRIEND))
    talk()
    if not until_battle(12):
        fails.append(('standard', 'no battle'))
    else:
        if (g.rd('wOtherTrainerClass'), g.rd('wOtherTrainerID')) != (K['CAL'] + K['PLAYER_FEMALE'], 1):
            fails.append(('standard', f'trainer {g.rd("wOtherTrainerClass")} #{g.rd("wOtherTrainerID")}'))
        if [g.rd('wOTPlayerName', i) for i in range(7)] != FRIEND[:7]:
            fails.append(('standard', "the trainer isn't named for the friend"))
        if g.rd('wOTPartyCount') != len(mine):
            fails.append(('standard', f'{g.rd("wOTPartyCount")} Pokemon, not {len(mine)}'))
        for i, m in enumerate(mine[:g.rd('wOTPartyCount')]):
            b = g.addr('wOTPartyMon1') + i * L
            ot = bytes(g.m[1, b + k] for k in range(L))
            for field, w in (('MON_SPECIES', 1), ('MON_FORM', 1), ('MON_ITEM', 1), ('MON_MOVES', 4),
                             ('MON_DVS', 3), ('MON_PERSONALITY', 1), ('MON_EVS', 6), ('MON_HAPPINESS', 1)):
                f = K[field]
                if ot[f:f + w] != m[f:f + w]:
                    fails.append(('standard', f'#{i + 1} {field} {ot[f:f + w].hex()}, not {m[f:f + w].hex()}'))
            ups = [ot[K['MON_PP'] + k] & 0xc0 for k in range(4)]
            if ups != [m[K['MON_PP'] + k] & 0xc0 for k in range(4)] or not ot[K['MON_PP']] & 0x3f:
                fails.append(('standard', f'#{i + 1} PP {ot[K["MON_PP"]:K["MON_PP"] + 4].hex()}'))
            hp, maxhp = ot[K['MON_HP']:K['MON_HP'] + 2], ot[K['MON_MAXHP']:K['MON_MAXHP'] + 2]
            if ot[K['MON_LEVEL']] != 50 or hp != maxhp or maxhp == b'\0\0':
                fails.append(('standard', f'#{i + 1} level {ot[K["MON_LEVEL"]]}, HP {hp.hex()}/{maxhp.hex()}'))
        if {g.rd('wPartyMon1Level', i * L) for i in range(g.rd('wPartyCount'))} != {50}:
            fails.append(('standard', 'your party is not at level 50'))
        win()
        settle()
        after = party_block()
        if after[0] != before[0]:
            fails.append(('standard', 'party count changed'))
        else:
            start = g.addr('wPartyMon1') - g.addr('wPartyCount')
            skip = set(range(1, 8))
            for i in range(after[0]):
                b = start + i * L
                for f, w in ((K['MON_HP'], 2), (K['MON_STATUS'], 2), (K['MON_PP'], 4)):
                    skip |= set(range(b + f, b + f + w))
            diff = [i for i in range(len(before)) if before[i] != after[i] and i not in skip]
            if diff:
                fails.append(('standard', f'party changed at offsets {diff[:8]}'))
        if g.rd('wFriendBattleSlot') or g.rd('wCupLevel'):
            fails.append(('standard', 'left set afterwards'))

    # a Rising Star team: three of yours (hooked choice), at level 30
    g.load(base)
    write_slot(0, pack(mine[:3], K['LINK_RULE_RISING_STAR'], 0, FRIEND))
    write_slot(1, [0] * K['FRIEND_TEAM_LENGTH'])
    bank, addr = g.sym['BT_PartySelect']

    def choose(_):
        rf = g.pb.register_file
        g.wr('wBT_PartySelectCounter', 3)
        for i in range(3):
            g.wr('wBT_PartySelections', i, i)
        rf.F &= ~0x10
        sp = rf.SP
        rf.SP = sp + 2
        rf.PC = g.m[sp] | (g.m[sp + 1] << 8)
    g.pb.hook_register(bank, addr, choose, None)
    talk()
    if not until_battle(12):
        fails.append(('rising star', 'no battle'))
    else:
        if (g.rd('wPartyCount'), g.rd('wOTPartyCount')) != (3, 3):
            fails.append(('rising star', f'{g.rd("wPartyCount")} against {g.rd("wOTPartyCount")}'))
        levels = {g.rd('wPartyMon1Level', i * L) for i in range(3)} | {g.rd('wOTPartyMon1Level', i * L)
                                                                       for i in range(3)}
        if levels != {30}:
            fails.append(('rising star', f'levels {levels}'))
        win()
        settle()
    g.pb.hook_deregister(bank, addr)

    # Look, Next and Remove, with two teams
    def screen_text():
        return bytes(g.rd('wTilemap', i) for i in range(20 * 18))

    g.load(base)
    write_slot(0, pack(mine, K['LINK_RULE_STANDARD'], 0, FRIEND))
    write_slot(1, pack(mine[:2], K['LINK_RULE_STANDARD'], 0, OTHER, (0x56, 0x78)))
    NEXT = bytes([0x8d, 0xa4, 0xb7, 0xb3])  # "Next", on the desk's menu
    YES = bytes([0x98, 0xa4, 0xb2])  # "Yes"

    def menu(item):
        # through any text to the desk's menu, then to the item (1-4)
        for _ in range(20):
            if NEXT in screen_text():
                break
            g.press('a', 40)
        g.tick(30)
        for _ in range(8):
            if g.rd('wMenuCursorY') == item:
                break
            g.press('down', 20)
        g.press('a', 60)

    talk()
    menu(2)  # Look
    if g.rd('wFriendTeamSlot') != 0:
        fails.append(('desk', f'started on slot {g.rd("wFriendTeamSlot")}'))
    g.tick(60)
    shown = screen_text()
    if bytes(FRIEND[:6]) not in shown:
        fails.append(('look', "the friend's name isn't shown"))
    g.press('a', 120)
    # then the summary screen: the team as you'd battle it (Standard: 50)
    g.tick(90)
    looked = [(g.rd('wTempMonSpecies'), g.rd('wTempMonLevel'))]
    g.press('down', 60)
    looked.append((g.rd('wTempMonSpecies'), g.rd('wTempMonLevel')))
    want = [(g.rd('wOTPartyMon1Species', i * L), 50) for i in range(2)]
    if g.rd('wOTPartyCount') < 2 or looked != want:
        fails.append(('look', f'summary showed {looked}, not {want}'))
    g.press('b', 120)
    if g.rd('wCupLevel') or g.rd('wFriendBattleSlot') or g.rd('wBattleScriptFlags'):
        fails.append(('look', 'left a battle set up'))
    menu(4)  # Next
    g.tick(30)
    if g.rd('wFriendTeamSlot') != 1:
        fails.append(('next', f'on slot {g.rd("wFriendTeamSlot")}'))
    menu(3)  # Remove
    for _ in range(10):
        if YES in screen_text():
            break
        g.press('a', 40)
    g.press('a', 60)  # yes
    for _ in range(6):
        g.press('b', 30)
    if read_slot(1)[:2] == [ord('F'), ord('B')]:
        fails.append(('remove', 'the team is still kept'))
    if read_slot(0)[:2] != [ord('F'), ord('B')]:
        fails.append(('remove', 'the other team went too'))
    if bytes(g.m[0, g.sym['sLinkBattleStats'][1] + i] for i in range(64)) != records:
        fails.append(('remove', 'the link records changed'))

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
