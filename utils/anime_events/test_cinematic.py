#!/usr/bin/env python3
"""Check the story scene effects (engine/events/cinematic.asm) in the running
game (PyBoy), calling them as the scene macros do:

- scene_begin keeps the palettes, and weather lightning doesn't strike
  until scene_end;
- scene_tint blends every color on screen halfway to the tint, exactly
  (x & t) + ((x ^ t) & %0111101111011110) / 2 per color, the text box's
  palette aside, and two tints compound;
- scene_flash and scene_pulse come back to the scene's starting palettes;
- scene_end brings back the palettes exactly as they were, and the map's
  music, restarting it only if the scene changed it; scene_end_keep_music
  brings back the palettes and leaves the music alone;
- nothing draws a random number.

Usage (from the repository root, after make):
  python3 utils/anime_events/test_cinematic.py SAVE.sav
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_friend_records import Caller, Game, rgbasm_values  # noqa: E402

TINTS = {'TINT_DARK': (0, 0, 0), 'TINT_GREEN': (4, 31, 6), 'TINT_PURPLE': (20, 2, 31), 'TINT_WHITE': (31, 31, 31)}


def rgb(r, g, b):
    return r | g << 5 | b << 10


def blend(x, t):
    return (x & t) + (((x ^ t) & 0x7bde) >> 1)


def main():
    K = rgbasm_values(['OW_WEATHER_LIGHTNING_DISABLED_F', 'OW_WEATHER_DO_FLY_F', 'CINEMATIC_ACTIVE_F', *TINTS], None)
    g = Game(open(sys.argv[1], 'rb').read())
    g.boot()
    caller = Caller(g)
    fails = []
    randoms = []
    g.pb.hook_register(*g.sym['Random'], lambda _: randoms.append(1), None)

    def pals(label):
        """16 palettes (BG then OB) of 4 colors, from WRAM bank 5."""
        a = g.sym[label][1]
        b = [g.m[5, a + k] for k in range(128)]
        return [b[k] | b[k + 1] << 8 for k in range(0, 128, 2)]

    def call(label, var=None):
        if var is not None:
            g.m[g.sym['hScriptVar'][1]] = var
        caller.call(label)

    def check(cond, what):
        if not cond:
            fails.append(what)

    g.tick(300)  # (the map's name sign gone)
    for _ in range(2):
        start_targets, start_screen = pals('wBGPals1'), pals('wBGPals2')
        music = (g.rd('wMusicIDLo'), g.rd('wMusicIDHi'))
        randoms.clear()

        call('CinematicBegin')
        check(g.rd('wCinematicFlags') & 1 << K['CINEMATIC_ACTIVE_F'], 'scene_begin: not marked active')
        # no lightning during the scene
        g.wr('wWeatherFlags', g.rd('wWeatherFlags') & ~(1 << K['OW_WEATHER_LIGHTNING_DISABLED_F'])
             & ~(1 << K['OW_WEATHER_DO_FLY_F']))
        whites = []
        hook = g.sym['SetWhitePals']
        g.pb.hook_register(*hook, lambda _: whites.append(1), None)
        caller.call('Lightning')
        g.pb.hook_deregister(*hook)
        check(not whites, 'lightning struck during a scene')
        check(pals('wCinematicSavedPals') == start_targets, 'scene_begin: the palettes not kept')

        # a tint: halfway, exactly, the text box's palette (BG 7) aside, and on screen
        call('CinematicTint', K['TINT_GREEN'])
        t = rgb(*TINTS['TINT_GREEN'])
        want = [blend(x, t) if not 28 <= i < 32 else x for i, x in enumerate(start_targets)]
        got = pals('wBGPals1')
        check(got == want, f'scene_tint GREEN: {[hex(c) for c in got[:4]]} not {[hex(c) for c in want[:4]]}')
        check(pals('wBGPals2') == got, 'scene_tint: the screen did not reach the tint')
        # a second tint compounds
        call('CinematicTint', K['TINT_DARK'])
        want2 = [blend(x, 0) if not 28 <= i < 32 else x for i, x in enumerate(want)]
        check(pals('wBGPals1') == want2, 'scene_tint DARK after GREEN: not compounded')

        # a flash, and a pulse, each come back to the scene's starting palettes
        call('CinematicFlash', 2)
        check(pals('wBGPals1')[:28] == start_targets[:28], 'scene_flash: BG palettes not back')
        check(pals('wBGPals2')[:28] == start_targets[:28], 'scene_flash: the screen not back')
        call('CinematicPulse', K['TINT_PURPLE'])
        check(pals('wBGPals2')[:28] == start_targets[:28], 'scene_pulse: the screen not back')

        # the scene changes the music: scene_end restarts the map's
        call('CinematicTint', K['TINT_WHITE'])
        g.wr('wMusicIDLo', (g.rd('wMapMusic') + 1) & 0xff)
        call('CinematicEnd')
        check(not g.rd('wCinematicFlags'), 'scene_end: still marked active')
        check(pals('wBGPals2') == start_screen, 'scene_end: the screen palettes not as they were')
        check(pals('wBGPals1') == start_targets, 'scene_end: the palettes not as they were')
        check((g.rd('wMusicIDLo'), g.rd('wMusicIDHi')) == (g.rd('wMapMusic'), 0),
              "scene_end: the map's music not back")
        check(not randoms, f'{len(randoms)} random numbers drawn')

        # unchanged music isn't restarted; scene_end without a scene does nothing
        call('CinematicBegin')
        g.wr('wMusicIDLo', g.rd('wMapMusic'))
        g.wr('wMusicIDHi', 0)
        restarts = []
        hook = g.sym['RestartMapMusic']
        g.pb.hook_register(*hook, lambda _: restarts.append(1), None)
        call('CinematicEnd')
        call('CinematicEnd')
        g.pb.hook_deregister(*hook)
        check(not restarts, "scene_end restarted the map's music when it hadn't changed")
        del music

    # scene_end_keep_music: the palettes back, the scene's music left playing
    start_screen = pals('wBGPals2')
    call('CinematicBegin')
    call('CinematicTint', K['TINT_PURPLE'])
    other = (g.rd('wMapMusic') + 1) & 0xff
    g.wr('wMusicIDLo', other)
    restarts = []
    hook = g.sym['RestartMapMusic']
    g.pb.hook_register(*hook, lambda _: restarts.append(1), None)
    call('CinematicEndKeepMusic')
    g.pb.hook_deregister(*hook)
    check(not restarts and g.rd('wMusicIDLo') == other, 'scene_end_keep_music: the music was changed')
    check(pals('wBGPals2') == start_screen, 'scene_end_keep_music: the palettes not as they were')
    check(not g.rd('wCinematicFlags'), 'scene_end_keep_music: still marked active')

    # (and outside a scene, lightning still strikes)
    whites = []
    g.pb.hook_register(*g.sym['SetWhitePals'], lambda _: whites.append(1), None)
    g.wr('wWeatherFlags', g.rd('wWeatherFlags') & ~(1 << K['OW_WEATHER_LIGHTNING_DISABLED_F'])
         & ~(1 << K['OW_WEATHER_DO_FLY_F']))
    caller.call('Lightning')
    check(whites, 'lightning no longer strikes outside a scene')

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
