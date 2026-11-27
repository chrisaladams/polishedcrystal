"""Audiovisual review report: suspicious events, deduplicated and classified.

    python3 -m qa.av.review RUN_DIR      (a directory written by qa/run.py)

Reads every test result's `av` records and writes RUN_DIR/av_review.md. Each record is a
suspicion (an anomaly with artifacts), classified as:

  confirmed   a defect by an objective criterion (e.g. a CPU write to VRAM the PPU is using)
  suspect     needs a person: shown with its screenshots / frame strip / audio
  expected    a known legitimate transition (boot black frames, battle flashes, intended silence)
  emulator    appears on some emulators or hardware models and not others: an emulator
              or revision difference until proven otherwise

Nothing is hidden: expected and emulator-class events are listed too, with the reason.
"""
import json
import os
import sys


def classify(rec, seen_on):
    """Return (class, reason) for one anomaly record. seen_on: set of 'backend/model' that saw its signature."""
    kind, ctx = rec['kind'], rec.get('context', {})
    n_total = rec.get('n_runs', 1)
    if len(seen_on) < n_total and n_total > 1:
        return 'emulator', f'seen on {sorted(seen_on)} only, not on all {n_total} runs'
    if kind in ('ILLEGAL_VRAM', 'ILLEGAL_OAM'):
        return 'confirmed', 'CPU write to VRAM/OAM while the PPU was using it (dropped on real hardware)'
    if kind == 'BLANK_RUN':
        if ctx.get('boot') or rec.get('frame', 99999) < 2400:
            return 'expected', 'blank frames during boot / intro'
        if ctx.get('transition'):
            return 'expected', 'blank frames during a screen transition'
        return 'suspect', 'a long blank screen outside the intro'
    if kind == 'FLICKER':
        if ctx.get('in_battle'):
            return 'expected', 'battle animation flash'
        return 'suspect', 'the picture alternates between two frames'
    if kind == 'SPRITE_EXPECTED':
        return 'expected', rec.get('detail', '')
    if kind == 'SPRITE_INTEGRITY':
        return 'suspect', rec.get('detail', '')
    if kind == 'SPRITE_FLICKER':
        return 'suspect', 'visible sprite count alternates every frame'
    if kind in ('SILENCE', 'AUDIO_GLITCH', 'FREQ_ANOMALY'):
        return 'suspect', rec.get('detail', '')
    if kind == 'MUSIC_INDEPENDENT_LOOPS':
        return 'expected', 'channels loop on independent periods (authored: e.g. a short drum loop under a long melody); a changed length between builds is caught by the build comparison'
    if kind in ('MUSIC_NO_LOOP', 'MUSIC_DESYNC', 'SFX_BREAKS_MUSIC'):
        return 'suspect', rec.get('detail', '')
    return 'suspect', 'unclassified'


def build(results):
    """results: list of per-test result dicts with an `av` list. Returns the grouped structure."""
    runs = {}
    for r in results:
        if not r.get('av'):
            continue
        key = r['name'].split('.')[-1] if False else r['name']
        runs.setdefault(key, []).append(r)
    groups = {}
    for name, rs in runs.items():
        n_runs = len({(r['backend'], r.get('model')) for r in rs})
        for r in rs:
            who = f"{r['backend']}/{r.get('model') or '-'}"
            for rec in r['av']:
                rec = dict(rec, test=name, n_runs=n_runs)
                g = groups.setdefault((name, rec['kind'], rec['sig']), dict(rec=rec, seen_on=set(), count=0))
                g['seen_on'].add(who)
                g['count'] += rec.get('count', 1)
    out = []
    for (name, kind, sig), g in groups.items():
        cls, why = classify(g['rec'], g['seen_on'])
        out.append(dict(test=name, kind=kind, sig=sig, cls=cls, reason=why, seen_on=sorted(g['seen_on']),
                        count=g['count'], rec=g['rec']))
    order = {'confirmed': 0, 'suspect': 1, 'emulator': 2, 'expected': 3}
    return sorted(out, key=lambda x: (order[x['cls']], x['test'], x['kind']))


def write(run_dir):
    data = json.load(open(os.path.join(run_dir, 'results.json')))
    items = build(data['results'])
    meta = data['meta']
    lines = ['# Audiovisual review', '',
             f"ROM `{meta['rom']['sha1'][:12]}`, commit `{meta['git']['commit'][:10]}`, run {meta['time_utc']}.",
             'Suspicious events only: nothing here required watching a whole play session. '
             'Classes: **confirmed** (objective defect), **suspect** (needs a person), **emulator** '
             '(differs between emulators/revisions), **expected** (known legitimate).', '']
    counts = {c: sum(1 for i in items if i['cls'] == c) for c in ('confirmed', 'suspect', 'emulator', 'expected')}
    lines.append('| confirmed | suspect | emulator | expected |')
    lines.append('|---|---|---|---|')
    lines.append('| %(confirmed)d | %(suspect)d | %(emulator)d | %(expected)d |' % counts)
    lines.append('')
    for cls in ('confirmed', 'suspect', 'emulator', 'expected'):
        sel = [i for i in items if i['cls'] == cls]
        if not sel:
            continue
        lines += [f'## {cls} ({len(sel)})', '']
        for i in sel:
            rec = i['rec']
            lines.append(f"### {i['kind']} `{i['sig']}` in {rec.get('where', '?')} ({i['test']})")
            lines.append(f"- {rec['detail']}")
            lines.append(f"- class: **{cls}**: {i['reason']}; seen on {', '.join(i['seen_on'])}; {i['count']} occurrence(s)")
            for k, v in (rec.get('artifacts') or {}).items():
                if v:
                    lines.append(f'- {k}: `{os.path.relpath(v, run_dir) if os.path.isabs(v) else v}`')
            lines.append('')
    p = os.path.join(run_dir, 'av_review.md')
    open(p, 'w').write('\n'.join(lines) + '\n')
    print(p, counts)
    return counts


if __name__ == '__main__':
    d = sys.argv[1] if len(sys.argv) > 1 else None
    if d and os.path.basename(d) == 'latest':
        base = os.path.dirname(d)
        runs = sorted(x for x in os.listdir(base) if os.path.exists(os.path.join(base, x, 'results.json')))
        d = os.path.join(base, runs[-1])
    write(d)
