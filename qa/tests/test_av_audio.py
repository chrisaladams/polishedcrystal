"""Music sequencing and sound-effect tests, from the sound engine's own state (SameBoy).

music loops   every song either ends (a jingle) or loops with all four channels in step
sfx           a sound effect played over music must leave the music exactly where it would have
              been, and the music must still be audible afterwards
"""
import os

import numpy as np

from qa.av import audio, music
from qa.framework import qa_test

PROVENANCE = 'boot to the title screen; songs and effects are started by calling the ROM routines (injected), then observed'


def _quiet_room_game(ctx):
    """Continue from the smoke save and stand in a static indoor map. NOT the title screen: its attract
    timer restarts the title sequence (and music) every ~126 s and would override the song under test."""
    from qa.gb import fixtures as F
    from qa.gb.consts import map_ids
    from qa.tests.test_map_smoke import build, pick_tile
    g = ctx.boot('smoke_base', build)
    gr, nr = map_ids('VIOLET_POKECENTER_1F')
    F.teleport(g, gr, nr, 2, 2, settle=60)
    t = pick_tile(g) or (2, 2)
    F.teleport(g, gr, nr, t[0], t[1], settle=60)
    g.tick(120)
    return g


def _shard(items, i, n):
    items = sorted(items)
    lim = int(os.environ.get('QA_AUDIO_LIMIT', '0')) or None
    sel = items[i::n]
    return sel[:lim] if lim else sel


def _make_music(i, n):
    @qa_test(suites=('av', 'full'), covers=('av.music_loops',), backends=('sameboy',), models=('CGB-E',), provenance=PROVENANCE,
             timeout=7200, name=f'test_av_audio.music_loops_{i}of{n}')
    def shard(ctx):
        g = _quiet_room_game(ctx)
        songs = _shard(music.song_ids().items(), i, n)
        kinds = {}
        for name, sid in songs:
            r = music.validate_song(g, sid, max_frames=int(os.environ.get('QA_MUSIC_MAX_FRAMES', '10800')))
            kinds.setdefault(r['kind'], []).append(name)
            if r['kind'] == 'desync':
                ctx.expect(False, f'{name}: channels loop but not together: {r.get("channel_frames")}')
                ctx.av.append(dict(kind='MUSIC_DESYNC', detail=f'{name}: channels repeat with different periods', where=name,
                                   sig=f'md-{name}', count=1, artifacts={}, context=r, frame=0))
            elif r['kind'] == 'unbounded':
                ctx.av.append(dict(kind='MUSIC_NO_LOOP', detail=f'{name}: neither ended nor looped in {r["frames"] / 60:.0f} s',
                                   where=name, sig=f'mn-{name}', count=1, artifacts={}, context=r, frame=0))
        ctx.note(f'{len(songs)} songs: ' + ', '.join(f'{k} {len(v)}' for k, v in kinds.items()))
        if kinds.get('unbounded'):
            ctx.note('undecided within the trace (longer than the limit or never loops): ' + ', '.join(kinds['unbounded'][:12]))
            ctx.uncover('av.music_loops', f'{len(kinds["unbounded"])} songs not decided')
    return shard


def _make_sfx(i, n):
    @qa_test(suites=('av', 'full'), covers=('av.sfx', 'av.silence'), backends=('sameboy',), models=('CGB-E',), provenance=PROVENANCE,
             timeout=7200, name=f'test_av_audio.sfx_keeps_music_{i}of{n}')
    def shard(ctx):
        g = _quiet_room_game(ctx)
        ids = music.song_ids()
        song = ids.get('MUSIC_ROUTE_29') or next(iter(ids.values()))
        music.play(g, song)
        g.tick(240)
        g.enable_av(40, guard=False)           # PCM capture only: the python call() hook stays usable
        g.save_point()
        base = g.frame
        controls = {}
        for k in range(1, 701):                      # engine state at every frame since the snapshot
            g.tick(1)
            controls[k] = music.engine_state(g)
        control = controls[600]
        ctl = audio.stats(audio.mono(g.audio_pcm(reset=True)[-48000:]))
        ctx.note('control: music audible, rms %.3f over the last second' % ctl['rms'])
        ctx.expect(ctl['rms'] > 0.01, 'the control run is silent: the test cannot tell anything')
        changed, quiet, stopped = [], [], []
        sfx = _shard(music.sfx_ids().items(), i, n)
        for name, sid in sfx:
            g.restore_point()
            base = g.frame
            g.audio_pcm(reset=True)
            g.call('PlaySFX', de=sid)
            # compare at the same number of frames since the snapshot: the call itself takes a few
            k = max(1, g.frame - base)
            g.tick(600 - k if k < 600 else 0)
            st = music.engine_state(g)
            control = controls[min(600, max(1, g.frame - base))]
            if st[0] != control[0]:
                stopped.append(name)
            elif st != control:
                diff = [ch + 1 for ch in range(4) if st[1][ch][:2] != control[1][ch][:2]]
                changed.append((name, diff))
            pcm = audio.mono(g.audio_pcm(reset=True)[-48000:])
            if audio.stats(pcm)['rms'] < 0.01 and name not in stopped:
                quiet.append(name)
        ctx.note(f'{len(sfx)} effects: music engine state differed after {len(changed)}, stopped by {len(stopped)}, quiet afterwards {len(quiet)}')
        if stopped:
            ctx.note('effects that stop the music (intended for fanfares?): ' + ', '.join(stopped[:12]))
        for name, diff in changed[:10]:
            ctx.expect(False, f'{name}: music channels {diff} are not where they would have been')
            ctx.av.append(dict(kind='SFX_BREAKS_MUSIC', detail=f'{name} leaves music channels {diff} out of place', where=name,
                               sig=f'sfx-{name}', count=1, artifacts={}, context={}, frame=0))
        for name in quiet[:10]:
            ctx.expect(False, f'{name}: the music is silent after the effect')
            ctx.av.append(dict(kind='SILENCE', detail=f'music silent after {name}', where=name, sig=f'sq-{name}', count=1, artifacts={}, context={}, frame=0))
    return shard


for _i in range(4):
    _make_sfx(_i, 4)
for _i in range(4):
    _make_music(_i, 4)


@qa_test(suites=('av', 'hardware', 'full'), covers=('av.audio_cross', 'av.models'), backends=('sameboy',), models=('CGB-0', 'CGB-E', 'AGB'),
         provenance='Continue from one save on both emulators (input); the warp into each town is injected; the music is the '
                    'game\'s own map music', timeout=1800)
def audio_cross_emulator(ctx):
    """Map music recorded from PyBoy and from this SameBoy model, from the same save and the same warp,
    compared after normalising level and aligning in time (loudness-envelope cross-correlation, then
    band-energy fingerprints). Small differences are expected between emulators; a large one is
    reported (class 'emulator'), never silently passed."""
    from qa.gb import fixtures as F, saves
    from qa.gb.consts import map_ids
    from qa.gb.emu import Game
    from qa.tests.test_map_smoke import build, pick_tile
    path, meta = ctx.fixture('smoke_base', build)
    towns = ['NEW_BARK_TOWN', 'VIOLET_CITY', 'GOLDENROD_CITY']
    secs = 12

    def record(g, backend_audio):
        saves.boot_continue(g, meta['where'])
        out = {}
        for t in towns:
            gr, nr = map_ids(t)
            F.teleport(g, gr, nr, 2, 2, settle=30)
            tile = pick_tile(g) or (2, 2)
            F.teleport(g, gr, nr, tile[0], tile[1], settle=30)
            if backend_audio == 'pyboy':
                pcm = audio.capture(g, 60 * secs)
            else:
                g.audio_pcm(reset=True)
                g.tick(60 * secs)
                pcm = g.audio_pcm(reset=True)
            out[t] = audio.mono(pcm)
        return out
    p = Game(rom=ctx.rom, sav=path, workdir=ctx.out, audio=True)
    rec_p = record(p, 'pyboy')
    p.close()
    s = ctx.game(sav=path)
    s.enable_av(120, guard=False)
    rec_s = record(s, 'sameboy')
    for t in towns:
        a, b = rec_p[t], rec_s[t]
        for tag, x in (('pyboy', a), (f'sameboy_{ctx.model}', b)):
            audio.write_wav(os.path.join(ctx.out, f'{t}_{tag}.wav'), (x * 32767).astype(np.int16)[:, None].repeat(2, 1))
            ctx.artifacts.append(os.path.join(ctx.out, f'{t}_{tag}.wav'))
        c = audio.compare(a, b)
        sa, sb = audio.stats(a), audio.stats(b)
        ctx.note(f'{t}: similarity {c["similarity"]:.2f}, lag {c["lag_s"]:.2f}s, level diff {c["level_db"]:.1f} dB; '
                 f'rms pyboy {sa["rms"]:.3f} / sameboy {sb["rms"]:.3f}')
        ctx.expect(sb['rms'] > 0.01, f'{t}: SameBoy {ctx.model} produced no music')
        ctx.expect(sa['rms'] > 0.005, f'{t}: PyBoy produced no music')
        if c['similarity'] < 0.5:
            ctx.av.append(dict(kind='AUDIO_GLITCH', detail=f'{t}: PyBoy and SameBoy {ctx.model} music differ (similarity {c["similarity"]:.2f})',
                               where=t, sig=f'ace-{t}', count=1, artifacts={'wav': os.path.join(ctx.out, f'{t}_pyboy.wav')}, context=c, frame=0))
