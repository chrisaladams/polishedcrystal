"""Assisted story-stage checkpoints.

Playing the whole game legitimately is slow; most scenario testing needs a game in a
particular *stage* (N badges, a strong party, the Pokegear). The ladder builds those
states by taking a real New Game (button input to the bedroom) and then INJECTING the
stage: badge bits, engine flags, a party (via the ROM's own GivePoke), money, and a
warp to that stage's city. Every checkpoint is labelled `assisted` and records exactly
what was injected, so nothing is passed off as legitimate play. A separate background
campaign (qa/gb/campaign.py) keeps checking that real play reaches the early stages.

Checkpoints are machine snapshots (PyBoy or SameBoy loadable only by the backend that
made them), cached under qa/.cache/ladder/<rom sha1>/.
"""
import json
import os

from .consts import C, map_ids
from .emu import Game, default_rom, sha1
from . import fixtures as F, saves

JOHTO_BADGES = ['ZEPHYR', 'HIVE', 'PLAIN', 'FOG', 'MINERAL', 'STORM', 'GLACIER', 'RISING']
KANTO_BADGES = ['BOULDER', 'CASCADE', 'THUNDER', 'RAINBOW', 'MARSH', 'SOUL', 'VOLCANO', 'EARTH']
TEAM = ['CHARIZARD', 'BLASTOISE', 'VENUSAUR', 'PIKACHU', 'ALAKAZAM', 'GENGAR', 'TYRANITAR', 'DRAGONITE']

# name, badges earned, party level, party size, city where the player stands
STAGES = [
    ('starter',   0, 5,  1, 'ELMS_LAB'),
    ('violet',    1, 14, 3, 'VIOLET_CITY'),
    ('azalea',    2, 18, 4, 'AZALEA_TOWN'),
    ('goldenrod', 3, 24, 5, 'GOLDENROD_CITY'),
    ('ecruteak',  4, 30, 6, 'ECRUTEAK_CITY'),
    ('cianwood',  5, 34, 6, 'CIANWOOD_CITY'),
    ('olivine',   6, 38, 6, 'OLIVINE_CITY'),
    ('mahogany',  7, 42, 6, 'MAHOGANY_TOWN'),
    ('blackthorn', 8, 50, 6, 'BLACKTHORN_CITY'),
    ('vermilion', 11, 56, 6, 'VERMILION_CITY'),
    ('fuchsia',   14, 62, 6, 'FUCHSIA_CITY'),
    ('indigo',    16, 75, 6, 'INDIGO_PLATEAU'),
    ('postgame',  16, 95, 6, 'PALLET_TOWN'),
]
BY_NAME = {s[0]: s for s in STAGES}


def cache_dir(rom=None):
    d = os.path.join(saves.CACHE, 'ladder', sha1(rom or default_rom())[:12])
    os.makedirs(d, exist_ok=True)
    return d


def set_engine_flag(g, name):
    g.call('EngineFlagAction', bc=1 << 8, de=C[name])


def apply_stage(g, stage):
    """Inject `stage` into a running game. Returns the list of what was injected."""
    name, nbadges, level, size, city = stage
    done = []
    for flag in ('ENGINE_POKEGEAR', 'ENGINE_PHONE_CARD', 'ENGINE_MAP_CARD', 'ENGINE_RADIO_CARD', 'ENGINE_EXPN_CARD',
                 'ENGINE_POKEDEX'):
        set_engine_flag(g, flag)
    done.append('pokegear cards + pokedex flags')
    j = (1 << min(nbadges, 8)) - 1
    k = (1 << max(0, nbadges - 8)) - 1
    g.wr('wJohtoBadges', j)
    g.wr('wKantoBadges', k)
    done.append(f'{nbadges} badge bits')
    g.wr('wMoney', 0x0f)
    g.wr('wMoney', 0x42, 1)
    g.wr('wMoney', 0x3f, 2)
    done.append('999999 money')
    species = ['TOTODILE'] if name == 'starter' else TEAM[:size]
    for sp in species:
        F.give_mon(g, C[sp], level)
    done.append(f'party {species} at level {level}')
    return done


def build(stage_name, rom=None, rebuild=False):
    """Path of the checkpoint for `stage_name` (built on first use)."""
    stage = BY_NAME[stage_name]
    d = cache_dir(rom)
    path = os.path.join(d, stage_name + '.state')
    meta = path[:-6] + '.json'
    if os.path.exists(path) and os.path.exists(meta) and not rebuild:
        return path
    with saves.build_lock(path):
        if os.path.exists(path) and os.path.exists(meta) and not rebuild:
            return path
        g = Game(rom=rom, workdir=os.path.join(d, 'build-' + stage_name))
        F.new_game_to_bedroom(g)
        done = apply_stage(g, stage)
        gr, nr = map_ids(stage[4])
        from qa.tests.test_map_smoke import pick_tile        # a walkable tile from the map's own collision data
        F.teleport(g, gr, nr, 2, 2, settle=60)
        tile = pick_tile(g) or (2, 2)
        F.teleport(g, gr, nr, tile[0], tile[1], settle=90)
        g.tick(60)
        g.dump_state(path)
        json.dump({'stage': stage_name, 'where': F.where(g), 'provenance': 'assisted',
                   'real': 'New Game to the bedroom by button input', 'injected': done + [f'warp to {stage[4]}'],
                   'rom_sha1': sha1(rom or default_rom())}, open(meta, 'w'), indent=1)
        g.close()
    return path


def load(g, stage_name, rom=None):
    """Load checkpoint `stage_name` into game g (a PyBoy Game of the same ROM)."""
    g.tick(30)
    g.load_state_file(build(stage_name, rom))
    g.tick(5)
