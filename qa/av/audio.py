"""Audio capture and analysis (PCM from PyBoy or SameBoy, 48 kHz).

Everything here produces *suspicions with numbers*, not verdicts: a loud click can be the
game's design, silence can be a scene with no music. Classification lives in review.py."""
import numpy as np

RATE = 48000


def mono(pcm):
    x = np.asarray(pcm, dtype=np.float32)
    if x.ndim == 2:
        x = x.mean(axis=1)
    return x / 32768.0


def capture(g, frames):
    """Run `frames` frames and return the PCM heard (int16, (n, 2)) on either backend."""
    if hasattr(g, 'audio_pcm'):
        g.audio_pcm(reset=True)
        g.tick(frames)
        return g.audio_pcm(reset=True)
    if not getattr(g, 'audio', False):
        raise RuntimeError('create the PyBoy Game with audio=True to capture audio')
    chunks = []
    for _ in range(frames):
        g.tick(1, False)
        chunks.append(g.frame_pcm())
    return np.concatenate(chunks) if chunks else np.zeros((0, 2), np.int16)


def write_wav(path, pcm, rate=RATE):
    import wave
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(np.asarray(pcm, dtype=np.int16).tobytes())
    return path


def rms_series(x, win=0.05):
    n = int(RATE * win)
    if len(x) < n:
        return np.array([float(np.sqrt((x ** 2).mean())) if len(x) else 0.0])
    k = len(x) // n
    return np.sqrt((x[:k * n].reshape(k, n) ** 2).mean(axis=1))


def silence_runs(x, thresh=0.003, min_seconds=1.0, win=0.05):
    """[(start_s, length_s)] of stretches whose RMS stays below thresh."""
    r = rms_series(x, win)
    quiet = r < thresh
    out, i = [], 0
    while i < len(quiet):
        if quiet[i]:
            j = i
            while j < len(quiet) and quiet[j]:
                j += 1
            if (j - i) * win >= min_seconds:
                out.append((i * win, (j - i) * win))
            i = j
        else:
            i += 1
    return out


def stats(x):
    """Level, DC offset, clipping and step statistics of a mono float signal."""
    if len(x) == 0:
        return dict(rms=0.0, peak=0.0, dc=0.0, clip=0, big_steps=0)
    d = np.abs(np.diff(x))
    return dict(rms=float(np.sqrt((x ** 2).mean())), peak=float(np.abs(x).max()), dc=float(x.mean()),
                clip=int((np.abs(x) > 0.999).sum()), big_steps=int((d > 0.5).sum()))


def spectral_track(x, hop=0.1):
    """Dominant frequency (Hz) and band energies per hop: [(t, peak_hz, rms)]."""
    n = int(RATE * hop)
    out = []
    win = np.hanning(n)
    for i in range(0, len(x) - n, n):
        seg = x[i:i + n] * win
        mag = np.abs(np.fft.rfft(seg))
        f = np.fft.rfftfreq(n, 1 / RATE)
        k = int(np.argmax(mag[1:])) + 1
        out.append((i / RATE, float(f[k]), float(np.sqrt((x[i:i + n] ** 2).mean()))))
    return out


def frequency_anomalies(x, hop=0.1, max_hz=9000, min_rms=0.01):
    """Windows that are loud yet dominated by a frequency above max_hz (whine / aliasing), and
    isolated one-window jumps of more than 3 octaves between neighbours at similar level."""
    tr = spectral_track(x, hop)
    out = []
    for i, (t, hz, r) in enumerate(tr):
        if r > min_rms and hz > max_hz:
            out.append(('high-frequency whine', t, hz))
        if 0 < i < len(tr) - 1 and r > min_rms:
            a, b, c = tr[i - 1][1], hz, tr[i + 1][1]
            if a > 0 and c > 0 and b > 0 and abs(np.log2(b / a)) > 3 and abs(np.log2(b / c)) > 3 and abs(np.log2(a / c)) < 1:
                out.append(('isolated pitch glitch', t, hz))
    return out


BANDS = np.geomspace(60, 12000, 25)


def fingerprint(x, hop=0.1):
    """Per-hop band energies in dB (24 bands), minus the clip's mean: level-independent."""
    n = int(RATE * hop)
    rows = []
    win = np.hanning(n)
    f = np.fft.rfftfreq(n, 1 / RATE)
    for i in range(0, len(x) - n, n):
        mag = np.abs(np.fft.rfft(x[i:i + n] * win)) ** 2
        rows.append([10 * np.log10(mag[(f >= lo) & (f < hi)].sum() + 1e-9) for lo, hi in zip(BANDS[:-1], BANDS[1:])])
    fp = np.array(rows, dtype=np.float32)
    return fp - fp.mean() if len(fp) else fp


def compare(a, b, max_lag_s=1.0):
    """Compare two mono clips after normalisation and alignment.

    Aligns by cross-correlating the loudness envelopes (emulators start a few frames apart),
    then reports the correlation of the band-energy fingerprints and the level ratio.
    Returns dict(similarity 0..1, lag_s, level_ratio_db)."""
    ra, rb = rms_series(a, 0.02), rms_series(b, 0.02)
    m = min(len(ra), len(rb))
    if m < 20:
        return dict(similarity=0.0, lag_s=0.0, level_db=0.0, note='too short')
    ra, rb = ra[:m] - ra[:m].mean(), rb[:m] - rb[:m].mean()
    lags = range(-int(max_lag_s / 0.02), int(max_lag_s / 0.02) + 1)
    best, best_lag = -2, 0
    for lag in lags:
        if lag >= 0:
            x, y = ra[lag:], rb[:m - lag]
        else:
            x, y = ra[:m + lag], rb[-lag:]
        if len(x) < 10 or x.std() == 0 or y.std() == 0:
            continue
        c = float(np.corrcoef(x, y)[0, 1])
        if c > best:
            best, best_lag = c, lag
    shift = int(best_lag * 0.02 * RATE)
    a2, b2 = (a[shift:], b) if shift >= 0 else (a, b[-shift:])
    n = min(len(a2), len(b2))
    fa, fb = fingerprint(a2[:n]), fingerprint(b2[:n])
    k = min(len(fa), len(fb))
    if k < 5:
        return dict(similarity=0.0, lag_s=best_lag * 0.02, level_db=0.0, note='too short after alignment')
    corr = float(np.corrcoef(fa[:k].ravel(), fb[:k].ravel())[0, 1])
    lvl = 20 * np.log10((np.sqrt((a2[:n] ** 2).mean()) + 1e-9) / (np.sqrt((b2[:n] ** 2).mean()) + 1e-9))
    return dict(similarity=corr, lag_s=best_lag * 0.02, level_db=float(lvl))
