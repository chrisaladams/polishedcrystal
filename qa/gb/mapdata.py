"""Static map data parsed from the repository (attributes, warps, object events)."""
import glob
import os
import re

from .consts import C
from .emu import ROOT

_cache = {}


def attributes():
    """{const: {'label', 'const', 'connections': [(dir, label, const, offset)]}}"""
    if 'attr' in _cache:
        return _cache['attr']
    maps, cur = {}, None
    for line in open(os.path.join(ROOT, 'data/maps/attributes.asm')):
        m = re.match(r'\s*map_attributes\s+(\w+),\s*(\w+),', line)
        if m and not line.lstrip().startswith(';'):
            cur = dict(label=m.group(1), const=m.group(2), connections=[])
            maps[cur['const']] = cur
            continue
        m = re.match(r'\s*connection\s+(north|south|west|east),\s*(\w+),\s*(\w+),\s*(-?\d+)', line)
        if m and cur:
            cur['connections'].append((m.group(1), m.group(2), m.group(3), int(m.group(4))))
    _cache['attr'] = maps
    return maps


def dims(const):
    """(width, height) in blocks."""
    w, h = C[const + '_WIDTH'], C[const + '_HEIGHT']
    return w, h


def map_file(label):
    p = os.path.join(ROOT, 'maps', label + '.asm')
    return p if os.path.exists(p) else None


OBJ_EVENT = re.compile(r'^\s+(object_event|itemball_event|tmhmball_event|cuttree_event|rock_event|fruittree_event|'
                       r'pokemon_event|strengthboulder_event|smashrock_event|keyitem_event|hiddenitem_event|'
                       r'\w+ball_event|\w+tree_event|\w+_event)\b')


def parse_map(label):
    """Warp and object-event info from maps/<label>.asm."""
    path = map_file(label)
    out = dict(warps=[], objects=0, path=path)
    if not path:
        return out
    section = None
    for line in open(path, encoding='utf-8'):
        s = line.strip()
        if s.startswith('def_warp_events'):
            section = 'warp'
        elif s.startswith('def_coord_events') or s.startswith('def_bg_events'):
            section = 'other'
        elif s.startswith('def_object_events'):
            section = 'obj'
        elif re.match(r'^\w+:', line) or s.startswith(('object_const_def', 'def_callbacks', 'def_scene')):
            section = None
        elif section == 'warp':
            m = re.match(r'\s*warp_event\s+(-?\d+),\s*(-?\d+),\s*(\w+),\s*(-?\d+)', line)
            if m:
                out['warps'].append((int(m.group(1)), int(m.group(2)), m.group(3), int(m.group(4))))
        elif section == 'obj' and OBJ_EVENT.match(line):
            out['objects'] += 1
    return out
