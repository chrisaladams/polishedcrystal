"""Read the loaded map's collision from the running game (PyBoy backend), exactly
as GetCoordTileCollision does: blocks sit in wOverworldMapBlocks with a 3-block
border, and wDecompressedCollisions holds 4 bytes per block (TL, TR, BL, BR)."""

PASSABLE = {0x00, 0x02, 0x14, 0x18, 0x1c}   # floor, coast sand, long/tall/visual grass


def tile_collision(g, x, y):
    """Collision byte of map tile (x, y) (as wXCoord/wYCoord count them)."""
    w, h = g.rd('wMapWidth'), g.rd('wMapHeight')
    if not (0 <= x < 2 * w and 0 <= y < 2 * h):
        return None
    d, e = x + 4, y + 4
    mb, mbase = g.sym['wOverworldMapBlocks']
    addr = mbase + 1 + (w + 6) * (1 + (e >> 1)) + (d >> 1)
    block = g.read(addr, mb)           # name the bank: without it SameBoy reads whichever WRAM bank is mapped
    bank, base = g.sym['wDecompressedCollisions']
    return g.read(base + block * 4 + (d & 1) + 2 * (e & 1), bank)


CARPETS = {0x70, 0x76, 0x78, 0x7e}          # warp carpets: how a map edge exit is drawn


def walkable(g, x, y, edge=False):
    c = tile_collision(g, x, y)
    return c in PASSABLE or (edge and c in CARPETS)


def ascii_map(g):
    w, h = 2 * g.rd('wMapWidth'), 2 * g.rd('wMapHeight')
    return '\n'.join(''.join('.' if walkable(g, x, y) else '#' for x in range(w)) for y in range(h))
