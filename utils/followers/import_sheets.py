#!/usr/bin/env python3
"""Import walking sprite sheets as follower sprites.

Each sheet is a standard 16x96 overworld sprite (pokecrystal order: facing
down, up and left, then the same three with the walking frame), or a 96x16
PokeWilds strip (left walking, left, up walking, up, down walking, down; in
colour on a transparent background: its darkest colour becomes black, its
lightest the light shade and any others the dark shade). It's saved as
gfx/followers/<name>.png, reordered for the game: down, down walking, up, up
walking, left, left walking. The first two frames then double as the party
menu mini and the overworld icon, so a Pokemon with a walking sprite needs no
mini or icon of its own.

Usage (from the repository root):
  python3 utils/followers/import_sheets.py SHEET_DIR [--map NAME=FILE ...]

Each mini in gfx/minis_icons.asm is matched to SHEET_DIR/<name>.png by name,
ignoring case, underscores and a "_plain" suffix; --map gives a sheet for a
name that doesn't match (the name as in gfx/minis/, e.g. pikachu_surf). Sheets
that match nothing are listed. Then run utils/followers/make_tables.py.
"""
import argparse
import os
import re
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'gfx', 'followers')
ORDER = [0, 3, 1, 4, 2, 5]  # standard frame -> game frame order


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower().replace('_plain', ''))


def mini_names():
    names = []
    for line in open(os.path.join(ROOT, 'gfx', 'minis_icons.asm')):
        m = re.match(r'\w+Mini::\s+INCBIN "gfx/minis/(\w+)\.2bpp\.lzp"', line)
        if m:
            names.append(m.group(1))
    return names


PW_ORDER = [5, 4, 3, 2, 1, 0]  # PokeWilds strip frame -> game frame order


def strip_to_grey(im):
    """A colour strip with transparency -> the four shades, by brightness."""
    im = im.convert('RGBA')

    def lum(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]
    data = list(im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata())
    cols = sorted({c for c in data if c[3]}, key=lum)
    shade = {}
    if cols:
        shade[cols[0]] = 0          # black
        for c in cols[1:]:
            shade[c] = 85           # dark
        if len(cols) > 2:
            shade[cols[-1]] = 170   # light
    out = Image.new('L', im.size, 255)
    out.putdata([shade[c] if c[3] else 255 for c in data])
    return out


def convert(src, dst):
    im = Image.open(src)
    if im.size == (96, 16):
        im = strip_to_grey(im)
        frames = [im.crop((16 * k, 0, 16 * k + 16, 16)) for k in PW_ORDER]
    elif im.size == (16, 96):
        im = im.convert('L')
        # snap to the four Game Boy shades
        im = im.point(lambda v: min((0, 85, 170, 255), key=lambda s: abs(s - v)))
        frames = [im.crop((0, 16 * k, 16, 16 * k + 16)) for k in ORDER]
    else:
        raise ValueError(f'{src}: {im.size}, expected 16x96 or 96x16')
    out = Image.new('L', (16, 96))
    for game, frame in enumerate(frames):
        out.paste(frame, (0, 16 * game))
    out.save(dst)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('sheets')
    ap.add_argument('--map', action='append', default=[], metavar='NAME=FILE')
    args = ap.parse_args()
    files = {norm(f[:-4]): f for f in os.listdir(args.sheets) if f.endswith('.png')}
    extra = dict(m.split('=', 1) for m in args.map)
    used = set()
    done = 0
    for name in mini_names():
        src = extra.get(name)
        if src is None and norm(name) in files:
            src = os.path.join(args.sheets, files[norm(name)])
            used.add(files[norm(name)])
        if src is None:
            continue
        convert(src, os.path.join(OUT, name + '.png'))
        done += 1
    print(f'imported {done} sprites into gfx/followers/')
    unused = sorted(set(files.values()) - used)
    if unused:
        print('sheets matching no mini:', ', '.join(unused))


if __name__ == '__main__':
    sys.exit(main())
