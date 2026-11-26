#!/usr/bin/env python3
"""Build the Random Battle set table (data/link/random_battle_sets.asm) from
the optimised sets in data/best_sets.json.

Random Battle gives each player six random level 50 Pokemon. The sets come
from the best-set optimiser, made friendly for casual play:
- Choice items (which lock the user into one move), Life Orb and the status
  orbs (which hurt the user) become a type-boosting item for the set's first
  attack, or Leftovers. A Toxic Orb stays on a Poison Heal user.
- An Assault Vest on a set with a status move becomes Leftovers: the vest
  stops its holder using status moves, which the optimiser doesn't model.
- Sets with Trick or Switcheroo (they swap items around) or Hidden Power
  (its type depends on DVs) are skipped.
- Up to two different sets per species, for variety.

Each entry is RANDOM_SET_LENGTH (9) bytes: species and form (dp), four
moves, the held item, the ability slot (ABILITY_1, ABILITY_2 or
HIDDEN_ABILITY), and the index of its type profile. Each distinct profile is
stored once, in RandomBattleProfiles, as RANDOM_PROFILE_LENGTH (5) bytes: the
two types as indexes into RANDOM_TYPES (the same twice for a single type),
and three bytes of weakness flags (bit i of the 24: weak to RANDOM_TYPES[i],
taking an immunity from the set's ability into account). The game uses the
types and weaknesses to give each random team a decent type spread
(engine/link/random_battle.asm).

Run from the repository root: python3 meta_sim/make_random_sets.py
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'data', 'link', 'random_battle_sets.asm')

FORMS = {'plain': 'PLAIN_FORM', 'alolan': 'ALOLAN_FORM', 'galarian': 'GALARIAN_FORM',
         'hisuian': 'HISUIAN_FORM', 'paldean': 'PALDEAN_FORM', 'armored': 'MEWTWO_ARMORED_FORM'}
FORM_SUFFIX = re.compile(r'_(plain|alolan|galarian|hisuian|paldean|armored)$')
SKIP_MOVES = {'TRICK', 'SWITCHEROO', 'HIDDEN_POWER'}
REPLACE_ITEMS = {'CHOICE_BAND', 'CHOICE_SPECS', 'CHOICE_SCARF', 'LIFE_ORB', 'FLAME_ORB',
                 'TOXIC_ORB'}
SETS_PER_SPECIES = 2
# type order for the type and weakness bytes (constants/type_constants.asm)
RANDOM_TYPES = ['NORMAL', 'FIGHTING', 'FLYING', 'POISON', 'GROUND', 'ROCK', 'BUG', 'GHOST',
                'STEEL', 'FIRE', 'WATER', 'GRASS', 'ELECTRIC', 'PSYCHIC', 'ICE', 'DRAGON',
                'DARK', 'FAIRY']
# abilities that make the holder immune to (or resist) an attacking type
ABILITY_IMMUNE = {'LEVITATE': {'GROUND'}, 'EARTH_EATER': {'GROUND'}, 'FLASH_FIRE': {'FIRE'},
                  'WELL_BAKED_BODY': {'FIRE'}, 'WATER_ABSORB': {'WATER'},
                  'STORM_DRAIN': {'WATER'}, 'DRY_SKIN': {'WATER'}, 'VOLT_ABSORB': {'ELECTRIC'},
                  'LIGHTNING_ROD': {'ELECTRIC'}, 'MOTOR_DRIVE': {'ELECTRIC'},
                  'SAP_SIPPER': {'GRASS'}}
ABILITY_HALVES = {'THICK_FAT': {'FIRE', 'ICE'}, 'HEATPROOF': {'FIRE'},
                  'PURIFYING_SALT': {'GHOST'}, 'WATER_BUBBLE': {'FIRE'}}


def weaknesses(types, ability, chart):
    """The attacking types that hit this set super effectively."""
    weak = []
    for atk in RANDOM_TYPES:
        mult = 1.0
        for t in types:
            mult *= chart.get(f'{atk}>{t}', 1.0)
        if atk in ABILITY_IMMUNE.get(ability, ()):
            mult = 0
        if atk in ABILITY_HALVES.get(ability, ()):
            mult /= 2
        if mult > 1:
            weak.append(atk)
    return weak
ABILITY_SLOTS = ['ABILITY_1', 'ABILITY_2', 'HIDDEN_ABILITY']


# forms with their own constant (SPECIES_FORMNAME_FORM)
SPECIAL_FORMS = {'tauros_paldean_fire': ('TAUROS', 'TAUROS_PALDEAN_FIRE_FORM'),
                 'tauros_paldean_water': ('TAUROS', 'TAUROS_PALDEAN_WATER_FORM'),
                 'ursaluna_bloodmoon': ('URSALUNA', 'URSALUNA_BLOODMOON_FORM')}


def build_types(mid):
    """The species' (default, faithful) types, from its base data file, whose
    type line may be in an `if DEF(FAITHFUL)` / `else` / `endc` block."""
    path = os.path.join(ROOT, 'data', 'pokemon', 'base_stats', f'{mid}.asm')
    found = {}
    state = None  # None: both builds; 'faithful' / 'default' inside a block
    for line in open(path):
        code = line.split(';')[0].strip()
        if code == 'if DEF(FAITHFUL)':
            state = 'faithful'
        elif code == 'else' and state == 'faithful':
            state = 'default'
        elif code == 'endc':
            state = None
        elif line.rstrip().endswith('; type') and code.startswith('db '):
            types = tuple(dict.fromkeys(t.strip() for t in code[3:].split(',')))
            for build in ((state,) if state else ('faithful', 'default')):
                found.setdefault(build, types)
    return found['default'], found['faithful']


def species_and_form(mid):
    if mid in SPECIAL_FORMS:
        return SPECIAL_FORMS[mid]
    m = FORM_SUFFIX.search(mid)
    base = FORM_SUFFIX.sub('', mid)
    form = FORMS[m.group(1)] if m else 'PLAIN_FORM'
    return base.upper(), form


def main():
    best = json.load(open(os.path.join(HERE, 'data', 'best_sets.json')))
    mons = json.load(open(os.path.join(HERE, 'data', 'pokemon.json')))
    moves = json.load(open(os.path.join(HERE, 'data', 'moves.json')))
    items = json.load(open(os.path.join(HERE, 'data', 'items.json')))
    type_item = {v['param']: k for k, v in items.items() if v.get('held') == 'HELD_TYPE_BOOST'}
    chart = json.load(open(os.path.join(HERE, 'data', 'typechart.json')))
    by_species = {}
    for key, st in sorted(best.items()):
        mid = key.split('|')[0]
        mon = mons.get(mid)
        if not mon or mon.get('legendary') or not mon.get('fully_evolved'):
            continue
        if SKIP_MOVES & set(st['moves']) or len(st['moves']) != 4:
            continue
        item = st['item']
        if item in REPLACE_ITEMS and not (item == 'TOXIC_ORB' and st['ability'] == 'POISON_HEAL'):
            attack = next((m for m in st['moves'] if moves[m]['cat'] != 'STATUS'), None)
            item = type_item.get(moves[attack]['type'], 'LEFTOVERS') if attack else 'LEFTOVERS'
        if item == 'ASSAULT_VEST' and any(moves[m]['cat'] == 'STATUS' for m in st['moves']):
            item = 'LEFTOVERS'
        ab = mon['abilities']
        slot = ABILITY_SLOTS[ab.index(st['ability'])] if st['ability'] in ab else 'ABILITY_1'
        default_types, faithful_types = build_types(mid)
        assert default_types == tuple(mon['types']), (mid, default_types, mon['types'])
        entry = (tuple(st['moves']), item, slot, tuple(mon['types']),
                 tuple(weaknesses(mon['types'], st['ability'], chart)),
                 faithful_types, tuple(weaknesses(faithful_types, st['ability'], chart)))
        sets = by_species.setdefault(mid, [])
        if entry not in sets and len(sets) < SETS_PER_SPECIES:
            sets.append(entry)
    lines = ['; Random Battle sets: generated by meta_sim/make_random_sets.py from',
             '; meta_sim/data/best_sets.json. Do not edit by hand.', '',
             'RandomBattleSets:']
    # the default build's profiles, then (in the faithful build only) those of
    # sets whose species has other types there (FAITHFUL base data)
    profiles = []
    for mid in sorted(by_species):
        for mvs, item, slot, types, weak, ftypes, fweak in by_species[mid]:
            if (types, weak) not in profiles:
                profiles.append((types, weak))
    faithful_profiles = []
    for mid in sorted(by_species):
        for mvs, item, slot, types, weak, ftypes, fweak in by_species[mid]:
            if (ftypes, fweak) not in profiles + faithful_profiles:
                faithful_profiles.append((ftypes, fweak))
    every = profiles + faithful_profiles
    n = 0
    for mid in sorted(by_species):
        species, form = species_and_form(mid)
        for mvs, item, slot, types, weak, ftypes, fweak in by_species[mid]:
            lines.append(f'\tdp {species}, {form}')
            lines.append(f'\tdb {", ".join(mvs)}')
            here, there = every.index((types, weak)), every.index((ftypes, fweak))
            if here == there:
                lines.append(f'\tdb {item}, {slot}, {here}')
            else:
                lines += ['if DEF(FAITHFUL)', f'\tdb {item}, {slot}, {there} ; {"/".join(ftypes)}',
                          'else', f'\tdb {item}, {slot}, {here}', 'endc']
            n += 1
    lines += ['RandomBattleSetsEnd:', '', 'RandomBattleProfiles:']

    def profile_lines(i, types, weak):
        t1 = RANDOM_TYPES.index(types[0])
        t2 = RANDOM_TYPES.index(types[-1])
        bits = sum(1 << RANDOM_TYPES.index(t) for t in weak)
        return [f'\tdb {t1}, {t2} ; {i}: {"/".join(types)}',
                f'\tdb ${bits & 0xff:02x}, ${(bits >> 8) & 0xff:02x}, ${bits >> 16:02x}'
                f' ; weak to {", ".join(weak) or "nothing"}']
    for i, (types, weak) in enumerate(profiles):
        lines += profile_lines(i, types, weak)
    if faithful_profiles:
        lines.append('if DEF(FAITHFUL) ; (types only the faithful build has)')
        for i, (types, weak) in enumerate(faithful_profiles, len(profiles)):
            lines += profile_lines(i, types, weak)
        lines.append('endc')
    lines += ['RandomBattleProfilesEnd:', '',
              f'DEF NUM_RANDOM_BATTLE_SETS EQU {n}',
              f'ASSERT NUM_RANDOM_TYPES == {len(RANDOM_TYPES)}',
              'ASSERT RANDOM_SET_LENGTH == 9',
              'ASSERT RANDOM_PROFILE_LENGTH == 5', '',
              'ASSERT RandomBattleSetsEnd - RandomBattleSets == NUM_RANDOM_BATTLE_SETS * RANDOM_SET_LENGTH',
              'if DEF(FAITHFUL)',
              f'ASSERT RandomBattleProfilesEnd - RandomBattleProfiles == {len(every)} * RANDOM_PROFILE_LENGTH',
              'else',
              f'ASSERT RandomBattleProfilesEnd - RandomBattleProfiles == {len(profiles)} * RANDOM_PROFILE_LENGTH',
              'endc', '']
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, 'w').write('\n'.join(lines))
    print(f'wrote {OUT}: {n} sets for {len(by_species)} species, {len(profiles)} type profiles'
          f' (and {len(faithful_profiles)} more in the faithful build)')


if __name__ == '__main__':
    sys.exit(main())
