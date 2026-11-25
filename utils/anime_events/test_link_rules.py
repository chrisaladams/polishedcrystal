#!/usr/bin/env python3
"""Check the Cable Club's rules (engine/link/link_rules.asm, docs/rules-matrix.md)
in the running game (PyBoy), calling the checks directly with made-up teams:

- the desk's check of your own team (CheckLocalLinkBattleParty), for each
  format: team size, Eggs, the five banned legendaries (Rising Star), at
  most one legendary in any form (Standard), the Species and Item Clauses
  (Rising Star), and anything goes in Unrestricted;
- the check of a received team (CheckReceivedLinkBattleParty): the normalized
  level for Standard, any levels for Unrestricted;
- your team in a Friend Battle (CheckFriendBattleTeam), under the kept
  team's rules, as CupSelectTeam calls it;
- the evasion cap (BattleCommand_checkhit): a +6 evasion counts as +2 in
  every link format, Unrestricted too, and in a Friend Battle, and in full
  in single player.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_link_rules.py SAVE.sav
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_friend_records import Caller, Game, rgbasm_values  # noqa: E402

NAMES = ['PARTYMON_STRUCT_LENGTH', 'MON_SPECIES', 'MON_FORM', 'MON_ITEM', 'MON_LEVEL', 'MON_IS_EGG_F',
         'LINK_RULE_STANDARD', 'LINK_RULE_RANDOM', 'LINK_RULE_RISING_STAR', 'LINK_RULE_UNRESTRICTED',
         'LINK_RULE_WORLD', 'GALARIAN_FORM', 'PLAIN_FORM',
         'PIKACHU', 'RATTATA', 'PIDGEY', 'ODDISH', 'ZUBAT', 'SENTRET', 'ARTICUNO', 'ZAPDOS', 'SUICUNE',
         'MEWTWO', 'CELEBI', 'LEFTOVERS', 'CHARCOAL', 'MYSTIC_WATER', 'MAGNET']


def main():
    K = rgbasm_values(NAMES, None)
    L = K['PARTYMON_STRUCT_LENGTH']
    g = Game(open(sys.argv[1], 'rb').read())
    g.boot()
    caller = Caller(g)
    fails = []
    base = g.state()

    def mon(species, item=0, level=50, egg=False, form=None):
        return dict(species=K[species], item=K[item] if item else 0, level=level, egg=egg,
                    form=K['PLAIN_FORM'] if form is None else form)

    def put(prefix, count, team):
        """Write the team over the save's party structs (other fields kept)."""
        g.wr(count, len(team))
        for i, m in enumerate(team):
            def w(field, v):
                g.wr(prefix, v, i * L + K[field])
            w('MON_SPECIES', m['species'])
            w('MON_ITEM', m['item'])
            w('MON_LEVEL', m['level'])
            w('MON_FORM', m['form'] | (1 << K['MON_IS_EGG_F'] if m['egg'] else 0))

    def desk(rule, team):
        g.load(base)
        g.wr('wLinkBattleRules', K[rule])
        put('wPartyMon1', 'wPartyCount', team)
        caller.call('CheckLocalLinkBattleParty')
        return g.m[g.sym['hScriptVar'][1]] != 0

    def received(rule, level, team):
        g.load(base)
        g.wr('wLinkBattleRules', K[rule])
        g.wr('wLinkBattleLevel', level)
        put('wOTPartyMon1', 'wOTPartyCount', team)
        caller.call('CheckReceivedLinkBattleParty')
        return not caller.out['carry']

    def friend(rule, team):
        g.load(base)
        g.wr('wLinkBattleRules', K[rule])
        put('wOTPartyMon1', 'wOTPartyCount', team)
        caller.call('CheckFriendBattleTeam')
        return not caller.out['carry']

    def expect(what, got, want):
        if got != want:
            fails.append(f'{what}: {"allowed" if got else "refused"}, should be {"allowed" if want else "refused"}')

    six = [mon(s, i) for s, i in (('PIKACHU', 'LEFTOVERS'), ('RATTATA', 'CHARCOAL'), ('PIDGEY', 'MAGNET'),
                                  ('ODDISH', 'MYSTIC_WATER'), ('ZUBAT', 0), ('SENTRET', 0))]
    egg = mon('PIDGEY', egg=True)
    galarian = mon('ARTICUNO', form=K['GALARIAN_FORM'])
    cases = [
        # Standard: 1-6 at level 50, Eggs along, one legendary
        ('Standard', 'six', six, True),
        ('Standard', 'one', six[:1], True),
        ('Standard', 'none', [], False),
        ('Standard', 'seven', six + six[:1], False),
        ('Standard', 'an Egg along', six[:3] + [egg], True),
        ('Standard', 'only an Egg', [egg], False),
        ('Standard', 'one legendary', six[:5] + [mon('ARTICUNO')], True),
        ('Standard', 'one Uber', six[:5] + [mon('MEWTWO')], True),
        ('Standard', 'two legendaries', six[:4] + [mon('ARTICUNO'), mon('ZAPDOS')], False),
        ('Standard', 'a legendary and an Uber', six[:4] + [mon('SUICUNE'), mon('CELEBI')], False),
        ('Standard', 'Galarian Articuno and Zapdos', six[:4] + [galarian, mon('ZAPDOS')], False),
        ('Standard', 'two of a species', [six[0], six[0]], True),
        # Rising Star: three, no Eggs or Ubers, Species and Item Clauses
        ('RisingStar', 'three', six[:3], True),
        ('RisingStar', 'two', six[:2], False),
        ('RisingStar', 'four', six[:4], False),
        ('RisingStar', 'an Egg', six[:2] + [egg], False),
        ('RisingStar', 'Mewtwo', six[:2] + [mon('MEWTWO')], False),
        ('RisingStar', 'a legendary bird', six[:2] + [mon('ZAPDOS')], True),
        ('RisingStar', 'two of a species', [six[0], mon('PIKACHU', 'CHARCOAL'), six[2]], False),
        ('RisingStar', 'two holding one item', [six[0], mon('RATTATA', 'LEFTOVERS'), six[2]], False),
        ('RisingStar', 'two holding nothing', six[3:], True),
        # Unrestricted: anything, at its own level
        ('Unrestricted', 'Ubers and legendaries', [mon('MEWTWO'), mon('CELEBI'), mon('ARTICUNO'), mon('ZAPDOS')], True),
        ('Unrestricted', 'any levels', [mon('PIKACHU', level=5), mon('RATTATA', level=100)], True),
        ('Unrestricted', 'an Egg along', six[:1] + [egg], True),
        # Championship: six, no Eggs
        ('World', 'six', six, True),
        ('World', 'five', six[:5], False),
        ('World', 'six with an Egg', six[:5] + [egg], False),
    ]
    rule = {'Standard': 'LINK_RULE_STANDARD', 'RisingStar': 'LINK_RULE_RISING_STAR',
            'Unrestricted': 'LINK_RULE_UNRESTRICTED', 'World': 'LINK_RULE_WORLD'}
    for fmt, what, team, want in cases:
        expect(f'desk {fmt}, {what}', desk(rule[fmt], team), want)
        if team:  # (a received or Friend Battle team is never empty)
            expect(f'Friend Battle {fmt}, {what}', friend(rule[fmt], team), want)
    expect('desk Random, anything (a team is made for you)', desk('LINK_RULE_RANDOM', [egg]), True)

    # received teams: the level the format normalizes to, or any
    at50 = six[:3]
    expect('received Standard at level 50', received('LINK_RULE_STANDARD', 50, at50), True)
    expect('received Standard with one at 49', received('LINK_RULE_STANDARD', 50,
                                                        at50[:2] + [mon('PIDGEY', level=49)]), False)
    expect('received Standard with two legendaries', received('LINK_RULE_STANDARD', 50,
                                                             [mon('ARTICUNO'), mon('ZAPDOS')]), False)
    expect('received Unrestricted at any levels', received('LINK_RULE_UNRESTRICTED', 0,
                                                          [mon('PIKACHU', level=7), mon('MEWTWO', level=100)]), True)
    expect('received Rising Star at 30', received('LINK_RULE_RISING_STAR', 30,
                                                 [dict(m, level=30) for m in six[:3]]), True)
    expect('received Rising Star, two of a species', received('LINK_RULE_RISING_STAR', 30,
                                                             [dict(m, level=30) for m in (six[0], six[0], six[1])]),
           False)
    # the evasion cap: run checkhit from just before it, evasion +6 (c = 13),
    # and read c where it ends
    stop = g.sym['BattleCommand_checkhit.skip_evasion_cap']
    probe = {}

    def at_stop(_):
        # record c, then return to Caller as a ret would (nothing is pushed
        # between the two labels)
        rf = g.pb.register_file
        probe['c'] = rf.C
        rf.PC = g.m[rf.SP] | g.m[rf.SP + 1] << 8
        rf.SP += 2

    g.pb.hook_register(*stop, at_stop, None)
    for what, link_mode, rules, friend_slot, want in (
            ('a Standard link battle', 1, 'LINK_RULE_STANDARD', 0, 9),
            ('an Unrestricted link battle', 1, 'LINK_RULE_UNRESTRICTED', 0, 9),
            ('a Friend Battle', 0, 'LINK_RULE_UNRESTRICTED', 1, 9),
            ('single player', 0, 'LINK_RULE_STANDARD', 0, 13)):
        g.load(base)
        g.wr('wLinkMode', link_mode)
        g.wr('wLinkBattleRules', K[rules])
        g.wr('wFriendBattleSlot', friend_slot)
        probe.clear()
        caller.call('BattleCommand_checkhit.not_external_acc', B=7, C=13)
        if probe.get('c') != want:
            fails.append(f'evasion +6 in {what} counts as {probe.get("c")}, not {want} (7 is neutral)')
    g.pb.hook_deregister(*stop)

    # the level each format battles at
    for fmt, level in (('LINK_RULE_STANDARD', 50), ('LINK_RULE_RISING_STAR', 30), ('LINK_RULE_UNRESTRICTED', 0)):
        desk(fmt, six[:3])
        got = g.rd('wLinkBattleLevel')
        if got != level:
            fails.append(f'{fmt} battles at level {got}, not {level or "their own"}')

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
