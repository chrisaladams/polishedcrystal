"""Hardware-rule checks computed from emulator state (OAM, VRAM, LCD)."""

MAX_PER_LINE = 10


def oam_entries(g):
    o = g.oam()
    return [(i, o[i * 4], o[i * 4 + 1], o[i * 4 + 2], o[i * 4 + 3]) for i in range(40)]


def sprite_height(g):
    return 16 if g.read(0xff40) & 4 else 8


def line_pressure(g):
    """Per scanline: the OAM indices that cover it, in OAM order.

    Hardware draws only the first 10 that overlap a line (X position is
    irrelevant to the limit, even if off screen horizontally: x=0 still counts).
    Returns (lines, dropped) where dropped is {oam_index: [scanlines]}."""
    h = sprite_height(g)
    lines = {}
    for i, y, x, t, a in oam_entries(g):
        top = y - 16
        for ly in range(max(top, 0), min(top + h, 144)):
            lines.setdefault(ly, []).append(i)
    dropped = {}
    for ly, idx in lines.items():
        for i in idx[MAX_PER_LINE:]:
            dropped.setdefault(i, []).append(ly)
    return lines, dropped


def visible_sprites(g):
    """OAM entries on screen (Y 1..159, X 1..167)."""
    return [e for e in oam_entries(g) if 0 < e[1] < 160 and 0 < e[2] < 168]
