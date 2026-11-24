#!/usr/bin/env python3
"""Check the regional cups in the running game (PyBoy), from a save.

The Rising Star Cup (Route 36 National Park gate):
- while it runs, your party is the three you chose, in that order, at level
  30 and full HP, and the rounds are Bug Catcher Ellis, Picnicker Ruth and
  Cooltrainer Rex, at level 30;
- afterwards your party is back exactly as it was (no experience, nothing
  learned), healed; a loss ends the run there, without blacking out;
- the first win gives Leftovers and records it in wCupRecords, each one
  after a Rare Candy; backing out of choosing changes nothing;
- on a save with an old party species list where the records go, they start
  out clear.

The Kimono Cup (Ecruteak Dance Theatre):
- today's type follows the world clock's day (KimonoCupTypes); a team that
  isn't all that type is turned away;
- the rounds are Kimono Girls Sayo, Zuki and Miki with generated teams of
  3, 3 and 4 Pokemon, all of today's type, different species, at level 50;
- the first win with a type gives its item (Mystic Water for Water) and
  records it, each one after a Big Pearl; it works for the type with the
  fewest sets (Dragon) too.

The choice in the Battle Tower's party menu is made by a hook (the first
three of the party, or as given), and the battles are won or lost by setting
HP in RAM.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_cups.py SAVE.sav
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_wild_mons import Game, rgbasm_values  # noqa: E402

ROUNDS = (('BUG_CATCHER', 'RS_ELLIS'), ('PICNICKER', 'RS_RUTH'), ('COOLTRAINERM', 'RS_REX'))
KIMONO_ROUNDS = (('SAYO', 3), ('ZUKI', 3), ('MIKI', 4))
TYPES = ('NORMAL FIGHTING FLYING POISON GROUND ROCK BUG GHOST STEEL FIRE WATER GRASS ELECTRIC PSYCHIC '
         'ICE DRAGON DARK FAIRY').split()


def kimono_data():
    """The rotation, and each Random Battle species and form's types."""
    src = open(os.path.join(ROOT, 'engine', 'events', 'cups.asm')).read()
    table = src[src.index('KimonoCupTypes:'):src.index('assert_table_length NUM_KIMONO_TYPES')]
    rotation = re.findall(r'\b(' + '|'.join(TYPES) + r')\b', table)
    sets = open(os.path.join(ROOT, 'data', 'link', 'random_battle_sets.asm')).read()
    setpart, prof = sets.split('RandomBattleProfiles:')
    profiles = [tuple(map(int, m)) for m in re.findall(r'db (\d+), (\d+) ; \d+', prof)]
    types = {}
    for sp, form, p in re.findall(r'dp (\w+), (\w+)\n\tdb [^\n]+\n\tdb \w+, \w+, (\d+)', setpart):
        types[sp, form] = {TYPES[i] for i in profiles[int(p)]}
    return rotation, types


def expected_party(cls, tid):
    src = open(os.path.join(ROOT, 'data', 'trainers', 'parties.asm')).read()
    group = src[src.index(f'\tdef_trainer_class {cls}\n'):]
    start = group.index(f'\tdef_trainer {tid}, ')
    group = group[start:group.index('end_trainer', start)]
    return re.findall(r'tr_mon (\d+), (?:"\w+", )?(\w+)', group)


def main():
    save = open(sys.argv[1], 'rb').read()
    parties = {r: expected_party(*r) for r in ROUNDS}
    species = sorted({sp for p in parties.values() for _, sp in p})
    K = rgbasm_values(species + [c for c, _ in ROUNDS] + [t for _, t in ROUNDS] + [
        'GROUP_ROUTE_36_NATIONAL_PARK_GATE', 'MAP_ROUTE_36_NATIONAL_PARK_GATE', 'PARTYMON_STRUCT_LENGTH',
        'EXTSPECIES_MASK', 'LEFTOVERS', 'RARE_CANDY', 'CUPWON_RISING_STAR_F', 'CUP_RECORDS_LENGTH',
        'CUP_RECORDS_MAGIC_1', 'CUP_RECORDS_MAGIC_2', 'EVENT_RISING_STAR_PRIZE_PENDING',
        'MON_LEVEL', 'MON_HP', 'MON_MAXHP', 'MON_EXP', 'MON_SPECIES'], None)
    L = K['PARTYMON_STRUCT_LENGTH']
    g = Game(save)
    g.boot()
    fails = []
    picks = [0, 1, 2]

    # the Battle Tower party menu: choose `picks` (or back out with None)
    bank, addr = g.sym['BT_PartySelect']

    def choose(_):
        rf = g.pb.register_file
        if picks is None:
            rf.F |= 0x10  # carry: backed out
        else:
            g.wr('wBT_PartySelectCounter', len(picks))
            for i, p in enumerate(picks):
                g.wr('wBT_PartySelections', p, i)
            rf.F &= ~0x10
        sp = rf.SP
        rf.SP = sp + 2
        rf.PC = g.m[sp] | (g.m[sp + 1] << 8)
    g.pb.hook_register(bank, addr, choose, None)

    def items(item):
        for pocket in ('Items', 'Medicine', 'Balls'):
            for i in range(g.rd('wNum' + pocket)):
                if g.rd('w' + pocket, 2 * i) == K[item]:
                    return g.rd('w' + pocket, 2 * i + 1)
        return 0

    def party_block():
        a = g.addr('wPartyCount')
        n = g.addr('wPartyMonNicknamesEnd') - a
        return bytes(g.m[1, a + i] for i in range(n))

    def mon(prefix, i, field, n=1):
        b = g.addr(prefix) + i * L + K[field]
        return tuple(g.m[1, b + k] for k in range(n))

    def talk():
        g.warp(K['GROUP_ROUTE_36_NATIONAL_PARK_GATE'], K['MAP_ROUTE_36_NATIONAL_PARK_GATE'], 7, 3)
        g.press('up', 2, 3)
        g.tick(30)

    def until_battle(presses=24):
        for _ in range(presses):
            g.press('a', 40)
            if g.rd('wBattleMode'):
                break
        for _ in range(300):
            if g.rd('wBattleMode'):
                return True
            g.tick(2)
        return False

    def finish(win):
        g.tick(300)
        for i in range(400):
            if i < 20:
                if win:
                    for k in range(g.rd('wOTPartyCount')):
                        g.wr('wOTPartyMon1HP', 0, k * L)
                        g.wr('wOTPartyMon1HP', 0, k * L + 1)
                    g.wr('wEnemyMonHP', 0)
                    g.wr('wEnemyMonHP', 1, 1)
                    g.wr('wBattleMonHP', 3)
                    g.wr('wBattleMonHP', 0xe7, 1)
                    g.wr('wEnemyMonSpeed', 0)
                    g.wr('wEnemyMonSpeed', 1, 1)
                else:
                    for k in range(g.rd('wPartyCount')):
                        g.wr('wPartyMon1HP', 0, k * L)
                        g.wr('wPartyMon1HP', 0, k * L + 1)
                    g.wr('wBattleMonHP', 0)
                    g.wr('wBattleMonHP', 1, 1)
            g.press('a', 20)
            if not g.rd('wBattleMode'):
                break

    def settle():
        for _ in range(120):
            g.tick(30)
            g.press('b', 10)
            if not g.rd('wScriptRunning') and not g.rd('wBattleMode'):
                g.tick(60)
                if not g.rd('wScriptRunning'):
                    return

    def check_round(r, chosen):
        cls, tid = r
        where = f'{tid}'
        if (g.rd('wOtherTrainerClass'), g.rd('wOtherTrainerID')) != (K[cls], K[tid]):
            fails.append((where, f'battled class {g.rd("wOtherTrainerClass")} #{g.rd("wOtherTrainerID")}'))
        got = [(g.rd('wOTPartyMon1Level', i * L), g.rd('wOTPartyMon1Species', i * L)
                | (0x100 if g.rd('wOTPartyMon1Form', i * L) & K['EXTSPECIES_MASK'] else 0))
               for i in range(g.rd('wOTPartyCount'))]
        want = [(int(lv), K[sp]) for lv, sp in parties[r]]
        if got != want:
            fails.append((where, f'their team {got}, not {want}'))
        if g.rd('wPartyCount') != len(chosen):
            fails.append((where, f'your party has {g.rd("wPartyCount")}, not the {len(chosen)} chosen'))
        for k, p in enumerate(chosen):
            if mon('wPartyMon1', k, 'MON_SPECIES') != before_mons[p]:
                fails.append((where, f'your #{k + 1} is not the one chosen'))
            if mon('wPartyMon1', k, 'MON_LEVEL')[0] != 30:
                fails.append((where, f'your #{k + 1} is level {mon("wPartyMon1", k, "MON_LEVEL")[0]}, not 30'))
        if g.rd('wCupLevel') != 30:
            fails.append((where, f'wCupLevel {g.rd("wCupLevel")}'))

    base = g.state()
    before = party_block()
    before_mons = [mon('wPartyMon1', i, 'MON_SPECIES') for i in range(g.rd('wPartyCount'))]

    def compare_party(where):
        after = party_block()
        if after == before:
            return
        # healed is fine: compare all but HP, status and PP
        n = g.rd('wPartyCount')
        if after[0] != before[0]:
            fails.append((where, f'party count {after[0]}, not {before[0]}'))
            return
        start = g.addr('wPartyMon1') - g.addr('wPartyCount')
        healed = set()
        for i in range(n):
            b = start + i * L
            for f, w in (('MON_HP', 2), ('MON_STATUS', 2), ('MON_PP', 4)):
                if f in K:
                    healed |= set(range(b + K[f], b + K[f] + w))
        # (and the cup records, which follow the party count)
        records = set(range(g.addr('wCupRecords') - g.addr('wPartyCount'),
                            g.addr('wCupRecordsMagic') + 2 - g.addr('wPartyCount')))
        diff = [i for i in range(len(before)) if before[i] != after[i] and i not in healed | records]
        if diff:
            fails.append((where, f'party changed at offsets {diff[:8]}'))

    K.update(rgbasm_values(['MON_STATUS', 'MON_PP'], None))

    def run(expect_item, before_count):
        talk()
        for k, r in enumerate(ROUNDS):
            if not until_battle(30 if k == 0 else 20):
                fails.append(('the cup', f'round {k + 1} did not start'))
                return
            check_round(r, picks)
            finish(True)
        settle()
        compare_party(f'after winning (for the {expect_item})')
        if g.rd('wCupLevel'):
            fails.append(('the cup', 'wCupLevel still set afterwards'))
        if items(expect_item) != before_count + 1:
            fails.append(('the cup', f'{expect_item}: {before_count} -> {items(expect_item)}, not +1'))

    # win twice: Leftovers, then a Rare Candy
    g.load(base)
    run('LEFTOVERS', items('LEFTOVERS'))
    rec = g.rd('wCupRecords')
    if not (rec >> K['CUPWON_RISING_STAR_F']) & 1:
        fails.append(('records', 'the first win was not recorded'))
    run('RARE_CANDY', items('RARE_CANDY'))

    # choose the 3rd, 1st and 5th: that order
    g.load(base)
    picks = [2, 0, 4]
    talk()
    if until_battle(30):
        check_round(ROUNDS[0], picks)
        finish(False)
        settle()
    else:
        fails.append(('another choice', 'round 1 did not start'))

    # losing round one
    picks = [0, 1, 2]
    g.load(base)
    talk()
    if until_battle(30):
        finish(False)
        settle()
        if (g.rd('wMapGroup'), g.rd('wMapNumber')) != (K['GROUP_ROUTE_36_NATIONAL_PARK_GATE'],
                                                       K['MAP_ROUTE_36_NATIONAL_PARK_GATE']):
            fails.append(('losing', 'blacked out (left the gate)'))
        compare_party('after losing')
        if items('LEFTOVERS') != 0 and g.rd('wCupRecords') & (1 << K['CUPWON_RISING_STAR_F']):
            fails.append(('losing', 'a loss was recorded as a win'))
    else:
        fails.append(('losing', 'round 1 did not start'))

    # backing out
    picks = None
    g.load(base)
    talk()
    for _ in range(12):
        g.press('a', 40)
    settle()
    if g.rd('wBattleMode') or party_block() != before:
        fails.append(('backing out', 'something changed'))

    # an old party species list where the records go
    picks = [0, 1, 2]
    g.load(base)
    for i, v in enumerate((0x06, 0x41, 0x5e, 0x83, 0x44, 0x87, 0xff)):
        g.wr('wCupRecords', v, i)
    run('LEFTOVERS', items('LEFTOVERS'))
    rec = [g.rd('wCupRecords', i) for i in range(K['CUP_RECORDS_LENGTH'])]
    magic = (g.rd('wCupRecordsMagic'), g.rd('wCupRecordsMagic', 1))
    if rec != [1 << K['CUPWON_RISING_STAR_F']] + [0] * (K['CUP_RECORDS_LENGTH'] - 1):
        fails.append(('old save', f'records {rec} after one win'))
    if magic != (K['CUP_RECORDS_MAGIC_1'], K['CUP_RECORDS_MAGIC_2']):
        fails.append(('old save', 'records not marked as set up'))

    # the Kimono Cup
    rotation, set_types = kimono_data()
    if len(rotation) != 18 or len(set(rotation)) != 18:
        fails.append(('kimono', f'the rotation {rotation} is not the 18 types once each'))
    KK = rgbasm_values(sorted({n for key in set_types for n in key}) + ['SPECIESFORM_MASK', 'KIMONO_GIRL', 'SAYO', 'ZUKI', 'MIKI', 'GROUP_DANCE_THEATRE',
                                            'MAP_DANCE_THEATRE', 'MYSTIC_WATER', 'DRAGON_FANG', 'BIG_PEARL',
                                            'SQUIRTLE', 'DRATINI', 'RATTATA', 'WATER', 'DRAGON'], None)
    K.update(KK)
    by_value = {}
    for sp, form in set_types:
        by_value[KK[sp], KK[form]] = (sp, form)

    def kimono_talk(day, species):
        g.wr('wRTCDayLo', day)
        for i in range(g.rd('wPartyCount')):
            g.wr('wPartyMon1Species', K[species], i * L)
            g.wr('wPartyMon1Form', g.rd('wPartyMon1Form', i * L) & ~K['EXTSPECIES_MASK'], i * L)
        g.warp(K['GROUP_DANCE_THEATRE'], K['MAP_DANCE_THEATRE'], 4, 13)
        g.press('up', 2, 3)
        g.tick(30)

    def kimono_round(k, kind):
        name, size = KIMONO_ROUNDS[k]
        where = f'kimono {kind} round {k + 1}'
        if (g.rd('wOtherTrainerClass'), g.rd('wOtherTrainerID')) != (K['KIMONO_GIRL'], K[name]):
            fails.append((where, f'battled class {g.rd("wOtherTrainerClass")} #{g.rd("wOtherTrainerID")}'))
        n = g.rd('wOTPartyCount')
        team = []
        for i in range(n):
            form = g.rd('wOTPartyMon1Form', i * L)
            sp = g.rd('wOTPartyMon1Species', i * L) | (0x100 if form & K['EXTSPECIES_MASK'] else 0)
            team.append(by_value.get((sp, form & K['SPECIESFORM_MASK'] & ~K['EXTSPECIES_MASK']), (sp, form)))
            if g.rd('wOTPartyMon1Level', i * L) != 50:
                fails.append((where, f'their #{i + 1} is level {g.rd("wOTPartyMon1Level", i * L)}'))
            hp = (g.rd('wOTPartyMon1HP', i * L) << 8) | g.rd('wOTPartyMon1HP', i * L + 1)
            maxhp = (g.rd('wOTPartyMon1MaxHP', i * L) << 8) | g.rd('wOTPartyMon1MaxHP', i * L + 1)
            if i and (not hp or hp != maxhp):
                fails.append((where, f'their #{i + 1} HP {hp}/{maxhp}'))
        if n != size:
            fails.append((where, f'their team has {n}, not {size}'))
        if len({s for s, _ in team}) != len(team):
            fails.append((where, f'their team repeats a species: {team}'))
        off = [s for s in team if kind not in set_types.get(s, ())]
        if off:
            fails.append((where, f'not {kind}: {off} (team {team})'))
        levels = [g.rd('wPartyMon1Level', i * L) for i in range(g.rd('wPartyCount'))]
        if levels != [50, 50, 50]:
            fails.append((where, f'your team is at levels {levels}'))

    def kimono_run(day, species, kind, prize):
        party = party_block()
        before = items(prize)
        kimono_talk(day, species)
        for k in range(3):
            if not until_battle(30 if k == 0 else 20):
                fails.append((f'kimono {kind}', f'round {k + 1} did not start'))
                return
            kimono_round(k, kind)
            finish(True)
        settle()
        if items(prize) != before + 1:
            fails.append((f'kimono {kind}', f'{prize}: {before} -> {items(prize)}, not +1'))
        if g.rd('wCupLevel') or g.rd('wCupFoeSize'):
            fails.append((f'kimono {kind}', 'cup state left set afterwards'))
        return party

    water_day = rotation.index('WATER')
    dragon_day = rotation.index('DRAGON') + 18  # (the same type, 18 days on)
    picks = [0, 1, 2]
    g.load(base)
    kimono_run(water_day, 'SQUIRTLE', 'WATER', 'MYSTIC_WATER')
    bit = K['WATER']
    if not (g.rd('wCupRecords', 1 + bit // 8) >> (bit % 8)) & 1:
        fails.append(('kimono', 'the Water win was not recorded'))
    kimono_run(water_day, 'SQUIRTLE', 'WATER', 'BIG_PEARL')
    kimono_run(dragon_day, 'DRATINI', 'DRAGON', 'DRAGON_FANG')
    won = sum(bin(g.rd('wCupRecords', i)).count('1') for i in (1, 2, 3))
    if won != 2:
        fails.append(('kimono', f'{won} types recorded, not 2'))

    # the wrong type: turned away
    g.load(base)
    kimono_talk(water_day, 'RATTATA')
    if until_battle(14):
        fails.append(('kimono', 'a Normal team entered on a Water day'))
    settle()

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
