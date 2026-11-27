"""A battle policy driven by controller input.

Fight with the strongest move that has PP, send in the first healthy Pokemon when one
faints, refuse the "switch?" offer, never run, never use items. Hooks on the ROM's own
menu entry points tell it which screen the game is waiting on, so it presses the right
buttons instead of guessing."""
from .consts import C

_installed = {}


class _Events:
    """Which battle screen the game has reached since we last looked, from execution counters."""

    def __init__(self, g):
        self.c = {k: g.counter(label) for label, k in (
            ('BattleMenu', 'battle_menu'), ('MoveSelectionScreen', 'move_screen'),
            ('ForcePickSwitchMonInBattle', 'forced_switch'), ('OfferSwitch', 'offer'))}
        self.seen = {k: f() for k, f in self.c.items()}

    def __getitem__(self, k):
        return self.c[k]() != self.seen[k]

    def __setitem__(self, k, v):
        self.seen[k] = self.c[k]()


def _events(nav):
    g = nav.g
    ev = _installed.get(id(g))
    if ev is None:
        ev = _installed[id(g)] = _Events(g)
    return ev


def _move_power(g, move):
    bank, addr = g.sym['Moves']
    length = C['MOVE_LENGTH']
    return g.read_rom(bank, addr + (move - 1) * length + 2)


def best_move(g):
    """Index (0-3) of the strongest move with PP, or 0."""
    best, best_p = 0, -1
    for i in range(4):
        mv = g.rd('wBattleMonMoves', i)
        pp = g.rd('wBattleMonPP', i) & 0x3f
        if not mv or not pp:
            continue
        p = _move_power(g, mv)
        if p > best_p:
            best, best_p = i, p
    return best


def _cursor_to(nav, target, key='wMenuCursorY', limit=8):
    g = nav.g
    for _ in range(limit):
        cur = g.rd(key) - 1
        if cur == target:
            return True
        nav.press('down' if cur < target else 'up', 4, 8)
    return False


def first_healthy(g, skip):
    n = g.rd('wPartyCount')
    stride = g.sym['wPartyMon2'][1] - g.sym['wPartyMon1'][1]
    for i in range(n):
        if i == skip:
            continue
        if g.rd('wPartyMon1HP', i * stride) or g.rd('wPartyMon1HP', i * stride + 1):
            if not (g.rd('wPartyMon1Form', i * stride) & 0x20 if 'wPartyMon1Form' in g.sym else 0):   # not an egg
                return i
    return None


def play(nav, max_frames=36000):
    from .nav import Softlock
    g = nav.g
    ev = _events(nav)
    start = g.frame
    nav.battles += 1
    while g.in_battle():
        if g.frame - start > max_frames:
            raise Softlock('battle did not end in %d frames at %s' % (max_frames, nav.here()))
        if ev['move_screen']:
            ev['move_screen'] = 0
            _cursor_to(nav, best_move(g))
            nav.press('a', 4, 20)
        elif ev['forced_switch']:
            ev['forced_switch'] = 0
            tgt = first_healthy(g, g.rd('wCurBattleMon'))
            if tgt is not None:
                _cursor_to(nav, tgt)
            nav.press('a', 4, 20)
            nav.press('a', 4, 20)
        elif ev['offer']:
            ev['offer'] = 0
            for _ in range(10):
                if not g.in_battle():
                    break
                nav.press('b', 4, 18)
        elif ev['battle_menu']:
            ev['battle_menu'] = 0
            nav.press('a', 4, 20)           # FIGHT
        else:
            nav.press('a', 4, 14)
    g.tick(90)
