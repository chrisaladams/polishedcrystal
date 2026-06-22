"""L50 stat calculation, mirroring this ROM's CalcPkmnStatC
(engine/pokemon/mon_stats.asm).

Formula reproduced from the asm:
    inner   = 2*(base + DV) + 1 + (EV >> 2)
    non-HP  = floor(inner * level / 100) + 5          (STAT_MIN_NORMAL)
    HP      = floor(inner * level / 100) + level + 10  (STAT_MIN_HP)
    then nature: floor(stat * mult / 10), mult in {9,10,11}; HP is never natured.
    capped at 999.

Baseline used by the matrix (documented, uniform for every mon -> fair compare):
    DV = 15, EV = 252 in every stat (EV>>2 = 63), neutral nature.
This is the "theoretical max" build; it inflates absolute numbers but treats all
mons identically, which is what an all-vs-all damage comparison needs.
"""

DV_MAX = 15
EV_MAX = 252
LEVEL  = 50

def calc_stat(base, is_hp, dv=DV_MAX, ev=EV_MAX, level=LEVEL, nature_mult=10):
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
