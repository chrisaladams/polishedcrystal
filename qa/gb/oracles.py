"""State-consistency oracles: cheap checks on RAM that should hold at any quiet moment.

They find corruption by its symptoms (impossible HP, level, moves, stat stages, a party
list that disagrees with the party structs) wherever it came from, rather than by
knowing the cause in advance."""
from .consts import C


def _stride(g):
    return g.sym['wPartyMon2'][1] - g.sym['wPartyMon1'][1]


def party_problems(g):
    out = []
    n = g.rd('wPartyCount')
    if n > C['PARTY_LENGTH']:
        return [f'party count {n} > {C["PARTY_LENGTH"]}']
    s = _stride(g)
    for i in range(n):
        o = i * s
        species = g.rd('wPartyMon1Species', o)
        level = g.rd('wPartyMon1Level', o)
        hp = g.rd('wPartyMon1HP', o) << 8 | g.rd('wPartyMon1HP', o + 1)
        mx = g.rd('wPartyMon1MaxHP', o) << 8 | g.rd('wPartyMon1MaxHP', o + 1)
        tag = f'party[{i}] species {species}'
        if species == 0:
            out.append(f'{tag}: empty species inside the party')
        if not 1 <= level <= C['MAX_LEVEL']:
            out.append(f'{tag}: level {level}')
        if mx == 0 or mx > 999:
            out.append(f'{tag}: max HP {mx}')
        if hp > mx:
            out.append(f'{tag}: HP {hp} > max {mx}')
        moves = [g.rd('wPartyMon1Moves', o + k) for k in range(4)]
        if any(m > C['NUM_ATTACKS'] for m in moves):
            out.append(f'{tag}: invalid move id in {moves}')
        seen_empty = False
        for m in moves:
            if m == 0:
                seen_empty = True
            elif seen_empty:
                out.append(f'{tag}: move after an empty slot {moves}')
                break
        for k in range(4):
            pp = g.rd('wPartyMon1PP', o + k) & 0x3f
            if pp > 64:
                out.append(f'{tag}: PP {pp}')
    return out


def battle_problems(g):
    if not g.in_battle():
        return []
    out = []
    for who in ('Battle', 'Enemy'):
        hp = g.rd(f'w{who}MonHP') << 8 | g.rd(f'w{who}MonHP', 1)
        mx = g.rd(f'w{who}MonMaxHP') << 8 | g.rd(f'w{who}MonMaxHP', 1)
        if mx and hp > mx:
            out.append(f'{who} mon HP {hp} > max {mx}')
        lvl = g.rd(f'w{who}MonLevel')
        if lvl > C['MAX_LEVEL']:
            out.append(f'{who} mon level {lvl}')
    for who in ('Player', 'Enemy'):
        for k in range(8):
            v = g.rd(f'w{who}StatLevels', k)
            if not 1 <= v <= 13:
                out.append(f'{who} stat stage {k} = {v}')
    return out


def all_problems(g):
    return party_problems(g) + battle_problems(g)


class EnemyPicWatch:
    """Generic graphics-integrity oracle for battles: the enemy's front-pic tiles (vTiles2 $00-$30)
    must not change between two visits to the main battle menu while the same enemy is out.

    It knows nothing about which screen or routine might overwrite them (the Rising Cup defect was
    the party menu loading status icons over them); anything that does so between menus is caught.
    The baseline is taken at the first main menu after the enemy appears and again whenever its
    species, personality or form changes. Substitute/Transform-style effects can change the tiles
    legitimately and are skipped (see `volatile`)."""

    def __init__(self, g):
        self.g = g
        self.key = None
        self.base = None
        self.checks = 0

    def _hash(self):
        import hashlib
        g = self.g
        base = g.sym['vTiles2'][1] - 0x8000
        return hashlib.sha1(bytes(g.vram(0)[base:base + 0x31 * 16])).hexdigest()

    def volatile(self):
        g = self.g
        # enemy Transform / Substitute / Minimize-style states redraw the pic on purpose
        from .consts import C
        sub2, sub4 = g.rd('wEnemySubStatus2'), g.rd('wEnemySubStatus4')
        return bool(sub2 >> C['SUBSTATUS_TRANSFORMED'] & 1) or bool(sub4 >> C['SUBSTATUS_SUBSTITUTE'] & 1)

    def at_menu(self):
        """Call when the main battle menu is up. Returns a problem string or None."""
        g = self.g
        key = (g.rd('wEnemyMonSpecies'), g.rd('wEnemyMonPersonality'),
               g.rd('wEnemyMonPersonality', 1), g.rd('wEnemyMonForm') if 'wEnemyMonForm' in g.sym else 0)
        h = self._hash()
        if key != self.key:
            self.key, self.base = key, h
            return None
        if self.volatile():
            self.base = h
            return None
        self.checks += 1
        if h != self.base:
            self.base = h
            return 'enemy pic tiles changed between battle menus (species %d)' % key[0]
        return None
