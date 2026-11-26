#!/usr/bin/env python3
"""Check the linked championship's prize persistence (engine/link/world_link.asm:
WorldLinkClaim, WorldLinkCommitClaim, the receipt wWorldLinkReceipt) on one
cartridge (PyBoy, no cable): a champion's record is made directly, then the
routines and the Indigo Plateau desk are run, with reboots from saved files.

The rule: a game's saved receipt names the bracket whose prize it was given,
so the prize and the receipt are saved, or lost, together.

- the routines: a champion without the receipt is offered the prize, with it
  is told it has it; WorldLinkCommitClaim (at save) closes only a bracket the
  receipt names; a receipt for another bracket doesn't count;
- the desk, a repeat win (Bottle Cap) with a full Bag: nothing given and
  nothing claimed (the receipt isn't written), so making room and coming back
  gets it;
- saving then closes the bracket, and another visit gives nothing more;
- power lost after the save but before the bracket closed: the reloaded game
  has the receipt, so it's told it has the prize, not given it again;
- power lost before saving: the reloaded game has neither prize nor receipt,
  and is given the prize;
- after a completed save, corrupting the primary checksum restores the prize
  and receipt from backup without allowing a second claim;
- a first win (Ability Patch) with a full Bag: held at the desk with the
  receipt written, and given once there's room.

Usage (from the repository root, after make):
  python3 utils/linktest/test_world_prize.py SAVE.sav
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'utils', 'anime_events'))
import test_world_link as W  # noqa: E402
from test_friend_records import Caller  # noqa: E402
from test_wild_mons import rgbasm_values  # noqa: E402

fails = []
K = rgbasm_values(['WORLD_LINK_ID', 'WORLD_LINK_SEED', 'WORLD_LINK_HALF', 'WORLD_LINK_PARTNER_ID',
                   'WORLD_LINK_PARTNER_NAME', 'WORLD_LINK_STATUS', 'WORLD_LINK_PARTNER_STATUS', 'WORLD_LINK_LENGTH',
                   'WORLDLINK_CHAMPION', 'WORLDLINK_RUNNER_UP', 'WORLDLINK_CLOSED_F', 'WORLDDESK_CHAMPION',
                   'WORLDDESK_CLAIMED', 'WORLDDESK_NONE', 'CUPWON_WORLD_F', 'MAX_ITEMS', 'MAX_ITEM_STACK',
                   'BIG_NUGGET', 'BOTTLE_CAP', 'ABILITYPATCH', 'EVENT_WORLD_CUP_PRIZE_PENDING'], None)


def check(cond, where, what):
    if not cond:
        fails.append((where, what))


class Desk(W.Indigo):
    def __init__(self, sav):
        super().__init__(sav)
        self.caller = Caller(self.g)

    def call(self, label):
        self.caller.call(label)
        return self.g.m[self.g.sym['hScriptVar'][1]]

    def make_record(self, bracket_id, status=None, closed=False):
        """A champion's record for bracket_id, saved as WorldLinkSave saves it."""
        g = self.g
        status = K['WORLDLINK_CHAMPION'] if status is None else status
        for k in range(K['WORLD_LINK_LENGTH']):
            g.wr('wWorldLinkRecord', 0, k)
        g.wr('wWorldLinkRecord', bracket_id & 0xff, K['WORLD_LINK_ID'])
        g.wr('wWorldLinkRecord', bracket_id >> 8, K['WORLD_LINK_ID'] + 1)
        g.wr('wWorldLinkRecord', 0x34, K['WORLD_LINK_SEED'])
        g.wr('wWorldLinkRecord', 0x12, K['WORLD_LINK_SEED'] + 1)
        g.wr('wWorldLinkRecord', 0x11, K['WORLD_LINK_PARTNER_ID'])
        for k, v in enumerate([0x81, 0x8e, 0x81, 0x53, 0x53, 0x53, 0x53, 0x53]):  # "BOB"
            g.wr('wWorldLinkRecord', v, K['WORLD_LINK_PARTNER_NAME'] + k)
        g.wr('wWorldLinkRecord', status | (1 << K['WORLDLINK_CLOSED_F'] if closed else 0), K['WORLD_LINK_STATUS'])
        g.wr('wWorldLinkRecord', K['WORLDLINK_RUNNER_UP'], K['WORLD_LINK_PARTNER_STATUS'])
        self.call('WorldLinkSave')

    def reopen(self):
        """The bracket's record open again, as if the save's closing never
        happened (rewritten through WorldLinkSave, so it stays checked)."""
        self.call('WorldLinkLoad')
        s = self.g.rd('wWorldLinkRecord', K['WORLD_LINK_STATUS'])
        self.g.wr('wWorldLinkRecord', s & ~(1 << K['WORLDLINK_CLOSED_F']), K['WORLD_LINK_STATUS'])
        self.call('WorldLinkSave')

    def receipt(self):
        return tuple(self.g.rd('wWorldLinkReceipt', k) for k in range(3))

    def set_receipt(self, values):
        for k, v in enumerate(values):
            self.g.wr('wWorldLinkReceipt', v, k)

    def closed(self):
        return bool(self.g.m[0, 0xb1d5 + K['WORLD_LINK_STATUS']] & (1 << K['WORLDLINK_CLOSED_F']))

    def cup_won(self, won):
        self.call('CupCheckRecords')
        bit = 1 << K['CUPWON_WORLD_F']
        r = self.g.rd('wCupRecords')
        self.g.wr('wCupRecords', r | bit if won else r & ~bit)

    def bag_full(self, full):
        g = self.g
        n = K['MAX_ITEMS'] if full else K['MAX_ITEMS'] - 1
        g.wr('wNumItems', n)
        for i in range(n):
            g.wr('wItems', K['BIG_NUGGET'], 2 * i)
            g.wr('wItems', K['MAX_ITEM_STACK'], 2 * i + 1)
        g.wr('wItems', 0xff, 2 * n)

    def event(self, name):
        n = K[name]
        return bool(self.g.rd('wEventFlags', n // 8) & 1 << (n % 8))


def main():
    sav = sys.argv[1]
    out = os.path.join(os.path.dirname(os.path.abspath(sav)), 'world_prize')
    os.makedirs(out, exist_ok=True)
    ID, OTHER = 0x4321, 0x5555

    # the routines
    d = Desk(sav)
    d.make_record(ID)
    d.set_receipt((0, 0, 0))
    check(d.call('WorldLinkOpponent') == K['WORLDDESK_CHAMPION'], 'routines', 'no receipt: not offered the prize')
    d.call('WorldLinkClaim')
    check(d.receipt()[0] != 0 and d.receipt()[1:] == (ID & 0xff, ID >> 8),
          'routines', f'the receipt is {d.receipt()}, not this bracket')
    check(d.call('WorldLinkOpponent') == K['WORLDDESK_CLAIMED'], 'routines', 'with the receipt: not told it has it')
    d.set_receipt((d.receipt()[0], OTHER & 0xff, OTHER >> 8))
    check(d.call('WorldLinkOpponent') == K['WORLDDESK_CHAMPION'], 'routines', "another bracket's receipt counted")
    d.call('WorldLinkCommitClaim')
    check(not d.closed(), 'routines', "closed with another bracket's receipt")
    d.call('WorldLinkClaim')
    d.call('WorldLinkCommitClaim')
    check(d.closed(), 'routines', 'not closed with its receipt')
    check(d.call('WorldLinkOpponent') == K['WORLDDESK_NONE'], 'routines', 'a closed bracket still offered')
    d.g.pb.stop(save=False)

    # the desk: a repeat win with a full Bag, then room, then saving
    d = Desk(sav)
    d.make_record(ID)
    d.set_receipt((0, 0, 0))
    d.cup_won(True)
    d.bag_full(True)
    d.visit('b')
    check(d.items('BOTTLE_CAP') == 0, 'full Bag', 'a Bottle Cap with a full Bag?')
    check(d.receipt() == (0, 0, 0), 'full Bag', 'claimed with nothing given')
    check(not d.closed(), 'full Bag', 'the bracket closed with nothing given')
    d.bag_full(False)
    d.visit('b')
    check(d.items('BOTTLE_CAP') == 1, 'room', f'{d.items("BOTTLE_CAP")} Bottle Caps, not 1')
    check(d.receipt()[1:] == (ID & 0xff, ID >> 8), 'room', 'no receipt once given')
    unsaved = d.save(os.path.join(out, 'claimed_unsaved.sav'))  # (SRAM as it is: the claim never saved)

    # power lost before saving: the game reloads with neither prize nor
    # receipt (the record is still open), so it's given the prize
    d = Desk(unsaved)
    caps = d.items('BOTTLE_CAP')
    check(d.receipt() == (0, 0, 0), 'power cut, unsaved', 'a receipt that was never saved')
    d.cup_won(True)
    d.bag_full(False)
    d.visit('b')
    check(d.items('BOTTLE_CAP') == caps + 1, 'power cut, unsaved', 'not given the unsaved prize')
    d.game_save()
    check(d.closed(), 'saved', 'saving did not close the bracket')
    caps = d.items('BOTTLE_CAP')
    d.visit('b')
    check(d.items('BOTTLE_CAP') == caps, 'saved', 'given again after saving')
    # power lost after the save, before the bracket closed: reopen it on the
    # cartridge, and reboot from the saved game (which has the receipt)
    d.reopen()
    check(not d.closed(), 'window', '(could not reopen the record)')
    reopened = d.save(os.path.join(out, 'window.sav'))
    d = Desk(reopened)
    d.call('WorldLinkLoad')
    caps = d.items('BOTTLE_CAP')
    check(d.receipt()[1:] == (ID & 0xff, ID >> 8), 'window', 'the saved game lost its receipt')
    d.visit('b')
    check(d.items('BOTTLE_CAP') == caps, 'window', 'given again after the power cut')
    d.game_save()
    check(d.closed(), 'window', 'the next save did not close the bracket')

    # Damage the primary checksum after a complete save, then Continue.
    backup_caps = d.items('BOTTLE_CAP')
    bank, address = d.g.sym['sChecksum']
    primary_checksum = bank * 0x2000 + address - 0xa000
    damaged = d.save(os.path.join(out, 'damaged_primary.sav'))
    with open(damaged, 'r+b') as f:
        f.seek(primary_checksum)
        value = f.read(1)[0]
        f.seek(primary_checksum)
        f.write(bytes([value ^ 1]))
    d = Desk(damaged)
    check(backup_caps == 1 and d.items('BOTTLE_CAP') == backup_caps,
          'backup recovery', 'the backup did not restore the prize')
    check(d.closed() and d.receipt()[1:] == (ID & 0xff, ID >> 8),
          'backup recovery', 'the backup did not restore the receipt for the closed bracket')
    d.visit('b')
    check(d.items('BOTTLE_CAP') == backup_caps, 'backup recovery', 'given again after loading the backup')
    d.g.pb.stop(save=False)

    # a first win with a full Bag: held at the desk, the receipt written
    d = Desk(sav)
    d.make_record(ID)
    d.set_receipt((0, 0, 0))
    d.cup_won(False)
    d.bag_full(True)
    d.visit('b')
    check(d.items('ABILITYPATCH') == 0, 'first, full', 'an Ability Patch with a full Bag?')
    check(d.event('EVENT_WORLD_CUP_PRIZE_PENDING'), 'first, full', 'the prize not held at the desk')
    check(d.receipt()[1:] == (ID & 0xff, ID >> 8), 'first, full', 'no receipt for the held prize')
    d.bag_full(False)
    d.visit('b')
    check(d.items('ABILITYPATCH') == 1, 'first, room', 'the held Ability Patch not given')
    check(not d.event('EVENT_WORLD_CUP_PRIZE_PENDING'), 'first, room', 'still held after giving it')
    d.visit('b')
    check(d.items('ABILITYPATCH') == 1, 'first, again', 'given twice')
    d.g.pb.stop(save=False)

    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
