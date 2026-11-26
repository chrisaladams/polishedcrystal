#!/usr/bin/env python3
"""Check the Orange League in the running game (PyBoy), from a save:

- the Surf course and ice climb unlock the Cissy and Danny battles;
- choose matching types for Rudy's three rounds and two partners for Luana
  using the party menu, then check that the full party is restored;
- Drake won't battle until all four are beaten; then he battles with his
  team, and winning gives the Winner's Trophy and 3 Bottle Caps, once;
- afterwards each of them can be battled again.

The battles are won by setting the opposing team's HP to 0 in RAM, so this
checks the scripts, not the battles themselves.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_orange_league.py SAVE.sav
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_wild_mons import Game, rgbasm_values  # noqa: E402

LEADERS = (  # tag, map, where to stand, which way to face, class, badge flag
    ('Cissy', 'WARM_BEACH', 9, 22, 'up', 'CISSY_T', 'EVENT_BEAT_ORANGE_CREW_CISSY'),
    ('Danny', 'ROCKY_BEACH', 22, 27, 'right', 'DANNY_T', 'EVENT_BEAT_ORANGE_CREW_DANNY'),
    ('Rudy', 'BEAUTIFUL_BEACH', 16, 19, 'up', 'RUDY_T', 'EVENT_BEAT_ORANGE_CREW_RUDY'),
    ('Luana', 'VALENCIA_HOUSE', 5, 3, 'right', 'LUANA_T', 'EVENT_BEAT_ORANGE_CREW_LUANA'),
)
DRAKE = ('Drake', 'SHAMOUTI_HOUSE', 4, 2, 'up', 'DRAKE_T', 'EVENT_BEAT_DRAKE')
SURF_COURSE = 'EVENT_FINISHED_CISSYS_SURF_COURSE'
SUMMIT = 'EVENT_REACHED_DANNYS_SUMMIT'
MATCHUP_SPECIES = ('BULBASAUR', 'CHARMANDER', 'SQUIRTLE')
RUDY_ROUNDS = ('RUDY_GRASS', 'RUDY_FIRE', 'RUDY_WATER')
DANNY_ASCENT = (('up', 2), ('left', 1), ('up', 3), ('left', 1), ('up', 4),
                ('left', 1), ('up', 8), ('right', 2), ('up', 4), ('right', 3))
BEACH_TRAINERS = ('SIGHTSEERM_BLAISE', 'BEAUTY_IOANA', 'SIGHTSEERF_KAMILA',
                  'AROMA_LADY_HEATHER', 'BREEDER_BRENDA', 'SWIMMERM_EZRA')


def prepare_matchup_team(game, k):
    """Give this test fixture a selectable Pokémon for each of Rudy's rounds."""
    assert game.rd('wPartyCount') >= 3
    for i, species in enumerate(MATCHUP_SPECIES):
        offset = i * k['PARTYMON_STRUCT_LENGTH']
        game.wr('wPartyMon1Species', k[species], offset)
        game.wr('wPartyMon1Form', 0, offset)


def select_party(game, *picks):
    """Advance to each regular party menu and select a slot through normal input."""
    for pick in picks:
        opened = []
        game.pb.hook_register(*game.sym['PartyMenuSelect'], opened.append, True)
        try:
            for _ in range(45):
                game.press('a', 35)
                if opened:
                    break
            assert len(opened) == 1, 'expected the party menu'
        finally:
            game.pb.hook_deregister(*game.sym['PartyMenuSelect'])
        game.tick(40)
        if pick is None:
            game.press('b', 40)
            continue
        for _ in range(8):
            if game.rd('wMenuCursorY') == pick + 1:
                break
            game.press('down', 28)
        assert game.rd('wMenuCursorY') == pick + 1, 'could not select requested party slot'
        game.press('a', 40)


def finish_challenge_battle(game, k, *, win=True):
    """Resolve the chosen side's faint through the ordinary battle end."""
    menu = []
    game.pb.hook_register(*game.sym['LoadBattleMenu'], menu.append, True)
    for _ in range(40):
        if menu:
            break
        game.press('a', 45)
    game.pb.hook_deregister(*game.sym['LoadBattleMenu'])
    assert menu, 'the battle menu did not load'
    game.tick(45)

    party, active = ('wOTParty', 'wEnemyMonHP') if win else ('wParty', 'wBattleMonHP')
    length = k['PARTYMON_STRUCT_LENGTH']

    def faint_team(_):
        for i in range(game.rd(party + 'Count')):
            game.wr(party + 'Mon1HP', 0, i * length)
            game.wr(party + 'Mon1HP', 0, i * length + 1)
        game.wr(active, 0)
        game.wr(active, 0, 1)
        if win:
            game.wr('wBattleMonHP', game.rd('wBattleMonMaxHP'))
            game.wr('wBattleMonHP', game.rd('wBattleMonMaxHP', 1), 1)

    def skip_learning(_):
        # (the family saves' level 10 teams level up here; a new move's
        # "forget a move?" prompt would take the A presses, so skip it)
        rf = game.pb.register_file
        rf.PC = game.m[rf.SP] | (game.m[rf.SP + 1] << 8)
        rf.SP += 2

    game.wr('wBattleMonMoves', k['TACKLE'])
    game.wr('wBattleMonPP', 35)
    game.pb.hook_register(*game.sym['ResolveFaints'], faint_team, None)
    game.pb.hook_register(*game.sym['LearnMove'], skip_learning, None)
    try:
        for _ in range(270):
            if not game.rd('wBattleMode'):
                break
            game.press('a', 35)
        assert not game.rd('wBattleMode'), 'the challenge battle did not finish'
    finally:
        game.pb.hook_deregister(*game.sym['ResolveFaints'])
        game.pb.hook_deregister(*game.sym['LearnMove'])


def expected_parties():
    """(class, set id) -> [(level, species)] from the existing trainer data."""
    src = open(os.path.join(ROOT, 'data', 'trainers', 'parties.asm')).read()
    out = {}
    for cls in (entry[5] for entry in LEADERS + (DRAKE,)):
        group = src.split(f'def_trainer_class {cls}\n', 1)[1].split('SECTION "', 1)[0]
        for tid, party in re.findall(r'def_trainer (\w+), "\w+"\n(.*?)end_trainer', group, re.S):
            out[cls, tid] = re.findall(r'tr_mon (\d+), (\w+)', party)
    return out


def main():
    save = open(sys.argv[1], 'rb').read()
    parties = expected_parties()
    species = sorted({sp for party in parties.values() for _, sp in party})
    names = species + ['EVENT_GOT_MYSTICTICKET_FROM_RED', 'PARTYMON_STRUCT_LENGTH', 'BOTTLE_CAP', 'EVENT_GOT_ORANGE_LEAGUE_PRIZE', 'EXTSPECIES_MASK']
    names += [SURF_COURSE, SUMMIT, *MATCHUP_SPECIES, *RUDY_ROUNDS, 'SURF', 'PLAYER_SURF', 'TACKLE',
              'ENGINE_FOGBADGE', 'ENGINE_BADGES', 'EVENT_TEMPORARY_UNTIL_MAP_RELOAD_2',
              'GROUP_ROCKY_PEAK', 'MAP_ROCKY_PEAK',
              'MON_STATUS', 'MON_HP', 'MON_PP']
    names += ['EVENT_BEAT_' + trainer for trainer in BEACH_TRAINERS]
    names += ['EVENT_GOT_A_POKEMON_FROM_IVY', 'EVENT_OLIVINE_PORT_SAILOR_AT_GANGWAY',
              *(prefix + mp for prefix in ('GROUP_', 'MAP_') for mp in
                ('SEAGALLOP_FERRY_VERMILION_GATE', 'SEAGALLOP_FERRY_SHAMOUTI_GATE', 'VALENCIA_PORT'))]
    for leader in LEADERS + (DRAKE,):
        names += [leader[5], leader[6], 'GROUP_' + leader[1], 'MAP_' + leader[1]]
    K = rgbasm_values(names + ['STATUSFLAGS_NO_WILD_ENCOUNTERS_F'], None)
    L = K['PARTYMON_STRUCT_LENGTH']
    g = Game(save)
    g.boot()
    fails = []

    # (none of this is about wild Pokemon, and one walking up to a level 10
    # team waiting out a dialogue would start a battle)
    g.wr('wStatusFlags', g.rd('wStatusFlags') | (1 << K['STATUSFLAGS_NO_WILD_ENCOUNTERS_F']))

    def flag(name):
        n = K[name]
        return (g.rd('wEventFlags', n // 8) >> (n % 8)) & 1

    def setflag(name, on=True):
        n = K[name]
        g.wr('wEventFlags', (g.rd('wEventFlags', n // 8) & ~(1 << (n % 8))) | (int(on) << (n % 8)), n // 8)

    def bottle_caps():
        for i in range(g.rd('wNumItems')):
            if g.rd('wItems', 2 * i) == K['BOTTLE_CAP']:
                return g.rd('wItems', 2 * i + 1)
        return 0

    def visit(leader):
        _, mp, x, y, facing, _, _ = leader
        g.warp(K['GROUP_' + mp], K['MAP_' + mp], x, y)
        g.face(facing)
        g.tick(30)

    def until_battle(tries=20):
        for _ in range(tries):
            g.press('a', 40)
            if g.rd('wBattleMode'):
                break
        for _ in range(300):
            if g.rd('wBattleMode'):
                return True
            g.tick(2)
        return False

    def tiles(s):
        return bytes(0x7f if c == ' ' else 0x9f if c == '!' else 0x80 + ord(c) - 65 if c.isupper()
                     else 0xa0 + ord(c) - 97 for c in s)
    tallies = []  # what the Crew tally said after each badge (OrangeCrewTally)

    def watch_tally():
        screen = bytes(g.rd('wTilemap', i) for i in range(20 * 18))
        at = screen.find(tiles(' of the'))
        if at > 0 and 0xe0 <= screen[at - 1] <= 0xe9:
            seen = screen[at - 1] - 0xe0
        elif tiles('all four') in screen:
            seen = 4
        else:
            return
        if not tallies or tallies[-1][1] != seen or tallies[-1][0] != len(badges_won):
            tallies.append((len(badges_won), seen))

    badges_won = []

    def settle():
        # The badge and island hints can outlast a fixed button delay.
        for _ in range(90):
            watch_tally()
            g.tick(30)
            if not g.rd('wScriptRunning') and not g.rd('wBattleMode'):
                g.tick(45)
                if not g.rd('wScriptRunning'):
                    return
            g.press('b', 22)
        raise AssertionError('Orange League dialogue did not finish')

    def check_party(tag, cls, tid='1'):
        if g.rd('wOtherTrainerClass') != K[cls]:
            fails.append((tag, f'trainer class {g.rd("wOtherTrainerClass")}, not {cls}'))
        n = g.rd('wOTPartyCount')
        got = []
        for i in range(n):
            sp = g.rd('wOTPartyMon1Species', i * L)
            ext = g.rd('wOTPartyMon1Form', i * L) & K['EXTSPECIES_MASK']
            got.append((g.rd('wOTPartyMon1Level', i * L), sp | (0x100 if ext else 0)))
        if tid != '1':
            assert g.rd('wOtherTrainerID') == K[tid]
        want = [(50 if cls in ('RUDY_T', 'LUANA_T') else int(lv), K[sp]) for lv, sp in parties[cls, tid]]
        if got != want:
            fails.append((tag, f'team {got}, not {want}'))

    def move(direction, count=1, delay=23):
        g.face(direction)
        for _ in range(count):
            g.press(direction, delay)

    def position():
        return g.rd('wXCoord'), g.rd('wYCoord')

    def location():
        return g.rd('wMapGroup'), g.rd('wMapNumber')

    def map_id(mp):
        return K['GROUP_' + mp], K['MAP_' + mp]

    def check_ferries():
        vermilion = 'SEAGALLOP_FERRY_VERMILION_GATE'
        shamouti = 'SEAGALLOP_FERRY_SHAMOUTI_GATE'

        def sail_to(destination):
            for _ in range(55):
                if location() == map_id(destination):
                    break
                g.press('a', 40)
            assert location() == map_id(destination)
            g.tick(90)
            settle()

        setflag('EVENT_OLIVINE_PORT_SAILOR_AT_GANGWAY', False)
        g.warp(*map_id(vermilion), 6, 3)
        g.face('down')
        sail_to(shamouti)
        move('up', 3)
        assert location() == map_id('BEAUTIFUL_BEACH')
        move('down', 2)
        assert location() == map_id(shamouti)
        move('down', 3)
        setflag('EVENT_GOT_A_POKEMON_FROM_IVY')
        g.press('a', 90)
        g.press('down', 40)
        sail_to('VALENCIA_PORT')
        g.face('up')
        sail_to(shamouti)
        move('down')
        sail_to(vermilion)

    def party_identity():
        # Exclude HP, status and PP, which may be healed by these battles.
        ignored = {K[key] + i for key, length in (('MON_STATUS', 2), ('MON_HP', 2), ('MON_PP', 4))
                   for i in range(length)}
        return tuple(tuple(g.rd('wPartyMon1', i * L + j) for j in range(L) if j not in ignored)
                     for i in range(g.rd('wPartyCount')))

    def surf():
        g.face('down')
        for _ in range(9):
            g.press('a', 40)
            if g.rd('wPlayerState') == K['PLAYER_SURF']:
                settle()
                assert position() == (3, 24)
                return
        raise AssertionError('could not Surf from Warm Beach')

    def cissy_course():
        move('left', 6)
        move('down')
        assert position() == (3, 23)
        surf()
        move('down')
        assert position() == (3, 25) and flag('EVENT_TEMPORARY_UNTIL_MAP_RELOAD_2'), position()
        move('up', 2)
        settle()
        assert position() == (3, 23) and not flag('EVENT_TEMPORARY_UNTIL_MAP_RELOAD_2')
        surf()
        move('down')
        move('right', 5)
        move('up')
        move('right', 4)
        settle()
        assert position() == (12, 24) and flag(SURF_COURSE)
        move('up')
        move('left', 3)
        move('up')

    def danny_climb():
        for direction, count in DANNY_ASCENT:
            move(direction, count)
        assert position() == (24, 6)
        move('up', delay=60)
        assert location() == map_id('ROCKY_PEAK')
        move('up', delay=65)
        for direction in ('up', 'left', 'down', 'right', 'up', 'right', 'up'):
            move(direction, delay=105)
        settle()
        assert flag(SUMMIT) and position() == (13, 3)
        move('left', delay=90)
        assert location() == map_id('ROCKY_BEACH') and position() == (22, 26)
        move('down')
        g.face('right')

    # Play the badges out of Field Book order on one continuous save.
    for trainer in LEADERS + (DRAKE,):
        setflag(trainer[6], False)
    setflag(SURF_COURSE, False)
    setflag(SUMMIT, False)
    setflag('EVENT_GOT_ORANGE_LEAGUE_PRIZE', False)
    setflag('EVENT_GOT_MYSTICTICKET_FROM_RED', False)
    locked = g.state()
    for trainer in LEADERS + (DRAKE,):
        g.load(locked)
        visit(trainer)
        if until_battle(10):
            fails.append((trainer[0], 'battle before Red'))
    g.load(locked)
    setflag('EVENT_GOT_MYSTICTICKET_FROM_RED')
    caps = bottle_caps()
    season = g.state()
    visit(DRAKE)
    if until_battle(9):
        fails.append(('Drake', 'battled without the four badges'))
    g.load(season)
    check_ferries()
    g.load(season)
    prepare_matchup_team(g, K)
    for trainer in BEACH_TRAINERS:
        setflag('EVENT_BEAT_' + trainer)
    g.wr('wJohtoBadges', g.rd('wJohtoBadges') | (1 << (K['ENGINE_FOGBADGE'] - K['ENGINE_BADGES'])))
    g.wr('wPartyMon1Moves', K['SURF'])
    for leader in (LEADERS[3], LEADERS[1], LEADERS[2], LEADERS[0]):
        tag, cls, ev = leader[0], leader[5], leader[6]
        visit(leader)
        original = party_identity()
        same_party_species = [g.rd('wPartyMon1Species', i * L) for i in range(g.rd('wPartyCount'))]
        if tag in ('Cissy', 'Danny'):
            g.press('a', 45)
            settle()
            assert not flag(ev) and not g.rd('wBattleMode')
            if tag == 'Cissy':
                cissy_course()
            else:
                danny_climb()
        if tag == 'Luana':
            select_party(g, 0, 0, None)
            settle()
            assert not flag(ev) and party_identity() == original
            select_party(g, 0, 1)
            assert until_battle()
            finish_challenge_battle(g, K, win=False)
            settle()
            assert not flag(ev) and party_identity() == original and not g.rd('wCupLevel')
            select_party(g, 0, 2)
        if tag == 'Rudy':
            select_party(g, 1, None)
            settle()
            assert not flag(ev) and party_identity() == original
            select_party(g, 0)
            assert until_battle()
            finish_challenge_battle(g, K)
            select_party(g, 1)
            assert until_battle()
            finish_challenge_battle(g, K, win=False)
            settle()
            assert not flag(ev) and party_identity() == original and not g.rd('wCupLevel')
            for slot, tid in enumerate(RUDY_ROUNDS):
                select_party(g, slot)
                assert until_battle()
                check_party(tag, cls, tid)
                assert (g.rd('wPartyCount'), g.rd('wPartyMon1Species')) == (1, same_party_species[slot]), tid
                finish_challenge_battle(g, K)
                if slot < 2:
                    assert not flag(ev)
        else:
            assert until_battle(), f'{tag} did not battle'
            check_party(tag, cls)
            if tag == 'Luana':
                assert g.rd('wPartyCount') == 2
                assert g.rd('wPartyMon1Species', L) == same_party_species[2]
            finish_challenge_battle(g, K)
        settle()
        if tag in ('Rudy', 'Luana'):
            assert party_identity() == original and not g.rd('wCupLevel')
            assert location() == map_id(leader[1]) and position() == leader[2:4]
        if not flag(ev):
            fails.append((tag, 'no badge after winning'))
        badges_won.append(tag)
        if not any(n == len(badges_won) - 1 and seen == len(badges_won) for n, seen in tallies):
            fails.append((tag, f'the badge tally did not say {len(badges_won)} of four (saw {tallies})'))
        earned = g.state()
        if tag == 'Rudy':
            select_party(g, 0)
        elif tag == 'Luana':
            select_party(g, 0, 1)
        else:
            # Earlier badges permit rematches even if a save predates its course.
            setflag(SURF_COURSE if tag == 'Cissy' else SUMMIT, False)
        if not until_battle():
            fails.append((tag, 'no rematch'))
        g.load(earned)
    visit(DRAKE)
    if not until_battle():
        fails.append(('Drake', 'no battle with the four badges'))
    else:
        check_party('Drake', 'DRAKE_T')
        finish_challenge_battle(g, K)
        settle()
        if not flag('EVENT_BEAT_DRAKE') or not flag('EVENT_GOT_ORANGE_LEAGUE_PRIZE'):
            fails.append(('Drake', 'no trophy and prize after winning'))
        if bottle_caps() != caps + 3:
            fails.append(('Drake', f'Bottle Caps {caps} -> {bottle_caps()}, not +3'))
        if not until_battle():
            fails.append(('Drake', 'no rematch'))
        else:
            finish_challenge_battle(g, K)
            settle()
            if bottle_caps() != caps + 3:
                fails.append(('Drake', 'gave the prize again'))

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
