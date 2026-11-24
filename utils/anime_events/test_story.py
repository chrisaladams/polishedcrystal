#!/usr/bin/env python3
"""Follow Oak's field book from Red to the Pallet sketch on one in-memory save.

Travel is shortened with map warps and battle outcomes are forced. Story
flags are earned through interaction, including both full-pocket victories.
"""
import sys
from pathlib import Path

from test_cameos import CAMEOS
from test_movie_events import EVENTS
from test_orange_league import DRAKE, LEADERS
from test_whirl_cup import ROUNDS
from field_book_checkpoints import guide_checkpoints
from test_wild_mons import Game, rgbasm_values


def main(save):
    maps = {'SILVER_CAVE_ROOM_3', 'OAKS_LAB', 'RUINS_OF_ALPH_INNER_CHAMBER',
            'OLIVINE_PORT', 'PALLET_TOWN', *(entry[1] for entry in LEADERS + (DRAKE,)),
            *(entry[1] for entry in EVENTS)}
    flags = ['EVENT_GOT_MYSTICTICKET_FROM_RED', 'EVENT_BEAT_RED', 'EVENT_BEAT_DRAKE',
             'EVENT_GOT_ORANGE_LEAGUE_PRIZE', 'EVENT_BEAT_MOLLY', 'EVENT_RESCUED_PROF_HALE',
             'EVENT_BEAT_IRON_MASK_MARAUDER', 'EVENT_BEAT_MEWTWO_CLONES', 'EVENT_WON_WHIRL_CUP',
             'EVENT_WON_PALLET_INVITATIONAL', 'EVENT_MOLLY_PATCH_PENDING', 'EVENT_WHIRL_CUP_PRIZE_PENDING',
             'EVENT_MARAUDER_REWARD_PENDING', *(entry[6] for entry in LEADERS)]
    names = flags + [prefix + m for m in maps for prefix in ('GROUP_', 'MAP_')]
    names += ['EVENT_GOT_A_POKEMON_FROM_ELM', 'EVENT_BEAT_ELITE_FOUR', 'RED', 'ASH_T', 'SQUIRTLE', 'PARTYMON_STRUCT_LENGTH', 'MAX_ITEMS', 'MAX_ITEM_STACK',
              'DAILYFLAGS2_RED_IN_MOUNT_SILVER_F', 'BIG_NUGGET', 'MYSTIC_WATER', 'ABILITYPATCH', 'EVENT_TIME_TRAVEL_FINISHED',
              'EVENT_CERULEAN_CAVE_MEWTWO', 'EVENT_OLIVINE_PORT_SPRITES_AFTER_HALL_OF_FAME',
              *(entry[5] for entry in LEADERS + (DRAKE,)), *(entry[5] for entry in EVENTS),
              *(cls for cls, _ in ROUNDS)]
    k = rgbasm_values(names, None)
    g = Game(Path(save).read_bytes())
    g.boot()
    texts = []

    def record_text(_):
        regs = g.pb.register_file
        texts.append((regs.B, regs.HL))

    g.pb.hook_register(*g.sym['MapTextbox'], record_text, None)

    def flag(name, value=None):
        offset, bit = divmod(k[name], 8)
        byte = g.rd('wEventFlags', offset)
        if value is None:
            return bool(byte & (1 << bit))
        g.wr('wEventFlags', (byte | 1 << bit) if value else (byte & ~(1 << bit)), offset)

    def visit(mp, x, y, facing):
        g.warp(k['GROUP_' + mp], k['MAP_' + mp], x, y)
        g.face(facing)

    def settle():
        for _ in range(160):
            g.press('b', 50)
            if not g.rd('wScriptRunning') and not g.rd('wBattleMode'):
                g.tick(60)
                if not g.rd('wScriptRunning'):
                    return
        raise AssertionError('dialogue did not finish')

    def read(mp, x, y, facing, label):
        visit(mp, x, y, facing)
        texts.clear()
        g.press('a', 60)
        if label.startswith(('OaksLabFieldBook.', 'FieldBookNotes.')):
            g.press('a', 60)  # Next stop
        settle()
        assert g.sym[label] in texts, f'{label} was not shown when examining {mp} from {x},{y}'

    def menu_book(page, side=False):
        g.press('start', 90)
        count = g.rd('wMenuItemsList')
        assert 0 < count <= 10, 'Start menu did not open'
        # Match the printed label with the string from this build of the ROM.
        bank, addr = g.sym['StartMenu.FieldBookString']
        label = bytes(g.m[bank, addr + i] for i in range(len('Field Book')))
        screen = bytes(g.rd('wTilemap', i) for i in range(20 * 18))
        offset = screen.find(label)
        assert offset >= 0, 'Field Book missing from Start menu'
        row, column = divmod(offset, 20)
        assert column + len(label) < 20 and count < g.rd('wMenuBorderBottomCoord') < 18
        # Walk the cursor to the book as the player would, including wrap.
        for _ in range(count):
            if g.rd('wMenuCursorY') == row:
                break
            g.press('down', 12)
        assert g.rd('wMenuCursorY') == row
        location = (g.rd('wMapGroup'), g.rd('wMapNumber'), g.rd('wXCoord'), g.rd('wYCoord'))
        texts.clear()
        g.press('a', 60)
        if side:
            g.press('down', 16)
        g.press('a', 60)
        settle()
        assert g.sym[page] in texts, f'wrong Start menu page: {page}'
        assert location == (g.rd('wMapGroup'), g.rd('wMapNumber'), g.rd('wXCoord'), g.rd('wYCoord'))

    def book(page):
        menu_book('OaksLabFieldBook.' + page)
        read('OAKS_LAB', 2, 2, 'up', 'OaksLabFieldBook.' + page)
        print('Read field book:', page, flush=True)

    def battle(cls, win=True):
        for _ in range(55):
            if g.rd('wBattleMode'):
                break
            g.press('a', 40)
        assert g.rd('wBattleMode') and g.rd('wOtherTrainerClass') == k[cls], f'expected battle with {cls}'
        g.tick(400)
        if win:
            party, count, loser, survivor = 'wOTPartyMon1HP', 'wOTPartyCount', 'wEnemyMonHP', 'wBattleMonHP'
        else:
            party, count, loser, survivor = 'wPartyMon1HP', 'wPartyCount', 'wBattleMonHP', 'wEnemyMonHP'
        for i in range(g.rd(count)):
            offset = i * k['PARTYMON_STRUCT_LENGTH']
            g.wr(party, 0, offset)
            g.wr(party, 0, offset + 1)
        g.wr(loser, 0)
        g.wr(loser, 1, 1)
        g.wr(survivor, 3)
        g.wr(survivor, 231, 1)
        for _ in range(400):
            g.press('a', 30)
            if not g.rd('wBattleMode'):
                return
        raise AssertionError(f'{cls} battle did not finish')

    def fill_pocket():
        g.wr('wNumItems', k['MAX_ITEMS'])
        for i in range(k['MAX_ITEMS']):
            g.wr('wItems', k['BIG_NUGGET'], 2 * i)
            g.wr('wItems', k['MAX_ITEM_STACK'], 2 * i + 1)
        g.wr('wItems', 255, 2 * k['MAX_ITEMS'])

    def collect(pending, prize):
        assert flag(pending), pending
        # Discard one stack, then talk again. No rematch needed.
        g.wr('wNumItems', k['MAX_ITEMS'] - 1)
        g.wr('wItems', 255, 2 * (k['MAX_ITEMS'] - 1))
        g.press('a', 60)
        settle()
        assert not flag(pending) and any(g.rd('wItems', 2 * i) == k[prize]
                                          for i in range(g.rd('wNumItems'))), prize

    try:
        for name in flags:
            flag(name, False)
        g.wr('wDailyFlags2', g.rd('wDailyFlags2') & ~(1 << k['DAILYFLAGS2_RED_IN_MOUNT_SILVER_F']))
        # An existing save that already played the original Celebi story and caught Mewtwo.
        flag('EVENT_TIME_TRAVEL_FINISHED', True)
        flag('EVENT_CERULEAN_CAVE_MEWTWO', True)
        flag('EVENT_OLIVINE_PORT_SPRITES_AFTER_HALL_OF_FAME', False)
        guide_checkpoints(g, menu_book)
        original = g.state()
        flag('EVENT_GOT_A_POKEMON_FROM_ELM', False)
        flag('EVENT_BEAT_ELITE_FOUR', False)
        read('OAKS_LAB', 2, 2, 'up', 'FieldBookNotes.Starter')
        g.load(original)
        visit('SILVER_CAVE_ROOM_3', 8, 7, 'up')
        battle('RED')
        settle()
        assert flag('EVENT_GOT_MYSTICTICKET_FROM_RED') and g.sym['Red.Note'] in texts
        book('Crew')
        for _, mp, x, y, facing, cls, badge in LEADERS + (DRAKE,):
            visit(mp, x, y, facing)
            battle(cls)
            settle()
            assert flag(badge), badge
        book('Alph')
        molly, mask, echo = EVENTS
        fill_pocket()
        visit(molly[1], *molly[3], molly[4])
        battle(molly[5])
        settle()
        assert flag('EVENT_BEAT_MOLLY')
        collect('EVENT_MOLLY_PATCH_PENDING', 'ABILITYPATCH')
        book('Hale')
        read('RUINS_OF_ALPH_INNER_CHAMBER', 5, 14, 'up', 'HaleStatueScript.Note')
        assert flag('EVENT_RESCUED_PROF_HALE')
        flag('EVENT_TIME_TRAVEL_FINISHED', False)
        book('Shrine')
        flag('EVENT_TIME_TRAVEL_FINISHED', True)
        book('Mask')
        visit(mask[1], *mask[3], mask[4])
        battle(mask[5])
        settle()
        assert g.sym['IlexForestIronMaskScript.Vision'] in texts
        book('Echo')
        visit(echo[1], *echo[3], echo[4])
        battle(echo[5])
        settle()
        book('Cup')
        species = []
        for i in range(g.rd('wPartyCount')):
            offset = i * k['PARTYMON_STRUCT_LENGTH']
            species.append(g.rd('wPartyMon1Species', offset))
            g.wr('wPartyMon1Species', k['SQUIRTLE'], offset)
        fill_pocket()
        visit('OLIVINE_PORT', 13, 8, 'up')
        for cls, _ in ROUNDS:
            battle(cls)
        settle()
        assert flag('EVENT_WON_WHIRL_CUP')
        collect('EVENT_WHIRL_CUP_PRIZE_PENDING', 'MYSTIC_WATER')
        for i, original in enumerate(species):
            g.wr('wPartyMon1Species', original, i * k['PARTYMON_STRUCT_LENGTH'])
        book('Final')
        ash = CAMEOS[0]
        visit(ash[1], *ash[3], ash[4])
        battle('DRAKE_T')
        battle('ASH_T', win=False)
        settle()
        assert not flag('EVENT_WON_PALLET_INVITATIONAL')
        assert g.rd('wMapGroup') == k['GROUP_PALLET_TOWN'] and g.rd('wMapNumber') == k['MAP_PALLET_TOWN']
        battle('DRAKE_T')
        battle('ASH_T')
        settle()
        assert flag('EVENT_WON_PALLET_INVITATIONAL')
        book('Champion')
        read('OAKS_LAB', 5, 1, 'up', 'OaksLabPoster.Sketch')
        visit(ash[1], *ash[3], ash[4])
        battle('ASH_T')
        print('Passed Red, four badges, Drake, the rescue, both psychic encounters, the Cup, '
              'a final-round loss and retry, the sketch and the friendly rematch.')
    finally:
        g.pb.stop(save=False)


if __name__ == '__main__':
    main(sys.argv[1])
