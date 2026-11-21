"""Extract this ROM's L50-relevant battle data from the .asm source into JSON.

Reads (relative to --source, the ROM checkout root):
  data/pokemon/base_stats/*.asm   base stats, types, abilities, tm/hm learnset
  data/moves/moves.asm            move power/type/accuracy/category/effect
  data/moves/priorities.asm       move priority brackets
  data/types/type_matchups.asm    type effectiveness chart
  data/pokemon/evos_attacks.asm   level-up learnsets + evolution markers
  data/pokemon/egg_moves.asm      egg moves
  data/pokemon/legendary_mons.asm legendary / uber species

Writes data/{pokemon,moves,typechart,learnsets}.json next to this script, so
the rest of meta_sim works standalone off the committed JSON even without a
ROM checkout on hand; only re-running this extractor needs --source.

The extractor mirrors the shipped (non-faithful / Polished) values; it does
not change any game data.

Usage:
    python3 extract.py                          # --source defaults to cwd
    python3 extract.py --source /path/to/polishedcrystal
"""
import re, glob, os, json, argparse

HERE = os.path.dirname(os.path.abspath(__file__))
NF = True  # non-faithful (Polished) values


def pick(lines):
    """Return non-faithful branch when an if DEF(FAITHFUL)/else block wraps a line."""
    mode = None
    out = []
    for ln in lines:
        s = ln.strip()
        if s.startswith('if DEF(FAITHFUL)'):
            mode = 'if'; continue
        if mode and s.startswith('else'):
            mode = 'else'; continue
        if mode and s.startswith('endc'):
            mode = None; continue
        keep = (mode is None) or (mode == 'else' if NF else mode == 'if')
        if keep:
            out.append(s)
    return out


def norm(x):
    """Normalize a name for matching: strip underscores, lowercase."""
    return x.replace('_', '').lower()


def parse_mon(path):
    raw = open(path).read().splitlines()
    L = pick(raw)
    mon = {'id': os.path.basename(path)[:-4], 'tmhm': []}
    for s in L:
        m = re.match(r'db\s+(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*;.*BST', s)
        if m and 'stats' not in mon:
            hp, atk, df, spe, sat, sdf = map(int, m.groups())
            mon['stats'] = dict(hp=hp, atk=atk, defe=df, spe=spe, spa=sat, spd=sdf)
            mon['bst'] = hp + atk + df + spe + sat + sdf
        m2 = re.match(r'bst\s+(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)', s)
        if m2 and 'stats' not in mon:
            bst, hp, atk, df, sat, sdf, spe = map(int, m2.groups())
            mon['stats'] = dict(hp=hp, atk=atk, defe=df, spe=spe, spa=sat, spd=sdf)
            mon['bst'] = bst
        t = re.match(r'db ([A-Z_]+), ([A-Z_]+) ; type', s)
        if t and 'types' not in mon:
            mon['types'] = [t.group(1)] if t.group(1) == t.group(2) else [t.group(1), t.group(2)]
        a = re.search(r'abilities_for\s+\w+,\s*([A-Z_0-9]+),\s*([A-Z_0-9]+),\s*([A-Z_0-9]+)', s)
        if a:
            mon['abilities'] = [a.group(1), a.group(2), a.group(3)]
        g = re.match(r'dn GENDER_(F[\d_]+|UNKNOWN)', s)
        if g:
            # chance a wild/bred mon is female (None = genderless)
            mon['female'] = None if g.group(1) == 'UNKNOWN' else \
                float(g.group(1)[1:].replace('_', '.')) / 100
        tm = re.match(r'tmhm\s+(.+)$', s)
        if tm:
            mon['tmhm'] += [x.strip() for x in tm.group(1).split(',') if x.strip()]
    return mon if 'stats' in mon else None


FORM_SUFFIX = re.compile(r'_(plain|alolan|galarian|hisuian|armored|galar)$')


def species_of(mid):
    return FORM_SUFFIX.sub('', mid)


def extract(root):
    mons = {}
    for f in glob.glob(os.path.join(root, 'data/pokemon/base_stats/*.asm')):
        if os.path.basename(f) == 'egg.asm':
            continue
        m = parse_mon(f)
        if m:
            mons[m['id']] = m

    nmap = {}  # norm(id) -> id
    for i in mons:
        nmap.setdefault(norm(i), i)

    def resolve(name):
        """Map an evos_attacks / species name to a base_stats id."""
        k = norm(name)
        if k in nmap:
            return nmap[k]
        if k + 'plain' in nmap:
            return nmap[k + 'plain']
        return None

    # ---------------------------------------------------------- moves
    moves = {}
    for s in open(os.path.join(root, 'data/moves/moves.asm')).read().splitlines():
        m = re.match(r'\s*move\s+([A-Z_0-9]+),\s*(EFFECT_[A-Z_0-9]+),\s*(\d+),\s*([A-Z_]+),\s*'
                      r'(-?\d+),\s*(\d+),\s*(\d+),\s*([A-Z]+)', s)
        if m:
            n, eff, pw, ty, acc, pp, ch, cat = m.groups()
            moves[n] = dict(id=n, effect=eff, power=int(pw), type=ty, acc=int(acc),
                             pp=int(pp), chance=int(ch), cat=cat, prio=0)

    for s in open(os.path.join(root, 'data/moves/priorities.asm')).read().splitlines():
        m = re.match(r'\s*db\s+([A-Z_0-9]+),\s*(-?\d+)\s*$', s)
        if m and m.group(1) in moves:
            moves[m.group(1)]['prio'] = int(m.group(2))

    # Contact: Physical moves make contact unless listed in AbnormalContactMoves,
    # which flips the default either way (mirrors the ROM's CheckContactMove).
    abnormal = set()
    for s in open(os.path.join(root, 'data/moves/abnormal_contact_moves.asm')).read().splitlines():
        m = re.match(r'\s*db\s+([A-Z_0-9]+)', s)
        if m:
            abnormal.add(m.group(1))
    for n, mv in moves.items():
        mv['contact'] = (mv['cat'] == 'PHYSICAL') != (n in abnormal)

    # Move-list flags that abilities key off: Iron Fist (punch), Mega Launcher
    # (pulse), Bulletproof (bullet), Sharpness (slice), Soundproof (sound),
    # powder immunity, Wind Rider (wind). Each file is a plain `db MOVE` list.
    flag_files = {'punch': 'punching_moves', 'pulse': 'launcher_moves',
                  'bullet': 'bullet_moves', 'slice': 'slicing_moves',
                  'sound': 'sound_moves', 'powder': 'powder_moves',
                  'wind': 'wind_moves', 'high_crit': 'critical_hit_moves'}
    for flag, fn in flag_files.items():
        names = set()
        path = os.path.join(root, f'data/moves/{fn}.asm')
        if os.path.exists(path):
            for s in open(path).read().splitlines():
                m = re.match(r'\s*db\s+([A-Z_0-9]+)', s)
                if m:
                    names.add(m.group(1))
        for n, mv in moves.items():
            mv[flag] = n in names
    # Sheer Force applies when the move's script has an effectchance or
    # selfeffectchance command (CheckSheerForceNegation), not just when the
    # move has a nonzero chance byte.
    effect_ids = re.findall(r'^\s*const (EFFECT_[A-Z_0-9]+)',
                            open(os.path.join(root, 'constants/move_effect_constants.asm')).read(), re.M)
    labels = re.findall(r'^\s*dw (\w+)',
                        open(os.path.join(root, 'data/moves/effects_pointers.asm')).read(), re.M)
    scripts, cur = {}, None
    for s in open(os.path.join(root, 'data/moves/effects.asm')).read().splitlines():
        m = re.match(r'^(\w+):', s)
        if m:
            cur = m.group(1)
            scripts.setdefault(cur, [])
        elif cur and s.strip():
            scripts[cur].append(s.strip().split()[0])
    secondary = {eff for eff, lab in zip(effect_ids, labels)
                 if {'effectchance', 'selfeffectchance'} & set(scripts.get(lab, []))}
    script_of = dict(zip(effect_ids, labels))
    for mv in moves.values():
        mv['secondary'] = mv['effect'] in secondary
        # the move's battle script (data/moves/effects.asm), so the engine can
        # follow the ROM's command list (checkhit, effectchance, ...)
        mv['script'] = [c for c in scripts.get(script_of.get(mv['effect']), [])
                        if not c.startswith(';')]

    # Reckless boosts recoil moves and (Hi) Jump Kick (RecklessAbility).
    for mv in moves.values():
        mv['recoil'] = mv['effect'] in ('EFFECT_RECOIL_HIT', 'EFFECT_JUMP_KICK')

    # ------------------------------------------------------ type chart
    eff_map = {'NO_EFFECT': 0.0, 'NOT_VERY_EFFECTIVE': 0.5, 'SUPER_EFFECTIVE': 2.0}
    chart = {}
    for s in open(os.path.join(root, 'data/types/type_matchups.asm')).read().splitlines():
        m = re.match(r'\s*db\s+([A-Z_]+),\s*([A-Z_]+),\s*([A-Z_]+)', s)
        if m and m.group(3) in eff_map:
            chart[f"{m.group(1)}>{m.group(2)}"] = eff_map[m.group(3)]
    # Ground vs Flying is commented out of the data table; the engine enforces
    # it via the airborne-state check instead. Add it explicitly.
    chart['GROUND>FLYING'] = 0.0

    # ------------------------------------------------ learnsets + evolution
    level_moves = {}   # id -> list of [level, MOVE]
    can_evolve = set()
    cur = None
    for s in open(os.path.join(root, 'data/pokemon/evos_attacks.asm')).read().splitlines():
        s = s.strip()
        m = re.match(r'evos_attacks\s+(\w+)', s)
        if m:
            cur = resolve(m.group(1))
            if cur:
                level_moves.setdefault(cur, [])
            continue
        if cur is None:
            continue
        if s.startswith('evo_data'):
            can_evolve.add(cur); continue
        lm = re.match(r'learnset\s+(\d+),\s*([A-Z_0-9]+)', s)
        if lm and lm.group(2) in moves:
            level_moves[cur].append([int(lm.group(1)), lm.group(2)])

    egg = {}  # keyed by species constant
    cur = None
    for s in open(os.path.join(root, 'data/pokemon/egg_moves.asm')).read().splitlines():
        s = s.strip()
        dp = re.match(r'dp\s+([A-Z_0-9]+),\s*([A-Z_0-9]+)', s)
        if dp:
            cur = resolve(dp.group(1))
            if cur:
                egg.setdefault(cur, [])
            continue
        if cur is None:
            continue
        dbm = re.match(r'db\s+([A-Z_0-9]+)\s*$', s)
        if dbm and dbm.group(1) in moves:
            egg[cur].append(dbm.group(1))

    # ------------------------------------------------------- legendaries
    legendary_species = set()
    for s in open(os.path.join(root, 'data/pokemon/legendary_mons.asm')).read().splitlines():
        m = re.match(r'\s*dp\s+([A-Z_0-9]+)', s)
        if m:
            r = resolve(m.group(1))
            if r:
                legendary_species.add(species_of(r))
    legendary = {mid for mid in mons if species_of(mid) in legendary_species}

    # ------------------------------------------ assemble full move pool/mon
    LEVEL_CAP = 50
    learnsets = {}
    for mid, mon in mons.items():
        lv = [mv for lvl, mv in level_moves.get(mid, []) if lvl <= LEVEL_CAP]
        # forms without their own learnset fall back to the plain form's
        if not lv and mid.endswith(('_alolan', '_galarian', '_hisuian', '_armored', '_galar')):
            base = re.sub(r'_(alolan|galarian|hisuian|armored|galar)$', '_plain', mid)
            lv = [mv for lvl, mv in level_moves.get(base, []) if lvl <= LEVEL_CAP]
        pool = set(lv) | set(mon.get('tmhm', [])) | set(egg.get(mid, []))
        learnsets[mid] = sorted(p for p in pool if p in moves)
        mon['fully_evolved'] = mid not in can_evolve
        mon['legendary'] = mid in legendary
        mon.pop('tmhm', None)  # rolled into learnsets

    # weights (data/pokemon/body_data.asm, hectograms) for Low Kick
    forms = {'ALOLAN_FORM': '_alolan', 'GALARIAN_FORM': '_galarian', 'HISUIAN_FORM': '_hisuian',
             'PALDEAN_FORM': '_paldean', 'PLAIN_FORM': '_plain'}
    for s in open(os.path.join(root, 'data/pokemon/body_data.asm')).read().splitlines():
        m = re.match(r'\s*body_data\s+\d+,\s*(\d+),.*;\s*([A-Z0-9_]+)(?:\s*\((\w+)\))?', s)
        if not m:
            continue
        weight, name, form = int(m.group(1)), m.group(2).lower(), m.group(3)
        for key in ([name + forms[form]] if form in forms else [name, name + '_plain']):
            if key in mons and 'weight' not in mons[key]:
                mons[key]['weight'] = weight
    return mons, moves, chart, learnsets


def extract_abilities(root):
    """data/abilities/flags.asm -> {ABILITY: [FLAG, ...]} (e.g. IGNORABLE for
    Mold Breaker, NO_INTIMIDATE, NO_TRACE)."""
    out = {}
    for s in pick(open(os.path.join(root, 'data/abilities/flags.asm')).read().splitlines()):
        m = re.match(r'abilflag\s+([A-Z_0-9]+)\s*(?:,(.*))?$', s.split(';')[0].strip())
        if m:
            out[m.group(1)] = [f.strip() for f in (m.group(2) or '').split(',') if f.strip()]
    return out


def extract_items(root):
    """data/items/attributes.asm, in item-constant order -> {ITEM: {held, param}}."""
    names = []
    for s in open(os.path.join(root, 'constants/item_constants.asm')).read().splitlines():
        m = re.match(r'\s*const\s+([A-Z_0-9]+)', s)
        if m:
            names.append(m.group(1))
        elif names and re.match(r'\s*DEF NUM_ITEMS', s):
            break
    attrs = []
    for s in pick(open(os.path.join(root, 'data/items/attributes.asm')).read().splitlines()):
        m = re.match(r'item_attribute\s+[^,]+,\s*([A-Z_0-9]+),\s*([^,]+),', s)
        if m:
            attrs.append((m.group(1), m.group(2).strip()))
    out = {}
    for name, (held, param) in zip(names[1:], attrs):
        out[name] = {'held': None if held == '0' else held, 'param': param}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', default='.',
                     help='path to a Polished Crystal checkout (default: cwd)')
    args = ap.parse_args()

    mons, moves, chart, learnsets = extract(args.source)

    out = os.path.join(HERE, 'data')
    os.makedirs(out, exist_ok=True)
    json.dump(mons, open(os.path.join(out, 'pokemon.json'), 'w'), indent=0)
    json.dump(moves, open(os.path.join(out, 'moves.json'), 'w'), indent=0)
    json.dump(chart, open(os.path.join(out, 'typechart.json'), 'w'), indent=0)
    json.dump(learnsets, open(os.path.join(out, 'learnsets.json'), 'w'), indent=0)
    json.dump(extract_abilities(args.source), open(os.path.join(out, 'abilities.json'), 'w'),
              indent=0)
    json.dump(extract_items(args.source), open(os.path.join(out, 'items.json'), 'w'), indent=0)

    fe = sum(1 for m in mons.values() if m['fully_evolved'])
    empty = [k for k, v in learnsets.items() if not v]
    print(f"pokemon: {len(mons)} (fully-evolved {fe}, legendary {len(legendary_set(mons))})")
    print(f"moves: {len(moves)}   type-matchups: {len(chart)}   learnsets: {len(learnsets)}")
    print(f"avg movepool: {sum(len(v) for v in learnsets.values()) / len(learnsets):.1f}"
          f"   empty pools: {len(empty)} {empty}")
    sample = next(iter(learnsets.get('dragonite', learnsets.values())), [])
    print("sample dragonite pool:", learnsets.get('dragonite', sample)[:12], '...')


def legendary_set(mons):
    return [m for m in mons.values() if m.get('legendary')]


if __name__ == '__main__':
    main()
