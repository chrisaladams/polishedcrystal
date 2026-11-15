#!/usr/bin/env python3
"""Upgrade a save file from an older build of this game to the current build.

Polished Crystal's own save patcher (`make bsp`) only covers official releases.
Between releases, a save can stop loading ("Your save file does not match the
game version of this ROM") or load wrongly because the save version was bumped,
maps were renumbered, or saved fields were moved or re-purposed. This tool
bridges that gap by comparing two *profiles*: snapshots of a build's save
layout and ID numbering.

  profile   snapshot a build (the current checkout, or any git revision)
  identify  show how a save reads under each known profile
  upgrade   convert a save from one profile to another

What `upgrade` does, for both the main and the backup copy of the game data:

  * copies every saved field by name; a field that moved is copied to its new
    place, a field that is new in the target is cleared (and the run stops if
    that would discard non-zero data, unless --allow-reset is given)
  * translates every saved map group/number pair by map name
  * re-maps the visited-spawn (Fly) and event flag arrays by name
  * sets the save version and recomputes both checksums

It refuses to run if the two builds number items, Pokemon or moves
differently, since those are stored in bags, parties and boxes and it does not
translate them. Party and box Pokemon keep their stored stats; the game
recalculates them on level up or when they pass through the PC.

Usage (from the repository root, after `make`):

  python3 utils/save_upgrade/upgrade_save.py identify my.sav
  python3 utils/save_upgrade/upgrade_save.py upgrade my.sav my_new.sav \\
      --from utils/save_upgrade/profiles/v10-2026-01-family-rom.json
  python3 utils/save_upgrade/upgrade_save.py profile --rev <commit> -o old.json
"""

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PROFILE_DIR = os.path.join(HERE, 'profiles')

SAVED_BLOCKS = [('wOptions', 'wOptionsEnd'), ('wPlayerData', 'wPlayerDataEnd'),
                ('wCurMapData', 'wCurMapDataEnd'), ('wPokemonData', 'wPokemonDataEnd')]
SRAM_SYMBOLS = ['sSaveVersion',
                'sOptions', 'sPlayerData', 'sMapData', 'sPokemonData',
                'sGameData', 'sGameDataEnd', 'sChecksum',
                'sBackupOptions', 'sBackupPlayerData', 'sBackupMapData', 'sBackupPokemonData',
                'sBackupGameData', 'sBackupGameDataEnd', 'sBackupChecksum']
# Which SRAM area each saved WRAM block is stored in, for each copy.
COPIES = {
    'main': {'wOptions': 'sOptions', 'wPlayerData': 'sPlayerData',
             'wCurMapData': 'sMapData', 'wPokemonData': 'sPokemonData',
             '_range': ('sGameData', 'sGameDataEnd'), '_checksum': 'sChecksum'},
    'backup': {'wOptions': 'sBackupOptions', 'wPlayerData': 'sBackupPlayerData',
               'wCurMapData': 'sBackupMapData', 'wPokemonData': 'sBackupPokemonData',
               '_range': ('sBackupGameData', 'sBackupGameDataEnd'),
               '_checksum': 'sBackupChecksum'},
}
# ID lists a profile records. SPAWN_/EVENT_ are re-mapped; the rest must match.
CONST_FILES = ['constants/event_flags.asm', 'constants/map_data_constants.asm',
               'constants/item_constants.asm', 'constants/pokemon_constants.asm',
               'constants/move_constants.asm']
MUST_MATCH = ('constants/item_constants.asm', 'constants/pokemon_constants.asm',
              'constants/move_constants.asm')
# Constants in those files that are not stored in saves (NAM_* is the
# alphabetical order the bag sorts by).
NOT_STORED = ('NAM_',)
# Saved fields that were renamed without changing meaning (old name -> new name).
FIELD_RENAMES = {
    'wFarawayIslandSceneID': 'wFarawayIslandSouthSceneID',
    'wUndergroundPathSwitchRoomEntrancesSceneID': 'wGoldenrodUndergroundSwitchRoomSceneID',
}
# Maps that were renamed or split (old name -> new name).
MAP_RENAMES = {
    'FARAWAY_ISLAND': 'FARAWAY_ISLAND_SOUTH',
    'CELADON_DEPT_STORE_6F': 'CELADON_DEPT_STORE_ROOF',
    'ROUTE_3_POKECENTER_1F': 'ROUTE_3_CABLE_CAR_GATE',
}


# ---------------------------------------------------------------- profiles

def read_sym(path):
    sym = {}
    for line in open(path):
        m = re.match(r'([0-9a-fA-F]+):([0-9a-fA-F]{4}) (\S+)', line)
        if m:
            sym.setdefault(m.group(3), (int(m.group(1), 16), int(m.group(2), 16)))
    return sym


def read_map_table(checkout):
    group = number = 0
    maps = {}
    for line in open(os.path.join(checkout, 'constants/map_constants.asm')):
        s = line.split(';')[0].strip()
        if s.startswith('newgroup'):
            group, number = group + 1, 0
        elif s.startswith('map_const'):
            number += 1
            maps[f'{group},{number}'] = s.split()[1].rstrip(',')
    return maps


def read_constants(checkout):
    """Evaluate every `const NAME` in CONST_FILES with rgbasm, so macros such as
    const_skip/const_next are handled exactly as the build handles them."""
    by_file = {}
    for rel in CONST_FILES:
        text = open(os.path.join(checkout, rel)).read()
        by_file[rel] = sorted(set(re.findall(r'^\s*const\s+([A-Z_][A-Z0-9_]*)', text, re.M)))
    names = sorted({n for ns in by_file.values() for n in ns})
    with tempfile.NamedTemporaryFile('w', suffix='.asm', delete=False) as f:
        for n in names:
            f.write(f'IF DEF({n})\nPRINTLN "{n}={{d:{n}}}"\nENDC\n')
        asm = f.name
    try:
        out = subprocess.run(['rgbasm', '-P', 'includes.asm', '-o', os.devnull, asm],
                             cwd=checkout, capture_output=True, text=True)
    finally:
        os.unlink(asm)
    values = dict(line.split('=', 1) for line in out.stdout.splitlines() if '=' in line)
    if not values:
        sys.exit(f'could not evaluate constants in {checkout}:\n{out.stderr[:2000]}')
    return {rel: {n: int(values[n]) for n in ns if n in values} for rel, ns in by_file.items()}


def read_save_version(checkout):
    text = open(os.path.join(checkout, 'constants/misc_constants.asm')).read()
    return int(re.search(r'DEF SAVE_VERSION EQU (\d+)', text).group(1))


def find_sym(checkout):
    syms = [s for s in glob.glob(os.path.join(checkout, '*.sym'))
            if not any(t in os.path.basename(s) for t in ('faithful', 'debug', '_vc'))]
    if not syms:
        sys.exit(f'no .sym in {checkout}; build it first (make)')
    return max(syms, key=os.path.getmtime)


def make_profile(checkout, name, rev=None):
    sym = read_sym(find_sym(checkout))
    blocks = {}
    for start, end in SAVED_BLOCKS:
        bank, base = sym[start]
        size = sym[end][1] - base
        fields = {k: v[1] - base for k, v in sym.items()
                  if v[0] == bank and base <= v[1] < base + size
                  and k.startswith('w') and '.' not in k}
        blocks[start] = {'size': size, 'fields': fields}
    return {
        'name': name,
        'rev': rev or subprocess.run(['git', '-C', checkout, 'rev-parse', 'HEAD'],
                                     capture_output=True, text=True).stdout.strip(),
        'save_version': read_save_version(checkout),
        'sram': {s: list(sym[s]) for s in SRAM_SYMBOLS},
        'blocks': blocks,
        'maps': read_map_table(checkout),
        'constants': read_constants(checkout),
    }


def profile_from_rev(rev, name):
    """Check out `rev` in a temporary worktree, build it, and profile it."""
    tmp = tempfile.mkdtemp(prefix='saveprofile_')
    wt = os.path.join(tmp, 'build')
    subprocess.run(['git', '-C', ROOT, 'worktree', 'add', '-q', '--detach', wt, rev], check=True)
    try:
        print(f'building {rev} (this takes a minute)...', file=sys.stderr)
        subprocess.run(['make', f'-j{os.cpu_count() or 2}'], cwd=wt, check=True,
                       stdout=subprocess.DEVNULL)
        return make_profile(wt, name, rev)
    finally:
        subprocess.run(['git', '-C', ROOT, 'worktree', 'remove', '--force', wt])
        os.rmdir(tmp)


# ---------------------------------------------------------------- save file

class Save:
    def __init__(self, data, profile):
        self.data = data
        self.p = profile

    def sram_off(self, sname):
        bank, addr = self.p['sram'][sname]
        return bank * 0x2000 + addr - 0xa000

    def block_off(self, copy, block):
        return self.sram_off(COPIES[copy][block])

    def field_off(self, copy, name):
        for block, info in self.p['blocks'].items():
            if name in info['fields']:
                return self.block_off(copy, block) + info['fields'][name]
        raise KeyError(name)

    def version(self):
        o = self.sram_off('sSaveVersion')
        return self.data[o] << 8 | self.data[o + 1]

    def checksum_ok(self, copy):
        a, b = (self.sram_off(s) for s in COPIES[copy]['_range'])
        c = self.sram_off(COPIES[copy]['_checksum'])
        return sum(self.data[a:b]) & 0xffff == (self.data[c] | self.data[c + 1] << 8)

    def fix_checksum(self, copy):
        a, b = (self.sram_off(s) for s in COPIES[copy]['_range'])
        c = self.sram_off(COPIES[copy]['_checksum'])
        cs = sum(self.data[a:b]) & 0xffff
        self.data[c], self.data[c + 1] = cs & 0xff, cs >> 8


def map_pairs(profile):
    fields = {n for b in profile['blocks'].values() for n in b['fields']}
    return sorted(n[:-len('MapGroup')] for n in fields
                  if n.endswith('MapGroup') and n[:-len('MapGroup')] + 'MapNumber' in fields)


def flag_ids(profile, prefix):
    rel = {'SPAWN_': 'constants/map_data_constants.asm', 'EVENT_': 'constants/event_flags.asm'}[prefix]
    return {k: v for k, v in profile['constants'][rel].items() if k.startswith(prefix) and v >= 0}


def describe(save, copy='main'):
    p = save.p
    def loc(prefix):
        g = save.data[save.field_off(copy, prefix + 'MapGroup')]
        n = save.data[save.field_off(copy, prefix + 'MapNumber')]
        return p['maps'].get(f'{g},{n}', f'({g},{n})')
    spawns = flag_ids(p, 'SPAWN_')
    base = save.field_off(copy, 'wVisitedSpawns')
    towns = [k[6:] for k, v in sorted(spawns.items(), key=lambda kv: kv[1])
             if (save.data[base + v // 8] >> (v % 8)) & 1]
    return (f'location {loc("w")}, last Pokemon Center {loc("wLastSpawn")}\n'
            f'    Fly: {", ".join(towns) or "none"}')


# ---------------------------------------------------------------- upgrade

def check_ids_match(src, dst):
    problems = []
    for rel in MUST_MATCH:
        a, b = src['constants'][rel], dst['constants'][rel]
        moved = [k for k in a if k in b and a[k] != b[k] and not k.startswith(NOT_STORED)]
        if moved:
            problems.append(f'{rel}: {len(moved)} IDs renumbered, e.g. {moved[:5]}')
    if problems:
        sys.exit('these builds number stored IDs differently, which this tool does not '
                 'translate:\n  ' + '\n  '.join(problems))


def copy_fields(save, src, dst, copy, old_bytes, allow_reset, log):
    """Lay the saved blocks out the target's way, matching fields by name."""
    lost = []
    for block, dinfo in dst['blocks'].items():
        sinfo = src['blocks'][block]
        if sinfo['size'] != dinfo['size']:
            sys.exit(f'{block} is {sinfo["size"]} bytes in the source build and '
                     f'{dinfo["size"]} in the target; resizing is not supported')
        s_by_name = dict(sinfo['fields'])
        for old, new in FIELD_RENAMES.items():
            if old in s_by_name:
                s_by_name.setdefault(new, s_by_name[old])
        s_names_at = {}
        for n, o in sinfo['fields'].items():
            s_names_at.setdefault(o, set()).add(n)
        offsets = sorted(set(dinfo['fields'].values()) | {dinfo['size']})
        names_at = {}
        for n, o in dinfo['fields'].items():
            names_at.setdefault(o, []).append(n)
        sbase = save.block_off(copy, block)
        for o, end in zip(offsets, offsets[1:]):
            names = names_at[o]
            if any(n in s_names_at.get(o, ()) for n in names):
                continue                       # same field, same place
            src_off = next((s_by_name[n] for n in names if n in s_by_name), None)
            size = end - o
            if src_off is not None:
                save.data[sbase + o:sbase + end] = old_bytes[sbase + src_off:sbase + src_off + size]
                if src_off != o:
                    log.append(f'  moved {names[0]}: offset {src_off} -> {o}')
            else:
                # Old data here only counts as lost if the old field it belonged
                # to has no home in the target (a field that merely moved was
                # copied to its new place above).
                dst_names = set(dinfo['fields']) | {FIELD_RENAMES.get(n, n) for n in sinfo['fields']
                                                    if FIELD_RENAMES.get(n) in dinfo['fields']}
                old_owners = {n for n, so in sinfo['fields'].items() if o <= so < end}
                orphaned = any(FIELD_RENAMES.get(n, n) not in dst_names for n in old_owners) \
                    or not old_owners
                if orphaned and any(save.data[sbase + o:sbase + end]):
                    lost.append(f'{block}+{o} ({"/".join(names)})')
                save.data[sbase + o:sbase + end] = bytes(size)
    if lost and not allow_reset:
        sys.exit('these new fields would overwrite non-zero data from the old save:\n  '
                 + '\n  '.join(lost) + '\nre-run with --allow-reset if that is acceptable')
    if lost:
        log.append(f'  reset {len(lost)} fields that held old data: {", ".join(lost)}')


def remap_flags(save, copy, src, dst, prefix, old_bytes, log):
    s_ids, d_ids = flag_ids(src, prefix), flag_ids(dst, prefix)
    base_old = Save(old_bytes, src).field_off(copy, 'wVisitedSpawns' if prefix == 'SPAWN_' else 'wEventFlags')
    base_new = save.field_off(copy, 'wVisitedSpawns' if prefix == 'SPAWN_' else 'wEventFlags')
    def get(i):
        return (old_bytes[base_old + i // 8] >> (i % 8)) & 1
    def put(i, v):
        if v:
            save.data[base_new + i // 8] |= 1 << (i % 8)
        else:
            save.data[base_new + i // 8] &= ~(1 << (i % 8)) & 0xff
    used = set(d_ids.values())
    for name, i in s_ids.items():             # slots nothing uses any more
        if i not in used:
            put(i, 0)
    moved = 0
    for name, j in d_ids.items():
        v = get(s_ids[name]) if name in s_ids else 0
        if name in s_ids and s_ids[name] != j:
            moved += 1
        put(j, v)
    log.append(f'  {prefix[:-1].lower()} flags: {moved} renumbered')


def upgrade(data, src, dst, allow_reset):
    save = Save(bytearray(data), src)
    if save.version() != src['save_version']:
        sys.exit(f'save version is {save.version()}, but profile {src["name"]} is version '
                 f'{src["save_version"]}')
    for copy in COPIES:
        if not save.checksum_ok(copy):
            sys.exit(f'the {copy} copy fails its checksum under {src["name"]}; wrong profile?')
    for s in SRAM_SYMBOLS:
        if src['sram'][s] != dst['sram'][s]:
            sys.exit(f'{s} moved between the builds; moving SRAM areas is not supported')
    check_ids_match(src, dst)

    old = bytes(save.data)
    save.p = dst
    log = []
    dst_maps = {v: k for k, v in dst['maps'].items()}
    for copy in COPIES:
        log.append(f'[{copy} copy]')
        copy_fields(save, src, dst, copy, old, allow_reset, log)
        for prefix in map_pairs(dst):
            go, no = save.field_off(copy, prefix + 'MapGroup'), save.field_off(copy, prefix + 'MapNumber')
            g, n = save.data[go], save.data[no]
            if g in (0, 0xff) or n in (0, 0xff):
                continue                       # unset: no swarm, not roaming
            name = src['maps'].get(f'{g},{n}')
            if name is None:
                sys.exit(f'{prefix}MapGroup/Number = ({g},{n}) is not a map in {src["name"]}')
            key = dst_maps.get(MAP_RENAMES.get(name, name))
            if key is None:
                sys.exit(f'map {name} ({prefix}) has no equivalent in {dst["name"]}')
            ng, nn = map(int, key.split(','))
            if (ng, nn) != (g, n):
                log.append(f'  {prefix[1:] or "current"} map {name}: ({g},{n}) -> ({ng},{nn})')
            save.data[go], save.data[no] = ng, nn
        remap_flags(save, copy, src, dst, 'SPAWN_', old, log)
        remap_flags(save, copy, src, dst, 'EVENT_', old, log)
        save.fix_checksum(copy)
    o = save.sram_off('sSaveVersion')
    save.data[o], save.data[o + 1] = dst['save_version'] >> 8, dst['save_version'] & 0xff
    log.append(f'save version {src["save_version"]} -> {dst["save_version"]}')
    return save.data, log


# ---------------------------------------------------------------- CLI

def load_profile(path):
    if path in (None, 'current'):
        return make_profile(ROOT, 'current checkout')
    return json.load(open(path))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('profile', help='snapshot a build')
    p.add_argument('--rev', help='git revision to build and profile (default: current checkout)')
    p.add_argument('--name', help='label stored in the profile')
    p.add_argument('-o', '--output', required=True)
    p = sub.add_parser('identify', help='show how a save reads under each profile')
    p.add_argument('save')
    p = sub.add_parser('upgrade', help='convert a save between builds')
    p.add_argument('save')
    p.add_argument('output')
    p.add_argument('--from', dest='src', required=True, help='profile of the build that wrote the save')
    p.add_argument('--to', dest='dst', default='current',
                   help='profile of the target build (default: current checkout, after make)')
    p.add_argument('--allow-reset', action='store_true',
                   help='allow new fields to overwrite non-zero data from the old save')
    args = ap.parse_args()

    if args.cmd == 'profile':
        name = args.name or args.rev or 'current checkout'
        prof = profile_from_rev(args.rev, name) if args.rev else make_profile(ROOT, name)
        with open(args.output, 'w') as f:
            json.dump(prof, f, indent=1, sort_keys=True)
        print(f'wrote {args.output} ({prof["name"]}, save version {prof["save_version"]})')

    elif args.cmd == 'identify':
        data = open(args.save, 'rb').read()
        for path in sorted(glob.glob(os.path.join(PROFILE_DIR, '*.json'))):
            prof = json.load(open(path))
            save = Save(data, prof)
            ok = save.version() == prof['save_version'] and all(save.checksum_ok(c) for c in COPIES)
            print(f'{os.path.relpath(path, ROOT)}: '
                  + ('readable\n    ' + describe(save) if ok else
                     f'no match (save version {save.version()}, profile {prof["save_version"]})'))
        print('Pick the profile whose Fly towns match the save\'s story progress; '
              'builds with the same layout can all read as valid.')

    elif args.cmd == 'upgrade':
        src, dst = load_profile(args.src), load_profile(args.dst)
        data = open(args.save, 'rb').read()
        new, log = upgrade(data, src, dst, args.allow_reset)
        with open(args.output, 'wb') as f:
            f.write(new)
        print('\n'.join(log))
        print(f'wrote {args.output}')


if __name__ == '__main__':
    main()
