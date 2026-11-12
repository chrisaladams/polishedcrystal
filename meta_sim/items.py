"""Shared held-item constants/helpers for the 6v6 engine.

Multiplier/heuristic-style items: Choice Band/Specs/Scarf, Life Orb,
Leftovers, Eviolite, Toxic Orb, Flame Orb, Focus Sash. Not modeled: weather
rocks, type-boosting plates, Sitrus Berry, Black Sludge, Assault Vest, Rocky
Helmet, etc. -- the most commonly cited balance-relevant items, not an
exhaustive item layer.

Toxic/Flame Orb exist to switch on the abilities that need a self-inflicted
status: Poison Heal (Toxic Orb), Guts (Flame Orb: burn's Atk halving is
cancelled by Guts), and Quick Feet (Toxic Orb, since without Guts a burn's
Atk drop is a pure cost).

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

# Sweepers frailer than this (hp + (def+spd)/2 at L50) take Focus Sash instead
# of Choice Scarf / Life Orb: they are the ones most often OHKO'd from full.
FOCUS_SASH_BULK_THRESHOLD = 326

# Ability -> the self-status orb that activates it.
ORB_FOR_ABILITY = {'POISON_HEAL': 'TOXIC_ORB', 'GUTS': 'FLAME_ORB',
                   'QUICK_FEET': 'TOXIC_ORB'}
ORB_STATUS = {'TOXIC_ORB': 'tox', 'FLAME_ORB': 'brn'}


def eviolite_eligible(mid, mon):
    return (not mon.get('fully_evolved') and not mon.get('legendary')
            and mid not in EVIOLITE_EXCLUDED)


def pick_item(mid, mon, role, ability=None):
    """One heuristic item per mon for a whole 6v6 battle."""
    if eviolite_eligible(mid, mon):
        return 'EVIOLITE'
    s = mon['stats']
    if ability in ORB_FOR_ABILITY:
        return ORB_FOR_ABILITY[ability]
    if role in ('wall', 'pivot'):
        return 'LEFTOVERS'
    if role == 'tank':
        return 'CHOICE_BAND' if s['atk'] >= s['spa'] else 'CHOICE_SPECS'
    if role == 'sweeper':
        if s['hp'] + (s['defe'] + s['spd']) // 2 < FOCUS_SASH_BULK_THRESHOLD:
            return 'FOCUS_SASH'
        return 'CHOICE_SCARF' if s['spe'] < 160 else 'LIFE_ORB'
    return 'LEFTOVERS'
