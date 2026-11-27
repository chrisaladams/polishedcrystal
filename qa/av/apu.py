"""APU channel monitor: what the music engine intends against what the sound hardware does.

Needs SameBoy (it exposes each channel's volume, amplitude and period). Per frame, for each of the four
channels, it looks at

* the engine's view: is the channel playing a note (not a rest, volume > 0), its pitch/octave and the
  frequency the engine computed (wChannelNFrequency);
* the hardware's view: the channel's period register, volume and output amplitude;

and flags
  CHANNEL_DROPOUT  the engine voices a channel for many frames but the hardware never produces output
  PERIOD_MISMATCH  the channel's period register is not the frequency the engine computed
  PITCH_WRONG      the frequency the engine computed is not what the note/octave/transposition give,
                   using an independent reimplementation of the frequency table lookup

The third check is a second implementation of GetFrequency written from the table in ROM, so a fault in the
engine's arithmetic (as opposed to its data) is visible without a reference recording.
"""
import ctypes as C

from qa.gb.consts import C as K

CHANNELS = (1, 2, 3, 4)


class ApuMonitor:
    def __init__(self, g):
        self.g = g
        lib = g.lib
        for fn in ('GB_get_channel_volume', 'GB_get_channel_amplitude'):
            f = getattr(lib, fn)
            f.argtypes = [C.c_void_p, C.c_int]
            f.restype = C.c_uint8
        lib.GB_get_channel_period.argtypes = [C.c_void_p, C.c_int]
        lib.GB_get_channel_period.restype = C.c_uint16
        bank, addr = g.sym['FrequencyTable']
        self.table = [g.read_rom(bank, addr + 2 * i) | g.read_rom(bank, addr + 2 * i + 1) << 8 for i in range(14)]
        self.frames = 0
        self.voiced = [0] * 4
        self.audible = [0] * 4
        self.period_checked = [0] * 4
        self.period_bad = [0] * 4
        self.pitch_checked = [0] * 4
        self.pitch_bad = [0] * 4
        self.examples = {}
        self.rest_bit = K['NOTE_REST']
        self.slide_bit = K['SOUND_PITCH_SLIDE']
        g.frame_hooks.append(self.step)

    def detach(self):
        if self.step in self.g.frame_hooks:
            self.g.frame_hooks.remove(self.step)

    # -- independent model of GetFrequency (transposition 0 only; other cases are skipped, not guessed)
    def model_frequency(self, pitch, octave, transposition):
        start_oct, low = (transposition >> 4) & 0xf, transposition & 0xf
        a = start_oct + octave
        idx = low + pitch
        if idx >= len(self.table):
            return None
        freq = self.table[idx]
        if freq & 0x8000:
            freq -= 0x10000
        while a < 7 and a >= 0:
            freq >>= 1
            a += 1
        return freq & 0x7ff

    def step(self, g):
        if not g.rd('wMusicPlaying'):
            return
        self.frames += 1
        lib = g.lib
        for i, ch in enumerate(CHANNELS):
            p = f'wChannel{ch}'
            if not (g.rd(p + 'MusicAddress') | g.rd(p + 'MusicAddress', 1)):
                continue
            flags = g.rd(p + 'NoteFlags')
            rest = flags >> self.rest_bit & 1
            if rest or g.rd(p + 'NoteDuration') == 0:
                continue
            vol = g.rd(p + 'Intensity') >> 4 if ch != 3 else 1
            if vol == 0:
                continue
            self.voiced[i] += 1
            if lib.GB_get_channel_amplitude(g.gb, i) or lib.GB_get_channel_volume(g.gb, i):
                self.audible[i] += 1
            if ch == 4:
                continue
            freq = g.rd(p + 'Frequency') | g.rd(p + 'Frequency', 1) << 8
            if g.rd(p + 'Flags2') >> self.slide_bit & 1 or g.rd('wPitchTransposition'):
                continue
            # the channel's period register against the engine's frequency (vibrato, pitch slides and detune (PitchOffset) move the
            # register away from the base frequency on purpose, so only steady notes are compared)
            if not g.rd(p + 'VibratoExtent') and not g.rd(p + 'PitchWheelAmount') and not g.rd(p + 'PitchOffset'):
                period = lib.GB_get_channel_period(g.gb, i)
                self.period_checked[i] += 1
                if period != freq:
                    self.period_bad[i] += 1
                    self.examples.setdefault(('period', ch), 'channel %d: engine frequency %#x, APU period %#x' % (ch, freq, period))
            pitch, octave = g.rd(p + 'Pitch'), g.rd(p + 'Octave')
            exp = self.model_frequency(pitch, octave, g.rd(p + 'Transposition'))
            if exp is not None:
                self.pitch_checked[i] += 1
                if exp != freq:
                    self.pitch_bad[i] += 1
                    self.examples.setdefault(('pitch', ch), 'channel %d: pitch %d octave %d gives %#x, the engine computed %#x' % (ch, pitch, octave, exp, freq))

    def findings(self, min_frames=45, tolerance=0.02):
        out = []
        for i, ch in enumerate(CHANNELS):
            if self.voiced[i] >= min_frames and self.audible[i] == 0:
                out.append(('CHANNEL_DROPOUT', ch, 'channel %d voiced by the engine for %d frames, hardware output never rose above zero' % (ch, self.voiced[i])))
            if self.pitch_checked[i] >= min_frames and self.pitch_bad[i] > tolerance * self.pitch_checked[i]:
                out.append(('PITCH_WRONG', ch, '%d of %d frames: %s' % (self.pitch_bad[i], self.pitch_checked[i], self.examples.get(('pitch', ch), ''))))
            if self.period_checked[i] >= min_frames and self.period_bad[i] > 0.05 * self.period_checked[i]:
                out.append(('PERIOD_MISMATCH', ch, '%d of %d frames: %s' % (self.period_bad[i], self.period_checked[i], self.examples.get(('period', ch), ''))))
        return out

    def summary(self):
        return dict(frames=self.frames, voiced=self.voiced, audible=self.audible, period=[self.period_checked, self.period_bad],
                    pitch=[self.pitch_checked, self.pitch_bad])
