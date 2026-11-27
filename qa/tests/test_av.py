"""Audiovisual fidelity tests: pictures and sound are checked on their own, not inferred
from gameplay succeeding. See qa/av/ and docs/qa-av.md.

Every test that finds something suspicious adds a record to ctx.av; `python3 -m qa.av.review RUN`
turns those into a classified review report. References are never approved by tests."""
import json
import os

import numpy as np

from qa.av import audio, frames, monitor, music, refs, vram
from qa.framework import qa_test
from qa.gb import fixtures as F, hw

PROVENANCE_BOOT = 'New Game by button input to the bedroom (gameplay); nothing injected'


def _records(ctx, mon):
    for a in mon.anomalies.values():
        d = a.as_dict()
        d['count'] = mon.counts.get(a.signature, 1)
        ctx.av.append(d)


def _boot_monitored(ctx, seconds_audio=90):
    g = ctx.game()
    if hasattr(g, 'enable_av'):
        g.enable_av(seconds_audio)
    mon = monitor.FrameMonitor(g, os.path.join(ctx.out, 'av'), label=f'{ctx.backend}_{ctx.model}_')
    F.new_game_to_bedroom(g)
    g.tick(120)
    return g, mon


@qa_test(suites=('av', 'hardware', 'full'), covers=('hw.oam_lines', 'hw.vram_access', 'sprites.oam_budget', 'av.frames', 'av.flicker', 'av.ppu_timing', 'av.models'),
         backends=('pyboy', 'sameboy'), models=('CGB-0', 'CGB-E', 'AGB'), provenance=PROVENANCE_BOOT, timeout=900)
def boot_to_bedroom_monitored(ctx):
    """Frame monitor over the whole boot, intro and New Game: blank runs, flicker, sprite
    flicker, illegal VRAM/OAM access (SameBoy) and VBlank handler length (SameBoy)."""
    g, mon = _boot_monitored(ctx)
    _records(ctx, mon)
    s = mon.summary()
    ctx.note('frames %d, blank runs %d (longest %d), flicker events %d' % (
        s['stats']['frames'], s['stats']['blank_runs'], s['stats']['max_blank_run'], s['stats']['flicker_events']))
    if hasattr(g, 'access_report'):
        vw, vb, ow, ob, ev = g.access_report()
        ctx.note(f'PPU access: {vw} VRAM writes ({vb} illegal), {ow} OAM writes ({ob} illegal)')
        ctx.expect(vb == 0 and ob == 0, f'{vb} illegal VRAM / {ob} illegal OAM writes: {ev[:2]}')
        vbr = mon.vblank_report()
        if vbr:
            ctx.note('VBlank handler returned after the end of VBlank in %d of %d frames; worst line %s' % (
                vbr['returned_after_vblank'], vbr['total'], vbr['worst_line']))
    bad = [a for a in mon.anomalies.values() if a.kind in ('FLICKER', 'SPRITE_FLICKER')]
    ctx.expect(not bad, 'unexpected flicker: ' + '; '.join(a.detail for a in bad))


def _capture_checkpoints(g):
    """Deterministic checkpoints reached by input only: the title screen and the bedroom."""
    out = {}
    # align by game state, not by frame count: PyBoy skips the boot ROM, SameBoy plays it
    entered = g.counter('TitleScreenMain')
    for _ in range(3000):
        g.tick(1)
        if entered() > 3:
            break
    g.tick(60)
    out['title'] = g.frame_rgb()
    g.press('start', 4, 20)
    g.press('start', 4, 20)
    for _ in range(200):
        g.press('a', 4, 14)
        if g.rd('wMapGroup') == 24 and g.rd('wMapNumber') == 5:
            break
    g.tick(240)
    out['bedroom'] = g.frame_rgb()
    return out


@qa_test(suites=('av', 'hardware', 'full'), covers=('av.cross_emulator', 'av.frames', 'av.models'), backends=('sameboy',), models=('CGB-0', 'CGB-E', 'AGB'),
         provenance=PROVENANCE_BOOT, timeout=900)
def cross_emulator_frames(ctx):
    """Differential rendering: the same input sequence on PyBoy and on this SameBoy model must give
    the same pictures at the title screen and in the bedroom (tolerance: 24/255 per channel, 3 % of
    pixels, for emulator colour/timing differences). Also writes reference *candidates* (never approved)."""
    from qa.gb.emu import Game
    p = Game(rom=ctx.rom, workdir=ctx.out)
    pc = _capture_checkpoints(p)
    p.close()
    s = ctx.game()
    sc = _capture_checkpoints(s)
    for name in pc:
        d = frames.diff(pc[name], sc[name], tol=40)
        ctx.note(f'{name}: {d["fraction"] * 100:.2f}% pixels differ (mean abs {d["mean"]:.1f}), bbox {d["bbox"]}')
        frames.save(frames.diff_image(pc[name], sc[name], 40), os.path.join(ctx.out, f'diff_{name}.png'), 2)
        ctx.artifacts.append(os.path.join(ctx.out, f'diff_{name}.png'))
        ctx.expect(d['fraction'] < 0.05, f'{name}: PyBoy and SameBoy {ctx.model} differ in {d["fraction"] * 100:.1f}% of pixels')
        agree = d['fraction'] < 0.05
        refs.propose(f'{name}_{ctx.model}', sc[name], dict(
            rom_sha1=ctx.rom, emulators_agree=agree, emulators=['pyboy', f'sameboy {ctx.model}'],
            agreement_fraction=d['fraction'], note='candidate only: a person must review and approve',
            monitor_anomalies=[]))


@qa_test(suites=('av', 'full'), covers=('av.references',), backends=('sameboy',), models=('CGB-E',), provenance=PROVENANCE_BOOT)
def reference_frames(ctx):
    """Compare checkpoints with APPROVED references. Without an approved reference this skips
    (it is not a pass): see `python3 -m qa.av.refs list`."""
    g = ctx.game()
    cps = _capture_checkpoints(g)
    missing, mismatched = [], []
    for name, fr in cps.items():
        status, detail = refs.compare(f'{name}_{ctx.model}', fr, evidence=dict(rom_sha1=ctx.rom, emulators_agree=None))
        if status == 'unreferenced':
            missing.append(name)
        elif status == 'mismatch':
            mismatched.append(f'{name}: {detail["fraction"] * 100:.1f}% differ')
            frames.save(fr, os.path.join(ctx.out, f'ref_mismatch_{name}.png'), 2)
    ctx.expect(not mismatched, 'differs from the approved reference: ' + '; '.join(mismatched))
    if missing and not mismatched:
        ctx.skip('no approved reference for: ' + ', '.join(missing))


@qa_test(suites=('av', 'hardware', 'full'), covers=('av.oam', 'av.vram'), backends=('pyboy',), provenance='injected warp into each map; the player stands still',
         timeout=1800, name='test_av.oam_vram_integrity_maps')
def oam_vram_integrity_maps(ctx):
    """On every map: OAM entries are sane (no visible sprite using a blank tile, no duplicate entries),
    BG attributes valid, and at most 10 sprites per scanline. Suspicions are recorded, not hidden."""
    from qa.gb import collision, mapdata
    from qa.gb.consts import C, map_ids
    from qa.tests.test_map_smoke import build, pick_tile
    g = ctx.boot('smoke_base', build)
    g.save_point()
    problems = {}
    n = 0
    consts = sorted(mapdata.attributes())
    if os.environ.get('QA_MAP_LIMIT'):
        consts = consts[:int(os.environ['QA_MAP_LIMIT'])]
    for const in consts:
        g.restore_point()
        try:
            sg, sn = map_ids(const)
            F.teleport(g, sg, sn, 2, 2, settle=60)
            t = pick_tile(g)
            if t is None:
                continue
            F.teleport(g, sg, sn, t[0], t[1], settle=90)
            g.tick(40)
            n += 1
            for msg in vram.oam_problems(g) + vram.tilemap_problems(g):
                key = msg.split(' visible')[0].split(':')[0] if 'blank' not in msg else 'visible sprite using a blank tile'
                problems.setdefault(key, []).append(const)
        except Exception as e:
            problems.setdefault('harness error', []).append(f'{const}: {e}')
    ctx.note(f'{n} maps checked')
    for k, maps in problems.items():
        ctx.note(f'{k}: {len(maps)} maps, first {maps[:5]}')
        ctx.av.append(dict(kind='SPRITE_INTEGRITY', detail=f'{k} on {len(maps)} maps', where=','.join(maps[:3]), sig=f'oamv-{abs(hash(k)) % 10**6}',
                           count=len(maps), artifacts={}, context={'maps': maps[:20]}, frame=0))


@qa_test(suites=('av', 'hardware', 'full'), covers=('hw.vram_access', 'av.ppu_timing', 'av.models'), backends=('sameboy',), models=('CGB-0', 'CGB-E', 'AGB'),
         provenance='stage checkpoint is injected (qa/gb/ladder.py); the walk, menus and battle are input', timeout=1800)
def ppu_timing_in_gameplay(ctx):
    """Illegal VRAM/OAM access and VBlank handler length while playing: the New Game opening and the
    Elm's Lab intro through the navigator (real input), on this hardware model."""
    from qa.gb.nav import Navigator
    g = ctx.game()
    g.enable_av(120)
    mon = monitor.FrameMonitor(g, os.path.join(ctx.out, 'av'), label=f'{ctx.model}_')
    F.new_game_to_bedroom(g)
    nav = Navigator(g, seed=ctx.seed)
    try:
        nav.goto_map('ELMS_LAB')
    except Exception as e:
        ctx.note(f'navigator stopped: {type(e).__name__}: {str(e)[:100]}')
    _records(ctx, mon)
    vw, vb, ow, ob, ev = g.access_report()
    ctx.note(f'{g.frame} frames; PPU access: {vw} VRAM writes ({vb} illegal), {ow} OAM writes ({ob} illegal)')
    vbr = mon.vblank_report()
    if vbr:
        ctx.note('VBlank handler: returned after VBlank in %d/%d frames, worst line %s' % (vbr['returned_after_vblank'], vbr['total'], vbr['worst_line']))
    ctx.expect(vb == 0 and ob == 0, f'illegal PPU access: {ev[:2]}')


@qa_test(suites=('av', 'hardware', 'full'), covers=('av.audio_pcm',), backends=('sameboy',), models=('CGB-E',),
         provenance=PROVENANCE_BOOT)
def audio_boot_scan(ctx):
    """PCM analysis of the whole boot/intro/New Game: clipping, DC offset, whine/glitch frequencies,
    long silences. Silence before the first music and during the quiet intro is legitimate, so only
    silences after music has started are reported as suspicious."""
    g, mon = _boot_monitored(ctx)
    pcm = g.audio_pcm()
    x = audio.mono(pcm)
    audio.write_wav(os.path.join(ctx.out, 'boot.wav'), pcm)
    ctx.artifacts.append(os.path.join(ctx.out, 'boot.wav'))
    st = audio.stats(x)
    ctx.note('%.1f s of audio, rms %.3f, peak %.3f, dc %.4f, clipped samples %d' % (len(x) / audio.RATE, st['rms'], st['peak'], st['dc'], st['clip']))
    ctx.expect(len(x) > audio.RATE * 10, 'almost no audio was produced during the whole opening')
    ctx.expect(abs(st['dc']) < 0.05, f'DC offset {st["dc"]:.3f}')
    ctx.expect(st['clip'] == 0, f'{st["clip"]} clipped samples')
    fa = audio.frequency_anomalies(x)
    for kind, t, hz in fa[:5]:
        ctx.av.append(dict(kind='FREQ_ANOMALY', detail=f'{kind} at {t:.1f}s ({hz:.0f} Hz)', where='boot', sig=f'fa-{kind[:4]}', count=1, artifacts={'wav': os.path.join(ctx.out, 'boot.wav')}, context={}, frame=int(t * 60)))
    sil = audio.silence_runs(x, min_seconds=2.0)
    ctx.note('silent stretches over 2 s: %s' % [(round(a, 1), round(b, 1)) for a, b in sil[:8]])


@qa_test(suites=('av', 'full'), covers=('av.silence', 'av.flicker'), backends=('pyboy',), provenance='New Game by input, then the explorer plays on its own (gameplay)',
         timeout=1500)
def monitored_play_session(ctx):
    """The autonomous explorer plays from New Game for a fixed number of seconds with the picture
    and sound monitors attached; anything suspicious is recorded and classified in the review."""
    from qa.gb.emu import Game
    from qa.gb.explorer import Explorer
    g = Game(rom=ctx.rom, workdir=ctx.out, seed=ctx.seed, audio=True)
    F.new_game_to_bedroom(g)
    ex = Explorer(g, ctx.out, seed=ctx.seed, label='av', av=True)
    s = ex.run(budget_seconds=int(os.environ.get('QA_AV_PLAY_SECONDS', '150')))
    av, au = s['av'], s['av_audio']
    ctx.note('%d frames, %d maps, %d battles; blank runs %d (longest %d), flicker %d' % (
        s['frames'], s['maps_visited'], s['battles'], av['stats']['blank_runs'], av['stats']['max_blank_run'], av['stats']['flicker_events']))
    ctx.note('audio: %d seconds recorded, %d quiet' % (au['seconds'], au['quiet']) if au else 'audio not recorded')
    for a in av['anomalies']:
        ctx.av.append(a)
    for a in (au['anomalies'] if au else []):
        ctx.av.append(a)
    ctx.expect(not s['failures'], 'gameplay failures: %r' % (s['failures'][:2],))
