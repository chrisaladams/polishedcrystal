"""Differential comparison of two builds of the game: what changed on screen and in the audio.

This is not a reference approval: it compares a build under test with another build of the same
source tree (a baseline someone chose), and reports every difference. It finds a graphical or audio
change wherever it is, with no knowledge of what changed; a person decides whether a difference is
intended. Used to review a change set and to validate the other detectors.

    python3 -m qa.av.diffbuild frames BASE.gbc NEW.gbc [--every 4] [--out DIR]
    python3 -m qa.av.diffbuild audio  BASE.gbc NEW.gbc [--songs 40] [--frames 600] [--out DIR]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def _frames_for(rom, every, offset, workdir):
    import numpy as np
    from qa.gb import fixtures as F, mapdata, saves
    from qa.gb.consts import map_ids
    from qa.gb.emu import Game
    from qa.tests.test_map_smoke import build, pick_tile
    p = saves.fixture('smoke_base', build, rom=rom)
    meta = saves.fixture_meta(p)
    g = Game(rom=rom, sav=p, workdir=workdir)
    saves.boot_continue(g, meta['where'])
    g.save_point()
    out = {}
    for const in sorted(mapdata.attributes())[offset::every]:
        g.restore_point()
        try:
            sg, sn = map_ids(const)
            F.teleport(g, sg, sn, 2, 2, settle=60)
            t = pick_tile(g)
            if t is None:
                continue
            F.teleport(g, sg, sn, t[0], t[1], settle=90)
            g.tick(40)
            out[const] = g.frame_rgb()
        except Exception as e:           # a map that cannot be entered in this build is itself a difference
            out[const] = 'error: %s' % e
    g.close()
    return out


def compare_frames(base, new, every=4, offset=0, out=None, tolerance=0.002):
    import numpy as np
    wa = _frames_for(base, every, offset, out or '/tmp')
    wb = _frames_for(new, every, offset, out or '/tmp')
    diffs = []
    for const in wa:
        a, b = wa[const], wb.get(const)
        if isinstance(a, str) or isinstance(b, str) or b is None:
            if a != b:
                diffs.append(dict(map=const, kind='enter', detail='%s vs %s' % (a if isinstance(a, str) else 'ok', b if isinstance(b, str) else 'ok')))
            continue
        d = (np.abs(a.astype(int) - b.astype(int)).sum(axis=2) > 24)
        frac = float(d.mean())
        if frac > tolerance:
            diffs.append(dict(map=const, kind='pixels', fraction=round(frac, 4)))
            if out:
                from PIL import Image
                os.makedirs(out, exist_ok=True)
                strip = np.concatenate([a, b, np.where(d[:, :, None], 255, a // 3).astype('uint8')], axis=1)
                Image.fromarray(strip).save(os.path.join(out, 'diff_%s.png' % const))
    return dict(maps=len(wa), differing=len(diffs), diffs=diffs)


def _song_pcm(rom, ids, frames):
    import numpy as np
    from qa.av import music
    from qa.gb import saves
    from qa.gb import fixtures as F
    from qa.gb.consts import map_ids
    from qa.gb.sameboy import SBGame
    from qa.tests.test_map_smoke import build, pick_tile
    p = saves.fixture('smoke_base', build, rom=rom)
    g = SBGame(rom=rom, sav=p, workdir='/tmp', model='CGB-E', seed=1)
    saves.boot_continue(g, saves.fixture_meta(p)['where'])
    gr, nr = map_ids('VIOLET_POKECENTER_1F')
    F.teleport(g, gr, nr, 2, 2, settle=60)
    t = pick_tile(g) or (2, 2)
    F.teleport(g, gr, nr, t[0], t[1], settle=60)
    g.tick(120)
    g.enable_av(40, guard=False)
    out = {}
    for name, sid in ids:
        music.play(g, sid)
        g.tick(30)
        g.audio_pcm(reset=True)
        g.tick(frames)
        out[name] = np.array(g.audio_pcm(reset=True), dtype=np.int16)
    g.close()
    return out


def compare_audio(base, new, songs=40, frames=600, out=None):
    import numpy as np
    from qa.av import music
    ids = sorted(music.song_ids().items())
    step = max(1, len(ids) // songs)
    ids = ids[::step][:songs]
    a, b = _song_pcm(base, ids, frames), _song_pcm(new, ids, frames)
    diffs = []
    for name, _ in ids:
        x, y = a[name], b[name]
        n = min(len(x), len(y))
        if n == 0:
            continue
        if len(x) != len(y) or not np.array_equal(x[:n], y[:n]):
            xm, ym = x[:n].astype(float).mean(axis=1) if x.ndim > 1 else x[:n].astype(float), y[:n].astype(float).mean(axis=1) if y.ndim > 1 else y[:n].astype(float)
            first = int(np.argmax(np.abs(xm - ym) > 64)) if np.any(np.abs(xm - ym) > 64) else None
            rms = lambda v: float(np.sqrt((v ** 2).mean())) if len(v) else 0.0
            diffs.append(dict(song=name, first_diff_s=None if first is None else round(first / 48000, 3), rms_base=round(rms(xm)), rms_new=round(rms(ym)),
                              rms_diff=round(rms(xm - ym))))
    return dict(songs=len(ids), differing=len(diffs), diffs=diffs)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('what', choices=['frames', 'audio'])
    ap.add_argument('base')
    ap.add_argument('new')
    ap.add_argument('--every', type=int, default=4)
    ap.add_argument('--offset', type=int, default=0)
    ap.add_argument('--songs', type=int, default=40)
    ap.add_argument('--frames', type=int, default=600)
    ap.add_argument('--out', default=None)
    a = ap.parse_args(argv)
    r = compare_frames(a.base, a.new, a.every, a.offset, a.out) if a.what == 'frames' else compare_audio(a.base, a.new, a.songs, a.frames, a.out)
    print(json.dumps(r, indent=1))
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        json.dump(r, open(os.path.join(a.out, a.what + '.json'), 'w'), indent=1)
    return 1 if r['differing'] else 0


if __name__ == '__main__':
    sys.exit(main())
