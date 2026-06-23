"""Extract this ROM's L50-relevant battle data from the .asm source into JSON.

Reads (relative to repo root):
  data/pokemon/base_stats/*.asm   base stats, types, abilities, tm/hm learnset
  data/moves/moves.asm            move power/type/accuracy/category/effect
  data/moves/priorities.asm       move priority brackets
  data/types/type_matchups.asm    type effectiveness chart
  data/pokemon/evos_attacks.asm   level-up learnsets + evolution markers
  data/pokemon/egg_moves.asm      egg moves
  data/pokemon/legendary_mons.asm legendary / uber species

Writes meta_sim/data/{pokemon,moves,typechart,learnsets}.json

The extractor mirrors the shipped (non-faithful / Polished) values; it does not
change any game data. Run from the repo root:  python3 meta_sim/extract.py
"""
import re, glob, os, json

NF = True  # non-faithful (Polished) values

def pick(lines):
    """Return non-faithful branch when an if DEF(FAITHFUL)/else block wraps a line."""
    mode=None; out=[]
    for ln in lines:
        s=ln.strip()
        if s.startswith('if DEF(FAITHFUL)'): mode='if'; continue
        if mode and s.startswith('else'): mode='else'; continue
        if mode and s.startswith('endc'): mode=None; continue
        keep = (mode is None) or (mode=='else' if NF else mode=='if')
        if keep: out.append(s)
    return out

def norm(x):
    """Normalize a name for matching: strip underscores, lowercase."""
    return x.replace('_','').lower()

# ---------------------------------------------------------------- pokemon
def parse_mon(path):
    raw=open(path).read().splitlines()
    L=pick(raw)
    mon={'id':os.path.basename(path)[:-4], 'tmhm':[]}
    for s in L:
        m=re.match(r'db\s+(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\s*;.*BST',s)
        if m and 'stats' not in mon:
            hp,atk,df,spe,sat,sdf=map(int,m.groups())
            mon['stats']=dict(hp=hp,atk=atk,defe=df,spe=spe,spa=sat,spd=sdf); mon['bst']=hp+atk+df+spe+sat+sdf
        t=re.match(r'db ([A-Z_]+), ([A-Z_]+) ; type',s)
        if t and 'types' not in mon:
            mon['types']=[t.group(1)] if t.group(1)==t.group(2) else [t.group(1),t.group(2)]
        a=re.search(r'abilities_for\s+\w+,\s*([A-Z_0-9]+),\s*([A-Z_0-9]+),\s*([A-Z_0-9]+)',s)
        if a: mon['abilities']=[a.group(1),a.group(2),a.group(3)]
        tm=re.match(r'tmhm\s+(.+)$',s)
        if tm:
            mon['tmhm']+= [x.strip() for x in tm.group(1).split(',') if x.strip()]
    return mon if 'stats' in mon else None

mons={}
for f in glob.glob('data/pokemon/base_stats/*.asm'):
    if os.path.basename(f)=='egg.asm': continue
    m=parse_mon(f)
    if m: mons[m['id']]=m

NMAP={}  # norm(id) -> id
for i in mons: NMAP.setdefault(norm(i), i)

def resolve(name):
    """Map an evos_attacks / species name to a base_stats id."""
    k=norm(name)
    if k in NMAP: return NMAP[k]
    if k+'plain' in NMAP: return NMAP[k+'plain']
    return None

# ---------------------------------------------------------------- moves
moves={}
for s in open('data/moves/moves.asm').read().splitlines():
    m=re.match(r'\s*move\s+([A-Z_0-9]+),\s*(EFFECT_[A-Z_0-9]+),\s*(\d+),\s*([A-Z_]+),\s*(-?\d+),\s*(\d+),\s*(\d+),\s*([A-Z]+)',s)
    if m:
        n,eff,pw,ty,acc,pp,ch,cat=m.groups()
        moves[n]=dict(effect=eff,power=int(pw),type=ty,acc=int(acc),pp=int(pp),chance=int(ch),cat=cat,prio=0)

# priorities
for s in open('data/moves/priorities.asm').read().splitlines():
    m=re.match(r'\s*db\s+([A-Z_0-9]+),\s*(-?\d+)\s*$',s)
    if m and m.group(1) in moves:
        moves[m.group(1)]['prio']=int(m.group(2))

# contact flag: a move makes contact if it's Physical, except for the entries
# in AbnormalContactMoves (which flip the default -- a few Physical moves that
# don't make contact, and a couple of Special moves that do). Mirrors the ROM's
# CheckContactMove. Used by Tough Claws (data/moves/abnormal_contact_moves.asm).
abnormal=set()
for s in open('data/moves/abnormal_contact_moves.asm').read().splitlines():
    m=re.match(r'\s*db\s+([A-Z_0-9]+)\s*(;.*)?$',s)
    if m and m.group(1) in moves:
        abnormal.add(m.group(1))
for n,mv in moves.items():
    mv['contact']=(mv['cat']=='PHYSICAL') != (n in abnormal)

# move-flag lists that ability triggers key off (Iron Fist/punch, Mega Launcher/
# pulse, Bulletproof/bullet, Sharpness/slice, Soundproof+Punk Rock/sound,
# powder). Each file is a simple `db MOVE` list; mirror them onto each move.
FLAG_FILES={'punch':'punching_moves','pulse':'launcher_moves','bullet':'bullet_moves',
            'slice':'slicing_moves','sound':'sound_moves','powder':'powder_moves'}
for flag,fn in FLAG_FILES.items():
    names=set()
    try: src=open(f'data/moves/{fn}.asm').read().splitlines()
    except FileNotFoundError: src=[]
    for s in src:
        mm=re.match(r'\s*db\s+([A-Z_0-9]+)',s)
        if mm and mm.group(1) in moves: names.add(mm.group(1))
    for n,mv in moves.items(): mv[flag]=n in names
# recoil flag (Reckless) straight off the effect
for n,mv in moves.items(): mv['recoil']=mv['effect']=='EFFECT_RECOIL_HIT'

# ---------------------------------------------------------------- type chart
EFF={'NO_EFFECT':0.0,'NOT_VERY_EFFECTIVE':0.5,'SUPER_EFFECTIVE':2.0}
chart={}
for s in open('data/types/type_matchups.asm').read().splitlines():
    m=re.match(r'\s*db\s+([A-Z_]+),\s*([A-Z_]+),\s*([A-Z_]+)',s)
    if m and m.group(3) in EFF:
        chart[f"{m.group(1)}>{m.group(2)}"]=EFF[m.group(3)]
# Ground vs Flying is commented out of the data table; the engine enforces it
# via the airborne-state check instead (type_matchups.asm). Add it explicitly.
chart['GROUND>FLYING']=0.0

# ---------------------------------------------------------------- learnsets + evolution
level_moves={}   # id -> list of [level, MOVE]
can_evolve=set()
cur=None
for s in open('data/pokemon/evos_attacks.asm').read().splitlines():
    s=s.strip()
    m=re.match(r'evos_attacks\s+(\w+)',s)
    if m:
        cur=resolve(m.group(1)); level_moves.setdefault(cur,[]) if cur else None
        continue
    if cur is None: continue
    if s.startswith('evo_data'):
        can_evolve.add(cur); continue
    lm=re.match(r'learnset\s+(\d+),\s*([A-Z_0-9]+)',s)
    if lm and lm.group(2) in moves:
        level_moves[cur].append([int(lm.group(1)), lm.group(2)])

# egg moves, keyed by species constant
egg={}
cur=None
for s in open('data/pokemon/egg_moves.asm').read().splitlines():
    s=s.strip()
    dp=re.match(r'dp\s+([A-Z_0-9]+),\s*([A-Z_0-9]+)',s)
    if dp:
        cur=resolve(dp.group(1)); egg.setdefault(cur,[]) if cur else None
        continue
    if cur is None: continue
    dbm=re.match(r'db\s+([A-Z_0-9]+)\s*$',s)
    if dbm and dbm.group(1) in moves:
        egg[cur].append(dbm.group(1))

# ---------------------------------------------------------------- legendaries
FORM_SUFFIX=re.compile(r'_(plain|alolan|galarian|hisuian|armored|galar)$')
def species_of(mid): return FORM_SUFFIX.sub('', mid)

legendary_species=set()
for s in open('data/pokemon/legendary_mons.asm').read().splitlines():
    m=re.match(r'\s*dp\s+([A-Z_0-9]+)',s)
    if m:
        r=resolve(m.group(1))
        if r: legendary_species.add(species_of(r))
legendary={mid for mid in mons if species_of(mid) in legendary_species}

# ---------------------------------------------------------------- assemble learnsets (full move pool per mon)
LEVEL_CAP=50
learnsets={}
for mid,mon in mons.items():
    lv=[mv for lvl,mv in level_moves.get(mid,[]) if lvl<=LEVEL_CAP]
    # forms without their own learnset fall back to the plain form's
    if not lv and mid.endswith(('_alolan','_galarian','_hisuian','_armored','_galar')):
        base=re.sub(r'_(alolan|galarian|hisuian|armored|galar)$','_plain',mid)
        lv=[mv for lvl,mv in level_moves.get(base,[]) if lvl<=LEVEL_CAP]
    pool=set(lv)|set(mon.get('tmhm',[]))|set(egg.get(mid,[]))
    learnsets[mid]=sorted(p for p in pool if p in moves)
    mon['fully_evolved'] = mid not in can_evolve
    mon['legendary'] = mid in legendary
    mon.pop('tmhm', None)  # rolled into learnsets

os.makedirs('meta_sim/data',exist_ok=True)
json.dump(mons,open('meta_sim/data/pokemon.json','w'),indent=0)
json.dump(moves,open('meta_sim/data/moves.json','w'),indent=0)
json.dump(chart,open('meta_sim/data/typechart.json','w'),indent=0)
json.dump(learnsets,open('meta_sim/data/learnsets.json','w'),indent=0)

fe=sum(1 for m in mons.values() if m['fully_evolved'])
empty=[k for k,v in learnsets.items() if not v]
print(f"pokemon: {len(mons)} (fully-evolved {fe}, legendary {len(legendary)})")
print(f"moves: {len(moves)}   type-matchups: {len(chart)}   learnsets: {len(learnsets)}")
print(f"avg movepool: {sum(len(v) for v in learnsets.values())/len(learnsets):.1f}   empty pools: {len(empty)} {empty}")
print("sample dragonite pool:", learnsets['dragonite'][:12], '...')
