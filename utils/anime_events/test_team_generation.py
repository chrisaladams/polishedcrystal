#!/usr/bin/env python3
"""Check that generated teams always finish (PyBoy), so no cup or link format
can hang a Game Boy.

CupMakeTeam (engine/events/cup_teams.asm) and LinkRandomBattle_MakeTeam
(engine/link/random_battle.asm) draw sets from the Random Battle sets until
the team fits, starting over after too many misses. That only ends if enough
different species fit. This makes each kind of team the game asks for, many
times over, each within a time limit (Caller's 600 frames):

- typed teams for every type, four (Kimono Cup's Miki) and six (more than any
  cup asks), as the Kimono, Whirl and Rudy rounds draw;
- three of any type (the Rental Cup) and the Random Battle format's six;
- every typed team really is of its type and has no species twice.

If someone trims the Random Battle sets so a type has too few species, this
fails, instead of a Kimono Cup hanging on that type's day.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_team_generation.py SAVE.sav
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_friend_records import Caller, Game, rgbasm_values  # noqa: E402

TYPES = ['NORMAL', 'FIGHTING', 'FLYING', 'POISON', 'GROUND', 'ROCK', 'BUG', 'GHOST', 'STEEL', 'FIRE', 'WATER',
         'GRASS', 'ELECTRIC', 'PSYCHIC', 'ICE', 'DRAGON', 'DARK', 'FAIRY']
ROUNDS = 3  # (each kind of team, this many times, from different random states)


def main():
    K = rgbasm_values(TYPES + ['CUPTYPE_ANY', 'RENTAL_CUP_TEAM_SIZE', 'PARTYMON_STRUCT_LENGTH', 'MON_FORM',
                               'EXTSPECIES_MASK', 'SPECIESFORM_MASK'], None)
    L = K['PARTYMON_STRUCT_LENGTH']
    g = Game(open(sys.argv[1], 'rb').read())
    g.boot()
    caller = Caller(g)
    fails = []
    base = g.state()

    def team(prefix):
        n = g.rd(prefix + 'Count')
        out = []
        for i in range(n):
            a = g.addr(prefix + 'Mon1') + i * L
            out.append((g.m[1, a], g.m[1, a + K['MON_FORM']]))
        return out

    def types_of(species, form):
        """Its two types, as the game's base data has them (GetBaseData)."""
        g.wr('wCurSpecies', species)
        g.wr('wCurForm', form & K['SPECIESFORM_MASK'])
        caller.call('GetBaseData')
        return g.rd('wBaseType1'), g.rd('wBaseType2')

    def make(label, regs, prefix, size, what, of_type=None):
        for r in range(ROUNDS):
            g.load(base)
            g.tick(17 * r + 1)  # (a different random state each round)
            try:
                caller.call(label, **regs)
            except AssertionError:
                fails.append(f'{what}: did not finish within the time limit (round {r + 1})')
                return
            got = team(prefix)
            if len(got) != size:
                fails.append(f'{what}: {len(got)} Pokemon, not {size}')
            species = [(s, f & K['EXTSPECIES_MASK']) for s, f in got]
            if len(set(species)) != len(species):
                fails.append(f'{what}: a species twice: {species}')
            if of_type is not None:
                off = [s for s, f in got if of_type not in types_of(s, f)]
                if off:
                    fails.append(f'{what}: species {off} are not of the type')

    for t in TYPES:
        for size in (4, 6):
            make('CupMakeTeam', {'B': size, 'C': K[t]}, 'wOTParty', size, f'{size} {t} type', K[t])
    make('CupMakeTeam', {'B': K['RENTAL_CUP_TEAM_SIZE'], 'C': K['CUPTYPE_ANY']}, 'wOTParty',
         K['RENTAL_CUP_TEAM_SIZE'], 'the Rental Cup team')
    make('LinkRandomBattle_MakeTeam', {}, 'wParty', 6, 'the Random Battle team')

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
