#!/usr/bin/env python3
"""Check the fixed battle settings (LockLinkOptions, engine/menus/
initial_options_menu.asm) in the running game (PyBoy).

Natures, abilities and the physical/special split on, perfect IVs off and
Modern EVs are the same on every cartridge, so any two can link:

- continuing a save whose settings differ corrects them before continuing
  redoes the party's EVs and stats (FixPlayerEVsAndStats, as on every
  continue), so the stats are the fixed settings';
- continuing a save already on them changes no setting;
- LockLinkOptions, from every mix of those settings, leaves exactly the
  fixed ones, keeps the others (experience scaling, affection, colors, ...)
  and says whether anything changed;
- the New Game screen offers only the others.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_link_options.py SAVE.sav
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_friend_records import Caller, Game, rgbasm_values  # noqa: E402

NAMES = ['NATURES_OPT', 'ABILITIES_OPT', 'COLOR_VARY_OPT', 'PERFECT_IVS_OPT', 'TRADED_AS_OT_OPT', 'AFFECTION_OPT',
         'SCALED_EXP_OPT', 'PSS_OPT', 'LINK_OPTMASK', 'EV_OPTMASK', 'EVS_OPT_CLASSIC', 'EVS_OPT_MODERN',
         'LINK_OPTS_LOCKED', 'LINK_EVS_LOCKED', 'PARTYMON_STRUCT_LENGTH', 'MON_MAXHP', 'NUM_STATS']


def main():
    K = rgbasm_values(NAMES, None)
    save = bytearray(open(sys.argv[1], 'rb').read())
    fails = []

    def check(cond, what):
        if not cond:
            fails.append(what)

    # where the save keeps its options (outside the checksummed game data)
    probe = Game(bytes(save))
    sym = probe.sym
    probe.pb.stop(save=False)
    bank, addr = sym['sOptions']
    base = bank * 0x2000 + addr - 0xa000
    off1 = sym['wInitialOptions'][1] - sym['wOptions'][1]
    off2 = sym['wInitialOptions2'][1] - sym['wOptions'][1]
    locked1 = K['LINK_OPTS_LOCKED']
    personal = 1 << K['SCALED_EXP_OPT'] | 1 << K['AFFECTION_OPT'] | 1 << K['COLOR_VARY_OPT']

    def boot(opts1, opts2):
        s = bytearray(save)
        s[base + off1] = opts1
        s[base + off2] = opts2
        g = Game(bytes(s))
        fixes = []
        g.pb.hook_register(*g.sym['FixPlayerEVsAndStats'], lambda _: fixes.append(1), None)
        g.boot()
        return g, fixes

    def stats(g):
        L = K['PARTYMON_STRUCT_LENGTH']
        out = []
        for i in range(g.rd('wPartyCount')):
            a = g.addr('wPartyMon1') + i * L + K['MON_MAXHP']
            out.append(bytes(g.m[1, a + k] for k in range(2 * K['NUM_STATS'])))
        return out

    # a save from before, with other battle settings (natures off, perfect IVs
    # on, Classic EVs), and some personal ones
    other1 = (1 << K['ABILITIES_OPT']) | (1 << K['PERFECT_IVS_OPT']) | (1 << K['PSS_OPT']) | personal
    other2 = K['EVS_OPT_CLASSIC']
    g, fixes = boot(other1, other2)
    o1, o2 = g.rd('wInitialOptions'), g.rd('wInitialOptions2')
    check(o1 & K['LINK_OPTMASK'] == locked1, f'old save: battle settings {o1:08b}, not the fixed ones')
    check(o2 & K['EV_OPTMASK'] == K['LINK_EVS_LOCKED'], f'old save: EV mode {o2 & 3}, not Modern')
    check(o1 & personal == personal, 'old save: personal settings were changed')
    check(fixes, "old save: the party's EVs and stats weren't redone")
    redone = stats(g)
    caller = Caller(g)
    caller.call('FixPlayerEVsAndStats')
    check(stats(g) == redone, "old save: the party's stats weren't what the fixed settings give")
    g.pb.stop(save=False)

    # a save already on the fixed settings: nothing changes
    same2 = (save[base + off2] & ~K['EV_OPTMASK']) | K['LINK_EVS_LOCKED']
    g, fixes = boot(locked1 | personal, same2)
    check(g.rd('wInitialOptions') == locked1 | personal and g.rd('wInitialOptions2') == same2,
          'a save on the fixed settings: settings changed')

    # LockLinkOptions from every mix of the battle settings
    caller = Caller(g)
    bits = [K['NATURES_OPT'], K['ABILITIES_OPT'], K['PERFECT_IVS_OPT'], K['PSS_OPT']]
    for mix in range(16):
        for ev in (0, K['EVS_OPT_CLASSIC'], K['EVS_OPT_MODERN']):
            o1 = personal | sum(1 << b for i, b in enumerate(bits) if mix >> i & 1)
            o2 = ev | (same2 & ~K['EV_OPTMASK'])
            g.wr('wInitialOptions', o1)
            g.wr('wInitialOptions2', o2)
            caller.call('LockLinkOptions')
            n1, n2 = g.rd('wInitialOptions'), g.rd('wInitialOptions2')
            want_change = (o1 & K['LINK_OPTMASK']) != locked1 or ev != K['LINK_EVS_LOCKED']
            if n1 != (o1 & ~K['LINK_OPTMASK']) | locked1 or n2 != (o2 & ~K['EV_OPTMASK']) | K['LINK_EVS_LOCKED']:
                fails.append(f'LockLinkOptions from {o1:08b}/{o2:08b}: {n1:08b}/{n2:08b}')
            if caller.out['carry'] != want_change:
                fails.append(f'LockLinkOptions from {o1:08b}/{o2:08b}: said changed={caller.out["carry"]}')

    # the New Game screen's rows: only the settings that aren't fixed
    bank, addr = g.sym['InitialOptionsMenuItems']
    rom = open(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'polishedcrystal-3.2.3.gbc'), 'rb').read()
    at = bank * 0x4000 + addr - 0x4000 if bank else addr
    items = list(rom[at:at + rom[at] + 2])
    check(items == [5, 5, 6, 8, 9, 10, 0xff], f'the New Game rows are {items}')
    g.pb.stop(save=False)

    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
