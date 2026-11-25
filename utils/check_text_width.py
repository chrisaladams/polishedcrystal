#!/usr/bin/env python3
"""Fail if a text line is wider than the text box (18 columns).

A line that's one character too long writes over the box's right frame, and
that character stays there for the rest of the text. This checks every
`text`/`line`/`cont`/`para`/`next` line in maps/ and data/ as printed: "#"
prints as "Poké" (4 columns) and 'd 'l 'm 'r 's 't 'v are one tile each.
Lines that insert a name (@, <...>, {...}) can't be measured here, and are
skipped, as are upstream files drawn at other widths (the Pokédex, ability
descriptions).

Usage (from the repository root; make test runs it):
  python3 utils/check_text_width.py
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIDTH = 18
OTHER_WIDTHS = {'data/pokemon/dex_entries.asm', 'data/abilities/descriptions.asm'}


def width(s):
    return len(re.sub(r"'[dlmrstv]", 'x', s).replace('#', 'Poké'))


def main():
    bad = []
    for path in sorted(glob.glob(os.path.join(ROOT, 'maps', '*.asm')) +
                       glob.glob(os.path.join(ROOT, 'data', '**', '*.asm'), recursive=True)):
        rel = os.path.relpath(path, ROOT)
        if rel in OTHER_WIDTHS:
            continue
        for n, line in enumerate(open(path, encoding='utf-8', errors='replace'), 1):
            m = re.match(r'\s*(text|line|cont|para|next)\s+"(.*)"\s*(;.*)?$', line)
            if not m or re.search(r'[@<{]', m.group(2)):
                continue
            if width(m.group(2)) > WIDTH:
                bad.append(f'{rel}:{n}: {width(m.group(2))} columns: "{m.group(2)}"')
    for b in bad:
        print(b)
    print(f'{len(bad)} text lines wider than {WIDTH} columns')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
