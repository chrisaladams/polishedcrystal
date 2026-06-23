"""Shared held-item constants/helpers for the 6v6 engine.

Multiplier/heuristic-style items: Choice Band/Specs/Scarf, Life Orb,
Leftovers, Eviolite, Toxic Orb, Flame Orb, Focus Sash. Not modeled: weather
rocks, type-boosting plates, Sitrus Berry, Black Sludge, Assault Vest, Rocky
Helmet, etc. -- the most commonly cited balance-relevant items, not an
exhaustive item layer.

Toxic/Flame Orb exist specifically to activate the conditional abilities that
were otherwise dead weight without a self-status trigger: Poison Heal (always
wants Toxic Orb), Guts (always wants Flame Orb -- burn boosts Atk and Guts
cancels the physical halving), Quick Feet (wants Toxic Orb over Flame Orb,
since without Guts the burn Atk-halving is a real cost Quick Feet doesn't
need). This directly un-blocks Gliscor's Poison Heal, previously flagged as
"can't activate, number is unreliable."

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

# roster median bulk (hp + (def+spd)/2), used to flag "frail" sweepers that
# want Focus Sash over Choice Scarf/Life Orb (see teams.classify's docstring
# for the same thresholds).
FOCUS_SASH_BULK_THRESHOLD = 326


def eviolite_eligible(mid, mon):
    return (not mon.get('fully_evolved') and not mon.get('legendary')
            and mid not in EVIOLITE_EXCLUDED)


def pick_item(mid, mon, role, ability=None):
    """One heuristic item per mon for a whole 6v6 battle."""
    if eviolite_eligible(mid, mon):
        return 'EVIOLITE'
    s = mon['stats']
    if ability == 'POISON_HEAL':
        return 'TOXIC_ORB'
    if ability == 'GUTS':
        return 'FLAME_ORB'
    if ability == 'QUICK_FEET':
        return 'TOXIC_ORB'
    if role in ('wall', 'pivot'):
        return 'LEFTOVERS'
    if role == 'tank':
        return 'CHOICE_BAND' if s['atk'] >= s['spa'] else 'CHOICE_SPECS'
    if role == 'sweeper':
        bulk = s['hp'] + (s['defe'] + s['spd']) // 2
        if bulk < FOCUS_SASH_BULK_THRESHOLD:
            return 'FOCUS_SASH'
        return 'CHOICE_SCARF' if s['spe'] < 160 else 'LIFE_ORB'
    return 'LEFTOVERS'
