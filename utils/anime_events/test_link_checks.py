#!/usr/bin/env python3
"""Check the Cable Club desk's link checks (PerformLinkChecks,
engine/link/link.asm) on one cartridge, with the other side's replies
scripted: each byte exchange (Serial_ExchangeBytes) is answered from a
list instead of a cable, and the nybble exchanges echo.

- the other game's own replies: the checks pass (LINK_ERR_SUCCESS);
- a different ROM checksum, sent properly: LINK_ERR_MISMATCH_BUILD;
- different rules, sent properly: LINK_ERR_MISMATCH_RULES;
- what comes when the other game isn't exchanging yet (no preamble, or
  bytes that aren't the nybble bytes the checksum and rules are sent as):
  LINK_ERR_TRANSFER, which the desk answers by offering to try again, never
  "not the same build" or "different rules" (the false verdict a family
  member could take for needing a new ROM);
- no preamble in the first exchanges either: LINK_ERR_TRANSFER, and the
  search for it stops at the end of what can come (it used to search on
  past the buffer).

Usage (from the repository root, after make):
  python3 utils/anime_events/test_link_checks.py SAVE.sav
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_friend_records import Caller, Game, rgbasm_values  # noqa: E402

NAMES = ['LINK_GAME_ID', 'LINK_VERSION', 'LINK_MIN_TRADE_VERSION', 'SERIAL_PREAMBLE_BYTE',
         'SERIAL_POLISHED_PREAMBLE_BYTE', 'LINK_COLOSSEUM', 'LINK_RULE_STANDARD', 'LINK_RULE_RISING_STAR',
         'LINK_ERR_SUCCESS', 'LINK_ERR_MISMATCH_BUILD', 'LINK_ERR_MISMATCH_RULES', 'LINK_ERR_TRANSFER',
         'USING_EXTERNAL_CLOCK', 'SERIAL_POLISHED_MAX_PREAMBLE_LENGTH']


def main():
    K = rgbasm_values(NAMES, None)
    errs = {K[n]: n for n in NAMES if n.startswith('LINK_ERR_')}
    g = Game(open(sys.argv[1], 'rb').read())
    g.boot()
    caller = Caller(g)
    base = g.state()
    fails = []
    replies = []

    def ret():
        rf = g.pb.register_file
        sp = rf.SP
        rf.PC = g.m[sp] | g.m[sp + 1] << 8
        rf.SP = sp + 2

    def exchange_bytes(_):
        rf = g.pb.register_file
        de = rf.D << 8 | rf.E
        data = replies.pop(0) if replies else []
        for k, v in enumerate(data):
            g.m[de + k] = v
        ret()

    def exchange_nybble(_):
        ret()  # (the other side gives back what was sent)

    g.pb.hook_register(*g.sym['Serial_ExchangeBytes'], exchange_bytes, None)
    g.pb.hook_register(*g.sym['Link_ExchangeNybble'], exchange_nybble, None)
    g.pb.hook_register(*g.sym['PrepareForLinkTransfers'], lambda _: ret(), None)

    POL = K['SERIAL_POLISHED_PREAMBLE_BYTE']
    V, M = K['LINK_VERSION'], K['LINK_MIN_TRADE_VERSION']
    room = K['LINK_COLOSSEUM'] - 1

    def nyb(x):
        return [0x10 | x >> 4, 0x10 | x & 15]

    def run(third=None, first=None, checksum=None, rules=None):
        g.load(base)
        g.wr('wChosenCableClubRoom', room)
        g.wr('wLinkBattleRules', K['LINK_RULE_STANDARD'])
        g.m[g.sym['hSerialConnectionStatus'][1]] = K['USING_EXTERNAL_CLOCK']
        cs = checksum if checksum is not None else g.rd('wRomChecksum') | g.rd('wRomChecksum', 1) << 8
        good_third = ([POL, g.rd('wInitialOptions'), g.rd('wInitialOptions2')] + nyb(cs & 0xff) + nyb(cs >> 8)
                      + [0x10 | (K['LINK_RULE_STANDARD'] if rules is None else rules)])
        replies[:] = [first if first is not None else [POL, K['LINK_GAME_ID']],
                      [POL, V >> 8, V & 0xff, M >> 8, M & 0xff, room],
                      third if third is not None else good_third]
        caller.call('PerformLinkChecks')
        got = g.m[g.sym['hScriptVar'][1]]
        return errs.get(got, got)

    def expect(what, got, want):
        if got != want:
            fails.append(f'{what}: {got}, not {want}')

    expect('the same game', run(), 'LINK_ERR_SUCCESS')
    cs = g.rd('wRomChecksum') | g.rd('wRomChecksum', 1) << 8
    expect('another build', run(checksum=cs ^ 0x0101), 'LINK_ERR_MISMATCH_BUILD')
    expect('other rules', run(rules=K['LINK_RULE_RISING_STAR']), 'LINK_ERR_MISMATCH_RULES')
    stale = [POL] + [0xff] * 8
    expect('nothing exchanged yet (all $ff)', run(third=stale), 'LINK_ERR_TRANSFER')
    expect('garbled checksum bytes', run(third=[POL, 0, 0, 0x7a, 0x13, 0x22, 0x91, 0x10]), 'LINK_ERR_TRANSFER')
    expect('no preamble in the options exchange', run(third=[0xff] * 12), 'LINK_ERR_TRANSFER')
    expect('no preamble in the first exchange', run(first=[0xfe] * 12), 'LINK_ERR_TRANSFER')

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
