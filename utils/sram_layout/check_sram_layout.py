#!/usr/bin/env python3
"""Check that no save address has moved.

An older save is read at fixed SRAM addresses, so every SRAM label (bank and
address) must stay where it was. This compares the build's .sym against
utils/sram_layout/sram_layout.txt, the labels as they were when it was last
written. New labels (a new record placed in free SRAM) are fine and listed;
a moved or missing label is an error.

Usage (from the repository root, after make):
  python3 utils/sram_layout/check_sram_layout.py polishedcrystal-3.2.3.sym
  python3 utils/sram_layout/check_sram_layout.py polishedcrystal-3.2.3.sym --write
      (only after a deliberate, migrated layout change, or to add new labels)
"""
import argparse
import os
import re
import sys

BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sram_layout.txt')


def sram_labels(path):
    out = {}
    for line in open(path):
        m = re.match(r'([0-9a-f]{2}):([ab][0-9a-f]{3}) (s\w+)$', line.strip())
        if not m:  # (local labels have a '.', and aren't save fields)
            continue
        slot = re.match(r'sBoxMons\w+?Mon(\d+)', m.group(3))
        if slot and int(slot.group(1)) > 2:
            continue  # (the box database's slots are one macro: the first two show its layout)
        out[m.group(3)] = (int(m.group(1), 16), int(m.group(2), 16))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('sym')
    ap.add_argument('--write', action='store_true', help='rewrite the baseline from this build')
    args = ap.parse_args()
    now = sram_labels(args.sym)
    if args.write:
        with open(BASELINE, 'w') as f:
            f.write('; SRAM labels (bank:address name) that older saves depend on.\n'
                    '; Written by check_sram_layout.py --write; see docs/sram-allocation.md.\n')
            for name, (bank, addr) in sorted(now.items(), key=lambda kv: (kv[1], kv[0])):
                f.write(f'{bank:02x}:{addr:04x} {name}\n')
        print(f'{len(now)} SRAM labels written to {os.path.relpath(BASELINE)}')
        return
    base = {}
    for line in open(BASELINE):
        if line.startswith(';') or not line.strip():
            continue
        loc, name = line.split()
        bank, addr = loc.split(':')
        base[name] = (int(bank, 16), int(addr, 16))
    problems = []
    for name, loc in base.items():
        if name not in now:
            problems.append(f'{name} is gone (was {loc[0]:02x}:{loc[1]:04x})')
        elif now[name] != loc:
            problems.append(f'{name} moved from {loc[0]:02x}:{loc[1]:04x} to {now[name][0]:02x}:{now[name][1]:04x}')
    new = sorted(set(now) - set(base))
    for name in new:
        print(f'new: {now[name][0]:02x}:{now[name][1]:04x} {name}')
    for p in problems:
        print('ERROR:', p)
    print(f'{len(base)} save labels checked, {len(problems)} moved or gone, {len(new)} new')
    sys.exit(1 if problems else 0)


if __name__ == '__main__':
    main()
