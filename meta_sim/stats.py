"""L50 stat calculation, mirroring this ROM's CalcPkmnStatC
(engine/pokemon/mon_stats.asm).

Formula reproduced from the asm:
    inner   = 2*(base + DV) + 1 + (EV >> 2)
    non-HP  = floor(inner * level / 100) + 5          (STAT_MIN_NORMAL)
    HP      = floor(inner * level / 100) + level + 10  (STAT_MIN_HP)
    then nature: floor(stat * mult / 10), mult in {9,10,11}; HP is never natured.
    capped at 999.

Every mon gets the same DVs and EVs in every stat and a neutral nature, so
the comparison is fair; which DVs and EVs is the stat profile, chosen with the
META_STAT_PROFILE environment variable:
    family (default)  DV 8, EV 64: what the family's real link teams have. Read
                      from their saves: DVs are random (about 8 on average),
                      EVs come from ordinary play (0 to 510 in total, spread
                      over every stat), natures random (neutral on average).
    random            DV 15, EV 0: Random Battle teams.
    max               DV 15, EV 252: the theoretical maximum build.
The profile matters for balance: the DVs and EVs add the same amount to every
mon's stats, and the bigger that amount, the smaller the gap between a high
base stat and a low one. The max build adds about 52 points to every stat,
real teams about 21, so under the max build strong base stats look weaker
than they are in real play.
"""
import os

DV_MAX = 15
EV_MAX = 252
LEVEL  = 50
PROFILES = {'family': (8, 64), 'random': (15, 0), 'max': (DV_MAX, EV_MAX)}
PROFILE = os.environ.get('META_STAT_PROFILE', 'family')
DV, EV = PROFILES[PROFILE]

def calc_stat(base, is_hp, dv=None, ev=None, level=LEVEL, nature_mult=10):
    dv = DV if dv is None else dv
    ev = EV if ev is None else ev
    inner = 2 * (base + dv) + 1 + (ev >> 2)
    val = (inner * level) // 100
    val += (level + 10) if is_hp else 5
    if not is_hp:
        val = (val * nature_mult) // 10
    return min(val, 999)

ORDER = ['hp', 'atk', 'defe', 'spe', 'spa', 'spd']

def mon_stats(base_stats, **kw):
    """base_stats: dict with hp/atk/defe/spe/spa/spd -> L50 stat dict."""
    return {k: calc_stat(base_stats[k], k == 'hp', **kw) for k in ORDER}
