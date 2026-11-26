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
- the desk tells a player who has already won with today's type which new
  type comes next and in how many days (KimonoCupNextNew, from the saved
  wins, wrapping round the rotation), and one who has won with all 18 that
  they have; a new type for you adds nothing;
- the first win with a type gives its item (Mystic Water for Water) and
  records it, each one after a Big Pearl; it works for the type with the
  fewest sets (Dragon) too.

The Dragon Masters Cup (Blackthorn, the dragon house), after the Rising
Badge:
- the whole party enters (at least one Dragon type) at level 50; a party
  without one is turned away;
- the rounds are Dragon Tamers Erick and Aegon, then Clair (her gym team),
  their own teams at level 50;
- the first win gives a Dragon Scale and records it, each one after a PP Up.

The Rental Cup (Goldenrod Department Store 6F) supplies both sides with
three generated level-50 Pokémon. The original party returns after losses
and wins, and a full Bag leaves the first prize at the desk. "Look" shows
each rental in the summary screen (Down to the next), at level 50, and the
team entered afterwards is the one looked at.

The World Championship opens after Red. Seven visiting trainers form an
eight-person bracket with the player, using six level-50 Pokémon each.
Test the draw, advancement, a semifinal loss and retry, and both prizes;
and the bracket screen's record (wWorldCupDraw, wWorldCupResults): every
entrant's wins and where they went out, as an independent model of the
bracket (bracket.py's winner) has them, with the rest of the bracket played
out after you lose, and the closing screen naming that champion.

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
sys.path.insert(0, os.path.join(ROOT, 'utils', 'world_cup'))
from bracket import winner  # noqa: E402

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
        'EXTSPECIES_MASK', 'LEFTOVERS', 'RARE_CANDY', 'POKE_BALL', 'ENGINE_RISING_STAR_CANDY',
        'ENGINE_KURT_MAKING_BALLS', 'CUPWON_RISING_STAR_F', 'CUP_RECORDS_LENGTH',
        'CUP_RECORDS_MAGIC_1', 'CUP_RECORDS_MAGIC_2', 'EVENT_RISING_STAR_PRIZE_PENDING',
        'MON_LEVEL', 'MON_HP', 'MON_MAXHP', 'MON_EXP', 'MON_SPECIES', 'TACKLE'], None)
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

    def finish(win, *, faint_party=False):
        menu = []
        g.pb.hook_register(*g.sym['LoadBattleMenu'], menu.append, True)
        for _ in range(40):
            if menu:
                break
            g.press('a', 45)
        g.pb.hook_deregister(*g.sym['LoadBattleMenu'])
        assert menu, 'the battle did not show its command menu'
        g.tick(45)
        if win or faint_party:
            def force_faints(_):
                party, active = ('wOTParty', 'wEnemyMonHP') if win else ('wParty', 'wBattleMonHP')
                for i in range(g.rd(party + 'Count')):
                    g.wr(party + 'Mon1HP', 0, i * L)
                    g.wr(party + 'Mon1HP', 0, i * L + 1)
                g.wr(active, 0)
                g.wr(active, 0, 1)
                if win:
                    g.wr('wBattleMonHP', 3)
                    g.wr('wBattleMonHP', 0xe7, 1)

            g.wr('wBattleMonMoves', K['TACKLE'])
            g.wr('wBattleMonPP', 35)
            g.pb.hook_register(*g.sym['ResolveFaints'], force_faints, None)
        else:
            for button in ('down', 'right', 'a', 'down'):
                g.press(button, 40)
        for _ in range(260):
            if not g.rd('wBattleMode'):
                break
            g.press('a', 35)
        if win or faint_party:
            g.pb.hook_deregister(*g.sym['ResolveFaints'])
        assert not g.rd('wBattleMode'), 'the battle did not finish'

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

    def compare_party(where, ref=None):
        before_ = before if ref is None else ref
        after = party_block()
        if after == before_:
            return
        # healed is fine: compare all but HP, status and PP
        n = g.rd('wPartyCount')
        if after[0] != before_[0]:
            fails.append((where, f'party count {after[0]}, not {before_[0]}'))
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
        diff = [i for i in range(len(before_)) if before_[i] != after[i] and i not in healed | records]
        if diff:
            fails.append((where, f'party changed at offsets {diff[:8]}'))

    K.update(rgbasm_values(['MON_STATUS', 'MON_PP'], None))

    K.update(rgbasm_values(['MAX_ITEM_STACK', 'MAX_ITEMS', 'BIG_NUGGET'], None))

    def fill_items():
        g.wr('wNumItems', K['MAX_ITEMS'])
        for i in range(K['MAX_ITEMS']):
            g.wr('wItems', K['BIG_NUGGET'], 2 * i)
            g.wr('wItems', K['MAX_ITEM_STACK'], 2 * i + 1)
        g.wr('wItems', 0xff, 2 * K['MAX_ITEMS'])

    def free_item_slot():
        n = K['MAX_ITEMS'] - 1
        g.wr('wNumItems', n)
        g.wr('wItems', 0xff, 2 * n)

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

    # win four times: Leftovers, then a Rare Candy, then (the same day) a Poke
    # Ball, and the next day a Rare Candy again
    candy_bit = 1 << (K['ENGINE_RISING_STAR_CANDY'] - K['ENGINE_KURT_MAKING_BALLS'])  # (in wDailyFlags)

    def new_day():
        g.wr('wDailyFlags', g.rd('wDailyFlags') & ~candy_bit)

    g.load(base)
    new_day()
    run('LEFTOVERS', items('LEFTOVERS'))
    rec = g.rd('wCupRecords')
    if not (rec >> K['CUPWON_RISING_STAR_F']) & 1:
        fails.append(('records', 'the first win was not recorded'))
    run('RARE_CANDY', items('RARE_CANDY'))
    if not g.rd('wDailyFlags') & candy_bit:
        fails.append(('daily candy', "today's Rare Candy was not marked"))
    run('POKE_BALL', items('POKE_BALL'))
    new_day()
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

    talked = {}

    def kimono_talk(day, species):
        g.wr('wRTCDayLo', day)
        for i in range(g.rd('wPartyCount')):
            g.wr('wPartyMon1Species', K[species], i * L)
            g.wr('wPartyMon1Form', g.rd('wPartyMon1Form', i * L) & ~K['EXTSPECIES_MASK'], i * L)
        talked['party'] = party_block()  # (the party the cup must give back)
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

    def kimono_run(day, species, kind, prize=None):
        party = party_block()
        before = items(prize) if prize else None
        kimono_talk(day, species)
        for k in range(3):
            if not until_battle(30 if k == 0 else 20):
                fails.append((f'kimono {kind}', f'round {k + 1} did not start'))
                return
            kimono_round(k, kind)
            finish(True)
        settle()
        compare_party(f'kimono {kind} after winning', talked['party'])
        if prize and items(prize) != before + 1:
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

    # A full Bag records the win and preserves the prize after today's type changes.
    K.update(rgbasm_values(['CUP_KIMONO_PRIZE_OFFSET'], None))
    g.load(base)
    fill_items()
    kimono_run(water_day, 'SQUIRTLE', 'WATER')
    prize = K['CUP_KIMONO_PRIZE_OFFSET']
    if not g.rd('wCupRecords', 1 + bit // 8) & (1 << (bit % 8)):
        fails.append(('kimono full Bag', 'the win was lost'))
    if g.rd('wCupRecords', prize) != K['MYSTIC_WATER']:
        fails.append(('kimono full Bag', 'the reward was lost'))
    free_item_slot()
    g.wr('wRTCDayLo', water_day + 1)
    g.press('a', 50)
    settle()
    if g.rd('wCupRecords', prize) or items('MYSTIC_WATER') != 1:
        fails.append(('kimono full Bag', 'could not claim yesterday’s prize without a rematch'))

    # the wrong type: turned away
    g.load(base)
    kimono_talk(water_day, 'RATTATA')
    if until_battle(14):
        fails.append(('kimono', 'a Normal team entered on a Water day'))
    settle()

    # the way to all 18 types (KimonoCupNextNew), from the saved wins
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from test_friend_records import Caller
    KT = rgbasm_values(rotation, None)
    g.load(base)
    caller = Caller(g)
    caller.call('CupCheckRecords')

    def letters(s):
        # as the game names a type ("Water"): A-Z from $80, a-z from $a0
        s = s.capitalize()
        return bytes(0x80 + ord(c) - ord('A') if c.isupper() else 0xa0 + ord(c) - ord('a') for c in s)

    def next_new(day, won):
        for i in (1, 2, 3):
            g.wr('wCupRecords', 0, i)
        for name in won:
            v = KT[name]
            g.wr('wCupRecords', g.rd('wCupRecords', 1 + v // 8) | 1 << (v % 8), 1 + v // 8)
        g.wr('wRTCDayLo', day)
        caller.call('KimonoCupNextNew')
        days = g.m[g.sym['hScriptVar'][1]]
        name = bytes(g.rd('wStringBuffer4', i) for i in range(8)).split(b'\x53', 1)[0]  # (@ ends it)
        return days, name

    cases = [  # (day, types won, days to the next new type, its name)
        (water_day, [], 0, None),
        (water_day, ['WATER'], 1, rotation[(water_day + 1) % 18]),
        (water_day, ['WATER', rotation[(water_day + 1) % 18]], 2, rotation[(water_day + 2) % 18]),
        (17 + 18, [r for r in rotation if r != rotation[0]], 1, rotation[0]),  # (round to the start)
        (5, list(rotation), 18, None),
    ]
    for day, won, want_days, want_name in cases:
        days, name = next_new(day, won)
        if days != want_days or (want_name and name != letters(want_name)):
            fails.append(('kimono next type', f'day {day}, {len(won)} won: {days} days, {name}, '
                                              f'not {want_days} days, {want_name}'))
    # and at the desk: today's type won, the next one named
    g.load(base)
    caller.call('CupCheckRecords')
    next_new(water_day, ['WATER'])
    kimono_talk(water_day, 'SQUIRTLE')
    seen = False
    for _ in range(8):
        screen = bytes(g.rd('wTilemap', i) for i in range(20 * 18))
        if letters(rotation[(water_day + 1) % 18]) in screen:
            seen = True
            break
        g.press('a', 40)
    if not seen:
        fails.append(('kimono next type', 'the desk did not name the next new type'))
    settle()

    # the Dragon Masters Cup
    KD = rgbasm_values(['DRAGON_TAMER', 'ERICK', 'AEGON', 'CLAIR', 'GROUP_BLACKTHORN_DRAGON_SPEECH_HOUSE',
                        'MAP_BLACKTHORN_DRAGON_SPEECH_HOUSE', 'DRAGON_SCALE', 'PP_UP', 'CUPWON_DRAGON_F'], None)
    K.update(KD)
    DRAGON_ROUNDS = (('DRAGON_TAMER', 'ERICK'), ('DRAGON_TAMER', 'AEGON'), ('CLAIR', 1))

    def dragon_talk(species, badge=True):
        g.wr('wJohtoBadges', 0xff if badge else 0x7f)  # (the Rising Badge is the last)
        for i in range(g.rd('wPartyCount')):
            g.wr('wPartyMon1Species', K[species[i] if i < len(species) else 'RATTATA'], i * L)
            g.wr('wPartyMon1Form', g.rd('wPartyMon1Form', i * L) & ~K['EXTSPECIES_MASK'], i * L)
        talked['party'] = party_block()  # (the party the cup must give back)
        g.warp(K['GROUP_BLACKTHORN_DRAGON_SPEECH_HOUSE'], K['MAP_BLACKTHORN_DRAGON_SPEECH_HOUSE'], 5, 3)
        g.press('up', 2, 3)
        g.tick(30)

    def dragon_run(prize):
        before = items(prize)
        party = party_block()
        dragon_talk(['DRATINI'])
        for k, (cls, tid) in enumerate(DRAGON_ROUNDS):
            where = f'dragon round {k + 1}'
            if not until_battle(30 if k == 0 else 20):
                fails.append((where, 'did not start'))
                return
            want = (K[cls], K[tid] if isinstance(tid, str) else tid)
            if (g.rd('wOtherTrainerClass'), g.rd('wOtherTrainerID')) != want:
                fails.append((where, f'battled class {g.rd("wOtherTrainerClass")} #{g.rd("wOtherTrainerID")}'))
            theirs = [g.rd('wOTPartyMon1Level', i * L) for i in range(g.rd('wOTPartyCount'))]
            ours = [g.rd('wPartyMon1Level', i * L) for i in range(g.rd('wPartyCount'))]
            if set(theirs) != {50} or set(ours) != {50} or len(ours) != len(before_mons):
                fails.append((where, f'levels: theirs {theirs}, yours {ours}'))
            finish(True)
        settle()
        compare_party('dragon after winning', talked['party'])
        if items(prize) != before + 1:
            fails.append(('dragon', f'{prize}: {before} -> {items(prize)}, not +1'))
        return party

    g.load(base)
    dragon_run('DRAGON_SCALE')
    if not (g.rd('wCupRecords') >> K['CUPWON_DRAGON_F']) & 1:
        fails.append(('dragon', 'the win was not recorded'))
    dragon_run('PP_UP')

    g.load(base)
    dragon_talk([])
    if until_battle(14):
        fails.append(('dragon', 'a party without a Dragon type entered'))
    settle()

    g.load(base)
    dragon_talk(['DRATINI'], badge=False)
    if until_battle(14):
        fails.append(('dragon', 'entered without the Rising Badge'))
    settle()

    K.update(rgbasm_values(['GROUP_GOLDENROD_DEPT_STORE_6F', 'MAP_GOLDENROD_DEPT_STORE_6F',
                            'RENTAL_CUP_TEAM_SIZE', 'CUPWON_RENTAL_F', 'BOTTLE_CAP',
                            'EVENT_RENTAL_CUP_PRIZE_PENDING', 'SCHOOLBOY', 'JACK1',
                            'PICNICKER', 'GINA1', 'COOLTRAINERM', 'RS_REX', 'MON_EVS'], None))
    rental_map = (K['GROUP_GOLDENROD_DEPT_STORE_6F'], K['MAP_GOLDENROD_DEPT_STORE_6F'])

    def rental_talk():
        g.warp(*rental_map, 8, 3)
        g.face('up')

    def rental_team(prefix):
        team = []
        for i in range(g.rd(prefix + 'Count')):
            kind = mon(prefix + 'Mon1', i, 'MON_SPECIES')[0]
            form = g.rd(prefix + 'Mon1Form', i * L)
            species = kind | (0x100 if form & K['EXTSPECIES_MASK'] else 0)
            team.append((species, form & K['SPECIESFORM_MASK'] & ~K['EXTSPECIES_MASK']))
            if mon(prefix + 'Mon1', i, 'MON_LEVEL') != (50,):
                fails.append(('Rental level', f'{prefix} #{i + 1} was not level 50'))
            if any(mon(prefix + 'Mon1', i, 'MON_EVS', 6)):
                fails.append(('Rental EVs', f'{prefix} #{i + 1} inherited trainer EVs'))
        if len(team) != K['RENTAL_CUP_TEAM_SIZE'] or len({s for s, _ in team}) != len(team):
            fails.append(('Rental draw', f'invalid team {team}'))
        if not all(entry in by_value for entry in team):
            fails.append(('Rental draw', f'team outside the rental sets {team}'))
        return team

    # Look: each rental in the summary screen, then enter with them
    g.load(base)
    rental_talk()
    LOOK = bytes([0x8b, 0xae, 0xae, 0xaa])  # "Look", on the desk's menu
    for _ in range(20):
        if LOOK in bytes(g.rd('wTilemap', i) for i in range(20 * 18)):
            break
        g.press('a', 40)
    g.tick(20)

    def map_pals():
        a = g.sym['wBGPals2'][1]
        return bytes(g.m[5, a + k] for k in range(7 * 8))  # (the map's, not the text box's)
    pals_before = map_pals()
    g.press('down', 20)
    g.press('a', 90)
    looked = []
    for _ in range(3):
        looked.append((g.rd('wTempMonSpecies'), g.rd('wTempMonLevel')))
        g.press('down', 60)
    want = [(g.rd('wOTPartyMon1Species', i * L), 50) for i in range(3)]
    if looked != want:
        fails.append(('Rental look', f'summary showed {looked}, not {want}'))
    # Down past the last (with a party of six, more than the three rentals)
    # stays on it (GetStorageBoxMon once counted the OT party as yours)
    if (g.rd('wTempMonSpecies'), g.rd('wTempMonLevel')) != want[-1] or g.rd('wPartyCount') <= 3:
        fails.append(('Rental look', f'past the last rental: {g.rd("wTempMonSpecies")}, party {g.rd("wPartyCount")}'))
    g.press('b', 90)
    for _ in range(10):
        if LOOK in bytes(g.rd('wTilemap', i) for i in range(20 * 18)):
            break
        g.press('a', 40)
    if map_pals() != pals_before:
        fails.append(('Rental look', "the map's colors weren't restored afterwards"))
    assert until_battle(35), 'Rental Cup did not start after looking'
    entered = [g.rd('wPartyMon1Species', i * L) for i in range(3)]
    if entered != [s for s, _ in want]:
        fails.append(('Rental look', f'entered {entered}, not the rentals looked at {want}'))
    finish(False)
    settle()

    g.load(base)
    rental_talk()
    assert until_battle(35), 'Rental Cup did not start'
    rental_team('wParty')
    rental_team('wOTParty')
    finish(False)
    settle()
    compare_party('Rental after forfeiting')
    assert (g.rd('wMapGroup'), g.rd('wMapNumber')) == rental_map and not g.rd('wCupLevel')

    fill_items()
    home_team = None
    for i, (cls, trainer) in enumerate((('SCHOOLBOY', 'JACK1'), ('PICNICKER', 'GINA1'), ('COOLTRAINERM', 'RS_REX'))):
        assert until_battle(35 if not i else 20), f'Rental Cup round {i + 1} did not start'
        assert (g.rd('wOtherTrainerClass'), g.rd('wOtherTrainerID')) == (K[cls], K[trainer])
        got = rental_team('wParty')
        assert home_team in (None, got), 'the player’s rentals changed between rounds'
        home_team = got
        rental_team('wOTParty')
        finish(True)
    settle()
    compare_party('Rental after winning')
    assert not g.rd('wCupLevel') and not g.rd('wCupFoeSize')
    assert g.rd('wCupRecords') & (1 << K['CUPWON_RENTAL_F'])
    prize_byte, prize_bit = divmod(K['EVENT_RENTAL_CUP_PRIZE_PENDING'], 8)
    assert g.rd('wEventFlags', prize_byte) & (1 << prize_bit)
    free_item_slot()
    g.press('a', 50)
    settle()
    assert not g.rd('wEventFlags', prize_byte) & (1 << prize_bit) and items('BOTTLE_CAP') == 1

    roster = (('ASH_T', 1), ('DRAKE_T', 1), ('LEAF', 1), ('BLUE', 2),
              ('CHAMPION', 'LANCE'), ('CYNTHIA', 2), ('RED', 1))
    K.update(rgbasm_values([cls for cls, _ in roster] + [
        'LANCE', 'ABILITYPATCH', 'CUPWON_WORLD_F', 'MON_IS_EGG_F', 'NAME_LENGTH', 'MON_NAME_LENGTH',
        'GROUP_INDIGO_PLATEAU', 'MAP_INDIGO_PLATEAU', 'GROUP_INDIGO_PLATEAU_POKECENTER_1F',
        'MAP_INDIGO_PLATEAU_POKECENTER_1F',
        'EVENT_GOT_MYSTICTICKET_FROM_RED', 'EVENT_WORLD_CUP_PRIZE_PENDING'], None))
    world_map = (K['GROUP_INDIGO_PLATEAU_POKECENTER_1F'], K['MAP_INDIGO_PLATEAU_POKECENTER_1F'])
    world_win = 1 << K['CUPWON_WORLD_F']

    def event(name):
        byte, bit = divmod(K[name], 8)
        return byte, 1 << bit

    def world_talk():
        g.warp(K['GROUP_INDIGO_PLATEAU'], K['MAP_INDIGO_PLATEAU'], 11, 6)
        g.face('up')
        g.press('up', 90)
        assert (g.rd('wMapGroup'), g.rd('wMapNumber')) == world_map
        g.press('up', 20)
        g.face('left')
        for _ in range(3):
            g.press('left', 20)
        assert (g.rd('wXCoord'), g.rd('wYCoord')) == (6, 12)

    g.load(base)
    # Support the same fixture as the other cups, which may have five Pokémon.
    count = g.rd('wPartyCount')
    for i in range(count, 6):
        for field, length in (('wPartyMon1', L), ('wPartyMonOTs', K['NAME_LENGTH']),
                              ('wPartyMonNicknames', K['MON_NAME_LENGTH'])):
            for j in range(length):
                g.wr(field, g.rd(field, j), i * length + j)
    g.wr('wPartyCount', 6)
    before = party_block()
    red_byte, red_flag = event('EVENT_GOT_MYSTICTICKET_FROM_RED')
    prize_byte, prize_flag = event('EVENT_WORLD_CUP_PRIZE_PENDING')
    g.wr('wEventFlags', g.rd('wEventFlags', red_byte) & ~red_flag, red_byte)
    g.wr('wEventFlags', g.rd('wEventFlags', prize_byte) & ~prize_flag, prize_byte)
    world_talk()
    assert not until_battle(12), 'registration opened before Red'
    settle()

    g.wr('wEventFlags', g.rd('wEventFlags', red_byte) | red_flag, red_byte)
    g.wr('wCupRecords', g.rd('wCupRecords') & ~world_win)
    for count, egg in ((5, False), (6, True)):
        g.wr('wPartyCount', count)
        egg_offset = 5 * L
        original = g.rd('wPartyMon1IsEgg', egg_offset)
        if egg:
            g.wr('wPartyMon1IsEgg', original | (1 << K['MON_IS_EGG_F']), egg_offset)
        assert not until_battle(12), 'registered without six eligible Pokémon'
        settle()
        assert not g.rd('wCupLevel')
        g.wr('wPartyMon1IsEgg', original, egg_offset)
    g.wr('wPartyCount', 6)

    CUP_NAMES = ['Ash', 'Drake', 'Green', 'Blue', 'Lance', 'Cynthia', 'Red']  # (WorldCupTrainers)

    def tiles(s):
        out = []
        for ch in s:
            if ch == ':':
                out.append(0xbd)
            elif ch.isupper():
                out.append(0x80 + ord(ch) - ord('A'))
            else:
                out.append(0xa0 + ord(ch) - ord('a'))
        return bytes(out)

    def expected_results(draw, seed, rounds_won):
        # the whole bracket: you win your first rounds_won matches, then lose
        # (or are champion); every other match is the model's
        res = {i: [0, False] for i in range(8)}
        br, r = list(draw), 0
        while len(br) > 1:
            first, new = 8 - len(br), []
            for k in range(len(br) // 2):
                b, c = br[2 * k:2 * k + 2]
                if 0 in (b, c):
                    w = 0 if r < rounds_won else max(b, c)
                else:
                    w = winner(seed, first + k, b, c)
                res[w][0] += 1
                res[c if w == b else b][1] = True
                new.append(w)
            br, r = new, r + 1
        return res

    def world_run(rounds, lose=False):
        bracket = None
        for i in range(rounds):
            assert until_battle(45), f'World Championship round {i + 1} did not start'
            assert g.rd('wWorldCupRoundSize') == 8 >> i
            actual = [g.rd('wWorldCupBracket', j) for j in range(8 >> i)]
            if bracket is None:
                assert actual[0] == 0 and sorted(actual) == list(range(8)), actual
                bracket = actual
                bracket_draw = list(actual)
            assert bracket == actual
            cls, tid = roster[bracket[1] - 1]
            assert (g.rd('wOtherTrainerClass'), g.rd('wOtherTrainerID')) == (K[cls], K[tid] if isinstance(tid, str) else tid)
            for team in ('wParty', 'wOTParty'):
                assert g.rd(team + 'Count') == 6
                assert all(g.rd(team + 'Mon1Level', j * L) == 50 for j in range(6))
            seed = g.rd('wWorldCupSeed') | g.rd('wWorldCupSeed', 1) << 8
            first = 8 - len(bracket) + 1  # (this round's first trainers' match: WorldCupWinner)
            bracket = [0] + [winner(seed, first + (j - 2) // 2, *bracket[j:j + 2])
                             for j in range(2, len(bracket), 2)]
            if i == 0:
                draw, draw_seed = list(bracket_draw), seed
            loss = lose and i == rounds - 1
            finish(not loss, faint_party=loss)
        # the closing bracket screen names the champion
        want = expected_results(draw, draw_seed, rounds - 1 if lose else rounds)
        champ = [k for k, (w, _) in want.items() if w == 3]
        champ_name = (bytes(g.rd('wPlayerName', j) for j in range(8)).split(b'\x53')[0] if champ == [0]
                      else tiles(CUP_NAMES[champ[0] - 1]) if len(champ) == 1 else None)
        shown = None
        for _ in range(60):
            row = bytes(g.rd('wTilemap', 16 * 20 + j) for j in range(20))
            if tiles('Champion:') in row:
                shown = row
                if os.environ.get('LE_SHOTS'):
                    g.tick(30)
                    g.pb.tick(1, True)
                    g.pb.screen.image.save(os.path.join(os.environ['LE_SHOTS'], f'world_bracket_{rounds}{"_lost" if lose else ""}.png'))
                break
            if not g.rd('wScriptRunning') and not g.rd('wBattleMode'):
                break  # (over, and no screen: don't talk to the desk again)
            g.press('a', 40)
        if shown is None or champ_name is None or shown[12:12 + len(champ_name)] != champ_name:
            fails.append(('world bracket', f'closing screen {shown}, not champion {champ}'))
        # the record behind it
        got_draw = [g.m[2, g.addr('wWorldCupDraw') + j] for j in range(8)]
        got = [g.m[2, g.addr('wWorldCupResults') + j] for j in range(8)]
        exp = [want[k][0] | (0x80 if want[k][1] else 0) for k in range(8)]
        if got_draw != draw or got != exp:
            fails.append(('world bracket', f'draw {got_draw} results {got}, not {draw} {exp}'))
        settle()
        compare_party('World Championship after finishing')
        assert (g.rd('wMapGroup'), g.rd('wMapNumber')) == world_map and not g.rd('wCupLevel')

    world_run(2, lose=True)
    assert not g.rd('wCupRecords') & world_win
    fill_items()
    world_run(3)
    assert g.rd('wCupRecords') & world_win
    assert g.rd('wEventFlags', prize_byte) & prize_flag and not items('ABILITYPATCH')
    g.manual_save()
    saved = g.sram()
    g.pb.stop(save=False)
    g = Game(saved)
    g.boot()
    assert g.rd('wCupRecords') & world_win and g.rd('wEventFlags', prize_byte) & prize_flag
    world_talk()
    free_item_slot()
    g.press('a', 50)
    settle()
    assert not g.rd('wEventFlags', prize_byte) & prize_flag and items('ABILITYPATCH') == 1
    # Move the claimed prize to the first slot before freeing another slot.
    g.wr('wItems', K['ABILITYPATCH'])
    g.wr('wItems', 1, 1)
    free_item_slot()
    world_run(3)
    assert items('BOTTLE_CAP') == 1 and items('ABILITYPATCH') == 1

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
