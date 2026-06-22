"""Shared held-item constants/helpers for the 6v6 engine.

Multiplier/heuristic-style items only: Choice Band/Specs/Scarf, Life Orb,
Leftovers, Eviolite. Not modeled: weather rocks, type-boosting plates,
Sitrus Berry, Focus Sash, orbs, etc. -- the most commonly cited
balance-relevant items, not an exhaustive item layer.

Eviolite eligibility mirrors the shipped restriction in
engine/battle/effect_commands.asm (EvioliteExcludedSpecies): strong
cross-gen pre-evolutions are excluded even though they're NFE.
"""

EVIOLITE_EXCLUDED = {
    'scyther', 'rhydon', 'porygon2', 'electabuzz', 'magmar', 'magneton',
    'ursaring', 'piloswine', 'tangela', 'lickitung', 'golbat', 'dunsparce',
    'gligar', 'togetic', 'seadra', 'girafarig', 'stantler', 'primeape',
    'qwilfish_plain', 'qwilfish_hisuian', 'mr__mime_plain', 'mr__mime_galarian',
}

CHOICE_STAT_MULT = 1.5      # Band: atk, Specs: spa
CHOICE_SCARF_SPEED_MULT = 1.5
LIFE_ORB_DMG_MULT = 1.3
LIFE_ORB_RECOIL_FRAC = 1 / 10
LEFTOVERS_HEAL_FRAC = 1 / 16
EVIOLITE_DEF_MULT = 1.5


def eviolite_eligible(mid, mon):
    return (not mon.get('fully_evolved') and not mon.get('legendary')
            and mid not in EVIOLITE_EXCLUDED)


def pick_item(mid, mon, role):
    """One heuristic item per mon for a whole 6v6 battle."""
    if eviolite_eligible(mid, mon):
        return 'EVIOLITE'
    s = mon['stats']
    if role in ('wall', 'pivot'):
        return 'LEFTOVERS'
    if role == 'tank':
        return 'CHOICE_BAND' if s['atk'] >= s['spa'] else 'CHOICE_SPECS'
    if role == 'sweeper':
        return 'CHOICE_SCARF' if s['spe'] < 160 else 'LIFE_ORB'
    return 'LEFTOVERS'
