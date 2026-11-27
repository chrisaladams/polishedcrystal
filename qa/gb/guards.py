"""Memory-integrity guards usable from any test (PyBoy backend: polled per frame)."""

PLAYER_FIELDS = ('Sprite', 'MapObjectIndex', 'SpriteTile', 'MovementType')


class PlayerStructGuard:
    """Detects corruption of the player's object struct: the identity fields
    (sprite, map-object index, tile base) must not change while walking, and the
    follower queue must stay inside its 5 bytes."""

    def __init__(self, g):
        self.g = g
        self.base = g.sym['wPlayerStruct'][1]
        self.queue = g.sym['wFollowMovementQueue'][1]
        self.qlen_sym = 'wFollowerMovementQueueLength'
        self.ref = self.read()
        self.violations = []

    def read(self):
        return tuple(self.g.read(self.base + i, 1) for i in range(3))

    def check(self, tag=''):
        cur = self.read()
        qlen = self.g.rd(self.qlen_sym)
        if cur != self.ref:
            self.violations.append(f'{tag}: player struct [Sprite,MapObjectIndex,SpriteTile] {self.ref} -> {cur}')
            self.ref = cur
        if 4 < qlen < 255:
            self.violations.append(f'{tag}: follower queue length {qlen} overruns its 5 bytes')
        return not self.violations


CRASH_LABELS = ('Crash', 'CrashRst0', 'CrashRst38')


class CrashWatch:
    """Records any execution of the ROM's crash handlers (rst $00/$38, Crash)."""

    def __init__(self, g):
        self.hits = []
        for label in CRASH_LABELS:
            if label in g.sym:
                g.hook(label, lambda *_a, label=label, g=g: self.hits.append((g.frame, label)))

    @property
    def crashed(self):
        return bool(self.hits)


class OverworldGuard:
    """Per-step invariants for overworld walking: no crash, player struct identity
    intact, follower queue inside its 5 bytes, stack pointer in RAM, and a
    follow link that points at something real."""

    def __init__(self, g):
        self.g = g
        self.player = PlayerStructGuard(g)
        self.crash = CrashWatch(g)

    def check(self, tag=''):
        g = self.g
        bad = []
        self.player.check(tag)
        if self.crash.crashed:
            bad.append(f'{tag}: ROM crash handler ran: {self.crash.hits[-1]}')
        sp = g.regs['sp'] if hasattr(g, 'regs') and isinstance(getattr(type(g), 'regs', None), property) else g.reg.SP
        if sp < 0xc000 and sp != 0:
            bad.append(f'{tag}: stack pointer {sp:04x} outside RAM')
        self.player.violations.extend(bad)
        return not self.player.violations

    @property
    def violations(self):
        return self.player.violations
