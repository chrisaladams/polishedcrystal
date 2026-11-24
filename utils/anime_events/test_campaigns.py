#!/usr/bin/env python3
"""Exercise post-Red story clues, temporary actors, weather and save migration."""
import sys
from pathlib import Path

from test_orange_league import Game, rgbasm_values


BEACONS = ('FIRE', 'ICE', 'LIGHTNING')
STORY_FLAGS = ('READ_CINNABAR_CLONE_REPORT', 'HEARD_SHAMOUTI_BEACONS',
               *(f'TUNED_{name}_BEACON' for name in BEACONS), 'RESTORED_SHAMOUTI_BEACONS')
MARKER = 'CAMPAIGN_FLAGS_INITIALIZED'
SHRINE = 'SHAMOUTI_SHRINE_RUINS'
KEEPER = (SHRINE, 10, 18, 'up')
LAWRENCE = (SHRINE, 8, 12, 'up')


def old_book_save(game, save, flags, *, damage_primary):
    """Give both copies of an older save the retired book visibility bits."""
    data = bytearray(save)

    def offset(name):
        bank, addr = game.sym[name]
        return bank * 0x2000 + addr - 0xa000

    for prefix in ('s', 'sBackup'):
        first = offset(prefix + 'PlayerData') + game.addr('wEventFlags') - game.addr('wPlayerData')
        for flag in STORY_FLAGS:
            n, bit = divmod(flags[flag], 8)
            data[first + n] |= 1 << bit
        n, bit = divmod(flags[MARKER], 8)
        data[first + n] &= ~(1 << bit)
        lo, hi = offset(prefix + 'GameData'), offset(prefix + 'GameDataEnd')
        at = offset(prefix + 'Checksum')
        data[at:at + 2] = (sum(data[lo:hi]) & 0xffff).to_bytes(2, 'little')
    if damage_primary:
        data[offset('sChecksum')] ^= 1
    return bytes(data)


def main(path):
    original = Path(path).read_bytes()
    maps = (SHRINE, 'SHAMOUTI_COAST', 'WHIRL_ISLAND_LUGIA_CHAMBER',
            'RUINS_OF_ALPH_INNER_CHAMBER', 'ILEX_FOREST', 'ROUTE_22_PAST',
            *(f'{name}_ISLAND_ROOF' for name in BEACONS))
    flags = (*STORY_FLAGS, MARKER, 'GOT_MYSTICTICKET_FROM_RED', 'BEAT_LAWRENCE',
             'FOUGHT_LUGIA', 'TIME_TRAVEL_FINISHED', 'TIME_TRAVELING',
             'FOREST_IS_RESTLESS', 'BEAT_MOLLY', 'RESCUED_PROF_HALE')
    constants = rgbasm_values([*('EVENT_' + flag for flag in flags),
                               *(kind + name for name in maps for kind in ('GROUP_', 'MAP_')),
                               'LAWRENCE', 'SILVER_WING', 'PLAYER_CAUGHT_LUGIA_F', 'CELEBI',
                               'PARTYMON_STRUCT_LENGTH', 'OW_WEATHER_THUNDERSTORM', 'TACKLE',
                               'NUM_OBJECT_STRUCTS'], None)
    events = {name: constants['EVENT_' + name] for name in flags}
    game = Game(original)

    def flag(name, value=None):
        index, bit = divmod(events[name], 8)
        current = game.rd('wEventFlags', index)
        if value is None:
            return bool(current & (1 << bit))
        game.wr('wEventFlags', current | (1 << bit) if value else current & ~(1 << bit), index)

    def boot(save):
        nonlocal game
        game.pb.stop(save=False)
        game = Game(save)
        game.boot()

    def map_id(name):
        return constants['GROUP_' + name], constants['MAP_' + name]

    def on_map(name):
        return (game.rd('wMapGroup'), game.rd('wMapNumber')) == map_id(name)

    def visit(name, x, y, facing=None):
        game.warp(*map_id(name), x, y)
        assert on_map(name), name
        if facing:
            game.face(facing)

    def until(check, button, *, tries=160):
        for _ in range(tries):
            if check():
                return
            game.press(button, 45)
        raise AssertionError('overworld script did not reach its next state')

    def settle():
        game.tick(55)
        until(lambda: not game.rd('wScriptRunning') and not game.rd('wBattleMode'), 'b')

    def talk(where):
        visit(*where)
        game.press('a', 55)
        settle()

    def tune(name):
        talk((f'{name}_ISLAND_ROOF', 5, 4, 'up'))

    def actor_at(x, y):
        for i in range(1, constants['NUM_OBJECT_STRUCTS']):
            prefix = f'wObject{i}'
            if (game.rd(prefix + 'Sprite') and game.rd(prefix + 'MapX') == x + 4
                    and game.rd(prefix + 'MapY') == y + 4):
                return True
        return False

    def wing_count():
        for i in range(256):
            if not game.rd('wKeyItems', i):
                return sum(game.rd('wKeyItems', pos) == constants['SILVER_WING'] for pos in range(i))
        raise AssertionError('key items did not have a terminator')

    def finish_battle(win):
        menu = []
        game.pb.hook_register(*game.sym['LoadBattleMenu'], menu.append, True)
        until(lambda: bool(menu), 'a', tries=40)
        game.pb.hook_deregister(*game.sym['LoadBattleMenu'])
        game.tick(45)
        if win:
            def force_faints(_):
                for i in range(game.rd('wOTPartyCount')):
                    offset = i * constants['PARTYMON_STRUCT_LENGTH']
                    game.wr('wOTPartyMon1HP', 0, offset)
                    game.wr('wOTPartyMon1HP', 0, offset + 1)
                game.wr('wEnemyMonHP', 0)
                game.wr('wEnemyMonHP', 0, 1)
                game.wr('wBattleMonHP', 3)
                game.wr('wBattleMonHP', 0xe7, 1)

            game.wr('wBattleMonMoves', constants['TACKLE'])
            game.wr('wBattleMonPP', 35)
            game.pb.hook_register(*game.sym['ResolveFaints'], force_faints, None)
        else:
            for button in ('down', 'right', 'a', 'down'):
                game.press(button, 40)
        until(lambda: not game.rd('wBattleMode'), 'a', tries=260)
        if win:
            game.pb.hook_deregister(*game.sym['ResolveFaints'])
        settle()

    try:
        for damage in (False, True):
            boot(old_book_save(game, original, events, damage_primary=damage))
            assert flag(MARKER) and not any(flag(name) for name in STORY_FLAGS)
        for name in flags:
            if name != MARKER:
                flag(name, False)
        game.wr('wKeyItems', 0)
        flag('GOT_MYSTICTICKET_FROM_RED', True)
        base = game.state()

        # Existing catches and the old Lawrence victory leave the new quest open.
        flag('BEAT_LAWRENCE', True)
        flag('FOUGHT_LUGIA', True)
        game.wr('wPlayerCaught', game.rd('wPlayerCaught') | (1 << constants['PLAYER_CAUGHT_LUGIA_F']))
        game.wr('wKeyItems', constants['SILVER_WING'])
        game.wr('wKeyItems', 0, 1)
        tune('ICE')
        assert not flag('TUNED_ICE_BEACON')
        talk(KEEPER)
        assert flag('HEARD_SHAMOUTI_BEACONS') and not flag('RESTORED_SHAMOUTI_BEACONS')
        visit('SHAMOUTI_COAST', 6, 2)
        assert game.rd('wCurWeather') == constants['OW_WEATHER_THUNDERSTORM']
        tune('LIGHTNING')
        assert flag('TUNED_LIGHTNING_BEACON') and not flag('TUNED_FIRE_BEACON')
        game.manual_save()
        boot(game.sram() + original[0x8000:])
        settle()
        assert flag('TUNED_LIGHTNING_BEACON') and flag('FOUGHT_LUGIA') and wing_count() == 1
        for name in ('ICE', 'FIRE'):
            tune(name)
            assert flag(f'TUNED_{name}_BEACON')
        talk(KEEPER)
        assert flag('RESTORED_SHAMOUTI_BEACONS') and wing_count() == 1
        assert game.rd('wPlayerCaught') & (1 << constants['PLAYER_CAUGHT_LUGIA_F'])
        visit('WHIRL_ISLAND_LUGIA_CHAMBER', 9, 8)
        assert not actor_at(9, 5), 'a caught Lugia returned'
        visit('SHAMOUTI_COAST', 6, 2)
        assert game.rd('wCurWeather') != constants['OW_WEATHER_THUNDERSTORM']
        print('Checked the older-save route and a mid-quest Continue.', flush=True)

        # A fresh quest uses the existing Lawrence battle, with a retry on loss.
        game.load(base)
        talk(LAWRENCE)
        assert not flag('BEAT_LAWRENCE') and not game.rd('wBattleMode')
        talk(KEEPER)
        for name in BEACONS:
            tune(name)
        for win in (False, True):
            visit(*LAWRENCE)
            until(lambda: game.rd('wBattleMode'), 'a')
            assert game.rd('wOtherTrainerClass') == constants['LAWRENCE']
            finish_battle(win)
            assert flag('BEAT_LAWRENCE') == win and flag('RESTORED_SHAMOUTI_BEACONS') == win
            assert wing_count() == int(win)
            print('Checked Lawrence after a win.' if win else 'Checked Lawrence after a forfeit.', flush=True)
        visit('WHIRL_ISLAND_LUGIA_CHAMBER', 9, 8)
        assert not flag('FOUGHT_LUGIA') and actor_at(9, 5), 'the story did not unlock the original encounter'

        # The illusion redraw is temporary and keeps the original statue reachable.
        game.load(base)
        flag('BEAT_MOLLY', True)
        captures = {}

        def scene(_):
            regs = game.pb.register_file
            for stage in ('Illusion', 'Rescue'):
                if (regs.B, regs.HL) == game.sym[f'HaleStatueScript.{stage}']:
                    block = game.addr('wOverworldMapBlocks') + 9 * (game.rd('wMapWidth') + 6) + 5
                    captures[stage] = (game.m[block], actor_at(4, 12), actor_at(6, 12))

        game.pb.hook_register(*game.sym['MapTextbox'], scene, None)
        talk(('RUINS_OF_ALPH_INNER_CHAMBER', 5, 14, 'up'))
        assert captures == {'Illusion': (0x0f, True, False), 'Rescue': (0x18, False, True)}, captures
        assert flag('RESCUED_PROF_HALE') and not actor_at(4, 12) and not actor_at(6, 12)
        game.pb.hook_deregister(*game.sym['MapTextbox'])

        # With no Celebi in the party or GS Ball, the new shrine prompt can
        # still take returning players into the original time-travel sequence.
        game.load(base)
        for i in range(game.rd('wPartyCount')):
            assert game.rd('wPartyMon1Species', i * constants['PARTYMON_STRUCT_LENGTH']) != constants['CELEBI']
        visit('ILEX_FOREST', 10, 25, 'up')
        until(lambda: on_map('ROUTE_22_PAST'), 'a')
        assert flag('TIME_TRAVELING') and not flag('TIME_TRAVEL_FINISHED')
    finally:
        game.pb.stop(save=False)

    print('Passed campaign save migration, two beacon orders, weather, Lawrence retries, older captures, Alph illusion staging and the Ilex time-travel entry.')


if __name__ == '__main__':
    main(sys.argv[1])
