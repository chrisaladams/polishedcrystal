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

And the bound itself (RANDOM_MAX_START_OVERS, RandomNextInOrder), forced by
starting each generator past the limit:
- the sets taken in order make a full, legal team, the same every time;
- a type no set has (an impossible pool) falls to the second, relaxed pass,
  and still ends with a full team of different species;
- out of sets (both passes done), it returns with what it has: it ends.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_team_generation.py SAVE.sav
"""
import os
import re
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

    # the bound: start each generator past RANDOM_MAX_START_OVERS (a hook at
    # its .start_over, the first time), optionally with the in-order index
    # near the end, and see that it ends with a legal team
    sets = int(re.search(r'DEF NUM_RANDOM_BATTLE_SETS EQU (\d+)', open(os.path.join(
        os.path.dirname(os.path.dirname(HERE)), 'data', 'link', 'random_battle_sets.asm')).read()).group(1))
    K.update(rgbasm_values(['RANDOM_MAX_START_OVERS'], None))

    def forced(label, regs, prefix, size, what, index=0, foe_type=None):
        hook = g.sym[label + '.start_over']
        state = {'done': False}

        def past_limit(_):
            if not state['done']:
                state['done'] = True
                g.wr('wRandomStartOvers', K['RANDOM_MAX_START_OVERS'])
                g.wr('wRandomSeqIndex', index & 0xff)
                g.wr('wRandomSeqIndex', index >> 8, 1)
                if foe_type is not None:
                    g.wr('wCupFoeType', foe_type)
        g.load(base)
        g.pb.hook_register(*hook, past_limit, None)
        try:
            caller.call(label, **regs)
        except AssertionError:
            fails.append(f'{what}: did not end')
            return None
        finally:
            g.pb.hook_deregister(*hook)
        got = team(prefix)
        species = [(s, f & K['EXTSPECIES_MASK']) for s, f in got]
        if len(set(species)) != len(species):
            fails.append(f'{what}: a species twice: {species}')
        if size is not None and len(got) != size:
            fails.append(f'{what}: {len(got)} Pokemon, not {size}')
        return got

    first = forced('LinkRandomBattle_MakeTeam', {}, 'wParty', 6, 'Random Battle, in order')
    again = forced('LinkRandomBattle_MakeTeam', {}, 'wParty', 6, 'Random Battle, in order (again)')
    if first is not None and first != again:
        fails.append('Random Battle, in order: not the same team twice')
    for t in ('FIRE', 'DRAGON', 'FAIRY'):
        got = forced('CupMakeTeam', {'B': 4, 'C': K[t]}, 'wOTParty', 4, f'4 {t} type, in order')
        if got:
            off = [s for s, f in got if K[t] not in types_of(s, f)]
            if off:
                fails.append(f'4 {t} type, in order: species {off} are not of the type')
    # an impossible pool: a type no set has (wCupFoeType set to $7e after the
    # entry stored it), so only the relaxed second pass can fill the team
    forced('CupMakeTeam', {'B': 6, 'C': K['FIRE']}, 'wOTParty', 6, 'an impossible type (relaxed)', foe_type=0x7e)
    # out of sets: two picks from the end of the second pass, then it ends
    got = forced('CupMakeTeam', {'B': 6, 'C': K['CUPTYPE_ANY']}, 'wOTParty', None, 'out of sets',
                 index=2 * sets - 2)
    if got is not None and len(got) > 2:
        fails.append(f'out of sets: {len(got)} Pokemon from 2 sets left?')
    got = forced('LinkRandomBattle_MakeTeam', {}, 'wParty', None, 'Random Battle out of sets', index=2 * sets)
    if got is not None and len(got) != 0:
        fails.append(f'Random Battle out of sets: {len(got)} Pokemon with no sets left?')

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
