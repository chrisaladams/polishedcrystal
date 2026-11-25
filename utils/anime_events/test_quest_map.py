#!/usr/bin/env python3
"""Open the Pokégear map from START and exercise live and cross-region quest markers."""
import re
import sys
from pathlib import Path

from test_orange_league import ROOT
from test_wild_mons import Game, rgbasm_values

def main(path):
    root = Path(ROOT)
    g = Game(Path(path).read_bytes())
    source = (root / 'data/events/field_book.asm').read_text() + (root / 'engine/pokegear/quest_map.asm').read_text()
    flags = set(re.findall(r'\bEVENT_[A-Z0-9_]+', source))
    goal_names = re.findall(r'^\s*map_goal (\w+),', (root / 'data/events/quest_map_goals.asm').read_text(), re.M)
    k = rgbasm_values(flags | {'POKEGEAR_MAP_CARD_F', 'POKEGEAR_OBTAINED_F', 'SPAWN_GOLDENROD',
                                'SPAWN_OLIVINE', 'SPROUT_TOWER', 'DARK_CAVE', 'RUINS_OF_ALPH',
                                'OLIVINE_CITY', 'CERULEAN_CAVE', 'CINNABAR_ISLAND', 'WARM_BEACH',
                                'SHAMOUTI_ISLAND', 'SHRINE_RUINS', 'ICE_ISLAND', 'LIGHTNING_ISLAND',
                                'GOLDENROD_CITY', 'ECRUTEAK_CITY', 'NATIONAL_PARK', 'PALLET_TOWN',
                                'SPAWN_ECRUTEAK', 'CUP_RECORDS_MAGIC_1', 'CUP_RECORDS_MAGIC_2',
                                'CUPWON_RISING_STAR_F', 'CUPWON_RENTAL_F', 'CUPWON_DRAGON_F', 'WATER',
                                'ROUTE_31','ROUTE_39','CERULEAN_CITY','VERMILION_CITY','NEW_BARK_TOWN',
                                'SPAWN_AZALEA','SPAWN_VIOLET','GROUP_VIOLET_POKECENTER_1F','MAP_VIOLET_POKECENTER_1F'}, None)
    def bit(var, n, on=True):
        idx, mask = n // 8, 1 << (n % 8)
        v = g.rd(var, idx)
        g.wr(var, v | mask if on else v & ~mask, idx)

    def event(name, on=True):
        bit('wEventFlags', k['EVENT_' + name], on)

    def open_map():
        g.highlight_start_option('PokegearString')
        g.press('a', 180)
        g.press('right', 130)
        assert g.rd('wPokegearCard') == 1 and g.rd('wJumptableIndex') in (4, 6, 8), (g.rd('wPokegearCard'),g.rd('wJumptableIndex'),g.rd('wInPokegear'),g.rd('wPokegearFlags'))
        return [goal_names[g.rd('wQuestMapLeads', i)] for i in range(g.rd('wQuestMapCount'))]

    def tile(x, y):
        return g.rd('wTilemap', 20*y+x)

    def pin(landmark, value):
        bank, addr = g.sym['Landmarks']
        addr += 4 * k[landmark]
        x, y = (g.m[bank, addr] - 8)//8, (g.m[bank, addr+1] - 16)//8
        assert tile(x,y) == value, (landmark, x, y, hex(tile(x,y)), hex(value))
        assert g.rd('wAttrmap', 20*y+x) == 0

    def browse():
        g.press('select', 60)
        assert g.rd('wQuestMapSelected') == 0
    def select(goals_on_map, name):
        i = goals_on_map.index(name)
        for _ in goals_on_map:
            if i == g.rd('wQuestMapSelected'):
                return
            g.press('down', 14)
        raise AssertionError('Could not select ' + name)

    try:
        g.boot()
        base = g.state()
        for flag in flags:
            bit('wEventFlags', k[flag], False)
        g.wr('wJohtoBadges', 0)
        g.wr('wKantoBadges', 0)
        for suffix in ('GOLDENROD', 'OLIVINE', 'VIOLET', 'AZALEA', 'ECRUTEAK'):
            bit('wVisitedSpawns', k['SPAWN_' + suffix], False)
        for f in ('POKEGEAR_MAP_CARD_F', 'POKEGEAR_OBTAINED_F'):
            bit('wPokegearFlags', k[f])
        for flag in ('GOT_A_POKEMON_FROM_ELM', 'GOT_MYSTERY_EGG_FROM_MR_POKEMON',
                     'GAVE_MYSTERY_EGG_TO_ELM','VIOLET_GYM_FALKNER'):
            event(flag)
        early = g.state()
        leads = open_map()
        assert leads == ['Tower','Cave'], leads
        pin('SPROUT_TOWER', 0xec)
        pin('DARK_CAVE', 0x9f)
        browse()
        select(leads, 'Cave')
        pin('SPROUT_TOWER', 0x9f)
        pin('DARK_CAVE', 0xec)
        showed = []
        g.pb.hook_register(*g.sym['FarPrintText'], lambda _: showed.append(g.pb.register_file.HL), None)
        redraws = []
        g.pb.hook_register(*g.sym['DrawQuestMapBrowser'], redraws.append, True)
        g.press('a', 60)
        assert g.sym['FieldBookNotes.Cave'][1] in showed
        for _ in range(15):
            g.press('b', 15)
            if redraws:
                break
        else:
            raise AssertionError('directions did not return to the map')
        g.press('b', 60)
        pin('SPROUT_TOWER', 0xec)
        g.press('b', 90)
        assert not g.rd('wInPokegear')
        g.load(early)
        # Use the actual wall map at Violet's Pokémon Center, before acquiring a Map Card.
        bit('wPokegearFlags', k['POKEGEAR_MAP_CARD_F'], False)
        g.warp(k['GROUP_VIOLET_POKECENTER_1F'], k['MAP_VIOLET_POKECENTER_1F'], 9, 1)
        g.face('up')
        for _ in range(12):
            g.press('a', 50)
            if tile(10, 7) == 0xec:
                break
        pin('SPROUT_TOWER', 0xec)
        browse()
        select(leads, 'Cave')
        pin('DARK_CAVE', 0xec)
        g.press('b', 55)
        pin('SPROUT_TOWER', 0xec)
        g.press('b', 60)
        g.load(early)
        event('GOT_TM70_FLASH')
        leads = open_map()
        assert leads == ['Cave'], leads
        g.load(early)
        for flag in ('GOT_MYSTICTICKET_FROM_RED','GOT_KENYA','RESTORED_POWER_TO_KANTO',
                     'GOT_A_POKEMON_FROM_IVY','TIME_TRAVEL_FINISHED'):
            event(flag)
        bit('wVisitedSpawns', k['SPAWN_OLIVINE'])
        late = g.state()
        leads = open_map()
        assert set(leads) == set('Alph Mask CloneReport Cup Cissy Danny Rudy Luana Deliver Berries Copycat'.split()), leads
        pin('RUINS_OF_ALPH', 0xec)
        pin('OLIVINE_CITY', 0x9f)
        pin('ROUTE_31', 0x9f)
        pin('ROUTE_39', 0x9f)
        browse()
        select(leads, 'CloneReport')
        assert g.rd('wQuestMapRegion') == 1
        pin('CINNABAR_ISLAND', 0xec)
        select(leads, 'Cissy')
        assert g.rd('wQuestMapRegion') == 2
        pin('WARM_BEACH', 0xec)
        g.press('b', 55)
        pin('RUINS_OF_ALPH', 0xec)
        g.load(late)
        event('GOT_ORANGE_TICKET')
        event('READ_CINNABAR_CLONE_REPORT')
        leads = open_map()
        assert 'ShoreKeeper' in leads and 'Echo' in leads and 'CloneReport' not in leads, leads
        browse()
        select(leads, 'ShoreKeeper')
        pin('SHRINE_RUINS', 0xec)
        g.load(late)
        event('HEARD_SHAMOUTI_BEACONS')
        event('TUNED_FIRE_BEACON')
        leads = open_map()
        assert {'IceBeacon', 'LightningBeacon'} <= set(leads) and 'FireBeacon' not in leads, leads
        browse()
        select(leads, 'IceBeacon')
        pin('ICE_ISLAND', 0xec)
        pin('LIGHTNING_ISLAND', 0x9f)
        g.load(late)
        event('BEAT_MOLLY')
        event('BEAT_ORANGE_CREW_CISSY')
        event('GOT_A_POKEMON_FROM_IVY', False)
        leads = open_map()
        assert 'Cissy' not in leads and 'Alph' not in leads and leads[0] == 'Hale', leads
        browse()
        select(leads, 'Luana')
        pin('SHAMOUTI_ISLAND', 0xec)
        g.load(early)
        for flag in ('FOUGHT_SUDOWOODO','GOT_HM03_SURF','JASMINE_EXPLAINED_AMPHYS_SICKNESS',
                     'GOT_SECRETPOTION_FROM_PHARMACY'):
            event(flag)
        g.wr('wJohtoBadges', 0x0f)
        leads = open_map()
        assert 'Chuck' in leads and 'Amphy' in leads and 'Medicine' not in leads, leads
        g.load(early)
        for flag in ('BEAT_ELITE_FOUR','FAST_SHIP_FIRST_TIME','GOT_SS_TICKET_FROM_ELM'):
            event(flag)
        leads = open_map()
        assert set(leads) == {'Surge','Sabrina','Erika','Janine','Plant'}, leads
        browse()
        pin('VERMILION_CITY', 0xec)

        g.load(early)
        for city in ('GOLDENROD', 'ECRUTEAK'):
            bit('wVisitedSpawns', k['SPAWN_' + city])
        g.wr('wJohtoBadges', 0xff)
        g.wr('wCupRecordsMagic', 0)
        g.wr('wCupRecords', 0xff)  # an older save's party data, before cup records exist
        g.wr('wRTCDayLo', 2)
        g.wr('wRTCHours', 12)
        cups = g.state()
        leads = open_map()
        assert {'RisingCup', 'RentalCup', 'KimonoCup', 'DragonCup'} <= set(leads), leads
        assert g.rd('wCupRecords') == 0xff and g.rd('wCupRecordsMagic') == 0
        browse()
        select(leads, 'RentalCup')
        pin('GOLDENROD_CITY', 0xec)
        select(leads, 'KimonoCup')
        pin('ECRUTEAK_CITY', 0xec)
        g.wr('wCupFoeType', 0xff)
        g.press('a', 60)
        assert g.rd('wCupFoeType') == k['WATER']

        g.load(cups)
        for i, marker in enumerate(('CUP_RECORDS_MAGIC_1', 'CUP_RECORDS_MAGIC_2')):
            g.wr('wCupRecordsMagic', k[marker], i)
        g.wr('wCupRecords', sum(1 << k['CUPWON_' + s + '_F'] for s in ('RISING_STAR', 'RENTAL', 'DRAGON')))
        event('RISING_STAR_PRIZE_PENDING')
        leads = open_map()
        assert {'RisingCup', 'KimonoCup'} <= set(leads), leads
        assert not {'RentalCup', 'DragonCup'} & set(leads), leads

        g.load(cups)
        g.highlight_start_option('FieldBookString')
        g.press('a', 50)
        for _ in range(3):
            g.press('down', 20)
        g.press('a', 45)
        for _ in range(2):
            g.press('down', 20)
        shown = []
        g.pb.hook_register(*g.sym['MapTextbox'], lambda _: shown.append(g.pb.register_file.HL), None)
        g.wr('wCupFoeType', 0xff)
        g.press('a', 65)
        g.pb.hook_deregister(*g.sym['MapTextbox'])
        assert g.sym['FieldBookNotes.KimonoCup'][1] in shown and g.rd('wCupFoeType') == k['WATER']

        g.load(early)
        for flag in ('GOT_MYSTICTICKET_FROM_RED','WON_PALLET_INVITATIONAL','RESCUED_PROF_HALE',
                     'BEAT_IRON_MASK_MARAUDER','BEAT_MEWTWO_CLONES','BEAT_DRAKE','WON_WHIRL_CUP'):
            event(flag)
        finale = g.state()
        event('WHIRL_CUP_PRIZE_PENDING')
        leads = open_map()
        assert set(leads) == {'Sammy', 'Cup'}, leads
        browse()
        select(leads, 'Sammy')
        pin('PALLET_TOWN', 0xec)
        g.load(finale)
        event('OAK_WAS_SAMMY')
        assert not open_map()
        browse()
        g.press('b', 50)
        g.press('b', 60)
        assert not g.rd('wInPokegear')
        g.load(base)
        print('Passed progression pins, cup and reward leads, the Kimono type in both guides, cross-region browsing, completion and exit.')
    finally:
        g.pb.stop(save=False)

if __name__ == '__main__':
    main(sys.argv[1])
