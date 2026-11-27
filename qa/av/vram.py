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


def objects(g):
    """Live object structs: dicts with index, sprite, tile, palette, screen x/y (pixels, top-left of the 16x16)."""
    from qa.gb.consts import C
    base = g.sym['wPlayerStruct'][1]
    stride = C['OBJECT_LENGTH']
    out = []
    for i in range(C['NUM_OBJECT_STRUCTS']):
        a = base + i * stride
        sprite = g.read(a + C['OBJECT_SPRITE'])
        if not sprite:
            continue
        out.append(dict(index=i, sprite=sprite, tile=g.read(a + C['OBJECT_SPRITE_TILE']),
                        x=g.read(a + C['OBJECT_SPRITE_X']), y=g.read(a + C['OBJECT_SPRITE_Y']),
                        pal=g.read(a + C['OBJECT_PALETTE']) & 7, facing=g.read(a + C['OBJECT_FACING']),
                        invisible=bool(g.read(a + C['OBJECT_FLAGS1']) >> C['INVISIBLE_F'] & 1),
                        off_screen=bool(g.read(a + C['OBJECT_FLAGS2']) >> C['OFF_SCREEN_F'] & 1)))
    return out


_SPRITE_FILES = {}


def sprite_files():
    """{sprite id: path of its raw 2bpp graphic in the repository} for every overworld sprite whose
    graphic is a plain file (sprites built from Pokemon data have none and are not checked)."""
    if _SPRITE_FILES:
        return _SPRITE_FILES
    import os
    import re
    from qa.gb.emu import ROOT
    gfx = {}
    for m in re.finditer(r'^(\w+SpriteGFX)::\s*INCBIN\s+"([^"]+)"', open(os.path.join(ROOT, 'gfx/sprites.asm')).read(), re.M):
        gfx[m.group(1)] = m.group(2).replace('.lzp', '').replace('.lz', '')
    ids = [m.group(1) for m in re.finditer(r'^\s*overworld_sprite\s+(\w+),', open(os.path.join(ROOT, 'data/sprites/sprites.asm')).read(), re.M)]
    for i, label in enumerate(ids, 1):
        path = os.path.join(ROOT, gfx.get(label, ''))
        if os.path.isfile(path):
            _SPRITE_FILES[i] = path
    return _SPRITE_FILES


def blank_standing_sprites():
    """{sprite id: path} of sprites whose first frame (four 8x8 tiles) is entirely blank in the repository's own
    graphics: invisible trigger objects, drawn on purpose. Derived from the data, not listed by hand."""
    return {i: p for i, p in sprite_files().items() if not any(open(p, 'rb').read(64))}


def _slot(o):
    """(vram bank, first tile) of the 12 tiles an object's sprite occupies (tile bit 7 set: bank 0)."""
    return (0 if o['tile'] & 0x80 else 1), o['tile'] & 0x7f


def sprite_findings(g):
    """Sprite findings for the current screen, each judged against the one object that owns the OAM entry
    (by the VRAM tile slot the object's sprite was loaded into). Nothing is exempted by map.

    * sprite-tile-mismatch: a drawn OAM entry's tile data in VRAM differs from the repository graphic of
      the owning object's sprite (a failed, truncated or overwritten load); a blank tile is fine only when
      the repository graphic is blank there too (transparent corners, invisible trigger objects)
    * object-not-drawn: an object well inside the screen that is not hidden by the engine or a script has no
      OAM entry at all
    Returns [dict(kind, msg, expected, why)]."""
    from pathlib import Path
    out = []
    base = g.sym['wShadowOAM'][1]
    sh = [g.read(base + k) for k in range(160)]
    entries = [(i, sh[i * 4], sh[i * 4 + 1], sh[i * 4 + 2], sh[i * 4 + 3]) for i in range(40)
               if 0 < sh[i * 4] < 160 and 0 < sh[i * 4 + 1] < 168]
    v = (g.vram(0), g.vram(1))
    tall = g.read(0xff40) & 4
    files = sprite_files()
    objs = objects(g)
    drawn = set()
    for i, y, x, t, a in entries:
        bank = (a >> 3) & 1
        o = next((ob for ob in objs if _slot(ob)[0] == bank and _slot(ob)[1] <= t < _slot(ob)[1] + 12), None)
        if o is None:
            continue
        drawn.add(o['index'])
        path = files.get(o['sprite'])
        if not path:
            continue
        k = t - _slot(o)[1]
        raw = Path(path).read_bytes()
        if (k + 1) * 16 > len(raw):
            continue
        want, have = raw[k * 16:(k + 1) * 16], bytes(v[bank][t * 16:(t + 1) * 16])
        if want != have:
            out.append(dict(kind='sprite-tile-mismatch', expected=False, why='',
                            msg='OAM[%d] tile %d (bank %d) of object %d sprite %d differs from its graphic %s tile %d%s' % (
                                i, t, bank, o['index'], o['sprite'], os_basename(path), k, ' (blank in VRAM)' if not any(have) else '')))
    blank_ok = blank_standing_sprites()
    for o in objs:
        if o['facing'] == 0xff or o['invisible'] or o['off_screen'] or o['sprite'] in blank_ok:
            continue
        if 16 <= o['x'] <= 128 and 16 <= o['y'] <= 112 and o['index'] not in drawn:
            out.append(dict(kind='object-not-drawn', expected=False, why='',
                            msg='object %d (sprite %d) at (%d,%d) has no OAM entry' % (o['index'], o['sprite'], o['x'], o['y'])))
    return out


def os_basename(p):
    import os
    return os.path.basename(p)
