#!/usr/bin/env python3
"""Run QA suites.

    python3 qa/run.py general|map|battle|hardware|regression|full [options]
    python3 qa/run.py --list

Options:
    --seed N          seed for every randomised test (default 1; recorded in the report)
    --jobs N          parallel workers (default: CPU count)
    --backend B       pyboy | sameboy | all   (default: each test's own list)
    --models M,M      SameBoy hardware models (default CGB-E; e.g. CGB-0,CGB-E,AGB)
    --rom PATH        ROM to test (default: the freshly built one; its .sym must sit beside it)
    --only SUBSTR     run tests whose name contains SUBSTR
    --out DIR         report directory (default qa/reports/runs/<timestamp>)

Exit status is 0 only if nothing failed or errored. A skipped test is reported
as skipped, never as passed.
"""
import argparse
import importlib
import json
import multiprocessing as mp
import os
import pkgutil
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from qa import framework, meta          # noqa: E402
from qa.gb.emu import default_rom        # noqa: E402


def discover():
    import qa.tests
    for m in pkgutil.iter_modules(qa.tests.__path__):
        if m.name.startswith('test_'):
            importlib.import_module('qa.tests.' + m.name)
    return framework.REGISTRY


def _worker(name, backend, model, seed, out, rom, q):
    discover()
    test = next(t for t in framework.REGISTRY if t['name'] == name)
    q.put(framework.run_one(test, backend, model, seed, out, rom))


def plan(args):
    tests = [t for t in discover() if args.suite in t['suites'] or args.suite == 'full' and 'full' in t['suites']]
    if args.suite == 'full':
        tests = list(framework.REGISTRY)
    if args.only:
        tests = [t for t in tests if args.only in t['name']]
    jobs = []
    for t in tests:
        backends = t['backends'] if args.backend == 'default' else (
            ['pyboy', 'sameboy'] if args.backend == 'all' else [args.backend])
        backends = [b for b in backends if b in t['backends'] or args.backend != 'default']
        for b in backends:
            for model in ((args.models.split(',') if args.models else list(t['models'] or ('CGB-E',))) if b == 'sameboy' else [None]):
                jobs.append((t, b, model))
    return jobs


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('suite', nargs='?', default='general', choices=framework.SUITES)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--jobs', type=int, default=os.cpu_count() or 1)
    ap.add_argument('--backend', default='default', choices=('default', 'pyboy', 'sameboy', 'all'))
    ap.add_argument('--models', default=None, help='SameBoy models (default: each test\'s own list, else CGB-E)')
    ap.add_argument('--rom', default=None)
    ap.add_argument('--only', default=None)
    ap.add_argument('--out', default=None)
    ap.add_argument('--list', action='store_true')
    args = ap.parse_args(argv)
    rom = os.path.abspath(args.rom) if args.rom else default_rom()
    if args.list:
        for t in discover():
            print('%-52s %-28s %s' % (t['name'], ','.join(t['suites']), ','.join(t['backends'])))
        return 0
    if not os.path.exists(rom):
        print('ROM not found: %s (run `make` first)' % rom)
        return 2
    out_root = args.out or os.path.join(ROOT, 'qa', 'reports', 'runs', time.strftime('%Y%m%d-%H%M%S'))
    os.makedirs(out_root, exist_ok=True)
    jobs = plan(args)
    info = meta.collect(rom, args.seed, {'suite': args.suite, 'backend_option': args.backend, 'models': args.models or 'per-test default'})
    print('ROM %s sha1 %s  commit %s%s  seed %d' % (info['rom']['path'], info['rom']['sha1'][:12],
          info['git']['commit'][:10], '+dirty' if info['git']['dirty'] else '', args.seed))
    print('%d test runs, %d workers, report in %s' % (len(jobs), args.jobs, os.path.relpath(out_root, ROOT)))
    ctx = mp.get_context('spawn')
    pending, running, results = list(jobs), [], []
    while pending or running:
        while pending and len(running) < args.jobs:
            t, b, model = pending.pop(0)
            tag = '%s.%s%s' % (t['name'], b, '.' + model if model else '')
            q = ctx.Queue()
            p = ctx.Process(target=_worker, args=(t['name'], b, model, args.seed,
                                                  os.path.join(out_root, tag), rom, q))
            p.start()
            running.append((p, q, t, b, model, time.time(), tag))
        time.sleep(0.2)
        for item in list(running):
            p, q, t, b, model, t0, tag = item
            done = None
            if not q.empty():
                done = q.get()
            elif not p.is_alive():
                done = dict(name=t['name'], backend=b, model=model, status='error', seconds=round(time.time() - t0, 1),
                            failures=[], error='worker died (exit %s)' % p.exitcode, notes=[], artifacts=[],
                            provenance=t['provenance'], covers=list(t['covers']), seed=args.seed)
            elif time.time() - t0 > t['timeout']:
                p.terminate()
                done = dict(name=t['name'], backend=b, model=model, status='error', seconds=round(time.time() - t0, 1),
                            failures=[], error='timed out after %ds (possible softlock)' % t['timeout'], notes=[],
                            artifacts=[], provenance=t['provenance'], covers=list(t['covers']), seed=args.seed)
            if done:
                p.join(1)
                running.remove(item)
                results.append(done)
                print('%-6s %-60s %5.1fs' % (done['status'].upper(), tag, done['seconds']))
                for f in done['failures'][:3]:
                    print('       ', f[:300])
                if done['error'] and done['status'] == 'error':
                    print('       ', done['error'].strip().splitlines()[-1][:300])
    from qa import report
    report.write(out_root, info, results)
    bad = [r for r in results if r['status'] in ('fail', 'error')]
    counts = {s: sum(1 for r in results if r['status'] == s) for s in ('pass', 'fail', 'error', 'skip')}
    print('\n%s  (%s)' % ('FAILED' if bad else 'OK', ', '.join('%d %s' % (v, k) for k, v in counts.items())))
    print('report:', os.path.join(os.path.relpath(out_root, ROOT), 'summary.md'))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
