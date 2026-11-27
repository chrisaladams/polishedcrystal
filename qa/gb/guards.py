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
