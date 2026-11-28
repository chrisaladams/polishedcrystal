"""Inventory of testable content, read from the repository, and coverage accounting against it.

    python3 -m qa.inventory build            # -> qa/reports/inventory.json
    python3 -m qa.inventory report           # merge coverage records, write docs/qa-inventory.md

Inventory elements are identified by stable strings (a map constant, "MAP#2" for the third warp of a map,
"SPROUT_TOWER_2F:grass:day:RATTATA" for a wild table row, ...). A test records what it exercised with
`ctx.cover(kind, ids)`; the framework writes `coverage.json` in the test's report directory. `report` takes the
union of every coverage.json under qa/reports (runs, campaigns, coverage) and compares it with the inventory.
Only ids that exist in the inventory count (a typo cannot inflate coverage), and each id keeps the source that
covered it first. Nothing is counted for merely *existing*: an element is covered when a run exercised it.
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

INV_PATH = os.path.join(ROOT, 'qa/reports/inventory.json')
DOC_PATH = os.path.join(ROOT, 'docs/qa-inventory.md')

KIND_TITLES = {
    'map': 'Maps entered', 'map-hw': 'Maps entered on SameBoy with the execution guard (per model)',
    'connection': 'Map connections (directed) crossed on foot', 'warp': 'Warp events taken',
    'object': 'Object events (NPCs, items, trainers, Pokemon) interacted with', 'bg_event': 'Background events (signs, hidden items) read',
    'coord_event': 'Coordinate (trigger-tile) events triggered', 'scene': 'Scene scripts run',
    'wild_zone': 'Wild encounter zones (map + terrain) walked', 'wild_row': 'Wild table rows (map, terrain, time, species) seen',
    'music': 'Music tracks played and validated', 'sfx': 'Sound effects played and validated', 'cry': 'Pokemon cries played and heard',
    'follower': 'Follower species walked with', 'collision': 'Collision types exercised', 'menu': 'Menus and interfaces opened',
    'roaming': 'Roaming Pokemon maps checked', 'event_flag': 'Event flags set by played scripts', 'tod_map': 'Maps viewed at each time of day',
    'save_state': 'Save/load boundaries', 'script': 'Script labels executed',
}


def _read(path):
    return open(os.path.join(ROOT, path), encoding='utf-8', errors='replace').read()


def build():
    from qa.gb import mapdata
    inv = {}
    attrs = mapdata.attributes()
    inv['map'] = sorted(attrs)
    inv['map-hw'] = sorted(f'{m}@{model}' for m in attrs for model in ('CGB-E', 'AGB'))
    conns = []
    for const, a in attrs.items():
        for d, label, dst, off in a['connections']:
            conns.append(f'{const}->{dst}')
    inv['connection'] = sorted(set(conns))
    warps, objs, bgs, coords, scenes = [], [], [], [], []
    for const, a in attrs.items():
        path = mapdata.map_file(a['label'])
        if not path:
            continue
        text = open(path, encoding='utf-8').read()
        sec = None
        w = o = b = c = 0
        for line in text.splitlines():
            s = line.strip()
            if s.startswith('def_warp_events'):
                sec = 'w'
            elif s.startswith('def_coord_events'):
                sec = 'c'
            elif s.startswith('def_bg_events'):
                sec = 'b'
            elif s.startswith('def_object_events'):
                sec = 'o'
            elif re.match(r'^\w+:', line) or s.startswith(('object_const_def', 'def_callbacks', 'def_scene')):
                sec = None
            elif sec == 'w' and s.startswith('warp_event'):
                warps.append(f'{const}#{w}')
                w += 1
            elif sec == 'c' and s.startswith('coord_event'):
                coords.append(f'{const}#{c}')
                c += 1
            elif sec == 'b' and s.startswith('bg_event'):
                bgs.append(f'{const}#{b}')
                b += 1
            elif sec == 'o' and re.match(r'(object_event|\w+_event)\b', s):
                objs.append(f'{const}#{o}')
                o += 1
        n = len(re.findall(r'^\s*scene_script\b', text, re.M))
        scenes += [f'{const}#{i}' for i in range(n)]
    inv.update({'warp': sorted(warps), 'object': sorted(objs), 'bg_event': sorted(bgs), 'coord_event': sorted(coords), 'scene': sorted(scenes)})
    # wild tables
    zones, rows = set(), set()
    for f in sorted(glob.glob(os.path.join(ROOT, 'data/wild/*_grass.asm')) + glob.glob(os.path.join(ROOT, 'data/wild/*_water.asm'))):
        terrain = 'grass' if f.endswith('_grass.asm') else 'water'
        cur, tod = None, None
        for line in open(f, encoding='utf-8'):
            m = re.match(r'\s*def_(?:grass|water)_wildmons\s+(\w+)', line)
            if m:
                cur, tod = m.group(1), None
                if cur in attrs:
                    zones.add(f'{cur}:{terrain}')
                continue
            m = re.match(r'\s*;\s*(morn|day|nite)\b', line)
            if m:
                tod = m.group(1)
                continue
            m = re.match(r'\s*wildmon\s+[^,]+,\s*(\w+)', line)
            if m and cur in attrs:
                rows.add(f'{cur}:{terrain}:{tod or "all"}:{m.group(1)}')
    inv['wild_zone'] = sorted(zones)
    inv['wild_row'] = sorted(rows)
    # audio and species
    from qa.av import music
    inv['music'] = sorted(music.song_ids())
    inv['sfx'] = sorted(music.sfx_ids())
    species = [m.group(1) for m in re.finditer(r'^\s*const\s+(\w+)\s*(?:;.*)?$', _read('constants/pokemon_constants.asm'), re.M)]
    species = [s for s in species if s.isupper() and not s.startswith(('NUM_', 'PARTY', 'EGG', 'MAX_', 'MON_', 'UNOWN_', 'DEF_')) and s not in ('NO_MON', 'EGG')]
    inv['cry'] = sorted(set(species))
    inv['follower'] = sorted(set(species))
    colls = sorted(set(re.findall(r'^\s*(?:const|DEF)\s+(COLL_\w+)', _read('constants/collision_constants.asm'), re.M)))
    inv['collision'] = colls
    roam = sorted(set(re.findall(r'roam_map\s+(\w+)', _read('data/wild/roammon_maps.asm'))))
    inv['roaming'] = roam
    inv['event_flag'] = sorted(set(re.findall(r'^\s*const\s+(EVENT_\w+)', _read('constants/event_flags.asm'), re.M)))
    inv['tod_map'] = sorted(f'{m}@{t}' for m in attrs for t in ('morn', 'day', 'nite'))
    os.makedirs(os.path.dirname(INV_PATH), exist_ok=True)
    json.dump(inv, open(INV_PATH, 'w'), indent=0)
    return inv


def merge_coverage(inv):
    covered = {k: {} for k in inv}
    unknown = {}
    files = glob.glob(os.path.join(ROOT, 'qa/reports/**/coverage*.json'), recursive=True)
    for f in sorted(files, key=os.path.getmtime):
        try:
            data = json.load(open(f))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        src = os.path.relpath(f, os.path.join(ROOT, 'qa/reports'))
        for kind, ids in data.items():
            if kind not in inv or not isinstance(ids, list):
                continue
            valid = set(inv[kind])
            for i in ids:
                if i in valid:
                    covered[kind].setdefault(i, src)
                else:
                    unknown.setdefault(kind, set()).add(i)
    return covered, unknown, len(files)


def report():
    inv = json.load(open(INV_PATH)) if os.path.exists(INV_PATH) else build()
    covered, unknown, nfiles = merge_coverage(inv)
    lines = ['# QA content inventory and coverage', '',
             'Generated by `python3 -m qa.inventory report` from the repository and from every `coverage*.json` under `qa/reports/` '
             f'({nfiles} files). An element counts as covered only if a run exercised it; existence is not coverage. Emulation only.', '',
             '| Category | In repository | Exercised | % | Not yet exercised (first 6) |', '|---|---:|---:|---:|---|']
    for kind in KIND_TITLES:
        if kind not in inv:
            continue
        total, got = len(inv[kind]), len(covered[kind])
        missing = [i for i in inv[kind] if i not in covered[kind]][:6]
        lines.append(f'| {KIND_TITLES[kind]} | {total} | {got} | {100 * got / total:.1f} | ' + (', '.join(f'`{m}`' for m in missing) or '-') + ' |' if total else '')
    if unknown:
        lines += ['', 'Coverage records naming ids that are not in the inventory (ignored): ' + '; '.join(f'{k}: {len(v)}' for k, v in unknown.items())]
    open(DOC_PATH, 'w').write('\n'.join(l for l in lines if l is not None) + '\n')
    json.dump({k: sorted(v) for k, v in covered.items()}, open(os.path.join(ROOT, 'qa/reports/covered.json'), 'w'))
    print('\n'.join(lines))


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'report'
    if cmd == 'build':
        inv = build()
        print({k: len(v) for k, v in inv.items()})
    else:
        report()
