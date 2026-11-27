"""Save integrity: round trip, a corrupted primary save, and power cuts during a save.

State compared after Continue: map and position, party species/levels, and one
event flag the test sets before saving (so 'old' and 'new' saves are distinguishable).
"""
from qa.framework import qa_test
from qa.gb import fixtures as F, saves
from qa.gb.consts import C
from qa.tests.test_connections import build

PROVENANCE = 'boot/Continue: gameplay input; the save routine is called directly (injected); SRAM edits are injected'
FLAG = 'EVENT_GOT_TOTODILE' if False else None


def state_of(g):
    n = g.rd('wPartyCount')
    species = tuple(g.rd('wPartyMon1Species', i * (g.sym['wPartyMon2'][1] - g.sym['wPartyMon1'][1])) for i in range(n))
    level = tuple(g.rd('wPartyMon1Level', i * (g.sym['wPartyMon2'][1] - g.sym['wPartyMon1'][1])) for i in range(n))
    return {'where': F.where(g), 'party': (species, level), 'flag': saves_flag(g)}


def saves_flag(g):
    n = C['EVENT_LAKE_OF_RAGE_ELIXIR']        # any ordinary event flag: set by the test, not by play here
    return bool(g.rd('wEventFlags', n >> 3) >> (n & 7) & 1)


def continue_from(ctx, sram, expect_where, label):
    """Boot a fresh game from SRAM bytes and Continue. Returns state or a string."""
    import os
    path = os.path.join(ctx.out, label + '.sav')
    open(path, 'wb').write(sram)
    g = ctx.game(sav=path)
    try:
        saves.boot_continue(g, expect_where, max_presses=40)
    except TimeoutError:
        return 'no-continue'
    return state_of(g)


@qa_test(suites=('general', 'full'), covers=('save.roundtrip',), backends=('pyboy', 'sameboy'), provenance=PROVENANCE)
def save_round_trip(ctx):
    g = ctx.boot('connections_base', build)
    before = state_of(g)
    g.call('SilentGameSave')
    sram = saves.dump_sram(g) if hasattr(g, 'mem') else g.save_sram()
    after = continue_from(ctx, sram, before['where'], 'roundtrip')
    ctx.note('before %r' % (before,))
    ctx.expect(after == before, 'state after save + Continue differs: %r' % (after,))


@qa_test(suites=('general', 'full'), covers=('save.roundtrip',), backends=('sameboy',), provenance=PROVENANCE, timeout=900)
def corrupted_primary_save_recovers_from_backup(ctx):
    """Flip bytes in the primary save: Continue must load the identical state from the
    backup, or refuse to continue. Loading anything else would be silent data loss."""
    g = ctx.boot('connections_base', build)
    before = state_of(g)
    g.call('SilentGameSave')
    sram = bytearray(g.save_sram())
    primary = 1 * 0x2000 + (g.sym['sPlayerData'][1] - 0xa000)
    results = {}
    for off in (0x10, 0x200, 0x500):
        bad = bytearray(sram)
        bad[primary + off] ^= 0xff
        results['primary+%#x' % off] = continue_from(ctx, bytes(bad), before['where'], 'corrupt_%x' % off)
    ctx.note('outcomes: %r' % (results,))
    for k, v in results.items():
        ctx.expect(v == before or v == 'no-continue', f'corrupting {k}: Continue loaded a different state: {v!r}')
    recovered = sum(1 for v in results.values() if v == before)
    ctx.note(f'{recovered} of {len(results)} corruptions recovered from the backup; the rest refused to continue')


@qa_test(suites=('full', 'hardware'), covers=('save.roundtrip', 'hw.memory_guard'), backends=('sameboy',),
         provenance=PROVENANCE + '; power cut = SRAM snapshot taken just before the Nth cartridge-RAM write',
         timeout=1800)
def power_cut_during_save(ctx):
    """Cut power at many points inside a save (an SRAM snapshot before the Nth write), then
    boot each snapshot. Every one must load the OLD state or the NEW state intact;
    anything else is corruption. Emulated: real hardware is untested (see the report)."""
    g = ctx.boot('connections_base', build)
    old = state_of(g)
    old_sram = g.save_sram()
    # the NEW state differs by one event flag and one step of position
    n = C['EVENT_LAKE_OF_RAGE_ELIXIR']
    g.wr('wEventFlags', g.rd('wEventFlags', n >> 3) | 1 << (n & 7), n >> 3)
    new_where = F.where(g)
    snaps, writes = [], [0]
    cuts = set()

    def count_pass(game, addr, oldv, newv, pc):
        writes[0] += 1
    # pass 1: count the cartridge RAM writes a save performs, from a throwaway copy of the state
    g.write_watch(0xa000, 0xc000, count_pass)
    g.call('SilentGameSave')
    total = writes[0]
    ctx.note(f'a save performs {total} cartridge-RAM writes')
    ctx.expect(total > 100, 'implausibly few SRAM writes during a save')
    # pass 2: boot again, redo the same change, and snapshot before chosen writes
    g2 = ctx.boot('connections_base', build)
    g2.wr('wEventFlags', g2.rd('wEventFlags', n >> 3) | 1 << (n & 7), n >> 3)
    want = sorted({int(total * k / 40) for k in range(41)} | {0, 1, 2, total - 2, total - 1})
    seen = [0]

    def snap_pass(game, addr, oldv, newv, pc):
        if seen[0] in want:
            snaps.append((seen[0], game.save_sram(), game.where(pc)))
        seen[0] += 1
    g2.write_watch(0xa000, 0xc000, snap_pass)
    g2.call('SilentGameSave')
    new_sram = g2.save_sram()
    bad = []
    outcomes = {}
    for idx, sram, where in snaps:
        st = continue_from(ctx, sram, old['where'], f'cut_{idx}')
        kind = 'old' if st == old else ('new' if isinstance(st, dict) and st['party'] == old['party'] and st['flag'] and st['where'] == old['where'] else st)
        outcomes.setdefault(str(kind)[:40], []).append((idx, where))
        if not (kind in ('old', 'new') or kind == 'no-continue'):
            bad.append(f'cut before write {idx} (in {where}): loaded {st!r}')
    ctx.note('outcomes by kind: ' + ', '.join(f'{k}: {len(v)}' for k, v in outcomes.items()))
    for k, v in outcomes.items():
        if k == 'no-continue':
            ctx.note('Continue unavailable (the game offered New Game only) for cuts before write ' + ', '.join(str(i) for i, _ in v))
    for b in bad:
        ctx.expect(False, b)
    ctx.expect(not outcomes.get('no-continue'), 'a power cut during a save made Continue unavailable: the save was lost (cuts: %s)' %
               ', '.join(str(i) for i, _ in outcomes.get('no-continue', [])))
