"""Ways of reaching a game state, each labelled with how honest it is.

Provenance levels (reported with every test):
  GAMEPLAY  - reached only by button presses from power-on
  INJECTED  - memory writes / direct routine calls were used to skip ahead
"""
import os
import shutil

from .consts import C, map_ids
from .emu import Game

GAMEPLAY = 'gameplay'
INJECTED = 'injected'


def new_game_to_bedroom(g, max_presses=400):
    """Power on, choose New Game and accept every default by pressing A.
    Returns the number of presses. Pure button input."""
    g.tick(900)
    g.press('start', 4, 20)
    g.press('start', 4, 20)
    for i in range(max_presses):
        g.press('a', 4, 14)
        if (g.rd('wMapGroup'), g.rd('wMapNumber')) == map_ids('PLAYERS_HOUSE_2F'):
            g.tick(120)
            return i + 1
    raise TimeoutError('never reached the bedroom')


def give_mon(g, species, level, form=0):
    """Add a Pokemon to the party by calling the ROM's own GivePoke (INJECTED)."""
    g.wr('wCurPartySpecies', species & 0xff)
    g.wr('wCurPartyLevel', level)
    g.wr('wCurForm', form)
    g.wr('wCurItem', 0)
    g.wr('wCurPlayerMove', 0)
    g.call('GivePoke', bc=0, de=0, hl=0, mash='b')
    g.tick(60)


def teleport(g, group, number, x, y, settle=600):
    """Warp by writing the map and coordinates and replaying map setup (INJECTED)."""
    for n, v in (('wMapGroup', group), ('wMapNumber', number), ('wXCoord', x), ('wYCoord', y),
                 ('wDefaultSpawnpoint', 255), ('wMapStatus', 1)):
        g.wr(n, v)
    g.mem[0xff92] = 0xf1        # hMapEntryMethod = MAPSETUP_WARP
    g.tick(settle)


def where(g):
    return g.rd('wMapGroup'), g.rd('wMapNumber'), g.rd('wXCoord'), g.rd('wYCoord')
