#!/usr/bin/env python3
"""Check that the overworld sprite palette tables are in the order of their
constants (constants/sprite_data_constants.asm), by each row's comment:

- npc_sprites.pal and npc_sprites_overcast.pal: the time-of-day palettes,
  once per time of day (morn, day, nite, eve);
- npc_sprites_darkness.pal: the time-of-day palettes, then the individual
  ones (only the time-of-day rows are read: the darkness lookup takes those);
- npc_single_object.pal: the individual palettes.

Both the color and the monochrome halves of each file are checked. A row in
the wrong place gives a sprite another palette's colors (the darkness table
once gave rain, sand, leaf green and faraway rock the emote palettes).

Usage (from the repository root): python3 utils/check_palette_tables.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def constant_names():
    src = open(os.path.join(ROOT, 'constants', 'sprite_data_constants.asm')).read()
    names, time_of_day = [], None
    for line in src.split('\n'):
        m = re.match(r'\s*ow_npc_pal_const (\w+)', line)
        if m:
            names.append(m.group(1).lower().replace('_', ' '))
        elif 'DEF NUM_OW_TIME_OF_DAY_PALS' in line:
            time_of_day = len(names)
        elif 'DEF NUM_OW_INDIVIDUAL_PALS' in line:
            return names[:time_of_day], names[time_of_day:]
    sys.exit('constants not found')


def halves(path):
    """The row comments of the color half and the monochrome half."""
    rows, out = [], []
    for line in open(path).read().split('\n'):
        if line.startswith(('else', 'endc')):
            out.append(rows)
            rows = []
        elif re.match(r'\s*(RGB|MONOCHROME_|RGB_MONOCHROME)', line) and ';' in line:
            rows.append(line.split(';', 1)[1].strip())
    return out


def main():
    time_of_day, individual = constant_names()
    expect = {
        'npc_sprites.pal': time_of_day * 4,
        'npc_sprites_overcast.pal': time_of_day * 4,
        'npc_sprites_darkness.pal': time_of_day + individual,
        'npc_single_object.pal': individual,
    }
    problems = 0
    for name, want in expect.items():
        for half, got in zip(('color', 'monochrome'), halves(os.path.join(ROOT, 'gfx', 'overworld', name))):
            for k, (g, w) in enumerate(zip(got, want)):
                if g != w:
                    print(f'{name} ({half}) row {k}: "{g}", expected "{w}"')
                    problems += 1
                    break
            if len(got) != len(want):
                print(f'{name} ({half}): {len(got)} rows, expected {len(want)}')
                problems += 1
    print(f'palette tables: {problems} problems')
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
