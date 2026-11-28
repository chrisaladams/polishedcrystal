"""NPC / sign / hidden-item / trigger-tile interaction sweep over every map.

See qa/gb/sweep.py. Starting positions and flag states are INJECTED (labelled); the A press and
everything after it (dialogue, scenes, battles) is real controller input. Results are kept per map
in qa/.cache/sweep/<rom>/<tag>/results.jsonl so an interrupted run resumes; set QA_SWEEP_RESUME=0
to start over. QA_SWEEP_LIMIT=N sweeps only the first N maps of each shard (development).
"""
import os

from qa.framework import qa_test
from qa.gb import saves, sweep
from qa.gb.consts import C
from qa.gb.emu import sha1

PROVENANCE = 'injected: player position and flag state; real input for the A press, dialogue and battles'


def run(ctx, state, shard, shards):
    name, builder = sweep.fixture_for(state)
    g = ctx.boot(name, builder)
    model = ctx.model or ''
    tag = '%s-%s-%s-%dof%d-seed%d' % (ctx.backend, model or 'x', state, shard, shards, ctx.seed)
    if os.environ.get('QA_SWEEP_TAG'):
        tag += '-' + os.environ['QA_SWEEP_TAG']
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


# ---- regressions found by the sweep -------------------------------------------------------------
def _objects_callback_maps():
    from qa.gb import mapdata
    out = []
    for const, a in sorted(mapdata.attributes().items()):
        path = mapdata.map_file(a['label'])
        if path and 'MAPCALLBACK_OBJECTS' in open(path, encoding='utf-8').read():
            out.append(const)
    return out


@qa_test(suites=('regression', 'map', 'full'), covers=('map.warps',), backends=('pyboy', 'sameboy'),
         models=('CGB-E', 'AGB'), provenance='injected: warp entry (MAPSETUP_WARP, as the `warp` script command and Fly do it)')
def violet_outskirts_house_warp_entry(ctx):
    """Regression: VioletOutskirtsHouseCaretaker (an objects callback) called showtext. MapSetupScript_Warp
    runs LoadMapObjects before EnableLCD, and waiting for a frame with the LCD off never ends (no VBlank
    interrupt, so DelayFrameHalt halts forever). Entered by a `warp`, the game froze on a white screen."""
    from qa.gb import fixtures as F
    from qa.gb.consts import map_ids
    from qa.gb.nav import Navigator
    g = ctx.boot(*sweep.fixture_for('default'))
    nav = Navigator(g)
    sg, sn = map_ids('VIOLET_OUTSKIRTS_HOUSE')
    F.teleport(g, sg, sn, 3, 7, settle=60)
    lcd_on = bool(g.read(0xff40) & 0x80)
    outcome = sweep.advance(nav, 2400)
    ctx.expect(lcd_on, 'the LCD is still off 60 frames after the warp (a callback is waiting for a frame)')
    ctx.expect(outcome == 'ok' and F.where(g)[:2] == (sg, sn),
               'control did not return after entering by warp: %s at %s, %s' % (outcome, F.where(g), g.where()))
    flag = C['EVENT_TEMPORARY_UNTIL_MAP_RELOAD_3']
    shown = g.read(g.sym['wEventFlags'][1] + (flag >> 3), 1) >> (flag & 7) & 1
    ctx.expect(shown, 'the "not alone" text did not run on entry')
    ctx.screenshot(g, 'violet_outskirts_house')


@qa_test(suites=('regression', 'map', 'full'), covers=('map.warps',), backends=('pyboy',),
         provenance='injected: warp entry into every map that declares an objects callback')
def objects_callbacks_survive_warp_entry(ctx):
    """Class check behind violet_outskirts_house_warp_entry: after a warp entry the LCD must be on, whatever
    the map's objects callback does (it runs while the LCD is still off in MapSetupScript_Warp)."""
    from qa.gb import fixtures as F
    from qa.gb.consts import map_ids
    from qa.gb.nav import Navigator
    g = ctx.boot(*sweep.fixture_for('default'))
    base = g.snap()
    maps = _objects_callback_maps()
    bad = []
    for const in maps:
        g.unsnap(base)
        sg, sn = map_ids(const)
        F.teleport(g, sg, sn, 2, 2, settle=240)
        if not g.read(0xff40) & 0x80:
            bad.append(const)
    ctx.note('%d maps with an objects callback entered by warp' % len(maps))
    ctx.expect(not bad, 'LCD still off 240 frames after a warp entry (a callback waits for a frame): %s' % bad)


@qa_test(suites=('regression', 'battle', 'full'), covers=(), backends=('pyboy',),
         provenance='harness regression: party memory edited directly')
def autobattle_party_flags(ctx):
    """Regression: the battle policy treated wPartyMonN's EXTSPECIES bit (0x20, species above 255, e.g. Cursola)
    as an egg, so it never switched to such a Pokemon and kept choosing a fainted one ('There's no will to
    battle!') until the 36000 frame limit. IS_EGG_MASK is 0x40."""
    from qa.gb import autobattle, fixtures as F
    g = ctx.boot(*sweep.fixture_for('default'))
    F.give_mon(g, C['TOTODILE'], 10)
    stride = g.sym['wPartyMon2'][1] - g.sym['wPartyMon1'][1]
    base = g.sym['wPartyMon1IsEgg'][1]
    ctx.expect(g.rd('wPartyCount') >= 2, 'fixture has fewer than two Pokemon')
    cur = g.read(base + stride, 1)
    g.write(base + stride, cur | 0x20, 1)
    ctx.expect(autobattle.first_healthy(g, 0) == 1, 'a Pokemon with the extended-species bit was skipped as an egg')
    g.write(base + stride, (cur & ~0x20) | 0x40, 1)
    ctx.expect(autobattle.first_healthy(g, 0) is None, 'a real egg was offered as a replacement')
    g.write(base + stride, cur, 1)
