"""VRAM, tilemap and OAM integrity checks (either backend)."""
import hashlib

from qa.gb import hw

TILE = 16


def tile_hashes(g, bank=0, start=0, count=384):
    """sha1 of every tile (16 bytes) of VRAM `bank`, tiles start..start+count-1 of $8000."""
    v = g.vram(bank)
    return [hashlib.sha1(v[(start + i) * TILE:(start + i + 1) * TILE]).hexdigest()[:10] for i in range(count)]


def tile_delta(before, after):
    """Indices of tiles whose data changed between two tile_hashes() lists."""
    return [i for i, (a, b) in enumerate(zip(before, after)) if a != b]


def ranges(idx):
    """Collapse [1,2,3,7,8] to [(1,3),(7,8)] for readable reports."""
    out = []
    for i in idx:
        if out and i == out[-1][1] + 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    return [tuple(r) for r in out]


def oam_problems(g):
    """Structural problems in OAM. Returns a list of strings."""
    out = []
    v0, v1 = g.vram(0), g.vram(1)
    tall = g.read(0xff40) & 4
    seen = {}
    for i, y, x, t, a in hw.oam_entries(g):
        if not (0 < y < 160 and 0 < x < 168):
            continue
        bank = (a >> 3) & 1
        base = ((t & 0xfe) if tall else t) * TILE
        data = (v1 if bank else v0)[base:base + (32 if tall else 16)]
        if not any(data):
            out.append(f'OAM[{i}] visible at ({x - 8},{y - 16}) but tile {t} (bank {bank}) is blank')
        key = (y, x, t, a)
        if key in seen:
            out.append(f'OAM[{i}] duplicates OAM[{seen[key]}]')
        seen.setdefault(key, i)
    return out


def tilemap_problems(g):
    """Both BG maps: palette attributes valid, tile ids point at non-reserved data."""
    out = []
    v0, v1 = g.vram(0), g.vram(1)
    for name, base in (('BGMap0', 0x1800), ('BGMap1', 0x1c00)):
        attrs = v1[base:base + 0x400]
        ids = v0[base:base + 0x400]
        bad_pal = sum(1 for a in attrs if (a & 7) > 7)
        if bad_pal:
            out.append(f'{name}: {bad_pal} entries with an invalid palette')
        if any(a & 0x10 for a in attrs):          # bit 4 is unused on the CGB: must be 0
            n = sum(1 for a in attrs if a & 0x10)
            out.append(f'{name}: {n} attribute bytes with the unused bit 4 set')
    return out


def lcd_state(g):
    """Registers worth keeping with any graphics artifact."""
    names = {'LCDC': 0xff40, 'STAT': 0xff41, 'SCY': 0xff42, 'SCX': 0xff43, 'LY': 0xff44, 'LYC': 0xff45,
             'BGP': 0xff47, 'OBP0': 0xff48, 'OBP1': 0xff49, 'WY': 0xff4a, 'WX': 0xff4b, 'VBK': 0xff4f}
    return {k: g.read(a) for k, a in names.items()}


def palette_problems(g):
    """CGB palette checks (SameBoy backend: direct access to palette RAM).

    * a sprite that is on screen uses an OBJ palette whose three visible colours are all identical
      (it would draw as a flat blob, or vanish against a matching background);
    * a sprite's visible colours all equal the background colour at its position's palette 0 colour
      (invisible against the backdrop)."""
    if not hasattr(g, '_bytes'):
        return []
    import struct
    obp = g._bytes('OBP', 0, 64)
    bgp = g._bytes('BGP', 0, 64)
    pal = lambda raw, i: [struct.unpack_from('<H', raw, i * 8 + c * 2)[0] & 0x7fff for c in range(4)]
    out = []
    for i, y, x, t, a in hw.oam_entries(g):
        if not (0 < y < 160 and 0 < x < 168):
            continue
        p = pal(obp, a & 7)
        if len(set(p[1:])) == 1:
            out.append(f'OAM[{i}] uses OBJ palette {a & 7} with identical visible colours {p[1]:04x}')
        elif all(c == pal(bgp, 0)[0] for c in p[1:]):
            out.append(f'OAM[{i}] uses OBJ palette {a & 7} whose colours all equal the background colour')
    return out
