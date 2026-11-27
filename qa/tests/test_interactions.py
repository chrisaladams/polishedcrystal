"""NPC / sign / hidden-item / trigger-tile interaction sweep over every map.

See qa/gb/sweep.py. Starting positions and flag states are INJECTED (labelled); the A press and
everything after it (dialogue, scenes, battles) is real controller input. Results are kept per map
in qa/.cache/sweep/<rom>/<tag>/results.jsonl so an interrupted run resumes; set QA_SWEEP_RESUME=0
to start over. QA_SWEEP_LIMIT=N sweeps only the first N maps of each shard (development).
"""
import os

from qa.framework import qa_test
from qa.gb import saves, sweep
from qa.gb.emu import sha1

PROVENANCE = 'injected: player position and flag state; real input for the A press, dialogue and battles'


def run(ctx, state, shard, shards):
    name, builder = sweep.fixture_for(state)
    g = ctx.boot(name, builder)
    model = ctx.model or ''
    tag = '%s-%s-%s-%dof%d-seed%d' % (ctx.backend, model or 'x', state, shard, shards, ctx.seed)
    results = os.path.join(saves.CACHE, 'sweep', sha1(ctx.rom)[:12], tag)
    limit = int(os.environ.get('QA_SWEEP_LIMIT', '0')) or None
    resume = os.environ.get('QA_SWEEP_RESUME', '1') != '0'
    s = sweep.run_shard(g, ctx.out, ctx.backend, model, state, shard, shards, seed=ctx.seed, limit=limit,
                        resume=resume, results_dir=results)
    ctx.note('%s %s %s shard %d/%d: %d of %d maps swept, %d interactions %s, outcomes %s' % (
        ctx.backend, model or '', state, shard, shards, s['maps_done'], s['maps_total'], s['interactions'], s['by_kind'], s['outcomes']))
    unt = s['untested']
    if unt:
        ctx.note('untested (%d): ' % len(unt) + '; '.join('%s %s: %s' % (m, t, why) for m, t, why in unt[:12]))
    exp = s.get('expected', [])
    if exp:
        by_map = {}
        for m, t, why in exp:
            by_map.setdefault(m, [0, why])[0] += 1
        ctx.note('expected stalls, not failures (%d in %d maps): ' % (len(exp), len(by_map)) +
                 '; '.join('%s x%d: %s' % (m, n, w[:70]) for m, (n, w) in sorted(by_map.items())[:8]))
    for sig, e in sorted(s['signatures'].items(), key=lambda kv: -kv[1]['count']):
        d = os.path.join(ctx.out, 'failures', sig)
        if os.path.isdir(d):
            ctx.artifacts.append(d)
        ctx.expect(False, '[%s] %s in %s x%d (first: %s): %s' % (sig, e['kind'], e['routine'], e['count'], e['targets'][0], e['detail'][:200]))
    longs = s['outcomes'].get('long', 0)
    if unt or longs or s['maps_done'] < s['maps_total'] or state != 'default':
        why = '%d targets/maps could not be exercised, %d scenes outlasted the budget' % (len(unt), longs)
        ctx.uncover('npc.interaction', why)


def _make(state, shard, shards, backend, suites, models=None):
    @qa_test(suites=suites, covers=('npc.interaction', 'hw.memory_guard'), backends=(backend,), models=models,
             provenance=PROVENANCE, timeout=6000, name='test_interactions.sweep_%s_%s_%dof%d' % (backend, state, shard, shards))
    def shard_test(ctx):
        run(ctx, state, shard, shards)
    return shard_test


for _i in range(4):
    _make('default', _i, 4, 'pyboy', ('map', 'full'))
    for _s in ('allflags', 'noflags', 'party'):
        _make(_s, _i, 4, 'pyboy', ('full',))
    _make('default', _i, 4, 'sameboy', ('hardware', 'full'), models=('CGB-E', 'AGB'))
