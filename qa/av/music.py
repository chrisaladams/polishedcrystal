"""Music engine validation from the engine's own state (no PCM needed).

The sound engine keeps, for each of its four channels, a script pointer, a loop counter
and a note duration in WRAM. A song that loops brings every channel back to a previous
(pointer, duration) combination at the same moment; a jingle ends with every channel off.
From that we can check, for every song, that it either ends cleanly or loops with all
channels in step, and that a sound effect leaves the music exactly where it would have been.
"""
from qa.gb.consts import C, values

CHANNELS = (1, 2, 3, 4)


def song_ids():
    """{name: id} of every MUSIC_ constant (from constants/music_constants.asm)."""
    import os
    import re
    from qa.gb.emu import ROOT
    names = []
    for line in open(os.path.join(ROOT, 'constants', 'music_constants.asm')):
        m = re.match(r'\s*const\s+(MUSIC_\w+)', line)
        if m:
            names.append(m.group(1))
    v = values(names)
    return {n: v[n] for n in names if n in v and n != 'MUSIC_NONE'}


def sfx_ids():
    import os
    import re
    from qa.gb.emu import ROOT
    names = []
    for line in open(os.path.join(ROOT, 'constants', 'sfx_constants.asm')):
        m = re.match(r'\s*const\s+(SFX_\w+)', line)
        if m:
            names.append(m.group(1))
    v = values(names)
    return {n: v[n] for n in names if n in v}


def engine_state(g):
    """One tuple describing the music engine: (playing, [(pointer, duration, loop) per channel])."""
    st = []
    for ch in CHANNELS:
        p = f'wChannel{ch}'
        st.append((g.rd(p + 'MusicAddress') | g.rd(p + 'MusicAddress', 1) << 8,
                   g.rd(p + 'NoteDuration'),
                   g.rd(p + 'LoopCount')))
    return (g.rd('wMusicPlaying'), tuple(st))


def play(g, song):
    """Start `song` from silence and check the engine actually loaded it."""
    g.call('PlayMusic', de=0)           # stop whatever is playing (MUSIC_NONE)
    g.tick(12)
    g.call('PlayMusic', de=song)
    g.tick(2)
    loaded = g.rd('wChannel1MusicID') | g.rd('wChannel1MusicID', 1) << 8
    if loaded != song:
        raise RuntimeError(f'asked for song {song}, the engine loaded {loaded}')


def trace(g, frames):
    """engine_state per frame for `frames` frames."""
    out = []
    for _ in range(frames):
        g.tick(1, False)
        out.append(engine_state(g))
    return out


def _events(states, ch=None):
    """Compress a per-frame trace to [(pointers, frames_held)]: one entry per change of any
    (or one given) channel's script pointer. A held note is one event however long it lasts."""
    ev, last, held = [], None, 0
    for s in states:
        ptrs = tuple(c[0] for c in s[1]) if ch is None else (s[1][ch][0],)
        if ptrs != last:
            if last is not None:
                ev.append((last, held))
            last, held = ptrs, 1
        else:
            held += 1
    return ev


def _period(ev, min_events=8, min_cycles=2, tolerance=0.02):
    """Smallest K events such that the last min_cycles*K events repeat with period K, or None.
    The pointer sequence must match exactly; the time each cycle takes may differ by
    `tolerance` (the engine's tempo accumulator makes note lengths wobble by a frame)."""
    n = len(ev)
    for k in range(min_events, n // min_cycles + 1):
        tail = ev[n - min_cycles * k:]
        if all(tail[i][0] == tail[i + k][0] for i in range(len(tail) - k)):
            t1 = sum(h for _, h in tail[:k])
            t2 = sum(h for _, h in tail[k:2 * k])
            if abs(t1 - t2) <= max(2, tolerance * t1):
                return k
    return None


def analyse(states, min_cycles=2):
    """Classify a recorded engine-state trace.

    Returns dict(kind, period_frames, ...):
      'ended'     the engine stopped (wMusicPlaying 0) and stayed stopped
      'loops'     the whole engine (all channels together) repeats exactly: same pointers, same
                  timing, for at least min_cycles periods
      'desync'    individual channels repeat, but not as one
      'unbounded' neither ended nor repeated within the trace (the trace may be too short)
    """
    n = len(states)
    if n > 30 and not any(s[0] for s in states[-30:]):
        return dict(kind='ended', period_frames=None, frames=n)
    ev = _events(states)
    k = _period(ev, min_cycles=min_cycles)
    if k:
        return dict(kind='loops', period_frames=sum(h for _, h in ev[len(ev) - k:]), frames=n, events=k)
    # each channel on its own: its loop length in FRAMES (event counts differ between channels)
    frames_per = []
    for ch in range(4):
        evc = _events(states, ch)
        k = _period(evc)
        frames_per.append(sum(h for _, h in evc[len(evc) - k:]) if k else None)
    live = [f for f in frames_per if f]
    if len(live) == 4:
        lo, hi = min(live), max(live)
        ratio = hi / lo
        compatible = ratio < 1.02 or all(abs(round(f / lo) * lo - f) <= 0.02 * f for f in live)
        if not compatible:
            return dict(kind='desync', period_frames=None, frames=n, channel_frames=frames_per)
        return dict(kind='loops', period_frames=hi, frames=n, channel_frames=frames_per,
                    note='channels loop individually with compatible lengths')
    return dict(kind='unbounded', period_frames=None, frames=n, channel_frames=frames_per)


def validate_song(g, song, chunk=1800, max_frames=21600):
    """Play `song` from a booted game and trace the engine until its behaviour is decided.

    Returns the analyse() dict plus 'frames' used. A loop is only accepted once it has been
    seen twice in a row (same period), so a repeated verse is not mistaken for the loop."""
    play(g, song)
    states = []
    confirmed = None
    while len(states) < max_frames:
        states += trace(g, chunk)
        r = analyse(states)
        if r['kind'] == 'ended':
            return r
        if r['kind'] == 'loops':
            if confirmed and abs(confirmed['period_frames'] - r['period_frames']) <= max(2, 0.02 * r['period_frames']):
                return r
            confirmed = r
        elif r['kind'] == 'desync':
            if confirmed is not None:
                confirmed = None
        if r['kind'] == 'desync' and len(states) >= max_frames // 2:
            return r
    r = analyse(states)
    r['note'] = 'no loop or end within %d frames (%.0f s)' % (len(states), len(states) / 60)
    return r
