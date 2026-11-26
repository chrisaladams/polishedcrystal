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
- scene_shadow / scene_unshadow: only a scene can shadow; the player goes
  black on screen and nobody else does, one of the link room's people goes
  black and another with the same palette doesn't, a Pokémon sprite (its
  palette read as two nybbles) goes black too and gets its palette back, a tint and scene_restore keep the shadow, unshadowing
  one reveals only that one, and scene_end gives every shadow its colors back;
- scene_enter, run as a real script: someone comes on just past the screen's
  left edge (then the right), in line with the player, and walks up beside
  them; the player doesn't move;
- scene_title, run as a real script: the line centered on a blank card, white
  on black, for about two seconds; the script goes on past its pointer; the
  map and its palettes come back exactly; A skips it;
- scene_weather: only a scene changes the weather; rain with its palette in
  the weather slot; snow's palette kept through scene_restore (not the one
  kept from before the snow); an unknown weather ignored;
  NONE clears the sky; scene_end brings back the map's own weather;
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
                       'CALM_SCREEN_F', 'GROUP_POKECENTER_2F', 'MAP_POKECENTER_2F', *TINTS], None)
    g = Game(open(sys.argv[1], 'rb').read())
    g.boot()
    # Use a quiet room with several actors sharing a palette.
    g.warp(K['GROUP_POKECENTER_2F'], K['MAP_POKECENTER_2F'], 9, 3)
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

    # scene_shadow and scene_unshadow: one character black, the others as they were
    K.update(rgbasm_values(['OBJECT_PAL_INDEX', 'OBJECT_PALETTE', 'OBJECT_PAL_SHADOW', 'PLAYER',
                            'OBJECT_MAP_OBJECT_INDEX', 'OAM_PALETTE', 'SPRITE_POKEMON'], None))
    structs = [g.sym['wObjectStructs'][1] + i * K['OBJECT_LENGTH'] for i in range(K['NUM_OBJECT_STRUCTS'])]
    shown = [b for b in structs[1:] if g.m[1, b + K['OBJECT_SPRITE']]
             and not g.m[1, b + K['OBJECT_FLAGS1']] >> K['INVISIBLE_F'] & 1]
    player = structs[0]
    pal_of = lambda b: g.m[1, b + K['OBJECT_PAL_INDEX']]  # noqa: E731

    def shown_black(b):
        slot = g.m[1, b + K['OBJECT_PALETTE']] & K['OAM_PALETTE']
        return pals('wBGPals2')[(8 + slot) * 4 + 1:(8 + slot) * 4 + 4] == [0, 0, 0]

    # (the link room's three people share one palette: one shadow must not darken the others)
    sharing = [b for b in shown if pal_of(b) == pal_of(shown[0])] if shown else []
    check(len(sharing) >= 2, f'the test wants two people with one palette on screen, not {len(sharing)}')
    own = pal_of(player)
    call('CinematicShadow', K['PLAYER'])
    check(pal_of(player) == own, 'scene_shadow outside a scene changed the player')
    call('CinematicBegin')
    call('CinematicShadow', K['PLAYER'])
    g.tick(2)
    check(pal_of(player) == K['OBJECT_PAL_SHADOW'], 'scene_shadow: the player not marked')
    check(shown_black(player), 'scene_shadow: the player not black on screen')
    check(not any(shown_black(b) for b in shown), 'scene_shadow: someone else went black too')
    if len(sharing) >= 2:
        one, other = sharing[:2]
        own_one = pal_of(one)
        call('CinematicShadow', g.m[1, one + K['OBJECT_MAP_OBJECT_INDEX']])
        g.tick(2)
        check(shown_black(one), 'scene_shadow: a person not black')
        check(not shown_black(other), 'scene_shadow: a person with the same palette went black too')
        # a Pokémon sprite reads its palette as two nybbles: the shadow is black all the same
        sprite = g.m[1, other + K['OBJECT_SPRITE']]
        own_other = pal_of(other)
        g.m[1, other + K['OBJECT_SPRITE']] = K['SPRITE_POKEMON']
        g.m[1, other + K['OBJECT_PAL_INDEX']] = 0x94
        call('CinematicShadow', g.m[1, other + K['OBJECT_MAP_OBJECT_INDEX']])
        g.tick(2)
        check(shown_black(other), 'scene_shadow: a Pokémon sprite not black')
        call('CinematicUnshadow', g.m[1, other + K['OBJECT_MAP_OBJECT_INDEX']])
        check(pal_of(other) == 0x94, f'scene_unshadow: a Pokémon sprite\'s palette {pal_of(other):#x}, not $94')
        g.m[1, other + K['OBJECT_SPRITE']] = sprite
        g.m[1, other + K['OBJECT_PAL_INDEX']] = own_other
    call('CinematicShadow', K['PLAYER'])  # (twice: its own palette still kept)
    call('CinematicTint', K['TINT_PURPLE'])
    call('CinematicRestoreNow')
    g.tick(2)
    check(shown_black(player), 'scene_shadow: a tint and scene_restore undid the shadow')
    call('CinematicUnshadow', K['PLAYER'])
    g.tick(2)
    check(pal_of(player) == own, f'scene_unshadow: palette {pal_of(player):#x}, not {own:#x}')
    check(not shown_black(player), 'scene_unshadow: the player still black')
    if len(sharing) >= 2:
        check(shown_black(one), 'scene_unshadow of the player revealed someone else too')
    call('CinematicShadow', K['PLAYER'])
    call('CinematicEnd')
    g.tick(20)
    check(pal_of(player) == own, 'scene_end: the player\'s palette not back')
    check(not shown_black(player), 'scene_end: the player still black')
    if len(sharing) >= 2:
        check(pal_of(one) == own_one, 'scene_end: a person\'s palette not back')
        check(not shown_black(one), 'scene_end: a person still black')

    # scene_enter: someone comes on from past the screen's edge and walks up
    # beside the player (the room is 8 tiles tall: from the left and the right)
    K.update(rgbasm_values(['OBJECT_MAP_X', 'OBJECT_MAP_Y', 'LEFT', 'RIGHT', 'MAPOBJECT_OBJECT_STRUCT_ID',
                            'MAPOBJECT_LENGTH', 'UNASSOCIATED_MAPOBJECT'], None))
    enter_bank, enter_addr = g.sym['CinematicEnter']
    if shown:
        who = g.m[1, shown[0] + K['OBJECT_MAP_OBJECT_INDEX']]
        px, py = g.rd('wXCoord'), g.rd('wYCoord')

        def where():
            mo = g.sym['wMapObjects'][1] + who * K['MAPOBJECT_LENGTH']
            sid = g.m[1, mo + K['MAPOBJECT_OBJECT_STRUCT_ID']]
            if sid == K['UNASSOCIATED_MAPOBJECT']:
                return None
            b = structs[sid]
            return g.m[1, b + K['OBJECT_MAP_X']] - 4, g.m[1, b + K['OBJECT_MAP_Y']] - 4

        for side, start_x, end_x in (('LEFT', px - 5, px - 1), ('RIGHT', px + 6, px + 1)):
            script = [K['setval_command'], K[side] << 5 | who,
                      K['callasm_command'], enter_bank, enter_addr & 0xff, enter_addr >> 8, K['end_command']]
            for k, v in enumerate(script):
                g.m[1, buf + k] = v
            g.wr('wMapReentryScriptBank', 0)
            g.wr('wMapReentryScriptAddress', buf & 0xff)
            g.wr('wMapReentryScriptAddress', buf >> 8, 1)
            g.wr('wMapReentryScriptQueueFlag', 1)
            first = None
            for _ in range(200):
                g.tick(1)
                if g.rd('wScriptRunning') and where() is not None:
                    first = where()
                    break
            check(first == (start_x, py), f'scene_enter {side}: came on at {first}, not {(start_x, py)}')
            for _ in range(300):
                g.tick(2)
                if not g.rd('wScriptRunning'):
                    break
            g.tick(10)
            check(where() == (end_x, py), f'scene_enter {side}: ended at {where()}, not beside the player {(end_x, py)}')
            check((g.rd('wXCoord'), g.rd('wYCoord')) == (px, py), f'scene_enter {side}: the player moved')

    # scene_title, as a real script: callasm CinematicTitle, dw text, end
    # (the text after the script; the word after callasm is the script's own)
    title = 'THE POWER OF ONE'
    text = [0x7f if ch == ' ' else 0x80 + ord(ch) - ord('A') for ch in title] + [0x53]
    title_bank, title_addr = g.sym['CinematicTitle']
    text_at = buf + 7
    script = [K['callasm_command'], title_bank, title_addr & 0xff, title_addr >> 8,
              text_at & 0xff, text_at >> 8, K['end_command']] + text
    for k, v in enumerate(script):
        g.m[1, buf + k] = v
    tilemap = g.sym['wTilemap'][1]
    screen_before = [g.m[tilemap + k] for k in range(20 * 18)]
    pals_before = pals('wBGPals2')
    g.wr('wMapReentryScriptBank', 0)
    g.wr('wMapReentryScriptAddress', buf & 0xff)
    g.wr('wMapReentryScriptAddress', buf >> 8, 1)
    g.wr('wMapReentryScriptQueueFlag', 1)
    col = (20 - len(title)) // 2
    card = None
    for frame in range(400):
        g.tick(1)
        row = [g.m[tilemap + 8 * 20 + k] for k in range(20)]
        if row[col:col + len(title)] == text[:-1]:
            card = frame
            break
    check(card is not None, 'scene_title: the line never showed, centered on row 8')
    if card is not None:
        g.tick(20)
        bg = pals('wBGPals2')
        check(bg[0] == 0 and bg[3] == 0x7fff, f'scene_title: palette 0 shows {bg[0]:#x} ground, {bg[3]:#x} letters')
        check(all(g.m[tilemap + k] == 0x7f for k in range(20 * 18) if not 160 + col <= k < 160 + col + len(title)),
              'scene_title: something else on the card')
        held = 20
        while g.rd('wScriptRunning') and held < 400:
            g.tick(1)
            held += 1
        check(100 <= held - 20 <= 220, f'scene_title: shown {held} frames after appearing, not about two seconds')
    for _ in range(200):
        g.tick(1)
        if not g.rd('wScriptRunning'):
            break
    g.tick(40)
    check(not g.rd('wScriptRunning'), 'scene_title: the script did not go on to its end')
    check([g.m[tilemap + k] for k in range(20 * 18)] == screen_before, 'scene_title: the map not drawn back as it was')
    # (the map's palettes, and those of the people on screen: ExitAllMenus
    # reloads only the sprite palettes in use, and the text box palette fresh)
    used = sorted({8 + (g.m[1, b + K['OBJECT_PALETTE']] & K['OAM_PALETTE']) for b in [player] + shown})
    after = pals('wBGPals2')
    check(after[:7 * 4] == pals_before[:7 * 4], 'scene_title: the map\'s palettes not back as they were')
    check(all(after[s * 4:s * 4 + 4] == pals_before[s * 4:s * 4 + 4] for s in used),
          'scene_title: the sprites\' palettes not back as they were')
    # A skips it
    g.wr('wMapReentryScriptBank', 0)
    g.wr('wMapReentryScriptAddress', buf & 0xff)
    g.wr('wMapReentryScriptAddress', buf >> 8, 1)
    g.wr('wMapReentryScriptQueueFlag', 1)
    for _ in range(400):
        g.tick(1)
        if [g.m[tilemap + 8 * 20 + k] for k in range(20)][col:col + len(title)] == text[:-1]:
            break
    g.tick(20)
    g.pb.button('a')
    for waited in range(200):
        g.tick(1)
        if not g.rd('wScriptRunning'):
            break
    check(waited < 60, f'scene_title: A did not skip it ({waited} frames more)')
    g.tick(40)
    check(not g.rd('wScriptRunning'), 'scene_title: after skipping, a script still running')

    # scene_weather: the scene's weather until scene_end, the map's own after
    K.update(rgbasm_values(['OW_WEATHER_NONE', 'OW_WEATHER_RAIN', 'OW_WEATHER_SNOW', 'PAL_OW_WEATHER',
                            'PAL_OW_RAIN'], None))
    own_weather = g.rd('wCurWeather')
    call('CinematicWeather', K['OW_WEATHER_RAIN'])
    check(g.rd('wCurWeather') == own_weather, 'scene_weather outside a scene changed the weather')
    call('CinematicBegin')
    call('CinematicWeather', K['OW_WEATHER_RAIN'])
    g.tick(4)
    check(g.rd('wCurWeather') == K['OW_WEATHER_RAIN'], f'scene_weather: weather {g.rd("wCurWeather")}, not rain')
    check(g.m[1, g.sym['wLoadedObjPal0'][1] + K['PAL_OW_WEATHER']] == K['PAL_OW_RAIN'],
          'scene_weather: the rain palette not loaded in the weather slot')
    call('CinematicEnd')
    g.tick(120)
    # (a scene kept the palettes from before its weather: scene_restore must
    # put the weather's slot back as the weather is now, not as it was kept)
    slot = slice((8 + K['PAL_OW_WEATHER']) * 4, (8 + K['PAL_OW_WEATHER']) * 4 + 4)
    call('CinematicBegin')
    kept = pals('wBGPals2')[slot]
    call('CinematicWeather', K['OW_WEATHER_SNOW'])
    g.tick(4)
    snow_pal = [c & 0x7fff for c in pals('wBGPals2')[slot]]  # (bit 15 isn't a color)
    check(snow_pal != [c & 0x7fff for c in kept], 'the test wants the snow palette to differ from the one kept')
    call('CinematicRestoreNow')
    g.tick(4)
    check([c & 0x7fff for c in pals('wBGPals2')[slot]] == snow_pal, 'scene_weather: scene_restore put back a stale palette for the snow')
    call('CinematicWeather', 99)
    check(g.rd('wCurWeather') == K['OW_WEATHER_SNOW'], 'scene_weather: an unknown weather changed it')
    call('CinematicWeather', K['OW_WEATHER_NONE'])
    g.tick(4)
    check(g.rd('wCurWeather') == K['OW_WEATHER_NONE'], 'scene_weather NONE: the sky not cleared')
    call('CinematicWeather', K['OW_WEATHER_RAIN'])
    g.tick(4)
    check(g.rd('wCurWeather') == K['OW_WEATHER_RAIN'], 'scene_weather: the rain not back')
    call('CinematicEnd')
    g.tick(20)
    check(g.rd('wCurWeather') == own_weather, f'scene_end: weather {g.rd("wCurWeather")}, not the map\'s {own_weather}')
    check(not g.rd('wCinematicFlags'), 'scene_end: the scene flags not cleared')
    g.tick(120)  # (the rain clears)

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
