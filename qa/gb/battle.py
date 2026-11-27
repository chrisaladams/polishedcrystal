"""Battle-driving helpers (button input; HP injection is marked INJECTED)."""
from . import fixtures as F

TILE = 16


def vtiles2_tiles(g, first, count, vbk=0):
    """Raw bytes of tiles first..first+count-1 of vTiles2 in VRAM bank vbk."""
    base = g.sym['vTiles2'][1] - 0x8000 + first * TILE
    return g.vram(vbk)[base:base + count * TILE]


def mash(g, button='a', presses=1, hold=4, wait=26):
    for _ in range(presses):
        g.press(button, hold, wait)


def cup_select_three(g):
    """At the Rising Star Cup organiser, facing him: talk through the rules and pick
    the first three party Pokemon in the Battle-Tower style menu. Pure input."""
    g.pb.button('up', 4) if hasattr(g, 'pb') else g.press('up')
    g.tick(20)
    for _ in range(14):
        g.press('a', 4, 30)        # greeting, rules, 'Enter?' -> Yes
    for b in ['a', 'a', 'down', 'a', 'a', 'down', 'a', 'a', 'a']:
        g.press(b, 4, 24)          # pick Pokemon 1-3 (Enter) then confirm
    g.tick(120)
