"""Pragmatic 6v6 battle engine + heuristic AI for meta-tuning.

This is the "Option A" engine: a clean, uniform turn simulator built on the
same L50 data the 1v1 matrix uses. It is NOT a port of the ROM's trainer AI
(engine/battle/ai/*.asm, ~4400 lines) -- it is a consistent yardstick applied
identically to both sides so cross-mon comparison is fair.

Models the high-impact ~80% of mechanics and approximates the long tail:
  modelled : damage + STAB + type chart, stat stages, the major statuses
             (sleep/paralysis/burn/poison/toxic/freeze + confusion), on-hit
             secondary effects (status/flinch/recoil), self-stat setup moves,
             recovery, Leech Seed, entry hazards (Spikes/Toxic Spikes),
             priority, switching, and a heuristic move/switch AI. Sleep Clause
             is mirrored from the shipped game (toggle: SLEEP_CLAUSE).
             Switch-in/event abilities: Imposter (Transform onto the foe's
             current types/stats/stages/ability/moves -- self-disarming,
             since the ability slot is overwritten by the copy), Intimidate
             (-1 foe Attack on switch-in), Levitate (immune to Ground moves
             and grounded hazards), Sturdy (survives a lethal hit from full
             HP at 1 HP), Regenerator (heal 1/3 max HP on switching out).
             Type-absorb abilities (Flash Fire, Water/Volt Absorb, Sap
             Sipper, Dry Skin-as-water-absorb): immune to their type, plus
             the on-absorb effect (heal 1/4 max HP, +1 Atk, or a permanent
             1.5x Fire-move boost for the rest of the battle). Damage-
             modifier abilities: Guts (1.5x Atk while statused, ignores the
             burn Atk drop), Thick Fat (0.5x incoming Fire/Ice), Solid Rock/
             Filter (0.75x incoming super-effective), Multiscale (0.5x
             incoming damage at full HP), Unaware (ignores the other mon's
             relevant stat stage when computing damage). Residual-turn
             abilities: Magic Guard (immune to all indirect damage --
             hazards, status, Leech Seed, confusion, recoil, Belly Drum),
             Speed Boost (+1 Speed each turn), Poison Heal (poison/toxic
             heals 1/8 max HP instead of damaging), Rock Head (no recoil
             from recoil-effect moves, unlike Life Orb recoil which it
             doesn't block). Status-immunity abilities (Insomnia/Vital
             Spirit block sleep, Own Tempo blocks confusion, Limber blocks
             paralysis, Water Veil blocks burn, Immunity blocks poison/
             toxic, Magma Armor blocks freeze) checked at every status-
             inflicting move and on-hit secondary. Hustle (1.5x Atk, 0.8x
             accuracy on attacking moves), Tinted Lens (2x not-very-
             effective damage), Motor Drive (immune to Electric + Speed
             boost, alongside the absorb cluster above), Lightning Rod
             (+1 SpAtk when actually hit by an Electric move -- unlike
             Motor Drive it does not grant immunity). Status-utility
             abilities: Natural Cure (clears status on switch-out), Shed Skin
             (30%/turn chance to clear status), Synchronize (reflects a
             paralysis/burn/poison/toxic it receives back onto the inflictor),
             Serene Grace (doubles on-hit secondary-effect chance), and the
             contact-status abilities Static/Flame Body/Poison Point (30%
             chance to par/brn/psn an attacker whose move made contact, per
             the ROM's contact rule). Move-flag abilities: Iron Fist, Tough
             Claws, Mega Launcher, Sharpness, Reckless (damage boosts) and
             Bulletproof/Soundproof (immunities), plus Overcoat/Grass-type
             powder immunity and Quick Feet. Variable/fixed-power moves:
             Seismic Toss/Night Shade, Super Fang, Gyro Ball, Reversal,
             Return, Magnitude (average), Facade/Hex/Venoshock/Acrobatics.
             Items include Focus Sash and the Toxic/Flame Orbs that switch on
             Poison Heal/Guts/Quick Feet.
  approxd.  : confusion as a flat self-hit chance; multi-hit as its average
             hit count; two-turn moves resolve in one turn; Explosion = big
             hit then user faints; Low Kick is a flat 80 BP (no weights in
             the extracted data); Avalanche never doubles; Dry Skin modeled as Water Absorb only
             (its Fire weakness/sun-and-rain HP drain are not modeled). Each
             mon commits to one (non-event) ability and one item for the
             whole battle (see abilities.py/items.py) instead of switching
             among abilities per move like the 1v1 matrix does.
  support   : Reflect / Light Screen (5 turns, half damage), Protect
             (1/3^n repeat success), Sucker Punch (fails unless the target
             attacks), Encore (3 turns), Roar (forced switch into hazards),
             Haze, Pain Split, Heal Bell, Rapid Spin (clears hazards and
             Leech Seed), Curse (both forms), U-turn / Volt Switch (switch to
             the best matchup after the hit), Knock Off (1.5x and removes the
             item), drain moves, Close Combat's defence drops, and on-hit
             stat changes (Icy Wind, Psychic, Crunch, Ancient Power...).
  weather   : Sun / Rain / Sand / Hail from moves or Drought / Drizzle /
             Sand Stream / Snow Warning, 5 turns (8 with the matching rock):
             Fire / Water x1.5 / x0.5, Rock Sp.Def x1.5 in sand, Ice Def x1.5
             in hail, 1/16 sand / hail chip, Thunder / Hurricane never miss in
             rain (50% in sun), Blizzard never misses in hail, Solar Beam
             halved outside sun, Swift Swim / Chlorophyll / Sand Rush / Slush
             Rush double Speed, Sand Force, Solar Power, Rain Dish, Dry Skin,
             Ice Body, Hydration, Sand Veil / Snow Cloak, sun-boosted Growth
             and Synthesis-style healing, sun prevents freezing, Cloud Nine.
  more      : Substitute, Baton Pass (passes boosts, Substitute, Leech Seed),
             Trick (choice-locks the target into its next move), Trick Room,
             Swagger, Rest (full heal + 2 turns asleep) and Sleep Talk,
             Pursuit (double power on a switching target), trapping (Mean
             Look, Wrap / Fire Spin / Whirlpool with Binding Band / Grip
             Claw, Shadow Tag, Arena Trap, Magnet Pull; Ghost types, Run Away
             and Shed Shell escape), Perish Song, Counter / Mirror Coat.
  ignored   : Sketch / Metronome, Transform outside Imposter, and abilities /
             items beyond the modeled subset above and in abilities.py /
             items.py.

Playstyle metrics: every Pmon counts what it did in the battle (damage dealt
and absorbed, KOs, turns on the field, statuses, healing, hazards, screens,
cures, pivots, phazes, hazard clears, foe stat drops); run_battle(...,
detail=True) returns them per mon. See STAT_KEYS.

Damage uses a random roll (0.85-1.00) since this is Monte Carlo; crits off.
"""
import random

from typechart import STAB, type_mult
import abilities
import items

CHOICE_ITEMS = {'CHOICE_BAND', 'CHOICE_SPECS', 'CHOICE_SCARF'}
SLEEP_CLAUSE = False         # shipped game dropped the Sleep Clause (sleep is unrestricted, 1-3 turns); mirror that here
MAX_TURNS = 300              # battle longer than this -> draw (anti-stall guard)

# ---- stat-stage multipliers (Gen table) --------------------------------------
def stage_mult(stage):
    stage = max(-6, min(6, stage))
    return (2 + stage) / 2 if stage >= 0 else 2 / (2 - stage)

# ---- self-boost moves: effect -> {stat: delta} -------------------------------
BOOST = {
    'EFFECT_ATTACK_UP_2':  {'atk': 2}, 'EFFECT_DEFENSE_UP_2': {'defe': 2},
    'EFFECT_SPEED_UP_2':   {'spe': 2}, 'EFFECT_SP_ATK_UP_2':  {'spa': 2},
    'EFFECT_SP_DEF_UP_2':  {'spd': 2}, 'EFFECT_DEFENSE_CURL': {'defe': 1},
    'EFFECT_DRAGON_DANCE': {'atk': 1, 'spe': 1},
    'EFFECT_BULK_UP':      {'atk': 1, 'defe': 1},
    'EFFECT_CALM_MIND':    {'spa': 1, 'spd': 1},
    'EFFECT_GROWTH':       {'atk': 1, 'spa': 1},
    'EFFECT_HONE_CLAWS':   {'atk': 1},
    'EFFECT_SHELL_SMASH':  {'atk': 2, 'spa': 2, 'spe': 2, 'defe': -1, 'spd': -1},
}
# opponent stat-drop status moves
DROP = {'EFFECT_SPEED_DOWN_2': {'spe': -2}, 'EFFECT_ATTACK_DOWN_2': {'atk': -2},
        'EFFECT_DEFENSE_DOWN_2': {'defe': -2}, 'EFFECT_ACCURACY_DOWN': {'acc': -1}}

# status-inflicting status moves: effect -> status key
INFLICT = {'EFFECT_SLEEP': 'slp', 'EFFECT_PARALYZE': 'par', 'EFFECT_TOXIC': 'tox',
           'EFFECT_POISON': 'psn', 'EFFECT_BURN': 'brn', 'EFFECT_CONFUSE': 'cnf'}
# on-hit secondary status: effect -> status key (applied at `chance`%)
ONHIT = {'EFFECT_BURN_HIT': 'brn', 'EFFECT_PARALYZE_HIT': 'par',
         'EFFECT_FREEZE_HIT': 'frz', 'EFFECT_POISON_HIT': 'psn'}
HEAL_EFFECTS = {'EFFECT_HEAL', 'EFFECT_HEALING_LIGHT', 'EFFECT_ROOST'}
# Recoil, mirroring BattleCommand_recoil: Double-Edge and Flare Blitz take 1/3
# of the damage dealt, every other recoil move 1/4; Rock Head / Magic Guard
# block it. It applies even when the hit KOs (recoil runs before
# postfainteffects in the move scripts).
RECOIL_EFFECTS = {'EFFECT_RECOIL_HIT', 'EFFECT_FLARE_BLITZ'}
RECOIL_THIRD = {'DOUBLE_EDGE', 'FLARE_BLITZ'}
RECHARGE_EFFECTS = {'EFFECT_HYPER_BEAM'}   # Hyper Beam / Giga Impact
RAMPAGE_EFFECTS = {'EFFECT_RAMPAGE'}       # Outrage / Thrash / Petal Dance
MULTI = {'EFFECT_MULTI_HIT': 3, 'EFFECT_DOUBLE_HIT': 2}

# ---- support / utility mechanics (checked against engine/battle/move_effects)
SCREEN_TURNS = 5                           # Reflect / Light Screen
SCREEN_DAMAGE_MULT = 0.5
ENCORE_TURNS = 3
# on-hit stat drops on the target, applied at the move's `chance`%
STAT_DROP_HIT = {'EFFECT_SP_DEF_DOWN_HIT': 'spd', 'EFFECT_DEFENSE_DOWN_HIT': 'defe',
                 'EFFECT_SPEED_DOWN_HIT': 'spe', 'EFFECT_ATTACK_DOWN_HIT': 'atk',
                 'EFFECT_SP_ATK_DOWN_HIT': 'spa'}
# on-hit self boosts, applied at the move's `chance`%
SELF_UP_HIT = {'EFFECT_DEFENSE_UP_HIT': {'defe': 1}, 'EFFECT_ATTACK_UP_HIT': {'atk': 1},
               'EFFECT_SPEED_UP_HIT': {'spe': 1},
               'EFFECT_ALL_UP_HIT': {'atk': 1, 'defe': 1, 'spa': 1, 'spd': 1, 'spe': 1}}
DRAIN_EFFECTS = {'EFFECT_LEECH_HIT'}       # heal half the damage dealt
PIVOT_EFFECTS = {'EFFECT_SWITCH_HIT'}      # U-turn / Volt Switch
KNOCK_OFF_MULT = 1.5

# ---- weather (engine/battle/move_effects/weather.asm, abilities.asm, endturn.asm)
WEATHER_TURNS = 5                          # moves and abilities alike (Gen VI rule)
WEATHER_ROCK_TURNS = 8                     # with the matching rock held
WEATHER_MOVES = {'EFFECT_SUNNY_DAY': 'sun', 'EFFECT_RAIN_DANCE': 'rain',
                 'EFFECT_SANDSTORM': 'sand', 'EFFECT_HAIL': 'hail'}
WEATHER_ABILITIES = {'DROUGHT': 'sun', 'DRIZZLE': 'rain', 'SAND_STREAM': 'sand',
                     'SNOW_WARNING': 'hail'}
WEATHER_ROCKS = {'sun': 'HEAT_ROCK', 'rain': 'DAMP_ROCK', 'sand': 'SMOOTH_ROCK',
                 'hail': 'ICY_ROCK'}
WEATHER_SPEED = {'SWIFT_SWIM': 'rain', 'CHLOROPHYLL': 'sun', 'SAND_RUSH': 'sand',
                 'SLUSH_RUSH': 'hail'}
WEATHER_NEGATORS = {'CLOUD_NINE', 'AIR_LOCK'}
SAND_IMMUNE_TYPES, HAIL_IMMUNE_TYPES = {'ROCK', 'GROUND', 'STEEL'}, {'ICE'}
SAND_IMMUNE_ABILITIES = {'SAND_VEIL', 'SAND_RUSH', 'SAND_FORCE', 'OVERCOAT', 'MAGIC_GUARD'}
HAIL_IMMUNE_ABILITIES = {'ICE_BODY', 'SNOW_CLOAK', 'SLUSH_RUSH', 'OVERCOAT', 'MAGIC_GUARD'}

# ---- other battlefield and volatile mechanics
TRICK_ROOM_TURNS = 5
PERISH_COUNT = 4                           # faints when the count runs out (3 turn ends)
BIND_TURNS = (4, 5)                        # Wrap / Fire Spin / Whirlpool
TRAP_ABILITIES = {'SHADOW_TAG', 'ARENA_TRAP', 'MAGNET_PULL'}


class Field:
    """State shared by both sides: weather and Trick Room."""
    def __init__(self):
        self.weather = None                # None / 'sun' / 'rain' / 'sand' / 'hail'
        self.weather_turns = 0
        self.trick_room = 0                # turns left


def weather_of(mon):
    """The weather as it affects `mon`'s battle (Cloud Nine on either active
    mon suppresses it)."""
    side = mon.side
    if side is None or side.field is None or side.field.weather is None:
        return None
    for s in (side, side.foe):
        if s is not None and s.mon.ability in WEATHER_NEGATORS and not s.mon.fainted:
            return None
    return side.field.weather


def set_weather(field, weather, holder):
    if field is None or field.weather == weather:
        return False
    field.weather = weather
    field.weather_turns = (WEATHER_ROCK_TURNS if holder.item == WEATHER_ROCKS[weather]
                           else WEATHER_TURNS)
    holder.weather_set += 1
    return True


def can_escape(mon):
    """Shed Shell, Run Away and Ghost types escape all trapping (UserCanSwitch)."""
    return mon.item == 'SHED_SHELL' or mon.ability == 'RUN_AWAY' or 'GHOST' in mon.types


def is_trapped(side, foe_side):
    """Can side's active mon switch out voluntarily?"""
    m = side.mon
    if can_escape(m):
        return False
    if m.bound or m.mean_looked:
        return True
    f = foe_side.mon if foe_side else None
    if f is None or f.fainted:
        return False
    if f.ability == 'SHADOW_TAG' and m.ability != 'SHADOW_TAG':
        return True
    if f.ability == 'ARENA_TRAP' and is_grounded(m):
        return True
    if f.ability == 'MAGNET_PULL' and 'STEEL' in m.types:
        return True
    return False


def is_grounded(mon):
    return 'FLYING' not in mon.types and mon.ability != 'LEVITATE'


# type-absorb abilities: ability -> the type it's immune to (and triggers on)
ABSORB_TYPES = {'FLASH_FIRE': 'FIRE', 'WATER_ABSORB': 'WATER',
                'VOLT_ABSORB': 'ELECTRIC', 'SAP_SIPPER': 'GRASS',
                'DRY_SKIN': 'WATER', 'MOTOR_DRIVE': 'ELECTRIC'}

# status-immunity abilities: ability -> the status key(s) they block
STATUS_IMMUNE = {'INSOMNIA': 'slp', 'VITAL_SPIRIT': 'slp', 'OWN_TEMPO': 'cnf',
                  'LIMBER': 'par', 'WATER_VEIL': 'brn', 'IMMUNITY': 'psn',
                  'MAGMA_ARMOR': 'frz'}

# contact-status abilities: a defender's ability -> the status it may inflict on
# an attacker whose move made contact (moves.json 'contact', which mirrors the
# ROM's CheckContactMove). Fires at CONTACT_STATUS_CHANCE.
CONTACT_STATUS = {'STATIC': 'par', 'FLAME_BODY': 'brn', 'POISON_POINT': 'psn'}
CONTACT_STATUS_CHANCE = 0.30

# Synchronize reflects these major statuses back onto whoever inflicted them
# (sleep/freeze are not reflected, mirroring the games).
SYNC_STATUSES = {'par', 'brn', 'psn', 'tox'}


def status_blocked(mon, st):
    block = STATUS_IMMUNE.get(mon.ability)
    if block is None:
        return False
    if block == 'psn':
        return st in ('psn', 'tox')
    return block == st


def apply_synchronize(victim, inflictor, st):
    """If `victim` has Synchronize, reflect a major status back onto the
    `inflictor` (no-op for sleep/freeze, a blocked/already-statused inflictor,
    or a victim without the ability)."""
    if victim.ability != 'SYNCHRONIZE' or st not in SYNC_STATUSES:
        return
    if inflictor.status is not None or status_blocked(inflictor, st):
        return
    inflictor.status = st
    if st == 'tox':
        inflictor.tox = 0


def eff_mult(move_type, defender, chart):
    """type_mult, plus the Levitate/Ground and type-absorb special cases."""
    if move_type == 'GROUND' and not is_grounded(defender):
        return 0.0
    if ABSORB_TYPES.get(defender.ability) == move_type:
        return 0.0
    return type_mult(move_type, defender.types, chart)


def apply_absorb(mon, move_type):
    """On-absorb side effect for an immune type-absorb ability hit."""
    ab = mon.ability
    if ABSORB_TYPES.get(ab) != move_type:
        return
    if ab == 'FLASH_FIRE':
        mon.flash_fire = True
    elif ab == 'SAP_SIPPER':
        mon.stage['atk'] = min(6, mon.stage['atk'] + 1)
    elif ab == 'MOTOR_DRIVE':
        mon.stage['spe'] = min(6, mon.stage['spe'] + 1)
    else:                       # WATER_ABSORB, VOLT_ABSORB, DRY_SKIN
        mon.hp = min(mon.maxhp, mon.hp + mon.maxhp / 4)


class Pmon:
    """Battle-time wrapper around a pokemon.json entry + a chosen moveset."""
    __slots__ = ('id', 'types', 'base', 'moves', 'ability', 'item', 'maxhp',
                 'hp', 'status', 'sleep', 'tox', 'stage', 'seeded', 'confused',
                 'fainted', 'locked_move', 'flash_fire', 'dmg_dealt', 'kos',
                 'status_infl', 'heal_done', 'recharging', 'rampage',
                 'rampage_move', 'side', 'last_move', 'encore', 'encore_move',
                 'protect_count', 'protected', 'cursed',
                 'dmg_taken', 'turns_active', 'hazards_set', 'screens_set',
                 'cures', 'pivots', 'phazes', 'hazards_cleared', 'stat_drops',
                 'sub_hp', 'bound', 'bound_by', 'mean_looked', 'perish',
                 'hit_phys', 'hit_spec', 'weather_set', 'subs_made', 'passes',
                 'tricks', 'trick_rooms', 'traps', 'perish_kos', 'perish_by')

    def __init__(self, mid, mon, moveset, ability=None, item=None):
        self.id = mid
        self.types = mon['types']
        self.base = mon['stats']           # already L50 stats dict
        self.moves = moveset               # list of move-name strings
        self.ability = ability             # one ability for the whole battle
        self.item = item                   # one held item for the whole battle
        self.maxhp = self.base['hp']
        self.hp = self.maxhp
        self.status = None                 # None/'par'/'brn'/'psn'/'tox'/'slp'/'frz'
        self.sleep = 0                     # remaining sleep turns
        self.tox = 0                       # toxic counter
        self.stage = dict(atk=0, defe=0, spa=0, spd=0, spe=0)
        self.seeded = False
        self.confused = 0
        self.fainted = False
        self.locked_move = None            # Choice-item move lock (index into self.moves)
        self.recharging = False            # must skip its next turn (Hyper Beam)
        self.rampage = 0                   # extra forced rampage turns left
        self.rampage_move = None
        self.flash_fire = False            # Flash Fire: permanent 1.5x own Fire moves once triggered
        self.dmg_dealt = 0.0                # sum of useful damage dealt, as a fraction of each target's max HP
        self.kos = 0                        # faints this mon's own moves directly caused
        self.status_infl = 0                # major statuses/confusion this mon's own moves landed on a foe
        self.heal_done = 0.0                # HP this mon recovered via its own heal moves / Leech Seed drain, as a fraction of its own max HP
        self.side = None                   # set by Side(); screens live on the side
        self.last_move = None              # index of the move used last (Encore target)
        self.encore = 0                    # turns left locked by Encore
        self.encore_move = None
        self.protect_count = 0             # consecutive successful Protects
        self.protected = False             # protected for the rest of this turn
        self.cursed = False                # Ghost-type Curse: loses 1/4 HP a turn
        # playstyle metrics (all per battle)
        self.dmg_taken = 0.0               # attack damage absorbed, as a fraction of own max HP
        self.turns_active = 0              # turns spent on the field
        self.hazards_set = 0               # Spikes / Toxic Spikes layers laid
        self.screens_set = 0               # Reflect / Light Screen put up
        self.cures = 0                     # team statuses cured (Heal Bell)
        self.pivots = 0                    # U-turn / Volt Switch switch-outs
        self.phazes = 0                    # foes forced out (Roar)
        self.hazards_cleared = 0           # Rapid Spin clears
        self.stat_drops = 0                # foe stat stages lowered (moves + secondaries + Haze)
        self.sub_hp = 0.0                  # Substitute's remaining HP (0 = none)
        self.bound = 0                     # turns left in Wrap / Fire Spin / Whirlpool
        self.bound_by = None               # the Pmon binding it
        self.mean_looked = False           # Mean Look / Block (until the trapper leaves)
        self.perish = 0                    # Perish Song count (0 = none)
        self.hit_phys = 0.0                # damage taken this turn, for Counter
        self.hit_spec = 0.0                # ... and for Mirror Coat
        self.weather_set = 0               # weather started (move or ability)
        self.subs_made = 0                 # Substitutes put up
        self.passes = 0                    # Baton Passes made
        self.tricks = 0                    # items swapped onto the foe
        self.trick_rooms = 0               # Trick Rooms started
        self.traps = 0                     # foes trapped (Mean Look / binding)
        self.perish_kos = 0                # foes fainted by this mon's Perish Song
        self.perish_by = None

    def stat(self, key, ignore_stage=False):
        stage = 0 if ignore_stage else self.stage.get(key, 0)
        v = self.base[key] * stage_mult(stage)
        if key == 'spe':
            if self.ability == 'QUICK_FEET' and self.status is not None:
                v *= 1.5                   # Quick Feet also ignores the par drop
            elif self.status == 'par':
                v *= 0.25
            if self.item == 'CHOICE_SCARF':
                v *= items.CHOICE_SCARF_SPEED_MULT
            w = WEATHER_SPEED.get(self.ability)
            if w and w == weather_of(self):
                v *= 2
        if key in ('defe', 'spd') and self.item == 'EVIOLITE':
            v *= items.EVIOLITE_DEF_MULT
        return v

    def reset_volatile(self):              # cleared on switch out
        self.stage = dict(atk=0, defe=0, spa=0, spd=0, spe=0)
        self.seeded = False
        self.confused = 0
        self.locked_move = None            # Choice lock releases on switch
        self.recharging = False
        self.rampage = 0
        self.rampage_move = None
        self.last_move = None
        self.encore = 0
        self.encore_move = None
        self.protect_count = 0
        self.protected = False
        self.cursed = False
        self.sub_hp = 0.0
        self.bound = 0
        self.bound_by = None
        self.mean_looked = False
        self.perish = 0
        self.perish_by = None
        self.flash_fire = False            # Flash Fire boost is lost on switch-out


class Side:
    def __init__(self, team, field=None):
        self.team = team                   # list[Pmon]
        self.field = field                 # shared Field (weather, Trick Room)
        self.foe = None                    # the opposing Side, set by run_battle
        self.active = 0
        self.spikes = 0                    # 0..3 layers
        self.tspikes = 0                   # 0..2 layers
        self.slept_by_foe = False          # sleep-clause bookkeeping
        self.reflect = 0                   # turns left
        self.light_screen = 0
        self.switched = False              # active changed after moves were chosen
        for m in team:
            m.side = self

    @property
    def mon(self):
        return self.team[self.active]

    def alive_indices(self):
        return [i for i, m in enumerate(self.team) if not m.fainted]


# ---- damage ------------------------------------------------------------------
def _damage_terms(att, dfn, move, chart):
    """Shared atk/def/STAB/multiplier setup for move_damage/expected_damage."""
    eff = eff_mult(move['type'], dfn, chart)
    if move.get(abilities.FLAG_IMMUNITIES.get(dfn.ability, '')):
        eff = 0.0                          # Bulletproof / Soundproof
    is_stab = move['type'] in att.types
    atk_mult, dmg_mult = abilities.offense_multipliers(att.ability, move, is_stab,
                                                       static_weather=False)
    w = weather_of(att)
    # Unaware: ignore the *other* mon's relevant stat stage when computing damage
    unaware_att, unaware_dfn = att.ability == 'UNAWARE', dfn.ability == 'UNAWARE'
    if move['cat'] == 'PHYSICAL':
        a = att.stat('atk', ignore_stage=unaware_dfn) * atk_mult
        d = dfn.stat('defe', ignore_stage=unaware_att)
        if att.ability == 'GUTS' and att.status is not None:
            a *= 1.5                       # Guts also ignores the burn Atk drop below
        elif att.status == 'brn' and move.get('id') != 'FACADE':
            a *= 0.5
        if att.ability == 'HUSTLE':
            a *= 1.5
        if att.item == 'CHOICE_BAND':
            a *= items.CHOICE_STAT_MULT
    else:
        a = att.stat('spa', ignore_stage=unaware_dfn) * atk_mult
        d = dfn.stat('spd', ignore_stage=unaware_att)
        if att.item == 'CHOICE_SPECS':
            a *= items.CHOICE_STAT_MULT
    if w == 'sand' and move['cat'] == 'SPECIAL' and 'ROCK' in dfn.types:
        d *= 1.5                           # SandstormSpDefBoost
    if w == 'hail' and move['cat'] == 'PHYSICAL' and 'ICE' in dfn.types:
        d *= 1.5                           # HailDefenseBoost
    if w == 'sun' and att.ability == 'SOLAR_POWER' and move['cat'] == 'SPECIAL':
        a *= 1.5
    stab = abilities.stab_mult(att.ability, is_stab)
    if w == 'sun':
        dmg_mult *= {'FIRE': 1.5, 'WATER': 0.5}.get(move['type'], 1.0)
    elif w == 'rain':
        dmg_mult *= {'WATER': 1.5, 'FIRE': 0.5}.get(move['type'], 1.0)
    if w == 'sand' and att.ability == 'SAND_FORCE' and move['type'] in ('ROCK', 'GROUND', 'STEEL'):
        dmg_mult *= 1.3
    if move['effect'] == 'EFFECT_SOLAR_BEAM' and w in ('rain', 'sand', 'hail'):
        dmg_mult *= 0.5
    if dfn.side is not None:
        if move['cat'] == 'PHYSICAL' and dfn.side.reflect:
            dmg_mult *= SCREEN_DAMAGE_MULT
        elif move['cat'] == 'SPECIAL' and dfn.side.light_screen:
            dmg_mult *= SCREEN_DAMAGE_MULT
    if att.item == 'LIFE_ORB':
        dmg_mult *= items.LIFE_ORB_DMG_MULT
    if att.ability == 'FLASH_FIRE' and att.flash_fire and move['type'] == 'FIRE':
        dmg_mult *= 1.5
    if dfn.ability == 'THICK_FAT' and move['type'] in ('FIRE', 'ICE'):
        dmg_mult *= 0.5
    if dfn.ability in ('SOLID_ROCK', 'FILTER') and eff > 1.0:
        dmg_mult *= 0.75
    if dfn.ability == 'MULTISCALE' and dfn.hp >= dfn.maxhp:
        dmg_mult *= 0.5
    if att.ability == 'TINTED_LENS' and 0 < eff < 1.0:
        dmg_mult *= 2.0
    return eff, a, d, stab, dmg_mult


# ---- variable/fixed-power moves ---------------------------------------------
# moves.json stores these with power=1 because the ROM works the real value out
# in battle. Seismic Toss/Night Shade and Super Fang skip the stat formula;
# the rest plug a computed power into it. Counter/Mirror Coat aren't modeled
# (they deal 0 here and the moveset picker never chooses them).
REVERSAL_POWER = [(1, 200), (4, 150), (9, 100), (16, 80), (32, 40)]  # px, BP


def fixed_damage(move, dfn):
    e = move['effect']
    if e == 'EFFECT_LEVEL_DAMAGE':
        return 50                           # the attacker's level
    if e == 'EFFECT_SUPER_FANG':
        return max(1, int(dfn.hp // 2))
    if e == 'EFFECT_COUNTER':
        return 0
    return None


def effective_power(move, att, dfn):
    e = move['effect']
    if e == 'EFFECT_GYRO_BALL':            # 25 * target speed / user speed
        return max(1, min(150, int(25 * dfn.stat('spe') / max(att.stat('spe'), 1))))
    if e == 'EFFECT_REVERSAL':             # by HP-bar pixels, out of 48
        px = int(48 * max(att.hp, 0) / att.maxhp)
        return next((bp for limit, bp in REVERSAL_POWER if px <= limit), 20)
    if e == 'EFFECT_RETURN':
        return 102                          # max happiness, like the max build
    if e == 'EFFECT_MAGNITUDE':
        return 71                           # average over the magnitude table
    if e == 'EFFECT_LOW_KICK':
        return 80                           # no species weights in the data
    if e == 'EFFECT_KNOCK_OFF' and dfn.item:
        return int(move['power'] * KNOCK_OFF_MULT)
    if e == 'EFFECT_CONDITIONAL_BOOST':
        mid = move.get('id')
        if mid == 'FACADE' and att.status not in (None, 'slp', 'frz'):
            return move['power'] * 2
        if mid == 'HEX' and dfn.status is not None:
            return move['power'] * 2
        if mid == 'VENOSHOCK' and dfn.status in ('psn', 'tox'):
            return move['power'] * 2
        if mid == 'ACROBATICS' and att.item is None:
            return move['power'] * 2
    return move['power']


def survives_at_1hp(dfn):
    """Sturdy / Focus Sash: a mon at full HP survives an otherwise-lethal hit
    with 1 HP. Checked before the hit lands; see consume_sash."""
    return dfn.hp >= dfn.maxhp and (dfn.ability == 'STURDY'
                                    or dfn.item == 'FOCUS_SASH')


def consume_sash(dfn):
    if dfn.ability != 'STURDY' and dfn.item == 'FOCUS_SASH':
        dfn.item = None                     # single use


def _resolve_damage(att, dfn, move, chart, roll):
    """Shared finisher for move_damage/expected_damage: one eff_mult/_damage_terms
    pass, applied with whichever damage roll the caller wants (RNG or the flat
    average). Returns (damage, type_effectiveness)."""
    eff, a, d, stab, dmg_mult = _damage_terms(att, dfn, move, chart)
    if eff == 0.0:
        return 0, 0.0
    fixed = fixed_damage(move, dfn)
    if fixed is not None:
        return fixed, eff                   # ignores stats, STAB and the roll
    power = effective_power(move, att, dfn)
    base = ((((2 * 50) // 5 + 2) * power * a) // d) // 50 + 2
    hits = MULTI.get(move['effect'], 1)
    if att.ability == 'SKILL_LINK' and move['effect'] == 'EFFECT_MULTI_HIT':
        hits = 5                            # Skill Link always lands the max
    return int(base * stab * eff * dmg_mult * roll) * hits, eff


def move_damage(att, dfn, move, chart, rng):
    """Rolled damage for a damaging move att->dfn (0 if non-damaging/immune)."""
    if move['cat'] == 'STATUS' or move['power'] <= 0:
        return 0, 1.0
    return _resolve_damage(att, dfn, move, chart, rng.uniform(0.85, 1.0))


def expected_damage(att, dfn, move, chart):
    """Deterministic average damage, for AI scoring (no RNG)."""
    if move['cat'] == 'STATUS' or move['power'] <= 0:
        return 0, eff_mult(move['type'], dfn, chart) if move['power'] else 1.0
    dmg, eff = _resolve_damage(att, dfn, move, chart, 0.925)
    acc = 1.0 if move['acc'] < 0 else move['acc'] / 100.0
    return dmg * acc, eff


# ---- heuristic AI ------------------------------------------------------------
def _max_expected_damage(attacker, defender, moves, chart):
    """Best expected damage `attacker` can deal `defender` with a damaging move."""
    best = 0.0
    for mv in attacker.moves:
        m = moves[mv]
        if m['cat'] == 'STATUS' or m['power'] <= 0:
            continue
        dmg, _ = expected_damage(attacker, defender, m, chart)
        best = max(best, dmg)
    return best


def choose_move(side, foe, moves, chart, rng=random):
    """Pick a move with a 1-ply look at the foe's likely response.

    A pure max-damage picker can't tell a fast revenge-killer (KOs before it's
    hit) from a frail flailer, or a durable waller (survives to status/heal/set
    up) from a mon that just dies. So utility is gated on survival: estimate
    whether the active will still be standing next turn, and only value
    setup/status/heal/hazards when it will."""
    att, dfn = side.mon, foe.mon
    if att.rampage:
        return att.rampage_move
    if att.encore and att.encore_move is not None:
        return att.encore_move
    if att.status == 'slp' and att.sleep > 0:
        for i, mv in enumerate(att.moves):
            if moves[mv]['effect'] == 'EFFECT_SLEEP_TALK':
                return i
    if att.locked_move is not None:
        return att.locked_move

    best_dmg_i, best_dmg = 0, 0.0
    for i, mv in enumerate(att.moves):
        m = moves[mv]
        if m['cat'] == 'STATUS' or m['power'] <= 0:
            continue
        dmg, _ = expected_damage(att, dfn, m, chart)
        if m['effect'] in RECHARGE_EFFECTS and dmg < dfn.hp:
            dmg *= 0.5                     # two turns per hit unless it KOs
        if dmg > best_dmg:
            best_dmg, best_dmg_i = dmg, i

    foe_dmg = _max_expected_damage(dfn, att, moves, chart)
    i_outspeed = att.stat('spe') > dfn.stat('spe')
    i_ko = best_dmg >= dfn.hp
    foe_ko = foe_dmg >= att.hp
    # "doomed": the foe is expected to faint me next turn whatever I do -- it
    # KOs me and I can't KO it first. No point setting up / statusing / healing.
    doomed = foe_ko and not (i_ko and i_outspeed)

    # If I can KO this turn, just do it (revenge-killing a faster glass cannon,
    # or trading when I'm slower -- swinging is right either way).
    if i_ko:
        return best_dmg_i

    util = []                              # (priority_score, index)
    for i, mv in enumerate(att.moves):
        e = moves[mv]['effect']
        if e in HEAL_EFFECTS and att.hp < att.maxhp * 0.6 and not doomed:
            # heal more eagerly the lower I am, but only if it isn't futile
            util.append((3.0 + (att.maxhp - att.hp) / att.maxhp, i))
        elif e in BOOST and not doomed and foe_dmg < att.hp * 0.5:
            # set up only when I clearly survive; better still if I'm faster
            util.append((2.0 + (0.6 if i_outspeed else 0.0), i))
        elif e in INFLICT and dfn.status is None and not doomed:
            st = INFLICT[e]
            if st == 'slp' and SLEEP_CLAUSE and foe.slept_by_foe:
                continue
            score = 1.5
            if st in ('slp', 'par') and not i_outspeed:
                score += 1.0      # neutralises a foe that would otherwise outrun me
            elif st in ('tox', 'psn', 'brn'):
                score += 0.4      # chip a bulky foe I can't break quickly
            util.append((score, i))
        elif (e == 'EFFECT_LEECH_SEED' and not dfn.seeded
              and 'GRASS' not in dfn.types and not doomed):
            util.append((1.6, i))
        elif e == 'EFFECT_SPIKES' and side_layers_left(foe, 'spikes') and not doomed:
            util.append((1.2, i))
        elif e == 'EFFECT_TOXIC_SPIKES' and side_layers_left(foe, 'tspikes') and not doomed:
            util.append((1.2, i))
        elif e in ('EFFECT_REFLECT', 'EFFECT_LIGHT_SCREEN') and not doomed:
            up = side.reflect if e == 'EFFECT_REFLECT' else side.light_screen
            want = 'PHYSICAL' if e == 'EFFECT_REFLECT' else 'SPECIAL'
            if not up and len(side.alive_indices()) >= 2 and best_category(dfn, moves) == want:
                util.append((2.0, i))
        elif e == 'EFFECT_HEAL_BELL':
            n = sum(1 for t in side.team if not t.fainted and t.status not in (None,))
            if n:
                util.append((1.8 + 0.5 * n, i))
        elif e == 'EFFECT_ROAR':
            boosts = sum(max(0, v) for v in dfn.stage.values())
            if len(foe.alive_indices()) >= 2 and (boosts >= 2 or foe.spikes >= 2):
                util.append((2.6 if boosts >= 2 else 1.6, i))
        elif e == 'EFFECT_HAZE':
            if sum(max(0, v) for v in dfn.stage.values()) >= 2:
                util.append((2.6, i))
        elif e == 'EFFECT_ENCORE':
            last = dfn.last_move
            if (last is not None and not dfn.encore and i_outspeed
                    and moves[dfn.moves[last]]['cat'] == 'STATUS'):
                util.append((2.5, i))
        elif e == 'EFFECT_PAIN_SPLIT':
            if att.hp < att.maxhp * 0.5 and dfn.hp > att.hp * 1.3 and not doomed:
                util.append((2.4, i))
        elif e == 'EFFECT_CURSE' and not doomed:
            if 'GHOST' in att.types:
                if not dfn.cursed and att.hp > att.maxhp * 0.6 and dfn.hp > dfn.maxhp * 0.5:
                    util.append((1.4, i))
            elif foe_dmg < att.hp * 0.5 and att.base['atk'] >= att.base['spa']:
                util.append((2.0, i))
        elif e == 'EFFECT_PROTECT':
            if att.protect_count == 0 and (dfn.status in ('tox', 'psn', 'brn') or dfn.seeded
                                          or dfn.cursed) and not i_ko:
                util.append((1.3, i))
        elif e == 'EFFECT_RAPID_SPIN':
            if side.spikes or side.tspikes or att.seeded or att.bound:
                util.append((2.2, i))
        elif e == 'EFFECT_COUNTER':
            want = 'PHYSICAL' if moves[att.moves[i]].get('id') == 'COUNTER' else 'SPECIAL'
            if best_category(dfn, moves) == want and att.hp > att.maxhp * 0.35:
                util.append((2.6, i))
        elif e in WEATHER_MOVES and not doomed:
            w = WEATHER_MOVES[e]
            field = side.field
            if field is not None and (field.weather != w or field.weather_turns <= 1):
                gain = weather_gain(side, w, moves)
                if gain > 0:
                    util.append((1.6 + 0.4 * min(gain, 3), i))
        elif e == 'EFFECT_SUBSTITUTE' and not doomed:
            if att.sub_hp <= 0 and att.hp > att.maxhp * 0.5:
                plan = any(moves[mv]['effect'] in BOOST or moves[mv]['effect']
                           in ('EFFECT_BATON_PASS',) for mv in att.moves)
                util.append((2.2 if plan else 1.4, i))
        elif e == 'EFFECT_BATON_PASS':
            boosts = sum(max(0, v) for v in att.stage.values())
            others = [j for j in side.alive_indices() if j != side.active]
            if others and (boosts >= 2 or att.sub_hp > 0) and (doomed or boosts >= 4):
                util.append((2.8, i))
        elif e == 'EFFECT_TRICK':
            if att.item in CHOICE_ITEMS and dfn.item not in CHOICE_ITEMS and sum(
                    moves[mv]['cat'] == 'STATUS' for mv in dfn.moves) >= 1:
                util.append((2.4, i))
        elif e == 'EFFECT_TRICK_ROOM' and not doomed and side.field is not None:
            if not side.field.trick_room and team_speed(side) < team_speed(foe):
                util.append((2.3, i))
        elif e == 'EFFECT_SWAGGER':
            if not dfn.confused and best_category(dfn, moves) == 'SPECIAL' and not doomed:
                util.append((1.3, i))
        elif e == 'EFFECT_MEAN_LOOK':
            if not dfn.mean_looked and not can_escape(dfn) and any(
                    moves[mv]['effect'] in ('EFFECT_PERISH_SONG', 'EFFECT_TOXIC')
                    for mv in att.moves):
                util.append((2.0, i))
        elif e == 'EFFECT_PERISH_SONG':
            if not dfn.perish and dfn.ability != 'SOUNDPROOF':
                foe_stuck = is_trapped(foe, side) or len(foe.alive_indices()) == 1
                i_can_leave = not is_trapped(side, foe) and len(side.alive_indices()) > 1
                if foe_stuck and i_can_leave:
                    util.append((2.6, i))
                elif sum(max(0, v) for v in dfn.stage.values()) >= 3 and i_can_leave:
                    util.append((2.0, i))
        elif e in PIVOT_EFFECTS:
            here = matchup_score(att, dfn, moves, chart)
            others = [j for j in side.alive_indices() if j != side.active]
            if others and max(matchup_score(side.team[j], dfn, moves, chart)
                              for j in others) - here >= 1.0:
                util.append((2.2 if doomed else 1.7, i))

    if util:
        util.sort(reverse=True)
        score, idx = util[0]
        # a damaging move that takes a big chunk still competes with weak utility
        dmg_frac = best_dmg / max(dfn.hp, 1)
        if dmg_frac < 0.5 or score >= 2.8:
            if rng.random() < 0.85:        # a little noise so it isn't robotic
                return idx
    return best_dmg_i


def team_speed(side):
    alive = [side.team[i] for i in side.alive_indices()]
    return sum(m.stat('spe') for m in alive) / max(1, len(alive))


def weather_gain(side, w, moves):
    """How much side's living team would gain from weather `w`."""
    gain = 0.0
    for i in side.alive_indices():
        m = side.team[i]
        if WEATHER_SPEED.get(m.ability) == w:
            gain += 1.5
        if (m.ability, w) in (('SOLAR_POWER', 'sun'), ('SAND_FORCE', 'sand'),
                              ('RAIN_DISH', 'rain'), ('DRY_SKIN', 'rain'),
                              ('ICE_BODY', 'hail'), ('HYDRATION', 'rain')):
            gain += 0.7
        boosted = {'sun': 'FIRE', 'rain': 'WATER'}.get(w)
        if boosted and boosted in m.types and any(moves[mv]['type'] == boosted for mv in m.moves):
            gain += 0.6
        if any(moves[mv].get('id') in {'rain': ('THUNDER', 'HURRICANE'), 'hail': ('BLIZZARD',),
                                       'sun': ('SOLAR_BEAM',)}.get(w, ()) for mv in m.moves):
            gain += 0.4
    return gain


def side_layers_left(side, kind):
    return side.spikes < 3 if kind == 'spikes' else side.tspikes < 2


def best_category(mon, moves):
    """'PHYSICAL' or 'SPECIAL': the category of the mon's strongest attack."""
    best, cat = -1, 'PHYSICAL'
    for mv in mon.moves:
        m = moves[mv]
        if m['cat'] != 'STATUS' and m['power'] > best:
            best, cat = m['power'], m['cat']
    return cat


def matchup_score(mon, foe, moves, chart):
    """How good is `mon` against active `foe`? offense - defense, for switching."""
    off = 0.0
    for mv in mon.moves:
        m = moves[mv]
        if m['cat'] != 'STATUS' and m['power'] > 0:
            off = max(off, eff_mult(m['type'], foe, chart) *
                      (STAB if m['type'] in mon.types else 1.0))
    deff = 0.0
    for mv in foe.moves:
        m = moves[mv]
        if m['cat'] != 'STATUS' and m['power'] > 0:
            deff = max(deff, eff_mult(m['type'], mon, chart))
    return off - deff


def choose_switch(side, foe, moves, chart, forced, rng=random):
    """Pick a teammate index to send in. Returns index, or None to stay."""
    if not forced and (side.mon.recharging or side.mon.rampage):
        return None                        # can't switch out mid-recharge/rampage
    if not forced and is_trapped(side, foe):
        return None
    if not forced and side.mon.perish and side.mon.perish <= 2:
        others = [i for i in side.alive_indices() if i != side.active]
        if others:                         # escape Perish Song while we still can
            return max(others, key=lambda i: matchup_score(side.team[i], foe.mon, moves, chart))
    alive = [i for i in side.alive_indices() if forced or i != side.active]
    if not alive:
        return None
    best_i, best = None, -99.0
    for i in alive:
        s = matchup_score(side.team[i], foe.mon, moves, chart)
        if s > best:
            best, best_i = s, i
    if forced:
        return best_i
    # voluntary switch only when current matchup is clearly bad and a teammate is clearly better
    cur = matchup_score(side.mon, foe.mon, moves, chart)
    if best - cur >= 2.0 and cur < 0 and rng.random() < 0.5:
        return best_i
    return None


# ---- per-turn mechanics ------------------------------------------------------
def apply_switch(side, idx, foe_side, chart):
    old = side.mon
    old.reset_volatile()
    if idx != side.active and not old.fainted:
        if old.ability == 'REGENERATOR':
            old.hp = min(old.maxhp, old.hp + old.maxhp / 3)
        if old.ability == 'NATURAL_CURE':   # cures status on switch-out
            old.status = None
            old.sleep = old.tox = 0
    side.active = idx
    m = side.mon
    # entry hazards (grounded mons only -- Flying-type or Levitate skip these)
    grounded = is_grounded(m)
    if side.spikes and grounded and m.ability != 'MAGIC_GUARD':
        m.hp -= m.maxhp * [0, 1/8, 1/6, 1/4][side.spikes]
    if side.tspikes and grounded:
        if 'POISON' in m.types:
            side.tspikes = 0               # absorbed
        elif 'STEEL' not in m.types and m.status is None:
            m.status = 'tox' if side.tspikes >= 2 else 'psn'
    if m.hp <= 0:
        m.fainted = True
        return

    # switch-in ability events (need to see the foe's already-active mon)
    if m.ability in WEATHER_ABILITIES:
        set_weather(side.field, WEATHER_ABILITIES[m.ability], m)
    foe = foe_side.mon if foe_side else None
    if foe and not foe.fainted:
        if m.ability == 'INTIMIDATE':
            foe.stage['atk'] = max(-6, foe.stage['atk'] - 1)
        if m.ability == 'IMPOSTER':
            # Transform onto the foe: types/stats/stages/ability/moves copy,
            # HP stays the user's own. Self-disarming -- once 'ability' is
            # overwritten it no longer reads as IMPOSTER, so this can't
            # re-trigger on a later switch-in.
            m.types = list(foe.types)
            m.base = dict(foe.base)
            m.stage = dict(foe.stage)
            m.ability = foe.ability
            m.moves = list(foe.moves)


def orb_can_status(mon, st):
    if status_blocked(mon, st):
        return False
    if st == 'tox':
        return 'POISON' not in mon.types and 'STEEL' not in mon.types
    return 'FIRE' not in mon.types


def end_of_turn(mon, foe_side, rng=random):
    """Residual damage/heal. Returns False if mon faints."""
    if mon.fainted:
        return False
    if mon.ability == 'SHED_SKIN' and mon.status is not None and rng.random() < 0.3:
        mon.status = None               # 30%/turn cure of any major status
        mon.sleep = mon.tox = 0
    if mon.ability == 'POISON_HEAL' and mon.status in ('psn', 'tox'):
        mon.hp = min(mon.maxhp, mon.hp + mon.maxhp / 8)
    elif mon.ability != 'MAGIC_GUARD':
        if mon.status == 'brn' or mon.status == 'psn':
            mon.hp -= mon.maxhp / 8
        elif mon.status == 'tox':
            mon.tox += 1
            mon.hp -= mon.maxhp * mon.tox / 16
        if mon.seeded:
            drain = min(mon.maxhp / 8, max(mon.hp, 0))
            mon.hp -= drain
            seeder = foe_side.mon            # Leech Seed transfers the drained HP
            if not seeder.fainted:
                if seeder.ability == 'LIQUID_OOZE':
                    seeder.hp -= drain       # Liquid Ooze: the drainer is hurt instead
                    if seeder.hp <= 0:
                        seeder.fainted = True
                else:
                    healed = min(seeder.maxhp - seeder.hp, drain)
                    seeder.hp += healed
                    seeder.heal_done += healed / seeder.maxhp
    if mon.cursed and mon.ability != 'MAGIC_GUARD':
        mon.hp -= mon.maxhp / 4
    def on_field(p):
        return p is not None and not p.fainted and p.side is not None and p.side.mon is p
    if mon.bound:
        if not on_field(mon.bound_by):
            mon.bound, mon.bound_by = 0, None
        else:
            if mon.ability != 'MAGIC_GUARD':
                mon.hp -= mon.maxhp * (1 / 6 if mon.bound_by.item == 'BINDING_BAND' else 1 / 8)
            mon.bound -= 1
            if not mon.bound:
                mon.bound_by = None
    if mon.mean_looked and not on_field(mon.mean_looked):
        mon.mean_looked = False
    w = weather_of(mon)
    if w == 'sand' and not (set(mon.types) & SAND_IMMUNE_TYPES) \
            and mon.ability not in SAND_IMMUNE_ABILITIES:
        mon.hp -= mon.maxhp / 16
    elif w == 'hail' and not (set(mon.types) & HAIL_IMMUNE_TYPES) \
            and mon.ability not in HAIL_IMMUNE_ABILITIES:
        mon.hp -= mon.maxhp / 16
    if mon.ability in ('SOLAR_POWER', 'DRY_SKIN') and w == 'sun':
        mon.hp -= mon.maxhp / 8
    heal = {('RAIN_DISH', 'rain'): 1 / 16, ('DRY_SKIN', 'rain'): 1 / 8,
            ('ICE_BODY', 'hail'): 1 / 16}.get((mon.ability, w), 0)
    if heal and mon.hp > 0:
        mon.hp = min(mon.maxhp, mon.hp + mon.maxhp * heal)
    if mon.ability == 'HYDRATION' and w == 'rain' and mon.status is not None:
        mon.status, mon.sleep, mon.tox = None, 0, 0
    if mon.perish and mon.hp > 0:
        mon.perish -= 1
        if mon.perish == 0:
            mon.hp = 0
            if mon.perish_by is not None and mon.perish_by.side is not mon.side:
                mon.perish_by.perish_kos += 1
    if mon.hp <= 0:
        mon.fainted = True
        return False
    if mon.item == 'LEFTOVERS' and mon.hp < mon.maxhp:
        mon.hp = min(mon.maxhp, mon.hp + mon.maxhp * items.LEFTOVERS_HEAL_FRAC)
    # self-status orbs fire at end of turn, so the status only starts ticking
    # on the following end_of_turn
    st = items.ORB_STATUS.get(mon.item)
    if st and mon.status is None and orb_can_status(mon, st):
        mon.status = st
        if st == 'tox':
            mon.tox = 0
    if mon.ability == 'SPEED_BOOST':
        mon.stage['spe'] = min(6, mon.stage['spe'] + 1)
    return True


def _pivot(att_side, dfn_side, moves, chart):
    """U-turn / Volt Switch: after the hit, bring in the teammate with the
    best matchup (if any is left)."""
    att = att_side.mon
    if att.fainted:
        return
    others = [i for i in att_side.alive_indices() if i != att_side.active]
    if not others or dfn_side.mon.fainted and len(dfn_side.alive_indices()) == 0:
        return
    best = max(others, key=lambda i: matchup_score(att_side.team[i], dfn_side.mon, moves, chart))
    att.pivots += 1
    apply_switch(att_side, best, dfn_side, chart)
    att_side.switched = True


def perform(att_side, dfn_side, moves, chart, rng, idx=None, foe_move=None, foe_moved=False,
            power_mult=1.0):
    """Execute the active mon's chosen action for att_side against dfn_side.
    `idx` is the move chosen at the start of the turn (the one turn order was
    decided by); `foe_move`/`foe_moved` describe the opponent's choice, which
    Sucker Punch needs."""
    att, dfn = att_side.mon, dfn_side.mon

    if att.recharging:                     # Hyper Beam's lost turn
        att.recharging = False
        return

    # pre-move status gates
    if att.status == 'frz':
        if rng.random() < 0.2:
            att.status = None
        else:
            return
    sleep_talk = None
    if att.status == 'slp':
        att.sleep -= 1
        if att.sleep <= 0:
            att.status = None
        else:
            if idx is None or moves[att.moves[idx]]['effect'] != 'EFFECT_SLEEP_TALK':
                return
            usable = [i for i, mv in enumerate(att.moves)
                      if moves[mv]['effect'] not in ('EFFECT_SLEEP_TALK', 'EFFECT_HEAL')
                      and moves[mv]['effect'] not in ('EFFECT_BIDE', 'EFFECT_SKY_ATTACK')]
            if not usable:
                return
            sleep_talk = rng.choice(usable)
    if att.status == 'par' and rng.random() < 0.25:
        return
    if att.confused > 0:
        att.confused -= 1
        if rng.random() < 0.5:             # hurt self in confusion (approx)
            if att.ability != 'MAGIC_GUARD':
                att.hp -= att.maxhp / 8
                if att.hp <= 0:
                    att.fainted = True
            return

    if idx is None:
        idx = choose_move(att_side, dfn_side, moves, chart, rng)
    if sleep_talk is not None:
        idx = sleep_talk                   # Sleep Talk calls a random other move
    if att.encore:
        att.encore -= 1
    mv = att.moves[idx]
    m = moves[mv]
    e = m['effect']
    att.last_move = idx

    # Protect: cumulative 1/3 success chance per consecutive use
    if e == 'EFFECT_PROTECT':
        if rng.random() < 1 / (3 ** att.protect_count):
            att.protected = True
            att.protect_count += 1
        else:
            att.protect_count = 0
        return
    att.protect_count = 0
    if dfn.protected and e != 'EFFECT_ROAR' and (
            m['cat'] != 'STATUS' or e in INFLICT or e in DROP
            or e in ('EFFECT_LEECH_SEED', 'EFFECT_ENCORE', 'EFFECT_PAIN_SPLIT')):
        att.rampage = 0
        return
    # Sucker Punch fails unless the target is about to use an attack
    if e == 'EFFECT_SUCKER_PUNCH' and (foe_moved or foe_move is None
                                       or moves[foe_move]['cat'] == 'STATUS'):
        return
    if att.item in CHOICE_ITEMS:
        att.locked_move = idx     # locks in on use, regardless of hit/miss

    # accuracy
    acc = m['acc']
    w = weather_of(att)
    if m.get('id') in ('THUNDER', 'HURRICANE'):
        acc = -1 if w == 'rain' else (50 if w == 'sun' else acc)
    elif m.get('id') == 'BLIZZARD' and w == 'hail':
        acc = -1
    if att.ability == 'HUSTLE' and m['cat'] != 'STATUS' and acc >= 0:
        acc *= 0.8
    if acc >= 0 and m['cat'] != 'STATUS' and (
            (dfn.ability == 'SAND_VEIL' and w == 'sand')
            or (dfn.ability == 'SNOW_CLOAK' and w == 'hail')):
        acc *= 0.8
    if acc >= 0 and rng.random() > acc / 100.0:
        att.rampage = 0                    # a miss ends a rampage, no confusion
        return

    if e in RAMPAGE_EFFECTS:
        if att.rampage:
            att.rampage -= 1
            if att.rampage == 0 and not status_blocked(att, 'cnf'):
                att.confused = rng.randint(2, 4)   # rampage over: user confused
        else:
            att.rampage = rng.randint(1, 2)        # 1-2 more forced turns
            att.rampage_move = idx

    if e == 'EFFECT_COUNTER':
        taken = att.hit_phys if m.get('id') == 'COUNTER' else att.hit_spec
        if taken <= 0 or eff_mult(m['type'], dfn, chart) == 0:
            return
        dmg = 2 * taken
        if dfn.sub_hp > 0:
            dfn.sub_hp = max(0.0, dfn.sub_hp - dmg)
            return
        dealt = min(dmg, dfn.hp)
        att.dmg_dealt += dealt / dfn.maxhp
        dfn.dmg_taken += dealt / dfn.maxhp
        dfn.hp -= dmg
        if dfn.hp <= 0:
            dfn.fainted = True
            att.kos += 1
        return

    if e == 'EFFECT_EXPLOSION':
        dmg, _ = move_damage(att, dfn, m, chart, rng)
        dmg *= 2
        sturdy = survives_at_1hp(dfn)
        att.dmg_dealt += min(dmg, dfn.hp) / dfn.maxhp
        dfn.dmg_taken += min(dmg, dfn.hp) / dfn.maxhp
        dfn.hp -= dmg
        att.hp = 0
        att.fainted = True
        if dfn.hp <= 0:
            if sturdy:
                dfn.hp = 1
                consume_sash(dfn)
            else:
                dfn.fainted = True
                att.kos += 1
        return

    if m['cat'] != 'STATUS' and m['power'] > 0:
        dmg, eff = move_damage(att, dfn, m, chart, rng)
        dmg = int(dmg * power_mult)
        if e in RECHARGE_EFFECTS and eff > 0:
            att.recharging = True          # recharges after any hit, even a KO
        if dfn.sub_hp > 0 and dmg > 0 and not m.get('sound') and att.ability != 'INFILTRATOR':
            hit = min(dmg, dfn.sub_hp)
            dfn.sub_hp -= hit
            if dfn.sub_hp <= 0:
                dfn.sub_hp = 0.0
            att.dmg_dealt += hit / dfn.maxhp
            if e in RECOIL_EFFECTS and att.ability not in ('MAGIC_GUARD', 'ROCK_HEAD'):
                att.hp -= max(1, hit * (1 / 3 if m.get('id') in RECOIL_THIRD else 1 / 4))
            if att.item == 'LIFE_ORB' and att.ability != 'MAGIC_GUARD':
                att.hp -= att.maxhp * items.LIFE_ORB_RECOIL_FRAC
            if att.hp <= 0:
                att.fainted = True
            if e in PIVOT_EFFECTS:
                _pivot(att_side, dfn_side, moves, chart)
            return
        if dmg == 0 and eff == 0.0:
            apply_absorb(dfn, m['type'])
        elif dmg > 0 and dfn.ability == 'LIGHTNING_ROD' and m['type'] == 'ELECTRIC':
            dfn.stage['spa'] = min(6, dfn.stage['spa'] + 1)
        sturdy = survives_at_1hp(dfn)
        dealt = min(dmg, dfn.hp)
        att.dmg_dealt += dealt / dfn.maxhp
        dfn.dmg_taken += dealt / dfn.maxhp
        dfn.hp -= dmg
        if m['cat'] == 'PHYSICAL':
            dfn.hit_phys += dealt
        else:
            dfn.hit_spec += dealt
        if e == 'EFFECT_TRAP' and dfn.hp > 0 and not dfn.bound and not can_escape(dfn):
            dfn.bound = rng.choice(BIND_TURNS) + (2 if att.item == 'GRIP_CLAW' else 0)
            dfn.bound_by = att
            att.traps += 1
        if e in DRAIN_EFFECTS and dealt > 0:
            if dfn.ability == 'LIQUID_OOZE':
                att.hp -= dealt / 2
            else:
                healed = min(att.maxhp - att.hp, dealt / 2)
                att.hp += healed
                att.heal_done += healed / att.maxhp
        if e == 'EFFECT_KNOCK_OFF' and dfn.item and dfn.ability != 'STICKY_HOLD':
            dfn.item = None
        if e == 'EFFECT_CLOSE_COMBAT':
            att.stage['defe'] = max(-6, att.stage['defe'] - 1)
            att.stage['spd'] = max(-6, att.stage['spd'] - 1)
        if e == 'EFFECT_RAPID_SPIN' and dmg > 0:
            if att_side.spikes or att_side.tspikes or att.seeded:
                att.hazards_cleared += 1
            att_side.spikes = att_side.tspikes = 0
            att.seeded = False
        if (e in RECOIL_EFFECTS and dealt > 0
                and att.ability not in ('MAGIC_GUARD', 'ROCK_HEAD')):
            frac = 1 / 3 if m.get('id') in RECOIL_THIRD else 1 / 4
            att.hp -= max(1, dealt * frac)
            if att.hp <= 0:
                att.fainted = True
        if att.item == 'LIFE_ORB' and dmg > 0 and att.ability != 'MAGIC_GUARD':
            att.hp -= att.maxhp * items.LIFE_ORB_RECOIL_FRAC
            if att.hp <= 0:
                att.fainted = True
        if dfn.hp <= 0:
            if sturdy:
                dfn.hp = 1
                consume_sash(dfn)
            else:
                dfn.fainted = True
                att.kos += 1
            if e in PIVOT_EFFECTS:
                _pivot(att_side, dfn_side, moves, chart)
            return
        # on-hit secondaries: Serene Grace doubles the trigger chance;
        # Shield Dust on the defender suppresses secondaries entirely.
        if dfn.ability == 'SHIELD_DUST':
            chance = 0
        elif att.ability == 'SERENE_GRACE':
            chance = m['chance'] * 2
        else:
            chance = m['chance']
        if e in ONHIT and dfn.status is None and rng.random() < chance / 100.0:
            st = ONHIT[e]
            if st == 'frz' and weather_of(att) == 'sun':
                pass                        # harsh sunlight prevents freezing
            elif st != 'slp' and not status_blocked(dfn, st):  # on-hit sleep doesn't exist; guard anyway
                dfn.status = st
                att.status_infl += 1
                if st == 'tox':
                    dfn.tox = 0
                apply_synchronize(dfn, att, st)
        if e == 'EFFECT_FLINCH_HIT' and rng.random() < chance / 100.0:
            pass                            # flinch handled by turn order in battle loop (approx: ignore)
        if e in STAT_DROP_HIT and rng.random() < chance / 100.0 \
                and dfn.ability not in ('CLEAR_BODY', 'WHITE_SMOKE'):
            k = STAT_DROP_HIT[e]
            if dfn.stage[k] > -6:
                dfn.stage[k] -= 1
                att.stat_drops += 1
        if e in SELF_UP_HIT and rng.random() < chance / 100.0:
            for k, d in SELF_UP_HIT[e].items():
                att.stage[k] = min(6, att.stage[k] + d)
        # contact-status abilities on the (surviving) defender vs a physical hit
        if m.get('contact') and not att.fainted and att.status is None:
            cs = CONTACT_STATUS.get(dfn.ability)
            if cs and not status_blocked(att, cs) and rng.random() < CONTACT_STATUS_CHANCE:
                att.status = cs
                apply_synchronize(att, dfn, cs)
        if e in PIVOT_EFFECTS:
            _pivot(att_side, dfn_side, moves, chart)
        return

    # ---- status / utility moves ----
    if (dfn.sub_hp > 0 and not m.get('sound') and att.ability != 'INFILTRATOR'
            and (e in INFLICT or e in DROP or e in ('EFFECT_LEECH_SEED', 'EFFECT_SWAGGER',
                                                    'EFFECT_TRICK', 'EFFECT_MEAN_LOOK',
                                                    'EFFECT_PAIN_SPLIT', 'EFFECT_ENCORE'))):
        return                              # blocked by the target's Substitute
    if e == 'EFFECT_GROWTH' and weather_of(att) == 'sun':
        att.stage['atk'] = min(6, att.stage['atk'] + 2)
        att.stage['spa'] = min(6, att.stage['spa'] + 2)
        return
    if e in BOOST:
        for k, d in BOOST[e].items():
            att.stage[k] = max(-6, min(6, att.stage.get(k, 0) + d))
        if e == 'EFFECT_SHELL_SMASH':
            pass
        return
    if e == 'EFFECT_BELLY_DRUM':
        att.stage['atk'] = 6
        if att.ability != 'MAGIC_GUARD':
            att.hp -= att.maxhp / 2
            if att.hp <= 0:
                att.fainted = True
        return
    if e in DROP:
        for k, d in DROP[e].items():
            if k in dfn.stage and dfn.stage[k] > -6:
                dfn.stage[k] = max(-6, min(6, dfn.stage[k] + d))
                att.stat_drops += 1
        return
    if e in INFLICT and (m.get('powder') and ('GRASS' in dfn.types
                                               or dfn.ability == 'OVERCOAT')
                         or m.get('sound') and dfn.ability == 'SOUNDPROOF'):
        return                              # powder / sound immunity
    if e in INFLICT and dfn.status is None:
        st = INFLICT[e]
        if st == 'cnf':
            if not status_blocked(dfn, st):
                dfn.confused = rng.randint(2, 4)
                att.status_infl += 1
            return
        if status_blocked(dfn, st):
            return
        if st == 'slp':
            if SLEEP_CLAUSE and dfn_side.slept_by_foe:
                return
            dfn.status = 'slp'
            dfn.sleep = rng.randint(1, 3)
            dfn_side.slept_by_foe = True
        else:
            dfn.status = st
            if st == 'tox':
                dfn.tox = 0
            apply_synchronize(dfn, att, st)
        att.status_infl += 1
        return
    if m.get('id') == 'REST':
        if att.hp < att.maxhp and att.status != 'slp':
            att.heal_done += (att.maxhp - att.hp) / att.maxhp
            att.hp = att.maxhp
            att.status, att.tox, att.sleep = 'slp', 0, 2
        return
    if e in HEAL_EFFECTS:
        frac = 0.5
        if e == 'EFFECT_HEALING_LIGHT':    # Synthesis-style: 2/3 in sun, 1/4 in other weather
            w = weather_of(att)
            frac = 2 / 3 if w == 'sun' else (0.25 if w else 0.5)
        healed = min(att.maxhp - att.hp, att.maxhp * frac)
        att.hp += healed
        att.heal_done += healed / att.maxhp
        return
    if e == 'EFFECT_LEECH_SEED':
        dfn.seeded = True
        return
    if e == 'EFFECT_SPIKES':
        if dfn_side.spikes < 3:
            att.hazards_set += 1
        dfn_side.spikes = min(3, dfn_side.spikes + 1)
        return
    if e == 'EFFECT_TOXIC_SPIKES':
        if dfn_side.tspikes < 2:
            att.hazards_set += 1
        dfn_side.tspikes = min(2, dfn_side.tspikes + 1)
        return
    if e in ('EFFECT_REFLECT', 'EFFECT_LIGHT_SCREEN'):
        attr = 'reflect' if e == 'EFFECT_REFLECT' else 'light_screen'
        if not getattr(att_side, attr):
            turns = SCREEN_TURNS + (3 if att.item == 'LIGHT_CLAY' else 0)
            setattr(att_side, attr, turns)
            att.screens_set += 1
        return
    if e == 'EFFECT_HEAL_BELL':
        for t in att_side.team:
            if not t.fainted and t.status is not None:
                t.status = None
                t.sleep = t.tox = 0
                att.cures += 1
        return
    if e == 'EFFECT_ROAR':
        others = [i for i in dfn_side.alive_indices() if i != dfn_side.active]
        if others and dfn.ability != 'SUCTION_CUPS':
            apply_switch(dfn_side, rng.choice(others), att_side, chart)
            dfn_side.switched = True
            att.phazes += 1
        return
    if e == 'EFFECT_HAZE':
        for mon in (att, dfn):
            for k in mon.stage:
                if mon is dfn and mon.stage[k] > 0:
                    att.stat_drops += mon.stage[k]
                mon.stage[k] = 0
        return
    if e == 'EFFECT_PAIN_SPLIT':
        avg = (att.hp + dfn.hp) / 2
        if avg > att.hp:
            att.heal_done += (avg - att.hp) / att.maxhp
        dfn.dmg_taken += max(0.0, dfn.hp - avg) / dfn.maxhp
        att.hp, dfn.hp = min(att.maxhp, avg), min(dfn.maxhp, avg)
        return
    if e == 'EFFECT_CURSE':
        if 'GHOST' in att.types:
            if not dfn.cursed:
                att.hp -= att.maxhp / 2
                dfn.cursed = True
                if att.hp <= 0:
                    att.fainted = True
        else:
            att.stage['atk'] = min(6, att.stage['atk'] + 1)
            att.stage['defe'] = min(6, att.stage['defe'] + 1)
            att.stage['spe'] = max(-6, att.stage['spe'] - 1)
        return
    if e in WEATHER_MOVES:
        set_weather(att_side.field, WEATHER_MOVES[e], att)
        return
    if e == 'EFFECT_SUBSTITUTE':
        if att.sub_hp <= 0 and att.hp > att.maxhp / 4:
            att.hp -= att.maxhp / 4
            att.sub_hp = att.maxhp / 4
            att.subs_made += 1
        return
    if e == 'EFFECT_BATON_PASS':
        others = [i for i in att_side.alive_indices() if i != att_side.active]
        if others:
            stage, sub, seeded = dict(att.stage), att.sub_hp, att.seeded
            best = max(others, key=lambda i: matchup_score(att_side.team[i], dfn, moves, chart))
            apply_switch(att_side, best, dfn_side, chart)
            new = att_side.mon
            new.stage, new.sub_hp, new.seeded = stage, sub, seeded
            att.passes += 1
            att_side.switched = True
        return
    if e == 'EFFECT_TRICK':
        if (att.item or dfn.item) and 'STICKY_HOLD' not in (att.ability, dfn.ability):
            att.item, dfn.item = dfn.item, att.item
            att.locked_move = dfn.locked_move = None
            att.tricks += 1
        return
    if e == 'EFFECT_TRICK_ROOM':
        field = att_side.field
        if field is not None:
            if field.trick_room:
                field.trick_room = 0
            else:
                field.trick_room = TRICK_ROOM_TURNS
                att.trick_rooms += 1
        return
    if e == 'EFFECT_SWAGGER':
        dfn.stage['atk'] = min(6, dfn.stage['atk'] + 2)
        if not dfn.confused and not status_blocked(dfn, 'cnf'):
            dfn.confused = rng.randint(2, 4)
            att.status_infl += 1
        return
    if e == 'EFFECT_MEAN_LOOK':
        if not dfn.mean_looked and not can_escape(dfn):
            dfn.mean_looked = att           # trapped until this mon leaves the field
            att.traps += 1
        return
    if e == 'EFFECT_PERISH_SONG':
        for mon in (att, dfn):
            if not mon.perish and mon.ability != 'SOUNDPROOF':
                mon.perish = PERISH_COUNT
                mon.perish_by = att
        return
    if e == 'EFFECT_ENCORE':
        if dfn.last_move is not None and not dfn.encore:
            dfn.encore = ENCORE_TURNS
            dfn.encore_move = dfn.last_move
        return
    # unmodelled status move: no-op


STAT_KEYS = ('dmg_dealt', 'kos', 'status_infl', 'heal_done', 'dmg_taken', 'turns_active',
             'hazards_set', 'screens_set', 'cures', 'pivots', 'phazes',
             'hazards_cleared', 'stat_drops', 'weather_set', 'subs_made', 'passes',
             'tricks', 'trick_rooms', 'traps', 'perish_kos')


def run_battle(team_a, team_b, moves, chart, seed=None, detail=False):
    """Run one 6v6. Returns (result, contrib_a, contrib_b):
      result    : 0 if side A wins, 1 if B, -1 on turn-limit draw.
      contrib_* : list of (dmg_dealt, kos, status_infl, heal_done) per mon, same
                  order as team_a/team_b.
                    dmg_dealt    : useful damage this mon dealt, summed as a
                                   fraction of each target's max HP (capped
                                   per-hit so overkill on an already-doomed mon
                                   doesn't inflate the score)
                    kos          : faints this mon's own moves directly caused
                    status_infl  : major statuses/confusion this mon's own
                                   moves landed on a foe
                    heal_done    : HP this mon recovered via its own heal moves
                                   or Leech Seed drain, as a fraction of its own
                                   max HP
                  A per-mon signal, unlike the team-wide win/loss, so a mon's
                  value isn't conflated with its teammates' (see sim6v6.py's
                  role-team-builder note)."""
    rng = random.Random(seed)
    field = Field()
    A, B = Side([Pmon(*t) for t in team_a], field), Side([Pmon(*t) for t in team_b], field)
    A.foe, B.foe = B, A
    apply_switch(A, 0, B, chart)
    apply_switch(B, 0, A, chart)

    def contrib(side):
        if detail:
            return [{k: getattr(m, k) for k in STAT_KEYS} | {'survived': not m.fainted}
                    for m in side.team]
        return [(m.dmg_dealt, m.kos, m.status_infl, m.heal_done) for m in side.team]

    for _ in range(MAX_TURNS):
        # ---- switching decisions (forced first if a side's active fainted) ----
        for s, foe in ((A, B), (B, A)):
            if s.mon.fainted:
                nxt = choose_switch(s, foe, moves, chart, forced=True, rng=rng)
                if nxt is not None:
                    apply_switch(s, nxt, foe, chart)
        if not A.alive_indices():
            return 1, contrib(A), contrib(B)
        if not B.alive_indices():
            return 0, contrib(A), contrib(B)
        acted = set()                      # sides whose turn was spent before moves
        for s, foe in ((A, B), (B, A)):
            if not s.mon.fainted:
                nxt = choose_switch(s, foe, moves, chart, forced=False, rng=rng)
                if nxt is not None:
                    # Pursuit: a foe holding it may hit the fleeing mon at double power
                    pi = next((i for i, mv in enumerate(foe.mon.moves)
                               if moves[mv]['effect'] == 'EFFECT_PURSUIT'), None)
                    if (pi is not None and not foe.mon.fainted and id(foe) not in acted
                            and rng.random() < 0.5):
                        perform(foe, s, moves, chart, rng, idx=pi, power_mult=2.0)
                        acted.add(id(foe))
                    if not s.mon.fainted:
                        apply_switch(s, nxt, foe, chart)
                    else:
                        nxt = choose_switch(s, foe, moves, chart, forced=True, rng=rng)
                        if nxt is not None:
                            apply_switch(s, nxt, foe, chart)
        if not A.alive_indices():
            return 1, contrib(A), contrib(B)
        if not B.alive_indices():
            return 0, contrib(A), contrib(B)
        for s in (A, B):
            s.mon.hit_phys = s.mon.hit_spec = 0.0

        # ---- order by (priority of chosen move, speed) ----
        # Each side's move is chosen once, here, and that same move is the one
        # used (turn order used to be decided by one choice and the attack
        # made with a second, independently randomised one).
        A.mon.turns_active += 1
        B.mon.turns_active += 1
        ia = choose_move(A, B, moves, chart, rng)
        ib = choose_move(B, A, moves, chart, rng)
        chosen = {id(A): ia, id(B): ib}
        pa, pb = moves[A.mon.moves[ia]]['prio'], moves[B.mon.moves[ib]]['prio']
        sa, sb = A.mon.stat('spe'), B.mon.stat('spe')
        if field.trick_room:               # slower mons move first within a priority
            sa, sb = -sa, -sb
        a_first = (pa, sa) > (pb, sb) or ((pa, sa) == (pb, sb) and rng.random() < 0.5)
        order = (A, B) if a_first else (B, A)
        A.switched = B.switched = False

        moved = set()
        for s, foe in (order, order[::-1]):
            if s.mon.fainted or foe.mon.fainted or s.switched or id(s) in acted:
                continue                   # a mon dragged in this turn doesn't act
            foe_idx = chosen[id(foe)] if not foe.switched else None
            perform(s, foe, moves, chart, rng, idx=chosen[id(s)],
                    foe_move=foe.mon.moves[foe_idx] if foe_idx is not None else None,
                    foe_moved=id(foe) in moved)
            moved.add(id(s))
        for s in (A, B):
            s.mon.protected = False
            s.reflect = max(0, s.reflect - 1)
            s.light_screen = max(0, s.light_screen - 1)
        # ---- residuals ----
        for s, foe in ((A, B), (B, A)):
            end_of_turn(s.mon, foe, rng)
        field.trick_room = max(0, field.trick_room - 1)
        if field.weather:
            field.weather_turns -= 1
            if field.weather_turns <= 0:
                field.weather = None
        if not A.alive_indices():
            return 1, contrib(A), contrib(B)
        if not B.alive_indices():
            return 0, contrib(A), contrib(B)
    return -1, contrib(A), contrib(B)
