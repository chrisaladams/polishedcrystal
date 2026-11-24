#!/usr/bin/env python3
"""Check in the running game that every Pokemon's walking sprite and colours
are drawn correctly.

For every species and form, it puts that Pokemon in party slot 1 of a save,
then, in the emulator:
- follower: opens and closes the start menu (the follower is refreshed),
  takes a step, and checks that the walking sprite's standing frames (down,
  up, left) and walking frames are in VRAM exactly as in
  gfx/followers/<name>.2bpp, that the follower's OAM uses them, and that the
  palette it's drawn with has the table's light and dark colours (colour 2 of
  those overworld palettes, for the current time of day);
- party menu: opens it and checks the mini (the sprite's first two frames) is
  in VRAM and OBJ palette 2 has the light and dark colours by day.

The expected sprite and colours come from the source files (gfx/followers/,
data/pokemon/overworld_icon_pals.asm, SHARE in make_tables.py), not from the
ROM, so a wrong table entry is caught.

Usage (from the repository root, after make):
  python3 utils/followers/test_followers.py SAVE.sav [--only NAME ...]
"""
import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'linktest'))
sys.path.insert(0, os.path.join(ROOT, 'meta_sim'))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'followers'))
import linktest as L                                      # noqa: E402
from oracle_pipeline import rgbasm_values                 # noqa: E402
from make_tables import SHARE                             # noqa: E402

ROM = os.path.join(ROOT, 'polishedcrystal-3.2.3.gbc')
NEW_BARK = (24, 2, 6, 5)  # map group, number, x, y: an outdoor map with room to walk
MON_NAMES = ['RED', 'BLUE', 'GREEN', 'PURPLE', 'BROWN', 'GRAY', 'PINK', 'TEAL', 'YELLOW',
             'ORANGE', 'AZURE', 'WHITE', 'BLACK', 'TAN']
FORM_SUFFIX = {'ALOLAN_FORM': '_alolan', 'GALARIAN_FORM': '_galarian', 'HISUIAN_FORM': '_hisuian',
               'PALDEAN_FORM': '_paldean', 'TAUROS_PALDEAN_FIRE_FORM': '_paldean_fire',
               'TAUROS_PALDEAN_WATER_FORM': '_paldean_water',
               'DUDUNSPARCE_THREE_SEGMENT_FORM': '_three_segment',
               'URSALUNA_BLOODMOON_FORM': '_bloodmoon', 'MEWTWO_ARMORED_FORM': '_armored',
               'PIKACHU_SURF_FORM': '_surf'}


def camel_to_stem():
    """Mini label (e.g. MrMime) -> sprite file stem (mr__mime), from the minis file and SHARE."""
    stems = {}
    for line in open(os.path.join(ROOT, 'gfx', 'followers.asm')):
        m = re.match(r'(\w+)Walk:: INCBIN "gfx/followers/(\w+)\.2bpp\.lzp"', line)
        if m:
            stems[m.group(1)] = m.group(2)
    return stems


def cases():
    """(label, species constant, form constant) for every species and form."""
    src = open(os.path.join(ROOT, 'data', 'pokemon', 'overworld_icon_pals.asm')).read()
    out = []
    for sp, form in re.findall(r'\ticonpal \w+, \w+ ; (\w+)(?:, (\w+))?\s*$', src, re.M):
        if sp == 'EGG':
            continue
        out.append((sp, form or 'PLAIN_FORM'))
    forms = re.findall(r'ext_const(?:_def \d+,)? (\w+_FORM)', open(os.path.join(
        ROOT, 'constants', 'pokemon_constants.asm')).read())
    for f in forms:
        for sp in ('UNOWN', 'ARBOK', 'PIKACHU', 'MAGIKARP'):
            if f.startswith(sp + '_') and (sp, f) not in out:
                out.append((sp, f))
    return out


def expected_sprite(sp, form, stems):
    base = sp.lower()
    names = []
    if form.startswith('UNOWN_'):
        names.append('unown_' + form[6:-5].lower())
    if sp == 'UNOWN':
        names.append('unown_a')
    elif form in FORM_SUFFIX:
        names.append(base + FORM_SUFFIX[form])
    names.append(base)
    names.append(base + '_two_segment')
    stem_set = set(stems.values())
    for n in names:
        if n in stem_set:
            return n
    # SHARE: a camel-case label sharing another's sprite
    camel = ''.join(w.capitalize() for w in base.split('_'))
    if camel in SHARE:
        return stems.get(SHARE[camel])
    return None


def expected_colours(sp, form):
    src = open(os.path.join(ROOT, 'data', 'pokemon', 'overworld_icon_pals.asm')).read()
    m = re.search(r'\ticonpal (\w+?)_(\w+), \w+ ; %s, %s\s*$' % (sp, form), src, re.M)
    if not m:
        cosmetic = {'UNOWN': 'NUM_UNOWN', 'ARBOK': 'NUM_ARBOK', 'PIKACHU': 'NUM_PIKACHU',
                    'MAGIKARP': 'NUM_MAGIKARP'}
        plain = form in ('PLAIN_FORM', 'UNOWN_A_FORM', 'ARBOK_JOHTO_FORM')
        if sp in cosmetic and not plain:
            m = re.search(r'rept %s - 1\n\ticonpal (\w+?)_(\w+), \w+' % cosmetic[sp], src)
        else:
            m = re.search(r'\ticonpal (\w+?)_(\w+), \w+ ; %s\s*$' % sp, src, re.M)
    light, dark = m.group(1), m.group(2)
    # PAL_MON_A_B: the name split may land inside a two-word name; fix it up
    for n in MON_NAMES:
        if (light + '_' + dark).startswith(n + '_') and (light + '_' + dark)[len(n) + 1:] in MON_NAMES:
            return n, (light + '_' + dark)[len(n) + 1:]
    return light, dark


def ow_palette_colours(rom, sym, light, dark, time, *, table='MapObjectPals'):
    """colour 2 (as two bytes) of the light and dark overworld palettes, at a time of day."""
    bank, addr = sym[table]
    off = bank * 0x4000 + (addr - 0x4000)
    n_tod = rgbasm_values(['NUM_OW_TIME_OF_DAY_PALS'], None)['NUM_OW_TIME_OF_DAY_PALS']
    def col2(name):
        i = MON_NAMES.index(name)
        o = off + (time * n_tod + i) * 8 + 4
        return rom[o], rom[o + 1]
    return col2(light), col2(dark)


def tiles(two_bpp, frames):
    return b''.join(two_bpp[f * 64:(f + 1) * 64] for f in frames)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('save')
    ap.add_argument('--only', nargs='*')
    args = ap.parse_args()
    from pyboy import PyBoy
    sym = L.load_sym(ROM[:-4] + '.sym')
    rom = open(ROM, 'rb').read()
    stems = camel_to_stem()
    todo = cases()
    names = sorted({sp for sp, _ in todo} | {f for _, f in todo} |
                   {'EXTSPECIES_MASK', 'FORM_MASK', 'SHINY_MASK', 'MON_IS_EGG_F'})
    K = rgbasm_values(names, None)

    pb = PyBoy(ROM, window='null', ram_file=open(args.save, 'rb'))
    pb.set_emulation_speed(0)
    m = pb.memory

    def tick(n):
        for _ in range(n):
            pb.tick(1, False)

    def press(b, wait=30, hold=5):
        pb.button_press(b); tick(hold); pb.button_release(b); tick(wait)

    def wr(name, v, k=0):
        a = sym[name][1] + k
        if 0xd000 <= a < 0xe000:
            m[1, a] = v
        else:
            m[a] = v

    def rd(name, k=0, bank=1):
        a = sym[name][1] + k
        return m[bank, a] if 0xd000 <= a < 0xe000 else m[a]

    tick(900)
    for b in ('start', 'start', 'a', 'a', 'a'):
        press(b, 200)
    for _ in range(4):
        press('b', 30)
    tick(60)
    g, n, x, y = NEW_BARK
    for nm, v in (('wMapGroup', g), ('wMapNumber', n), ('wXCoord', x), ('wYCoord', y),
                  ('wDefaultSpawnpoint', 255), ('wMapStatus', 1)):
        wr(nm, v)
    m[0xff92] = 0xf1
    tick(600)
    wr('wRepelEffect', 250)
    import io
    state = io.BytesIO()
    pb.save_state(state)

    fails = []
    checked = 0
    for sp, form in todo:
        sprite = expected_sprite(sp, form, stems)
        label = sp + ('' if form == 'PLAIN_FORM' else ', ' + form)
        if args.only and sprite not in args.only and sp.lower() not in args.only:
            continue
        if sprite is None:
            fails.append((label, 'no walking sprite found for it in gfx/followers/'))
            continue
        two = open(os.path.join(ROOT, 'gfx', 'followers', sprite + '.2bpp'), 'rb').read()
        light, dark = expected_colours(sp, form)
        species = K[sp]
        formbyte = (K[form] & K['FORM_MASK']) | (K['EXTSPECIES_MASK'] if species > 0xff else 0)

        def setup():
            state.seek(0)
            pb.load_state(state)
            wr('wPartyMon1Species', species & 0xff)
            wr('wPartyMon1Personality', rd('wPartyMon1Personality') & ~K['SHINY_MASK'] & 0xff)
            wr('wPartyMon1Personality', formbyte, 1)

        problems = []
        # follower
        setup()
        press('start', 40)
        press('b', 80)
        for _ in range(2):  # two steps: the follower appears on the first
            press('left', 10, 20)
        tick(40)
        vram = bytes(m[0, 0x8000:0x9800]) + bytes(m[1, 0x8000:0x9800])
        stand, walk = tiles(two, (0, 2, 4)), tiles(two, (1, 3, 5))
        at = vram.find(stand)
        if at < 0:
            problems.append('follower standing frames not in VRAM')
        if vram.find(walk) < 0:
            problems.append('follower walking frames not in VRAM')
        ranges = set()
        for blk in (stand, walk):
            i = vram.find(blk)
            while i >= 0:
                vb, off = divmod(i, 0x1800)
                if off % 16 == 0:
                    ranges.add((vb, off // 16))
                i = vram.find(blk, i + 1)
        if ranges:
            oam = []
            for _ in range(30):  # skip frames where the game is rebuilding OAM
                base = sym['wShadowOAM'][1]
                oam = [m[base + 4 * i:base + 4 * i + 4] for i in range(40)]
                if any(e[0] not in (0, 160) for e in oam):
                    break
                tick(1)
            pals = {e[3] & 7 for e in oam if e[0] not in (0, 160)
                    and any(vb == (e[3] >> 3) & 1 and first <= e[2] < first + 12
                            for vb, first in ranges)}
            if not pals:
                problems.append('no follower OAM uses its tiles')
            else:
                p = pals.pop()
                got = tuple(m[5, sym['wOBPals2'][1] + p * 8 + k] for k in range(2, 6))
                ok = False
                for time in range(4):
                    (l2, d2) = ow_palette_colours(rom, sym, light, dark, time)
                    if got == (l2[0], l2[1], d2[0], d2[1]):
                        ok = True
                if not ok:
                    problems.append(f'follower palette {got} is not {light}/{dark}')
        # party menu
        setup()
        press('start', 40)
        press('a', 250)
        vram = bytes(m[0, 0x8000:0x9800]) + bytes(m[1, 0x8000:0x9800])
        if vram.find(two[:128]) < 0:
            problems.append('party menu mini not in VRAM')
        got = tuple(m[5, sym['wOBPals1'][1] + 2 * 8 + k] for k in range(2, 6))
        (l2, d2) = ow_palette_colours(rom, sym, light, dark, 1)  # DAY
        if got != (l2[0], l2[1], d2[0], d2[1]):
            problems.append(f'party menu palette {got} is not {light}/{dark} by day')
        checked += 1
        if problems:
            fails.append((label + f' [{sprite}]', '; '.join(problems)))
    pb.stop(save=False)
    print(f'{checked} Pokemon and forms checked, {len(fails)} with problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
