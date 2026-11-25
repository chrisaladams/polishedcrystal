#!/usr/bin/env python3
"""Check the daily cup bulletin on the player's TV and Pokégear radio."""
import sys
from pathlib import Path

from test_orange_league import Game, rgbasm_values


def main(path):
    game = Game(Path(path).read_bytes())
    k = rgbasm_values([
        'EVENT_GOT_MYSTICTICKET_FROM_RED', 'ENGINE_RISINGBADGE', 'ENGINE_BADGES',
        'GROUP_PLAYERS_HOUSE_1F', 'MAP_PLAYERS_HOUSE_1F', 'POKEGEAR_OBTAINED_F',
        'POKEGEAR_RADIO_CARD_F', 'STATUSFLAGS2_ROCKETS_IN_RADIO_TOWER_F',
        'RADIO_SCROLL', 'OAKS_POKEMON_TALK_4',
    ], None)
    cups = (
        ('Rising', 'Park'), ('Whirl', 'Olivine'), ('Kimono', 'Ecruteak'),
        ('Dragon', 'Blackthorn'), ('Rental', 'Goldenrod'), ('World', 'Indigo'),
    )

    def name(label):
        bank, address = game.sym['CupSpotlightNames.' + label]
        return bytes(game.m[bank, address + i] for i in range(19)).split(b'\x53')[0]

    def row(y):
        return bytes(game.rd('wTilemap', y * 20 + x) for x in range(1, 19))

    def tv(day, cup):
        game.wr('wRTCDayLo', day)
        title, venue = map(name, cups[cup])
        game.face('up')
        for _ in range(25):
            game.press('a', 35)
            if row(14).startswith(title) and row(16).startswith(venue):
                break
        else:
            raise AssertionError(f'TV did not announce {cups[cup]} on day {day}')
        for _ in range(5):
            game.press('b', 30)
            if not game.rd('wScriptRunning'):
                break
        assert not game.rd('wScriptRunning')

    try:
        game.boot()
        game.warp(k['GROUP_PLAYERS_HOUSE_1F'], k['MAP_PLAYERS_HOUSE_1F'], 6, 2)
        red_byte, red_bit = divmod(k['EVENT_GOT_MYSTICTICKET_FROM_RED'], 8)
        rising = 1 << (k['ENGINE_RISINGBADGE'] - k['ENGINE_BADGES'])
        game.wr('wEventFlags', game.rd('wEventFlags', red_byte) & ~(1 << red_bit), red_byte)
        game.wr('wJohtoBadges', game.rd('wJohtoBadges') & ~rising)
        for day, cup in ((0, 0), (1, 2), (3, 4), (5, 0)):
            tv(day, cup)

        game.wr('wEventFlags', game.rd('wEventFlags', red_byte) | (1 << red_bit), red_byte)
        game.wr('wJohtoBadges', game.rd('wJohtoBadges') | rising)
        for day in range(len(cups)):
            tv(day, day)

        # Tune Oak's Pokémon Talk through the ordinary Pokégear menu.
        game.wr('wPokegearFlags', (1 << k['POKEGEAR_OBTAINED_F']) | (1 << k['POKEGEAR_RADIO_CARD_F']))
        game.wr('wStatusFlags2', game.rd('wStatusFlags2') & ~(1 << k['STATUSFLAGS2_ROCKETS_IN_RADIO_TOWER_F']))
        game.highlight_start_option('PokegearString')
        game.press('a', 100)
        game.press('right', 60, 1)
        for _ in range(50):
            tuning = game.rd('wRadioTuningKnob')
            if tuning == 16:
                break
            game.press('up' if tuning < 16 else 'down', 12, 1)
        assert game.rd('wRadioTuningKnob') == 16
        for _ in range(900):
            game.tick()
            if (game.rd('wCurRadioLine'), game.rd('wNextRadioLine')) == (k['RADIO_SCROLL'], k['OAKS_POKEMON_TALK_4']):
                break
        assert row(14) == name('World') and row(16).startswith(name('Indigo'))
        game.tick(120)
        assert game.rd('wCurRadioLine') == k['RADIO_SCROLL']
        assert game.rd('wNextRadioLine') != k['OAKS_POKEMON_TALK_4']
        print('Passed all six TV bulletins, progression gates and the radio handoff back to Oak.')
    finally:
        game.pb.stop(save=False)


if __name__ == '__main__':
    main(sys.argv[1])
