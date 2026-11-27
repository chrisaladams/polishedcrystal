"""Per-frame audiovisual monitor.

Attach to a game (`FrameMonitor(g, out)`); every frame it classifies the picture and keeps
the last few frames. When something suspicious happens it saves the surrounding frames,
a contact sheet, the LCD/OAM state and where the CPU is, and records an Anomaly with a
signature so repeats are counted once.

What it looks for (each is a *suspicion*, classified later as defect, emulator difference
or expected transition):
  BLANK_RUN        a uniform white/black/solid frame for more than `blank_frames` frames in a row
  FLICKER          the picture alternating between two very different frames (A,B,A,B ...)
  SPRITE_FLICKER   the number of visible sprites alternating by 4 or more
  ILLEGAL_VRAM / ILLEGAL_OAM   CPU writes to VRAM/OAM while the PPU is using them (SameBoy)
  VBLANK_OVERRUN   the VBlank handler returned later than `vblank_limit` lines into the next frame
"""
import hashlib
import os
import re
from collections import deque

import numpy as np

from qa.gb import hw
from . import frames, vram


class Anomaly:
    def __init__(self, kind, detail, frame, where, artifacts, context=None):
        self.kind, self.detail, self.frame, self.where = kind, detail, frame, where
        self.artifacts, self.context = artifacts, context or {}
        norm = re.sub(r'\d+', 'N', detail)
        self.signature = hashlib.sha1(f'{kind}|{where}|{norm}'.encode()).hexdigest()[:12]

    def as_dict(self):
        return dict(kind=self.kind, detail=self.detail, frame=self.frame, where=self.where, sig=self.signature,
                    artifacts=self.artifacts, context=self.context)


class FrameMonitor:
    def __init__(self, g, out, blank_frames=45, flicker_frames=6, flicker_fraction=0.25, ring=24,
                 allow=(), vblank_limit=100, label=''):
        self.g, self.out, self.label = g, out, label
        os.makedirs(out, exist_ok=True)
        self.blank_frames, self.flicker_frames, self.flicker_fraction = blank_frames, flicker_frames, flicker_fraction
        self.vblank_limit = vblank_limit
        self.allow = set(allow)            # anomaly kinds the scenario expects (e.g. FLICKER in a battle flash)
        self.ring = deque(maxlen=ring)
        self.anomalies = {}
        self.counts = {}                   # signature -> occurrences
        self.stats = dict(frames=0, blank_runs=0, max_blank_run=0, flicker_events=0)
        self._blank_kind, self._blank_len, self._blank_reported = None, 0, False
        self._flip = 0
        self._prev = self._prev2 = None
        self._sprites = deque(maxlen=8)
        self._last_access = (0, 0)
        self.context_fn = None             # optional callable returning dict(map=..., script=...)
        g.frame_hooks.append(self._on_frame)

    # ---- context
    def where(self):
        try:
            c = self.context_fn() if self.context_fn else {}
        except Exception:
            c = {}
        return c.get('map') or ('%s' % (self.g.where(),)).split('+')[0]

    def _record(self, kind, detail, extra=None):
        if kind in self.allow:
            return None
        g = self.g
        a = Anomaly(kind, detail, g.frame, self.where(), {}, extra)
        n = self.counts.get(a.signature, 0) + 1
        self.counts[a.signature] = n
        if n > 1:
            return a
        # first time: keep the evidence
        base = os.path.join(self.out, f'{self.label}{a.signature}')
        os.makedirs(base, exist_ok=True)
        fr = list(self.ring)
        a.artifacts['frames'] = frames.contact_sheet([f for _, f in fr[-12:]], os.path.join(base, 'frames.png'), cols=6)
        try:
            a.artifacts['screenshot'] = frames.save(g.frame_rgb(), os.path.join(base, 'now.png'), 2)
            a.artifacts['state'] = None
            g.dump_state(os.path.join(base, 'state.bin'))
            a.artifacts['state'] = os.path.join(base, 'state.bin')
        except Exception:
            pass
        a.context.update(lcd=vram.lcd_state(g), sprites=len(hw.visible_sprites(g)), pc=getattr(g, 'pc', None),
                         routine=g.where(), frame_number=g.frame, in_battle=bool(g.in_battle()),
                         transition=g.rd('wMapStatus') != 2)
        self.anomalies[a.signature] = a
        return a

    # ---- the per-frame check
    def _on_frame(self, g):
        fr = g.frame_rgb()
        self.stats['frames'] += 1
        self.ring.append((g.frame, fr))
        # blank frames
        kind = frames.classify_blank(fr)
        if kind and kind == self._blank_kind:
            self._blank_len += 1
        else:
            if self._blank_kind and self._blank_len > 0:
                self.stats['blank_runs'] += 1
            self._blank_kind, self._blank_len, self._blank_reported = kind, (1 if kind else 0), False
        self.stats['max_blank_run'] = max(self.stats['max_blank_run'], self._blank_len)
        if kind and self._blank_len > self.blank_frames and not self._blank_reported:
            self._blank_reported = True
            self._record('BLANK_RUN', f'{kind} frame for more than {self.blank_frames} frames in a row')
        # flicker: A,B,A,B
        if self._prev2 is not None:
            d_ab = frames.diff(self._prev, fr)['fraction']
            d_aa = frames.diff(self._prev2, fr)['fraction']
            if d_ab > self.flicker_fraction and d_aa < 0.02:
                self._flip += 1
            else:
                self._flip = 0
            if self._flip == self.flicker_frames:
                self.stats['flicker_events'] += 1
                self._record('FLICKER', f'picture alternating between two frames for {self.flicker_frames}+ frames')
        self._prev2, self._prev = self._prev, fr
        # sprite flicker
        n = len(hw.visible_sprites(g))
        self._sprites.append(n)
        s = list(self._sprites)
        if len(s) >= 6 and all(abs(s[i] - s[i + 1]) >= 4 for i in range(len(s) - 1)):
            self._record('SPRITE_FLICKER', 'visible sprite count alternating by 4 or more every frame')
        # PPU access timing and VBlank workload (SameBoy native monitors)
        if hasattr(g, 'access_report') and self.stats['frames'] % 30 == 0:
            vw, vb, ow, ob, ev = g.access_report()
            if (vb, ob) != self._last_access:
                self._last_access = (vb, ob)
                e = ev[-1] if ev else {}
                if vb:
                    self._record('ILLEGAL_VRAM', f'{vb} VRAM writes during PPU mode 3', dict(first=ev[:3]))
                if ob:
                    self._record('ILLEGAL_OAM', f'{ob} OAM writes during PPU mode 2/3', dict(first=ev[:3]))

    def vblank_report(self):
        """Distribution of the line at which the VBlank handler returned (SameBoy only)."""
        if not hasattr(self.g, 'vblank_lines'):
            return None
        h = self.g.vblank_lines()
        total = sum(h.values())
        if not total:
            return None
        over = {ly: n for ly, n in h.items() if self.vblank_limit <= ly < 144}
        late = sum(n for ly, n in h.items() if ly < 144)
        return dict(total=total, returned_after_vblank=late, worst_line=max((ly for ly in h if ly < 144), default=None),
                    beyond_limit=sum(over.values()), histogram=h)

    def summary(self):
        return dict(stats=self.stats, anomalies=[a.as_dict() for a in self.anomalies.values()],
                   occurrences=self.counts, vblank=self.vblank_report())
