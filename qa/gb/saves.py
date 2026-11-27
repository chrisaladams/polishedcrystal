"""Save fixtures: built once by driving the game, cached by ROM hash, reused by
every backend (PyBoy, SameBoy, Gearboy) by loading them as battery RAM and
pressing Continue. The save itself is written by the game's own routine."""
import hashlib
import os

from .consts import C, map_ids
from .emu import ROOT, Game, default_rom, sha1
from . import fixtures as F

CACHE = os.environ.get('QA_CACHE') or os.path.join(ROOT, 'qa', '.cache')
SRAM_BANKS, SRAM_BANK_SIZE = 4, 0x2000


def cache_dir(rom=None):
    d = os.path.join(CACHE, sha1(rom or default_rom())[:12])
    os.makedirs(d, exist_ok=True)
    return d


def dump_sram(g):
    """All 32 KiB of cartridge RAM from a running PyBoy Game."""
    return bytes(g.mem[bank, 0xa000 + i] for bank in range(SRAM_BANKS) for i in range(SRAM_BANK_SIZE))


def save_game(g):
    """Write the save with the game's own SilentGameSave routine (INJECTED)."""
    g.call('SilentGameSave', mash=None)
    g.tick(30)
    return dump_sram(g)


def boot_continue(g, expect, max_presses=60):
    """From power-on, press Start/A through the title and Continue until the saved
    map and position are loaded (expect = (group, number, x, y), from fixture()'s
    metadata). Pure button input; works on any backend. Returns frames used.

    The check must compare a full position: with randomised power-on RAM the map
    variables hold garbage until Continue loads them."""
    g.tick(900)
    start = g.frame
    for i in range(max_presses):
        g.press('start' if i < 2 else 'a', 4, 20)
        if F.where(g) == tuple(expect) and g.rd('wMapStatus') == 2:
            g.tick(90)
            if F.where(g) == tuple(expect):
                return g.frame - start
    raise TimeoutError('Continue never reached %r (at %r)' % (tuple(expect), F.where(g)))


def set_event(g, name, value=True):
    """Set or clear an event flag by constant name (INJECTED)."""
    n = C[name]
    byte, bit = n >> 3, n & 7
    cur = g.rd('wEventFlags', byte)
    g.wr('wEventFlags', (cur | 1 << bit) if value else (cur & ~(1 << bit)), byte)


def fixture_meta(path):
    import json
    return json.load(open(path[:-4] + '.json'))


def fixture(name, builder, rom=None, rebuild=False):
    """Path to the cached save `name`; builder(game) -> None builds it on a Game
    that has just finished a New Game (button input) and stands in the bedroom."""
    path = os.path.join(cache_dir(rom), name + '.sav')
    if os.path.exists(path) and not rebuild:
        return path
    g = Game(rom=rom, workdir=os.path.join(cache_dir(rom), 'build-' + name))
    F.new_game_to_bedroom(g)
    builder(g)
    sram = save_game(g)
    with open(path, 'wb') as f:
        f.write(sram)
    import json
    with open(path[:-4] + '.json', 'w') as f:
        json.dump({'where': F.where(g), 'rom_sha1': sha1(rom or default_rom()),
                   'provenance': 'new game by button input, then injected: ' + (builder.__doc__ or builder.__name__)}, f)
    g.close()
    return path
