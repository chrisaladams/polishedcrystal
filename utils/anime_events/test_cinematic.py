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
- nothing draws a random number;
- the lifecycle guards: a scene_begin inside a scene keeps the first one's
  palettes; a script ending with a scene still on ends it (Script_endall,
  Script_end); a new map drops it (RunMapSetupScript);
- scene_pan / scene_pan_back, run as a real script: while panned the player
  is hidden, the given steps away (the camera follows them), the follower put
  away; afterwards the player is back on the same tile, visible, the follower
  under them again;
- the Options row "Flash & Shake": left/right turns it Off and On (only
  CALM_SCREEN_F changes), shown as it is. (What Off does to a real scene is
  in test_movie_events.py, the clone scene.)

Usage (from the repository root, after make):
  python3 utils/anime_events/test_cinematic.py SAVE.sav
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from test_friend_records import Caller, Game, rgbasm_values  # noqa: E402

TINTS = {'TINT_DARK': (0, 0, 0), 'TINT_GREEN': (4, 31, 6), 'TINT_PURPLE': (20, 2, 31), 'TINT_WHITE': (31, 31, 31)}


def rgb(r, g, b):
    return r | g << 5 | b << 10


def blend(x, t):
    return (x & t) + (((x ^ t) & 0x7bde) >> 1)


def main():
    K = rgbasm_values(['OW_WEATHER_LIGHTNING_DISABLED_F', 'OW_WEATHER_DO_FLY_F', 'CINEMATIC_ACTIVE_F',
                       'CALM_SCREEN_F', *TINTS], None)
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

    # a scene_begin inside a scene keeps the first one's palettes
    start = pals('wBGPals1')
    call('CinematicBegin')
    call('CinematicTint', K['TINT_DARK'])
    call('CinematicBegin')
    check(pals('wCinematicSavedPals') == start, 'nested scene_begin: kept the tinted palettes')
    call('CinematicEnd')
    check(pals('wBGPals1') == start, 'nested scene_begin: not back to the first palettes')

    # a script that ends with a scene still on ends it
    call('CinematicBegin')
    call('CinematicTint', K['TINT_PURPLE'])
    call('Script_endall')
    check(not g.rd('wCinematicFlags'), 'Script_endall: the scene still on')
    check(pals('wBGPals1') == start, 'Script_endall: the palettes not back')

    # a new map drops a scene still on
    call('CinematicBegin')
    call('CinematicTint', K['TINT_GREEN'])
    g.warp(g.rd('wMapGroup'), g.rd('wMapNumber'), g.rd('wXCoord'), g.rd('wYCoord'))
    check(not g.rd('wCinematicFlags'), 'a new map: the scene still on')

    # (and outside a scene, lightning still strikes)
    whites = []
    g.pb.hook_register(*g.sym['SetWhitePals'], lambda _: whites.append(1), None)
    g.wr('wWeatherFlags', g.rd('wWeatherFlags') & ~(1 << K['OW_WEATHER_LIGHTNING_DISABLED_F'])
         & ~(1 << K['OW_WEATHER_DO_FLY_F']))
    caller.call('Lightning')
    check(whites, 'lightning no longer strikes outside a scene')

    # scene_pan and scene_pan_back, as a script in RAM: pan 4 down, wait, back
    # (through the room's furniture and people: the view isn't stopped)
    K.update(rgbasm_values(['setval_command', 'callasm_command', 'pause_command', 'end_command',
                            'DOWN', 'NOCLIP_TILES_F', 'NOCLIP_OBJS_F', 'OBJECT_FLAGS1', 'OBJECT_SPRITE', 'NUM_OBJECT_STRUCTS',
                            'OBJECT_LENGTH', 'SPRITE_FOLLOWER_MON', 'INVISIBLE_F'], None))
    g.tick(120)
    pan_bank, pan_addr = g.sym['CinematicPan']
    end_bank, end_addr = g.sym['CinematicPanEnd']
    steps = 4
    script = [K['setval_command'], K['DOWN'] << 4 | steps, K['callasm_command'], pan_bank, pan_addr & 0xff, pan_addr >> 8,
              K['pause_command'], 60,
              K['setval_command'], (K['DOWN'] ^ 1) << 4 | steps | 0x80,
              K['callasm_command'], pan_bank, pan_addr & 0xff, pan_addr >> 8,
              K['callasm_command'], end_bank, end_addr & 0xff, end_addr >> 8, K['end_command']]
    buf = g.sym['wStringBuffer5'][1]
    for k, v in enumerate(script):
        g.m[1, buf + k] = v

    def follower_shown():
        for i in range(K['NUM_OBJECT_STRUCTS']):
            b = g.sym['wObjectStructs'][1] + i * K['OBJECT_LENGTH']
            if g.m[1, b + K['OBJECT_SPRITE']] == K['SPRITE_FOLLOWER_MON']:
                return True
        return False

    def player_hidden():
        return bool(g.m[1, g.sym['wPlayerStruct'][1] + K['OBJECT_FLAGS1']] >> K['INVISIBLE_F'] & 1)

    start = (g.rd('wXCoord'), g.rd('wYCoord'))
    had_follower = follower_shown()
    # (queued as the game queues a script: RunMemScript starts it)
    g.wr('wMapReentryScriptBank', 0)
    g.wr('wMapReentryScriptAddress', buf & 0xff)
    g.wr('wMapReentryScriptAddress', buf >> 8, 1)
    g.wr('wMapReentryScriptQueueFlag', 1)
    panned = None
    for _ in range(400):
        g.tick(2)
        if (g.rd('wXCoord'), g.rd('wYCoord')) == (start[0], start[1] + steps):
            panned = (player_hidden(), follower_shown())
            break
    check(panned is not None, f'scene_pan: the camera did not get {steps} steps down')
    if panned:
        check(panned[0], 'scene_pan: the player was not hidden')
        check(not panned[1], 'scene_pan: the follower was still out')
    for _ in range(300):
        g.tick(2)
        if not g.rd('wScriptRunning'):
            break
    g.tick(30)
    check((g.rd('wXCoord'), g.rd('wYCoord')) == start,
          f'scene_pan_back: the player at {(g.rd("wXCoord"), g.rd("wYCoord"))}, not {start}')
    check(not player_hidden(), 'scene_pan_back: the player still hidden')
    flags = g.m[1, g.sym['wPlayerStruct'][1] + K['OBJECT_FLAGS1']]
    check(not flags & (1 << K['NOCLIP_TILES_F'] | 1 << K['NOCLIP_OBJS_F']), 'scene_pan_back: the player left able to walk through walls')
    check(follower_shown() == had_follower, f'scene_pan_back: follower {follower_shown()}, before {had_follower}')

    # the Options row
    def plain(label):
        bank, addr = g.sym[label]
        return bytes(g.m[bank, addr + i] for i in range(20)).split(b'\x53', 1)[0]
    g.tick(60)
    g.highlight_start_option('OptionString')
    g.press('a', 90)
    name = plain('OptionNames.FlashShake')
    order = re.findall(r'dw \.(\w+)', open(os.path.join(ROOT, 'data', 'options', 'option_names.asm')).read())
    item = order.index('FlashShake') + 1  # (wMenuSelection counts from 1)
    for _ in range(20):
        if g.rd('wMenuSelection') == item:
            break
        g.press('down', 12)
    screen = bytes(g.rd('wTilemap', i) for i in range(20 * 18))
    at = screen.find(name)
    if g.rd('wMenuSelection') != item or at < 0:
        fails.append('Options: no "Flash & Shake" row reached')
    else:
        before = g.rd('wOptions3')
        for press, calm, shown in (('right', True, 'OffString'), ('left', False, 'OnString')):
            g.press(press, 20)
            value_row = bytes(g.rd('wTilemap', (at // 20 + 1) * 20 + i) for i in range(20))  # (under the name)
            o = g.rd('wOptions3')
            check(bool(o & 1 << K['CALM_SCREEN_F']) == calm and (o ^ before) & ~(1 << K['CALM_SCREEN_F']) == 0,
                  f'Options {press}: wOptions3 {before:08b} -> {o:08b}')
            check(plain(shown) in value_row, f'Options {press}: the value shows {value_row}')
    g.press('b', 60)

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
