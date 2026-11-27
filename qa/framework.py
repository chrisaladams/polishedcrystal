"""Test registry and per-test context for the QA suite.

    from qa.framework import qa_test

    @qa_test(suites=('regression', 'map'), covers=('map.connections',),
             backends=('pyboy', 'sameboy'), provenance='...')
    def my_test(ctx):
        g = ctx.boot('fixture_name', builder_fn)
        ctx.expect(cond, 'what went wrong')

A test passes when it returns without raising and ctx.expect never failed.
"""
import json
import os
import random
import traceback

from qa.gb import saves
from qa.gb.emu import ROOT, default_rom

REGISTRY = []
SUITES = ('general', 'map', 'battle', 'hardware', 'regression', 'full')


class Skip(Exception):
    pass


def qa_test(suites=('general',), covers=(), backends=('pyboy',), provenance='', models=None,
            timeout=600, name=None):
    """Register a test. covers lists coverage areas (see qa/coverage.py)."""
    def deco(fn):
        REGISTRY.append(dict(fn=fn, name=name or fn.__module__.split('.')[-1] + '.' + fn.__name__,
                             suites=tuple(suites), covers=tuple(covers), backends=tuple(backends),
                             provenance=provenance, models=models, timeout=timeout))
        return fn
    return deco


class Ctx:
    def __init__(self, test, backend, model, seed, out, rom):
        self.test, self.backend, self.model, self.seed, self.out, self.rom = test, backend, model, seed, out, rom
        self.rng = random.Random(seed)
        self.failures = []
        self.notes = []
        self.artifacts = []
        self.games = []
        self.provenance = test['provenance']
        self.uncovered = {}
        os.makedirs(out, exist_ok=True)

    # ---- games and fixtures
    def game(self, sav=None):
        if self.backend == 'sameboy':
            from qa.gb.sameboy import SBGame
            g = SBGame(rom=self.rom, sav=sav, workdir=self.out, model=self.model or 'CGB-E', seed=self.seed)
        else:
            from qa.gb.emu import Game
            g = Game(rom=self.rom, sav=sav, workdir=self.out, seed=self.seed)
        self.games.append(g)
        return g

    def fixture(self, name, builder):
        path = saves.fixture(name, builder, rom=self.rom)
        return path, saves.fixture_meta(path)

    def boot(self, name, builder):
        """A game continued from fixture `name` (built on first use)."""
        path, meta = self.fixture(name, builder)
        g = self.game(sav=path)
        saves.boot_continue(g, meta['where'])
        return g

    # ---- reporting
    def expect(self, cond, msg):
        if not cond:
            self.failures.append(msg)
        return bool(cond)

    def note(self, msg):
        self.notes.append(str(msg))

    def uncover(self, tag, why):
        """Withdraw a declared coverage tag because this run only partly exercised it."""
        self.uncovered[tag] = why
        self.notes.append('coverage withdrawn for %s: %s' % (tag, why))

    def skip(self, why):
        raise Skip(why)

    def snapshot(self, g, tag, names=()):
        if hasattr(g, 'snapshot'):
            path = g.snapshot(tag, names=names)
        else:
            path = g.screenshot(tag)
        self.artifacts.append(path)
        return path

    def screenshot(self, g, tag):
        p = g.screenshot(tag)
        self.artifacts.append(p)
        return p


def run_one(test, backend, model, seed, out, rom):
    """Run one test/backend combination in this process; returns a result dict."""
    import time
    ctx = Ctx(test, backend, model, seed, out, rom)
    t0 = time.time()
    status, err = 'pass', None
    try:
        test['fn'](ctx)
        if ctx.failures:
            status = 'fail'
    except Skip as e:
        status, err = 'skip', str(e)
    except AssertionError as e:
        status, err = 'fail', ''.join(traceback.format_exception_only(type(e), e)).strip()
        ctx.failures.append(err)
    except Exception:
        status, err = 'error', traceback.format_exc()
    if status in ('fail', 'error'):
        for g in ctx.games:
            try:
                ctx.snapshot(g, 'failure_%d' % ctx.games.index(g))
            except Exception:
                pass
    for g in ctx.games:
        try:
            g.close()
        except Exception:
            pass
    return dict(name=test['name'], backend=backend, model=model, status=status, seconds=round(time.time() - t0, 1),
                failures=ctx.failures, error=err, notes=ctx.notes, artifacts=ctx.artifacts,
                provenance=ctx.provenance, covers=[c for c in test['covers'] if c not in ctx.uncovered],
                partial=ctx.uncovered, seed=seed)
