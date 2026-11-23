#!/usr/bin/env python3
"""Draw a walking sprite from text: utils/followers/drafts/<name>.txt -> gfx/followers/<name>.png

A draft has up to six 16x16 frames in the game's order (down, down walking,
up, up walking, left, left walking), separated by blank lines:
'#' black, 'x' dark, 'o' light, '.' transparent. A frame written as
"bob N" is frame N moved down a pixel (how floating Pokemon walk), and
"same N" is frame N unchanged.

Usage (from the repository root):
  python3 utils/followers/draw.py NAME [NAME ...]
"""
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SHADE = {'#': 0, 'x': 85, 'o': 170, '.': 255}


def parse(path):
    blocks = [b.strip('\n').split('\n') for b in open(path).read().split('\n\n') if b.strip()]
    frames = []
    for b in blocks:
        b = [line for line in b if not line.startswith(';')]
        if len(b) == 1:
            op, n = b[0].split()
            src = frames[int(n)]
            frames.append(['.' * 16] + src[:15] if op == 'bob' else list(src))
            continue
        if len(b) != 16 or any(len(line) != 16 for line in b):
            raise ValueError(f'{path}: frame {len(frames)} is not 16x16')
        frames.append(b)
    if len(frames) != 6:
        raise ValueError(f'{path}: {len(frames)} frames, expected 6')
    return frames


def main():
    for name in sys.argv[1:]:
        frames = parse(os.path.join(ROOT, 'utils', 'followers', 'drafts', name + '.txt'))
        im = Image.new('L', (16, 96))
        for k, f in enumerate(frames):
            for y, line in enumerate(f):
                for x, c in enumerate(line):
                    im.putpixel((x, 16 * k + y), SHADE[c])
        im.save(os.path.join(ROOT, 'gfx', 'followers', name + '.png'))
        print('drew', name)


if __name__ == '__main__':
    main()
