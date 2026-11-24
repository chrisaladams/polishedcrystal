#!/usr/bin/env python3
"""Test both Trainer Card pages, record migration, and the in-game reset choices."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'wild_mons'))
from test_wild_mons import Game  # noqa: E402


def main(save_path):
    original = Path(save_path).read_bytes()
    game = Game(original)
    symbols = game.sym
    game.pb.stop(save=False)

    def offset(name):
        bank, address = symbols[name]
        return bank * 0x2000 + address - 0xa000

    def counts(data, name, size=3):
        start = offset(name)
        return tuple(int.from_bytes(data[i:i + size], 'big') for i in range(start, start + 3 * size, size))

    def party_name(name):
        return bytes(ord(c) - ord('A') + 0x80 for c in name).ljust(7, b'\x53')

    def play(g, trainer_id, name, result, padding=0x53):
        wire_name = (party_name(name)[:len(name)] + b'\x53').ljust(10, bytes([padding]))
        for i, tile in enumerate(wire_name):
            g.wr('wOTPlayerName', tile, i)
        g.wr('wOTPlayerID', trainer_id >> 8)
        g.wr('wOTPlayerID', trainer_id & 255, 1)
        g.wr('wBattleResult', result)
        invoke(g, 'AddLastBattleToLinkRecord')

    def players(data):
        table = {}
        start = offset('sLinkCardPlayers')
        for i in range(data[offset('sLinkCardPlayerCount')]):
            row = data[start + 21 * i:start + 21 * (i + 1)]
            key = (int.from_bytes(row[:2], 'big'), row[2:9])
            assert key not in table
            table[key] = tuple(int.from_bytes(row[j:j + 2], 'big') for j in range(9, 21, 2))
        return table

    def screen(g):
        return bytes(g.rd('wTilemap', i) for i in range(360))

    def roster_row(g, row, trainer_id, name, totals):
        tiles = screen(g)
        start = 20 * (4 + row * 3) + 1
        text = party_name(name).split(b'\x53')[0]
        assert tiles[start:start + len(text)] == text, (name, tiles[start:start + 7])
        def digits(value, length):
            return bytes(0x7f if c == ' ' else 0xe0 + int(c) for c in value.rjust(length))
        assert tiles[start + 12:start + 17] == digits(f'{trainer_id:05}', 5)
        for i, total in enumerate(totals):
            pos = start + 20 + i * 6
            assert tiles[pos:pos + 5] == digits(str(total), 5), (name, i, total, tiles[pos:pos + 5])

    def restart(data):
        g = Game(data[:0x8000] + original[0x8000:])
        g.boot()
        # Continue may also talk to an NPC if the player saved at a link desk.
        for _ in range(40):
            if not g.rd('wScriptRunning'):
                break
            g.press('b', 40)
        assert not g.rd('wScriptRunning'), 'could not exit dialogue after Continue'
        return g

    def invoke(g, name):
        # Run the cartridge routine in isolation. Reload its SRAM in a new
        # emulator before issuing normal menu input.
        bank, pc = symbols[name]
        m, r = g.m, g.pb.register_file
        m[0xffff] = m[0xff0f] = 0
        m[0x2000] = m[symbols['hROMBank'][1]] = bank
        m[0xff90], m[0xff91] = 0x18, 0xfe  # jr to self after ret
        m[0xdff0], m[0xdff1] = 0x90, 0xff
        r.SP, r.PC = 0xdff0, pc
        for _ in range(60):
            g.tick()
            if r.PC in (0xff90, 0xff91):
                return
        raise AssertionError(name + ' did not return')

    def player_card(g):
        g.press('start', 90)
        name = bytes(g.rd('wPlayerName', i) for i in range(11)).split(b'\x53')[0]
        tiles = bytes(g.rd('wTilemap', i) for i in range(360))
        pos = tiles.index(name)
        for _ in range(g.rd('wMenuItemsList')):
            if g.rd('wMenuCursorY') == pos // 20:
                break
            g.press('down', 12)
        g.press('a', 100)
        assert g.rd('wJumptableIndex') == 1

    def page(g, index, totals):
        assert g.rd('wJumptableIndex') == index, ('wrong card page', index)
        for i, n in enumerate(totals):
            tiles = bytes(g.rd('wTilemap', (11 + i) * 20 + 10 + j) for j in range(8))
            # Crystal uses $7f for space, $e0..$e9 for digits.
            digits = bytes(t - 0xe0 + ord('0') for t in tiles if t != 0x7f)
            assert digits == str(n).encode(), (i, n, tiles)
        values = g.sram()
        assert counts(values, 'sLinkCardLifetime' if index == 7 else 'sLinkCardYear') == totals

    data = bytearray(original)
    first, end = offset('sLinkCardMarker'), offset('sLinkCardEnd')
    data[first:end] = bytes([0xff]) * (end - first)
    tag = offset('sLinkCardPlayerTag')
    roster_end = offset('sLinkCardPlayersEnd')
    data[tag:roster_end] = bytes([0xff]) * (roster_end - tag)
    old_names = ('CY', 'KIM', 'ASH', 'LEAF', 'SAM')
    for i, name in enumerate(old_names):
        start = offset('sLinkBattleRecord1') + i * 18
        data[start:start + 18] = ((400 + i).to_bytes(2, 'big') + party_name(name) +
                                   bytes([0x53]) * 3 + bytes([0, i + 1, 0, 0, 0, 0]))
    old = (9999, 255, 12)
    start = offset('sLinkBattleWins')
    data[start:start + 6] = b''.join(n.to_bytes(2, 'big') for n in old)
    g = restart(data)
    try:
        # First result on an older save, before ever opening the player card.
        play(g, 400, 'CY', 0)
        play(g, 777, 'CY', 1)
        play(g, 400, 'CY', 2, padding=0)
        active = g.sram()
        roster = players(active)
        assert len(roster) == 6
        assert roster[400, party_name('CY')] == (2, 0, 1, 1, 0, 1)
        assert roster[777, party_name('CY')] == (0, 1, 0, 0, 1, 0)
        g.pb.stop(save=False)
        g = restart(active)
        lifetime, year = (10000, 256, 13), (1, 1, 1)
        g.wr('wKantoBadges', 0)
        player_card(g)
        g.press('right', 45)
        assert g.rd('wJumptableIndex') == 3
        g.press('right', 50)
        page(g, 7, lifetime)
        g.press('down', 60)
        roster_row(g, 0, 400, 'CY', (2, 0, 1))
        g.press('right', 35)
        roster_row(g, 0, 404, 'SAM', (5, 0, 0))
        roster_row(g, 1, 777, 'CY', (0, 1, 0))
        g.press('left', 35)
        roster_row(g, 0, 400, 'CY', (2, 0, 1))
        g.press('b', 60)
        page(g, 7, lifetime)
        g.press('a', 50)
        page(g, 9, year)
        g.press('down', 60)
        roster_row(g, 0, 400, 'CY', (1, 0, 1))
        roster_row(g, 1, 777, 'CY', (0, 1, 0))
        g.press('b', 60)
        for choice in ('b', 'a'):  # B cancels, and A on the default No cancels.
            g.press('a', 50)
            g.press(choice, 65)
            page(g, 9, year)
        g.press('a', 50)
        g.press('down', 16)
        g.press('a', 65)
        page(g, 9, (0, 0, 0))
        g.press('down', 60)
        assert party_name('CY')[:2] not in screen(g)
        g.press('b', 60)
        assert all(row[3:] == (0, 0, 0) for row in players(g.sram()).values())
        g.press('left', 55)
        page(g, 7, lifetime)
        g.press('b', 70)
        # Reboot to verify a confirmed reset reached the cartridge immediately.
        reset = g.sram()
        g.pb.stop(save=False)
        g = restart(reset)
        g.wr('wKantoBadges', 1)
        player_card(g)
        g.press('left', 50)
        page(g, 7, lifetime)
        g.press('left', 50)
        assert g.rd('wJumptableIndex') == 5  # Kanto badges are still reachable
        g.press('right', 50)
        page(g, 7, lifetime)
        g.press('right', 50)
        page(g, 9, (0, 0, 0))
        g.press('right', 50)
        assert g.rd('wJumptableIndex') == 1
        play(g, 400, 'CY', 0)
        invoke(g, 'ErasePreviousSave')
        after = g.sram()
        assert counts(after, 'sLinkCardLifetime') == (10001, 256, 13)
        assert counts(after, 'sLinkCardYear') == (1, 0, 0)
        assert counts(after, 'sLinkBattleWins', 2) == (0, 0, 0)
        assert players(after)[400, party_name('CY')] == (3, 0, 1, 1, 0, 0)
    finally:
        g.pb.stop(save=False)

    # The full erase available from the title screen also preserves the card.
    g = Game(after + original[0x8000:])
    try:
        seen = set()
        for entry in ('TitleScreenMain', '_DeleteSaveData', 'VerticalMenu'):
            g.pb.hook_register(*symbols[entry], seen.add, entry)
        g.tick(900)
        if 'TitleScreenMain' not in seen:
            g.press('start', 180)
        assert 'TitleScreenMain' in seen, 'title screen did not open'
        for key in ('up', 'b', 'select'):
            g.pb.button_press(key)
        g.tick(8)
        for key in ('up', 'b', 'select'):
            g.pb.button_release(key)
        g.tick(160)
        assert '_DeleteSaveData' in seen, 'title shortcut did not open the erase screen'
        if 'VerticalMenu' not in seen:
            g.press('a', 90)
        assert 'VerticalMenu' in seen, 'erase confirmation did not open'
        g.press('down', 16)
        g.press('a', 200)
        cleared = g.sram()
        assert cleared[first:end] == after[first:end]
        assert cleared[tag:roster_end] == after[tag:roster_end]
        assert cleared[offset('sCheckValue1')] == 0, 'title-screen erase did not run'
        assert cleared[offset('sBackupCheckValue1')] == 0
    finally:
        g.pb.stop(save=False)

    # Blank battery RAM and resumed records at their 24-bit limit.
    g = restart(original)
    try:
        for symbol in ('sCheckValue1', 'sBackupCheckValue1', 'sLinkCardMarker', 'sLinkCardPlayerTag'):
            bank, address = symbols[symbol]
            g.m[bank, address] = 0xff
        invoke(g, 'OpenLinkCardRecords')
        assert counts(g.sram(), 'sLinkCardLifetime') == (0, 0, 0)
        assert not players(g.sram())
        bank, address = symbols['sLinkCardLifetime']
        for i in range(3):
            g.m[bank, address + i] = 0xff
        play(g, 400, 'CY', 0)
        assert counts(g.sram(), 'sLinkCardLifetime') == (0xffffff, 0, 0)
        assert counts(g.sram(), 'sLinkCardYear') == (1, 0, 0)
        for i in range(65):
            play(g, 500 + i, 'PAT', 1)
        play(g, 400, 'CY', 2)
        full = players(g.sram())
        assert len(full) == 65 and full[400, party_name('CY')] == (1, 0, 1, 1, 0, 1)
        assert (564, party_name('PAT')) not in full
        assert counts(g.sram(), 'sLinkCardYear') == (1, 65, 1)
        bank, address = symbols['sLinkCardPlayers']
        g.m[bank, address + 9] = g.m[bank, address + 10] = 0xff
        play(g, 400, 'CY', 0)
        assert players(g.sram())[400, party_name('CY')] == (65535, 0, 1, 2, 0, 1)
    finally:
        g.pb.stop(save=False)
    print('Passed named opponents, rematches, roster capacity, migration, page navigation, reset, restart and erase.')


if __name__ == '__main__':
    main(sys.argv[1])
