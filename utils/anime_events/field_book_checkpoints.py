"""Exercise the directions in the running game using completed quest milestones."""
from test_wild_mons import rgbasm_values

# (page expected, state change that completes it). A leading minus clears
# a hide flag when its character returns to their gym.
ROUTE = (
    ('Starter', 'GOT_A_POKEMON_FROM_ELM'), ('Errand', 'GOT_MYSTERY_EGG_FROM_MR_POKEMON'),
    ('ReturnEgg', 'GAVE_MYSTERY_EGG_TO_ELM'), ('Tower', 'GOT_TM70_FLASH'),
    ('Cave', '-VIOLET_GYM_FALKNER'), ('Violet', 'ENGINE_ZEPHYRBADGE'),
    ('Aide', 'GOT_TOGEPI_EGG_FROM_ELMS_AIDE'), ('Well', 'CLEARED_SLOWPOKE_WELL'),
    ('Bugsy', 'ENGINE_HIVEBADGE'), ('Cut', 'GOT_HM01_CUT'),
    ('Quiz', 'ENGINE_RADIO_CARD'), ('Whitney', 'ENGINE_PLAINBADGE'),
    ('Bottle', 'GOT_SQUIRTBOTTLE'), ('Tree', 'FOUGHT_SUDOWOODO'),
    ('BurnedTower', 'RELEASED_THE_BEASTS'), ('Morty', 'ENGINE_FOGBADGE'),
    ('Surf', 'GOT_HM03_SURF'), ('Lighthouse', 'JASMINE_EXPLAINED_AMPHYS_SICKNESS'),
    ('Medicine', 'GOT_SECRETPOTION_FROM_PHARMACY'), ('Chuck', 'ENGINE_STORMBADGE'),
    ('Amphy', 'JASMINE_RETURNED_TO_GYM'), ('Jasmine', 'ENGINE_MINERALBADGE'),
    ('Lake', 'DECIDED_TO_HELP_LANCE'), ('Hideout', 'CLEARED_ROCKET_HIDEOUT'),
    ('Pryce', 'ENGINE_GLACIERBADGE'), ('Takeover', 'BEAT_PETREL_1'),
    ('Director', 'RECEIVED_CARD_KEY'), ('CardKey', 'CLEARED_RADIO_TOWER'),
    ('Waterfall', 'GOT_HM06_WATERFALL'), ('Clair', 'BEAT_CLAIR'),
    ('DragonDen', 'ENGINE_RISINGBADGE'), ('League', 'BEAT_ELITE_FOUR'),
    ('Ticket', 'GOT_SS_TICKET_FROM_ELM'), ('Ship', 'FAST_SHIP_FIRST_TIME'),
    ('Surge', 'ENGINE_THUNDERBADGE'), ('Plant', 'MET_MANAGER_AT_POWER_PLANT'),
    ('Grunt', 'MET_ROCKET_GRUNT_AT_CERULEAN_GYM'), ('Bridge', 'LEARNED_ABOUT_MACHINE_PART'),
    ('Part', 'FOUND_MACHINE_PART_IN_CERULEAN_GYM'), ('Restore', 'RESTORED_POWER_TO_KANTO'),
    ('Cape', '-TRAINERS_IN_CERULEAN_GYM'), ('Misty', 'ENGINE_CASCADEBADGE'),
    ('Sabrina', 'ENGINE_MARSHBADGE'), ('Erika', 'ENGINE_RAINBOWBADGE'),
    ('Janine', 'ENGINE_SOULBADGE'), ('Radio', 'ENGINE_EXPN_CARD'), ('Flute', 'FOUGHT_SNORLAX'),
    ('Brock', 'ENGINE_BOULDERBADGE'), ('Blaine', 'ENGINE_VOLCANOBADGE'),
    ('Cinnabar', '-VIRIDIAN_GYM_BLUE'), ('Blue', 'ENGINE_EARTHBADGE'),
    ('Rematch', 'BEAT_ELITE_FOUR_AGAIN'), ('Oak', 'OPENED_MT_SILVER'),
)

ERRANDS = (
    ('Later', 'ENGINE_FLYPOINT_GOLDENROD'), ('Kenya', 'GOT_KENYA'),
    ('Deliver', 'GAVE_KENYA'), ('Reward', 'GOT_HP_UP_FROM_RANDY'),
    ('NoLeads', 'ENGINE_FLYPOINT_OLIVINE'), ('Berries', 'HEALED_MOOMOO'),
    ('NoLeads', 'RESTORED_POWER_TO_KANTO'), ('Copycat', 'MET_COPYCAT_FOUND_OUT_ABOUT_LOST_ITEM'),
    ('Club', 'GOT_LOST_ITEM_FROM_FAN_CLUB'), ('Pass', 'GOT_PASS_FROM_COPYCAT'),
)


def guide_checkpoints(g, read):
    def constant(milestone):
        name = milestone.lstrip('-')
        return name if name.startswith('ENGINE_') else 'EVENT_' + name

    values = rgbasm_values({constant(flag) for _, flag in ROUTE + ERRANDS}, None)
    bank, table = g.sym['EngineFlags']

    def change(milestone, completed):
        name = constant(milestone)
        value = values[name]
        if name.startswith('ENGINE_'):
            entry = table + 3 * value
            addr = g.m[bank, entry] + 256 * g.m[bank, entry + 1]
            mask = g.m[bank, entry + 2]
        else:
            addr = g.addr('wEventFlags') + value // 8
            mask = 1 << (value % 8)
        index = (1, addr) if addr >= 0xd000 else addr
        if completed != milestone.startswith('-'):
            g.m[index] |= mask
        else:
            g.m[index] &= ~mask

    original = g.state()
    for _, flag in ROUTE + ERRANDS:
        change(flag, False)
    start = g.state()
    pages = [name for name, _ in ROUTE] + ['Red']
    previous = 'Begin'
    for index, (page, flag) in enumerate(ROUTE):
        read('FieldBookNotes.' + page, recap=(previous, pages[index + 1]))
        change(flag, True)
        previous = page
    read('FieldBookNotes.Red', recap=('Oak', 'Alph'))
    g.load(start)
    for page, flag in ERRANDS:
        read('FieldBookNotes.' + page, side=True)
        change(flag, True)
    read('FieldBookNotes.NoLeads', side=True)
    g.load(original)
    print('Checked Johto and Kanto directions and three optional errands.', flush=True)
