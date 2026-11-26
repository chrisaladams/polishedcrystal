#!/usr/bin/env python3
"""Check the offline cups' team rules at their edges (CupSelectTeam,
engine/events/cups.asm), calling it directly with made-up parties, for the
cups that take the whole party (eggs aside):

- Whirl (3-6, every one a Water type): two is too few; three or six of them
  enter; an Egg in the party is left out (so three and an Egg enter, and two
  and an Egg are too few); one that isn't Water turns the team away, even
  with the others enough; a Water/other dual type counts;
- Dragon Masters (3-6, at least one Dragon type): none is turned away; one
  among others enters; a party of a Dragon and two Eggs is too few;
- World (exactly six): six enter; five and an Egg are too few;
- a Friend Battle under Standard rules (1-6, the Cable Club's own checks):
  one enters; two legendaries are refused (CUPTEAM_RULES).

And what enters is what's staged for the battle (wOTParty): the party's
Pokemon in party order, the Egg left out.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_cup_eligibility.py SAVE.sav
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_friend_records import Caller, Game, rgbasm_values  # noqa: E402

NAMES = ['PARTYMON_STRUCT_LENGTH', 'MON_SPECIES', 'MON_FORM', 'MON_ITEM', 'MON_LEVEL', 'MON_IS_EGG_F',
         'PLAIN_FORM', 'CUP_WHIRL', 'CUP_DRAGON', 'CUP_WORLD', 'CUP_FRIEND', 'LINK_RULE_STANDARD',
         'CUPTEAM_OK', 'CUPTEAM_SIZE', 'CUPTEAM_TYPE', 'CUPTEAM_RULES', 'CUPTEAM_EGG',
         'SQUIRTLE', 'PSYDUCK', 'GOLDEEN', 'MAGIKARP', 'LAPRAS', 'CHARMANDER', 'PIDGEY', 'RATTATA',
         'DRATINI', 'ZUBAT', 'ARTICUNO', 'ZAPDOS']


def main():
    K = rgbasm_values(NAMES, None)
    L = K['PARTYMON_STRUCT_LENGTH']
    g = Game(open(sys.argv[1], 'rb').read())
    g.boot()
    caller = Caller(g)
    base = g.state()
    fails = []
    codes = {K[n]: n for n in ('CUPTEAM_OK', 'CUPTEAM_SIZE', 'CUPTEAM_TYPE', 'CUPTEAM_RULES', 'CUPTEAM_EGG')}

    def mon(species, egg=False):
        return dict(species=K[species], egg=egg)

    def select(cup, team, rule=None):
        g.load(base)
        g.wr('wCupId', K[cup])
        if rule:
            g.wr('wLinkBattleRules', K[rule])
        g.wr('wPartyCount', len(team))
        for i, m in enumerate(team):
            g.wr('wPartyMon1', m['species'], i * L + K['MON_SPECIES'])
            g.wr('wPartyMon1', 50, i * L + K['MON_LEVEL'])
            g.wr('wPartyMon1', 0, i * L + K['MON_ITEM'])
            g.wr('wPartyMon1', K['PLAIN_FORM'] | (1 << K['MON_IS_EGG_F'] if m['egg'] else 0), i * L + K['MON_FORM'])
        caller.call('CupSelectTeam')
        got = g.m[g.sym['hScriptVar'][1]]
        staged = [g.rd('wOTPartyMon1', i * L + K['MON_SPECIES']) for i in range(g.rd('wOTPartyCount'))]
        return codes.get(got, got), staged

    def expect(cup, what, team, want, rule=None, staged=None):
        got, st = select(cup, team, rule)
        if got != want:
            fails.append(f'{cup}, {what}: {got}, not {want}')
        if staged is not None and st != [K[s] for s in staged]:
            fails.append(f'{cup}, {what}: staged {st}, not {[K[s] for s in staged]}')

    water = [mon(s) for s in ('SQUIRTLE', 'PSYDUCK', 'GOLDEEN', 'MAGIKARP', 'LAPRAS', 'SQUIRTLE')]
    egg = mon('PIDGEY', egg=True)
    W = 'CUP_WHIRL'
    expect(W, 'two Water', water[:2], 'CUPTEAM_SIZE')
    expect(W, 'three Water', water[:3], 'CUPTEAM_OK', staged=['SQUIRTLE', 'PSYDUCK', 'GOLDEEN'])
    expect(W, 'six Water', water, 'CUPTEAM_OK')
    expect(W, 'three Water and an Egg', [water[0], egg, water[1], water[2]], 'CUPTEAM_OK',
           staged=['SQUIRTLE', 'PSYDUCK', 'GOLDEEN'])
    expect(W, 'two Water and an Egg', [water[0], egg, water[1]], 'CUPTEAM_SIZE')
    expect(W, 'three Water and a Fire', water[:3] + [mon('CHARMANDER')], 'CUPTEAM_TYPE')
    expect(W, 'Lapras (Water/Ice) counts', [water[4], water[0], water[1]], 'CUPTEAM_OK')
    D = 'CUP_DRAGON'
    expect(D, 'no Dragon', [mon('PIDGEY'), mon('RATTATA'), mon('ZUBAT')], 'CUPTEAM_TYPE')
    expect(D, 'one Dragon among others', [mon('PIDGEY'), mon('DRATINI'), mon('RATTATA')], 'CUPTEAM_OK',
           staged=['PIDGEY', 'DRATINI', 'RATTATA'])
    expect(D, 'a Dragon and two Eggs', [mon('DRATINI'), egg, egg], 'CUPTEAM_SIZE')
    V = 'CUP_WORLD'
    expect(V, 'six', water, 'CUPTEAM_OK')
    expect(V, 'five and an Egg', water[:5] + [egg], 'CUPTEAM_SIZE')
    F = 'CUP_FRIEND'
    expect(F, 'one', [mon('PIDGEY')], 'CUPTEAM_OK', rule='LINK_RULE_STANDARD')
    expect(F, 'two legendaries', [mon('ARTICUNO'), mon('ZAPDOS')], 'CUPTEAM_RULES', rule='LINK_RULE_STANDARD')

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
