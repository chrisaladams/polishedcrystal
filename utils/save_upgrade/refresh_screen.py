#!/usr/bin/env python3
"""Rebuild a save's on-screen block snapshot (wScreenSave) for the current ROM.

A save keeps the block IDs that were on screen when it was made. On Continue,
the game loads the map and then copies that snapshot back over the blocks
around the player (MapSetupScript_Continue: LoadBlockData, then
LoadConnectionBlockData). If a later build renumbers a tileset's blocks (the
November 2026 upstream merge did for the Johto tilesets), the old snapshot
draws the wrong tiles around the player, e.g. rooftops on Route 41's sea.

This boots the save in the current ROM under PyBoy, and just before
LoadConnectionBlockData copies the snapshot back it refreshes the snapshot from
the freshly loaded map (what BufferScreen would store). It then writes those
30 blocks into both copies of the save and fixes the checksums. Nothing else in
the save changes.

Run from the repository root after `make` and upgrade_save.py:

  python3 utils/save_upgrade/refresh_screen.py upgraded.sav fixed.sav
"""
import argparse
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import upgrade_save as U                                   # noqa: E402

SCREEN_META_WIDTH, SCREEN_META_HEIGHT = 6, 5


def fresh_screen(rom, sav, sym):
    """Boot the save and return the 30 block IDs the current ROM's own map
    data puts on screen."""
    from pyboy import PyBoy
    bank, addr = sym['LoadConnectionBlockData']
    a_anchor = sym['hOverworldMapAnchor'][1]
    a_width = sym['wMapWidth'][1]
    a_screen = sym['wScreenSave'][1]
    wbank = sym['wScreenSave'][0]
    result = {}
    tmp = tempfile.mkdtemp()
    try:
        gbc = os.path.join(tmp, 'game.gbc')
        shutil.copy(rom, gbc)
        pb = PyBoy(gbc, window='null', ram_file=open(sav, 'rb'))

        def mem(a):
            return pb.memory[wbank, a] if 0xD000 <= a < 0xE000 else pb.memory[a]

        def hook(_):
            anchor = pb.memory[a_anchor] | (pb.memory[a_anchor + 1] << 8)
            stride = mem(a_width) + 6
            blocks = [mem(anchor + r * stride + c)
                      for r in range(SCREEN_META_HEIGHT) for c in range(SCREEN_META_WIDTH)]
            for i, v in enumerate(blocks):        # make the copy-back a no-op
                if 0xD000 <= a_screen + i < 0xE000:
                    pb.memory[wbank, a_screen + i] = v
                else:
                    pb.memory[a_screen + i] = v
            result['blocks'] = blocks

        pb.hook_register(bank, addr, hook, None)

        def press(b, wait):
            pb.button_press(b)
            for _ in range(6):
                pb.tick()
            pb.button_release(b)
            for _ in range(wait):
                pb.tick()
        for _ in range(900):
            pb.tick()
        for b in ('start', 'start', 'a', 'a', 'a'):
            press(b, 240)
            if 'blocks' in result:
                break
        pb.stop(save=False)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if 'blocks' not in result:
        sys.exit('the save never reached the map load (does it load on this ROM?)')
    return result['blocks']


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('save')
    ap.add_argument('out')
    ap.add_argument('--checkout', default='.')
    args = ap.parse_args()
    sym_path = U.find_sym(args.checkout)
    rom = sym_path[:-4] + '.gbc'
    sym = U.read_sym(sym_path)
    blocks = fresh_screen(rom, args.save, sym)
    prof = U.make_profile(args.checkout, 'current build')
    data = bytearray(open(args.save, 'rb').read())
    save = U.Save(data, prof)
    old = None
    for copy in U.COPIES:
        off = save.field_off(copy, 'wScreenSave')
        old = bytes(save.data[off:off + len(blocks)])
        save.data[off:off + len(blocks)] = bytes(blocks)
        save.fix_checksum(copy)
    open(args.out, 'wb').write(save.data)
    print(f'wScreenSave {old.hex(" ")}\n         -> {bytes(blocks).hex(" ")}\nwrote {args.out}')


if __name__ == '__main__':
    main()
