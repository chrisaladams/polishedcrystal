#!/usr/bin/env python3
"""Report memory use from an rgblink .map file, bank by bank.

For each region (ROM0, ROMX, VRAM, SRAM, WRAM0, WRAMX, HRAM): bytes used and
free per bank and the largest contiguous free gap, which matters more than
totals (a 152-byte total can be five small gaps). With --compare, also the
change from an older map, for before/after reports.

Usage (from the repository root, after make):
  python3 utils/memory_report.py polishedcrystal-3.2.3.map
  python3 utils/memory_report.py NEW.map --compare OLD.map
  python3 utils/memory_report.py NEW.map --markdown > report.md
"""
import argparse
import re
from collections import OrderedDict

BANK_SIZE = {'ROM0': 0x4000, 'ROMX': 0x4000, 'VRAM': 0x2000, 'SRAM': 0x2000,
             'WRAM0': 0x1000, 'WRAMX': 0x1000, 'HRAM': 0x7f}


def parse(path, rom_size=0x200000):
    """{(region, bank): {'used', 'free', 'gaps': [(start, size)], 'sections': [(name, start, size)]}}

    rgblink leaves out ROMX banks nothing was placed in; they count as empty
    (rom_size: the cartridge's ROM, 2 MiB here)."""
    banks = OrderedDict()
    cur = None
    for line in open(path, encoding='utf-8', errors='replace'):
        m = re.match(r'^(ROM0|ROMX|VRAM|SRAM|WRAM0|WRAMX|HRAM) bank #(\d+):', line)
        if m:
            cur = banks.setdefault((m.group(1), int(m.group(2))), {'used': 0, 'free': 0, 'gaps': [], 'sections': []})
            continue
        if cur is None:
            continue
        m = re.match(r'^\s+SECTION: \$([0-9a-f]+)(?:-\$([0-9a-f]+))? \(\$([0-9a-f]+) bytes?\) \["(.*)"\]', line)
        if m:
            size = int(m.group(3), 16)
            cur['sections'].append((m.group(4), int(m.group(1), 16), size))
            cur['used'] += size
            continue
        m = re.match(r'^\s+EMPTY: \$([0-9a-f]+)-\$([0-9a-f]+) \(\$([0-9a-f]+) bytes?\)', line)
        if m:
            cur['gaps'].append((int(m.group(1), 16), int(m.group(3), 16)))
            continue
        m = re.match(r'^\s+TOTAL EMPTY: \$([0-9a-f]+) bytes?', line)
        if m:
            cur['free'] = int(m.group(1), 16)
            continue
        if not line.strip():
            cur = None
    # (sections in a union or overlapping ones count once: use size - free)
    for (region, bank), b in banks.items():
        b['used'] = BANK_SIZE[region] - b['free'] if b['free'] or b['gaps'] else b['used']
    for bank in range(1, rom_size // BANK_SIZE['ROMX']):
        if ('ROMX', bank) not in banks:
            banks[('ROMX', bank)] = {'used': 0, 'free': BANK_SIZE['ROMX'], 'gaps': [(0x4000, BANK_SIZE['ROMX'])],
                                     'sections': []}
    return banks


def summary(banks):
    regions = OrderedDict()
    for (region, bank), b in banks.items():
        r = regions.setdefault(region, {'banks': 0, 'used': 0, 'free': 0, 'largest': 0, 'empty_banks': 0})
        r['banks'] += 1
        r['used'] += b['used']
        r['free'] += b['free']
        r['largest'] = max([r['largest']] + [size for _, size in b['gaps']])
        if b['free'] == BANK_SIZE[region]:
            r['empty_banks'] += 1
    return regions


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('map')
    ap.add_argument('--compare', help='an older .map, for the change')
    ap.add_argument('--markdown', action='store_true', help='Markdown tables')
    ap.add_argument('--rom-banks', type=int, default=12, help='how many of the freest ROMX banks to list')
    ap.add_argument('--rom-size', type=lambda s: int(s, 0), default=0x200000, help='the ROM size (default 2 MiB)')
    args = ap.parse_args()
    new = parse(args.map, args.rom_size)
    old = parse(args.compare, args.rom_size) if args.compare else None
    ns, os_ = summary(new), summary(old) if old else None

    def delta(a, b):
        return f' ({a - b:+d})' if old is not None else ''

    md = args.markdown
    print('## Totals\n' if md else 'Totals')
    if md:
        print('| Region | Banks | Used | Free | Largest gap | Empty banks |')
        print('|---|---:|---:|---:|---:|---:|')
    for region, r in ns.items():
        o = os_.get(region, {'used': 0, 'free': 0}) if os_ else None
        row = (region, r['banks'], f"{r['used']}{delta(r['used'], o['used']) if o else ''}",
               f"{r['free']}{delta(r['free'], o['free']) if o else ''}", r['largest'], r['empty_banks'])
        print(('| ' + ' | '.join(map(str, row)) + ' |') if md else
              f'  {row[0]:6} {row[1]:3} banks  used {row[2]:>12}  free {row[3]:>10}  largest gap {row[4]:5}'
              f'  empty banks {row[5]}')

    for region in ('SRAM', 'WRAM0', 'WRAMX', 'HRAM', 'ROM0', 'VRAM'):
        rows = [(bank, b) for (reg, bank), b in new.items() if reg == region]
        if not rows:
            continue
        print(f'\n## {region} by bank\n' if md else f'\n{region} by bank')
        if md:
            print('| Bank | Used | Free | Gaps (start: bytes) |')
            print('|---:|---:|---:|---|')
        for bank, b in rows:
            ob = old.get((region, bank)) if old else None
            gaps = ', '.join(f'${start:04x}: {size}' for start, size in b['gaps']) or 'none'
            free = f"{b['free']}{delta(b['free'], ob['free']) if ob else ''}"
            print(f'| {bank} | {b["used"]} | {free} | {gaps} |' if md else
                  f'  #{bank}: used {b["used"]:5}  free {free:>10}  gaps {gaps}')

    rom = sorted(((b['free'], bank, max([0] + [s for _, s in b['gaps']]))
                  for (reg, bank), b in new.items() if reg == 'ROMX'), reverse=True)
    print(f'\n## The {args.rom_banks} ROMX banks with the most free space\n' if md else
          f'\nThe {args.rom_banks} ROMX banks with the most free space')
    if md:
        print('| Bank | Free | Largest gap |')
        print('|---:|---:|---:|')
    for free, bank, largest in rom[:args.rom_banks]:
        print(f'| {bank} | {free} | {largest} |' if md else f'  #{bank}: free {free:5}  largest gap {largest}')


if __name__ == '__main__':
    main()
