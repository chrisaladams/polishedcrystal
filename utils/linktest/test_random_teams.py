#!/usr/bin/env python3
"""Check Random Battle teams: run the game's own LinkRandomBattle_MakeTeam
many times in an emulator and check every team against the rules (six
different species, no type on more than RANDOM_MAX_SAME_TYPE members, no
weakness shared by more than RANDOM_MAX_SAME_WEAK). First, every set in the
table is checked for a held item that blocks its own moves (an Assault Vest
with a status move).

Run from the repository root after `make`:

  python3 utils/linktest/test_random_teams.py SAVE.sav [--teams 300]
"""
import argparse
import collections
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, 'meta_sim'))

import linktest as L                                        # noqa: E402
from oracle_pipeline import asm_for_build, rgbasm_values    # noqa: E402

TYPES = ['NORMAL', 'FIGHTING', 'FLYING', 'POISON', 'GROUND', 'ROCK', 'BUG', 'GHOST',
         'STEEL', 'FIRE', 'WATER', 'GRASS', 'ELECTRIC', 'PSYCHIC', 'ICE', 'DRAGON',
         'DARK', 'FAIRY']
TRAP, STACK = 0xff90, 0xdff0


def load_sets():
    """(species byte, form byte, moves) -> (name, types, weaknesses) from the table."""
    lines = asm_for_build(open(os.path.join(ROOT, 'data/link/random_battle_sets.asm')).read()).splitlines()
    profiles = []
    for i, line in enumerate(lines):
        if re.match(r'\s*db \d+, \d+ ; \d+:', line):
            t1, t2 = (int(x) for x in line.split(';')[0].split('db')[1].split(','))
            wb = [int(x.strip().lstrip('$'), 16) for x in lines[i + 1].split(';')[0].split('db')[1].split(',')]
            bits = wb[0] | wb[1] << 8 | wb[2] << 16
            profiles.append(({TYPES[t1], TYPES[t2]}, [TYPES[k] for k in range(18) if bits >> k & 1]))
    raw = []
    for i, line in enumerate(lines):
        m = re.match(r'\s*dp (\w+), (\w+)', line)
        if m:
            moves = [x.strip() for x in lines[i + 1].split('db')[1].split(',')]
            types, weak = profiles[int(lines[i + 2].split(',')[2])]
            raw.append((m.group(1), m.group(2), moves, types, weak))
    names = sorted({n for r in raw for n in [r[0], r[1]] + r[2]})
    ids = rgbasm_values(names, None)
    sets = {}
    for sp, form, moves, types, weak in raw:
        spid = ids[sp]
        key = (spid & 0xff, (spid >> 8) << 5 | ids[form], tuple(ids[m] for m in moves))
        sets[key] = (sp.lower() + ('' if form == 'PLAIN_FORM' else '_' + form.lower()), types, weak)
    return sets


def table_problems():
    """Sets whose item stops them using one of their moves: an Assault Vest
    (no status moves while holding it) with a status move."""
    import json
    cats = {k: v['cat'] for k, v in json.load(open(os.path.join(ROOT, 'meta_sim', 'data', 'moves.json'))).items()}
    lines = asm_for_build(open(os.path.join(ROOT, 'data/link/random_battle_sets.asm')).read()).splitlines()
    out = []
    for i, line in enumerate(lines):
        m = re.match(r'\s*dp (\w+), (\w+)', line)
        if not m:
            continue
        moves = [x.strip() for x in lines[i + 1].split('db')[1].split(',')]
        item = lines[i + 2].split('db')[1].split(',')[0].strip()
        status = [mv for mv in moves if cats.get(mv) == 'STATUS']
        if item == 'ASSAULT_VEST' and status:
            out.append(f'{m.group(1)} {m.group(2)}: an Assault Vest with {", ".join(status)}')
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('save')
    ap.add_argument('--teams', type=int, default=300)
    ap.add_argument('--rom', default=os.path.join(ROOT, 'polishedcrystal-3.2.3.gbc'))
    args = ap.parse_args()
    from pyboy import PyBoy
    sym = L.load_sym(args.rom[:-4] + '.sym')
    lim = rgbasm_values(['RANDOM_MAX_SAME_TYPE', 'RANDOM_MAX_SAME_WEAK'], None)
    sets = load_sets()
    tmp = tempfile.mkdtemp()
    gbc = os.path.join(tmp, 'game.gbc')
    shutil.copy(args.rom, gbc)
    pb = PyBoy(gbc, window='null', ram_file=open(args.save, 'rb'))
    pb.set_emulation_speed(0)
    mem, reg = pb.memory, pb.register_file
    for _ in range(900):
        pb.tick(1, False)
    for b in ('start', 'start', 'a', 'a', 'a'):
        pb.button_press(b)
        for _ in range(6):
            pb.tick(1, False)
        pb.button_release(b)
        for _ in range(200):
            pb.tick(1, False)

    def wram(name, k=0):
        a = sym[name][1] + k
        return mem[1, a] if 0xd000 <= a < 0xe000 else mem[a]

    def run(name):
        bank, addr = sym[name]
        mem[0xff70] = 1
        mem[0xffff] = 0
        mem[0xff0f] = 0
        mem[0x2000] = bank
        mem[0xff87] = bank
        mem[TRAP], mem[TRAP + 1] = 0x18, 0xfe            # jr -2
        mem[STACK], mem[STACK + 1] = TRAP & 0xff, TRAP >> 8
        reg.SP = STACK
        reg.PC = addr
        for _ in range(3000):
            pb.tick(1, False)
            if reg.PC in (TRAP, TRAP + 1):
                return
        raise RuntimeError(f'{name} did not return')

    base = sym['wPartyMon1'][1]
    stride = sym['wPartyMon2'][1] - base
    off = {f: sym['wPartyMon1' + f][1] - base for f in ('Species', 'Form', 'Moves', 'Level', 'HP', 'MaxHP')}
    bad = 0
    table = table_problems()
    for p in table:
        print('set table:', p)
    bad += len(table)
    type_freq = collections.Counter()
    species_freq = collections.Counter()
    worst_type = worst_weak = 0
    for t in range(args.teams):
        run('LinkRandomBattle_MakeTeam')
        n = wram('wPartyCount')
        team = []
        problems = []
        for i in range(n):
            o = base + i * stride
            sp = mem[1, o + off['Species']]
            form = mem[1, o + off['Form']] & 0x3f
            moves = tuple(mem[1, o + off['Moves'] + j] for j in range(4))
            lvl = mem[1, o + off['Level']]
            hp = mem[1, o + off['HP']] << 8 | mem[1, o + off['HP'] + 1]
            mhp = mem[1, o + off['MaxHP']] << 8 | mem[1, o + off['MaxHP'] + 1]
            entry = sets.get((sp, form, moves))
            if not entry:
                problems.append(f'slot {i}: species {sp} form {form:#x} moves {moves} not in the table')
                continue
            if lvl != 50 or hp != mhp or not hp:
                problems.append(f'{entry[0]}: level {lvl}, HP {hp}/{mhp}')
            team.append(entry)
        if n != 6:
            problems.append(f'{n} Pokemon')
        names = [e[0] for e in team]
        base_species = [nm.split('_')[0] for nm in names]
        if len(set(base_species)) != len(base_species):
            problems.append(f'repeated species {names}')
        tc = collections.Counter(ty for e in team for ty in e[1])
        wc = collections.Counter(w for e in team for w in e[2])
        if tc and max(tc.values()) > lim['RANDOM_MAX_SAME_TYPE']:
            problems.append(f'type {tc.most_common(1)[0]}')
        if wc and max(wc.values()) > lim['RANDOM_MAX_SAME_WEAK']:
            problems.append(f'weakness {wc.most_common(1)[0]}')
        worst_type = max(worst_type, max(tc.values(), default=0))
        worst_weak = max(worst_weak, max(wc.values(), default=0))
        type_freq.update(tc)
        species_freq.update(names)
        if problems:
            bad += 1
            if bad <= 10:
                print(f'team {t + 1}: {names}: ' + '; '.join(problems))
        elif t < 5:
            print(f'team {t + 1}: ' + ', '.join(f'{nm} ({"/".join(sorted(e[1]))})'
                                                 for nm, e in zip(names, team)))
    pb.stop(save=False)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f'\n{args.teams - bad}/{args.teams} teams follow the rules; most of one type on a team: '
          f'{worst_type}, most sharing a weakness: {worst_weak}')
    print(f'{len(species_freq)} different species seen; types, by how many team members had them:')
    print('  ' + ', '.join(f'{ty} {c}' for ty, c in type_freq.most_common()))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
