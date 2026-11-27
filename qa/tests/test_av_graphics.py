"""Before-and-after graphics validation: menus, battle menus and map transitions.

The oracle for menus is simple and objective: whatever you open and close must leave the
screen as it was. For battles the enemy's sprite tiles must be untouched by the Pack,
party and summary screens, the bug class behind the Rising Cup report."""
import os

import numpy as np

from qa.av import frames, vram
from qa.framework import qa_test
from qa.gb import fixtures as F
from qa.gb.consts import map_ids

PROV_MENU = 'stage checkpoint and warp are injected; the menus are opened and closed with button input'


def _quiet_room(g):
    """Warp into a static indoor map (no animated tiles, no wandering NPCs)."""
    gr, nr = map_ids('VIOLET_POKECENTER_1F')
    F.teleport(g, gr, nr, 2, 2, settle=60)
    from qa.tests.test_map_smoke import pick_tile
    t = pick_tile(g) or (2, 2)
    F.teleport(g, gr, nr, t[0], t[1], settle=90)
    g.tick(60)


def _make_menu(backend_models):
    @qa_test(suites=('av', 'battle', 'full'), covers=('battle.hud',), backends=('pyboy', 'sameboy'), models=backend_models,
             provenance=PROV_MENU, timeout=1800, name='test_av_graphics.menus_restore_the_screen')
    def menus(ctx):
        """Start menu entries: opening and closing each must restore the overworld picture."""
        from qa.gb import ladder, saves
        if ctx.backend == 'pyboy':
            g = ctx.game()
            ladder.load(g, 'goldenrod')
        else:
            # SameBoy cannot load a PyBoy snapshot: Continue from a save made at that stage instead
            from qa.gb.emu import Game
            p = Game(rom=ctx.rom, workdir=ctx.out)
            ladder.load(p, 'goldenrod')
            sram = saves.save_game(p)
            sav = os.path.join(ctx.out, 'goldenrod.sav')
            open(sav, 'wb').write(sram)
            where = F.where(p)
            p.close()
            g = ctx.game(sav=sav)
            saves.boot_continue(g, where)
        _quiet_room(g)
        base = g.frame_rgb()
        bad, changed = [], []
        for idx in range(9):
            g.press('start', 4, 30)
            for _ in range(idx):
                g.press('down', 4, 10)
            g.press('a', 4, 40)
            g.tick(40)
            opened = g.frame_rgb()
            shown = frames.diff(base, opened, tol=40)['fraction']
            changed.append(round(shown, 2))
            for _ in range(6):                      # back out of whatever opened
                g.press('b', 4, 24)
            g.tick(60)
            after = g.frame_rgb()
            d = frames.diff(base, after, tol=40)
            if d['fraction'] > 0.02:
                bad.append((idx, d))
                ctx.screenshot(g, f'menu{idx}_after')
                frames.save(frames.diff_image(base, after, 40), os.path.join(ctx.out, f'menu{idx}_diff.png'), 2)
                ctx.av.append(dict(kind='MENU_RESIDUE', detail=f'Start-menu entry {idx}: screen differs from before after closing ({d["fraction"] * 100:.1f}% pixels)',
                                   where='VIOLET_POKECENTER_1F', sig=f'menu-{idx}', count=1,
                                   artifacts={'diff': os.path.join(ctx.out, f'menu{idx}_diff.png')}, context=dict(d), frame=g.frame))
            if not g_ready(g):
                break
        ctx.note('menu entries checked: %d; fraction of the screen each opened menu changed: %s; screen not restored after %d' % (idx + 1, changed, len(bad)))
        ctx.expect(sum(1 for c in changed if c > 0.05) >= 5, 'the menus did not visibly open (vacuous test): %s' % changed)
        ctx.expect(not bad, 'the screen was not restored after closing: ' + '; '.join(f'entry {i} ({d["fraction"] * 100:.1f}%)' for i, d in bad))
    return menus


def g_ready(g):
    return g.rd('wScriptMode') == 0 and not g.in_battle()


_make_menu(('CGB-E',))


def _hashes(g):
    """Tile hashes of the enemy pic (tiles $00-$30 of vTiles2) and the HUD/status icon tiles ($55-$5f)."""
    base = g.sym['vTiles2'][1] - 0x8000
    v = g.vram(0)
    import hashlib
    h = lambda a, b: [hashlib.sha1(v[base + i * 16:base + (i + 1) * 16]).hexdigest()[:8] for i in range(a, b)]
    return h(0, 0x31), h(0x55, 0x60)


@qa_test(suites=('av', 'battle', 'full'), covers=('battle.hud', 'battle.switching', 'cups.rising_star'), backends=('pyboy', 'sameboy'),
         models=('CGB-E', 'AGB'), provenance='cup entry and every menu action are button input; party/position are an injected fixture',
         timeout=1800)
def battle_menus_keep_enemy_sprite(ctx):
    """In the first Rising Star Cup battle: open and close the party menu and the summary
    screen. The enemy's sprite tiles must be identical afterwards (the Rising Cup bug class, for every
    menu, not just the forced switch). The Pack is not tested here: cup battles disable it."""
    from qa.gb import battle as B
    from qa.tests.test_rising_cup_hud import build
    g = ctx.boot('rising_cup_start', build)
    if hasattr(g, 'enable_exec_guard'):
        g.enable_exec_guard()                 # SameBoy: execution counters need the native callback
    B.cup_select_three(g)
    menu = g.counter('BattleMenu')
    seen = 0
    for _ in range(80):
        if menu() > seen:
            break
        g.press('a', 4, 26)
    ctx.expect(menu() > seen, 'never reached the first battle menu')
    g.tick(40)
    pic0, hud0 = _hashes(g)
    actions = {
        'party': ['up', 'left', 'right', 'a', 'b', 'b'],
        'summary': ['up', 'left', 'right', 'a', 'a', 'down', 'a', 'b', 'b', 'b', 'b'],
    }
    bad = []
    for name, keys in actions.items():
        seen = menu()
        g.press('up', 4, 8)
        g.press('left', 4, 8)
        before = g.frame_rgb()
        peak = 0.0
        for k in keys:
            g.press(k, 4, 24)
            peak = max(peak, frames.diff(before, g.frame_rgb(), tol=40)['fraction'])
        ctx.expect(peak > 0.1, f'{name}: the menu never visibly opened (peak change {peak:.2f}): the test would be vacuous')
        for _ in range(40):
            if menu() > seen:
                break
            g.press('b', 4, 24)
        g.tick(40)
        pic, hud = _hashes(g)
        changed = [i for i in range(len(pic0)) if pic0[i] != pic[i]]
        hchanged = [i + 0x55 for i in range(len(hud0)) if hud0[i] != hud[i]]
        ctx.note(f'{name}: enemy pic tiles changed {vram.ranges(changed)}, HUD tiles changed {vram.ranges(hchanged)}')
        if changed:
            bad.append(name)
            ctx.screenshot(g, f'after_{name}')
            ctx.av.append(dict(kind='VRAM_CLOBBER', detail=f'{name} menu left enemy pic tiles {vram.ranges(changed)} changed', where='battle', sig=f'vc-{name}',
                               count=1, artifacts={}, context=dict(tiles=changed), frame=g.frame))
    ctx.expect(not bad, 'enemy sprite tiles changed after: ' + ', '.join(bad))
