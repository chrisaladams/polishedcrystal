#!/usr/bin/env python3
"""Check the fixed game settings (LockLinkOptions, engine/menus/
initial_options_menu.asm) in the running game (PyBoy).

Every game setting is the same on every cartridge (the owner's decision:
everyone plays the same game, and any two can link): natures, abilities,
color variation and the physical/special split on; perfect IVs, traded
Pokemon obeying as your own, the affection bonus, scaled experience and no
experience off; Modern EVs; evolving in battle on. There is no New Game
options screen, and no New Game+:

- continuing a save whose settings differ corrects them before continuing
  redoes the party's EVs and stats (FixPlayerEVsAndStats, as on every
  continue), so the stats are the fixed settings';
- continuing a save already on them changes no setting;
- LockLinkOptions, from every mix of the settings, leaves exactly the fixed
  ones, keeps the second byte's other bits, and says whether anything
  changed; the old reset-options request bit is cleared;
- the main menu offers Continue, New Game, Options and Music Player, never
  New Game+, even once Leaf is beaten (when New Game+ used to appear);
- a New Game on a blank cartridge goes straight to Prof. Elm (no options
  screen) with the fixed settings.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_link_options.py SAVE.sav
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_friend_records import Caller, Game, rgbasm_values  # noqa: E402

NAMES = ['NATURES_OPT', 'ABILITIES_OPT', 'COLOR_VARY_OPT', 'PERFECT_IVS_OPT', 'TRADED_AS_OT_OPT', 'AFFECTION_OPT',
         'SCALED_EXP_OPT', 'PSS_OPT', 'LINK_OPTMASK', 'EV_OPTMASK', 'EVS_OPT_CLASSIC', 'EVS_OPT_MODERN',
         'LINK_OPTS_LOCKED', 'LINK_EVS_LOCKED', 'PARTYMON_STRUCT_LENGTH', 'MON_MAXHP', 'NUM_STATS',
         'GAME_OPTS2_MASK', 'GAME_OPTS2_LOCKED', 'NO_EXP_OPT', 'EVOLVE_IN_BATTLE_OPT', 'RESET_INIT_OPTS',
         'EVENT_BEAT_LEAF']


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
    mask2, locked2 = K['GAME_OPTS2_MASK'], K['GAME_OPTS2_LOCKED']

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

    # a save from before, with other settings: natures off, perfect IVs on,
    # scaled experience, the affection bonus and traded-as-own on, color
    # variation off; Classic EVs, no experience, no evolving in battle, and
    # the old reset-options request
    other1 = (1 << K['ABILITIES_OPT']) | (1 << K['PERFECT_IVS_OPT']) | (1 << K['PSS_OPT']) \
        | (1 << K['SCALED_EXP_OPT']) | (1 << K['AFFECTION_OPT']) | (1 << K['TRADED_AS_OT_OPT'])
    other2 = K['EVS_OPT_CLASSIC'] | (1 << K['NO_EXP_OPT']) | (1 << K['RESET_INIT_OPTS']) | (save[base + off2] & 0x08)
    g, fixes = boot(other1, other2)
    o1, o2 = g.rd('wInitialOptions'), g.rd('wInitialOptions2')
    check(o1 == locked1, f'old save: settings {o1:08b}, not the fixed {locked1:08b}')
    check(o2 & mask2 == locked2, f'old save: second settings {o2 & mask2:08b}, not the fixed {locked2:08b}')
    check(o2 & ~mask2 == other2 & ~mask2, "old save: the second byte's other bits were changed")
    check(fixes, "old save: the party's EVs and stats weren't redone")
    redone = stats(g)
    caller = Caller(g)
    caller.call('FixPlayerEVsAndStats')
    check(stats(g) == redone, "old save: the party's stats weren't what the fixed settings give")
    g.pb.stop(save=False)

    # a save already on the fixed settings (the family's): nothing changes
    same2 = (save[base + off2] & ~mask2) | locked2
    g, fixes = boot(locked1, same2)
    check(g.rd('wInitialOptions') == locked1 and g.rd('wInitialOptions2') == same2,
          'a save on the fixed settings: settings changed')

    # LockLinkOptions from every mix of the first byte, and each second
    caller = Caller(g)
    for o1 in range(256):
        for extra2 in (0, K['EVS_OPT_CLASSIC'], (1 << K['NO_EXP_OPT']) | K['EVS_OPT_MODERN'],
                       K['EVS_OPT_MODERN'], locked2, locked2 | (1 << K['RESET_INIT_OPTS'])):
            o2 = extra2 | (same2 & ~mask2)
            g.wr('wInitialOptions', o1)
            g.wr('wInitialOptions2', o2)
            caller.call('LockLinkOptions')
            n1, n2 = g.rd('wInitialOptions'), g.rd('wInitialOptions2')
            want_change = o1 != locked1 or o2 & mask2 != locked2
            if n1 != locked1 or n2 != (o2 & ~mask2) | locked2:
                fails.append(f'LockLinkOptions from {o1:08b}/{o2:08b}: {n1:08b}/{n2:08b}')
            if caller.out['carry'] != want_change:
                fails.append(f'LockLinkOptions from {o1:08b}/{o2:08b}: said changed={caller.out["carry"]}')
    g.pb.stop(save=False)

    # the main menu: no New Game+, even once Leaf is beaten
    s = bytearray(save)
    leaf = K['EVENT_BEAT_LEAF']
    bank, addr = sym['sPlayerData']
    events = sym['wEventFlags'][1] - sym['wPlayerData'][1]
    at = bank * 0x2000 + addr - 0xa000 + events + leaf // 8
    s[at] |= 1 << (leaf % 8)
    g = Game(bytes(s))
    g.boot()
    caller = Caller(g)
    check(g.rd('wSaveFileExists'), '(the save was not loaded)')
    caller.call('MainMenu_GetWhichMenu')
    menus = open(os.path.join(os.path.dirname(os.path.dirname(HERE)), 'engine', 'menus', 'main_menu.asm')).read()
    menus = re.findall(r'const (MAINMENU_MENU_\w+)', menus)
    check(menus == ['MAINMENU_MENU_NEW_GAME', 'MAINMENU_MENU_CONTINUE'], f'main menu lists: {menus}')
    check(caller.out['A'] == menus.index('MAINMENU_MENU_CONTINUE'),
          f'the main menu with Leaf beaten: menu {caller.out["A"]}, not Continue')
    check('NewGamePlus' not in g.sym and 'MainMenu_NewGamePlus' not in g.sym, 'New Game+ is still in the ROM')
    g.pb.stop(save=False)

    # a New Game on a blank cartridge: no options screen, straight to Prof.
    # Elm, with the fixed settings
    g = Game(bytes(0x8000))
    at_elm = []
    g.pb.hook_register(*g.sym['ProfElmSpeech'],
                       lambda _: at_elm.append((g.rd('wInitialOptions'), g.rd('wInitialOptions2'))), None)
    g.tick(900)
    for _ in range(12):
        for button in ('start', 'a'):
            if not at_elm:
                g.press(button, 120)
    check(at_elm, 'a New Game did not reach Prof. Elm')
    if at_elm:
        n1, n2 = at_elm[0]
        check(n1 == locked1 and n2 & mask2 == locked2, f'a New Game started with {n1:08b}/{n2:08b}')
    g.pb.stop(save=False)

    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
