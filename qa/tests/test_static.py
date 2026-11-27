"""Static and unit-level checks: repository data, source patterns, memory layout.
No emulation of gameplay; the unit test calls one ROM routine directly."""
import os
import re
import subprocess
import sys

from qa.framework import qa_test
from qa.gb import mapdata
from qa.gb.consts import C
from qa.gb.emu import ROOT


def _util(ctx, args, label):
    r = subprocess.run([sys.executable] + args, cwd=ROOT, capture_output=True, text=True)
    ctx.note(f'{label}: ' + (r.stdout.strip().splitlines() or ['(no output)'])[-1])
    ctx.expect(r.returncode == 0, f'{label} failed:\n{r.stdout[-600:]}{r.stderr[-300:]}')


@qa_test(suites=('general', 'hardware', 'regression', 'full'), covers=('data.layout', 'save.sram_layout'),
         provenance='static: symbol file and map file of the built ROM')
def sram_layout_unchanged(ctx):
    _util(ctx, ['utils/sram_layout/check_sram_layout.py', ctx.rom[:-4] + '.sym'], 'SRAM layout guard')


@qa_test(suites=('general', 'full'), covers=('data.tables',), provenance='static: repository data')
def text_and_palette_tables(ctx):
    _util(ctx, ['utils/check_text_width.py'], 'text width')
    _util(ctx, ['utils/check_palette_tables.py'], 'palette tables')


@qa_test(suites=('general', 'hardware', 'full'), covers=('data.layout',), provenance='static: map file of the built ROM')
def memory_regions_within_hardware(ctx):
    """Every placed section must lie inside its hardware region; report the headroom."""
    sys.path.insert(0, os.path.join(ROOT, 'utils'))
    import memory_report as M
    banks = M.parse(ctx.rom[:-4] + '.map', rom_size=os.path.getsize(ctx.rom))
    worst = {}
    for (region, bank), info in banks.items():
        size = M.BANK_SIZE[region]
        ctx.expect(info['used'] <= size, f'{region} bank {bank} uses {info["used"]} of {size} bytes')
        worst[region] = min(worst.get(region, size), info['free'])
    ctx.note('smallest free space in any bank: ' + ', '.join(f'{k} {v} B' for k, v in sorted(worst.items())))
    wram0 = banks.get(('WRAM0', 0))
    if wram0:
        ctx.note(f'WRAM0 free {wram0["free"]} B (the 256-byte stack is part of WRAM0: stack headroom is not measured here)')


@qa_test(suites=('general', 'regression', 'full'), covers=('follower.static', 'data.maps'),
         provenance='static: maps/*.asm and engine/overworld/follower.asm')
def follower_slot_budget(ctx):
    """The follower is map object FOLLOWER_OBJECT (the last slot). A map with that many
    object events has no slot for it; CanHaveFollower must refuse exactly then, and
    no map may exceed the table."""
    follower, total = C['FOLLOWER_OBJECT'], C['NUM_OBJECTS']
    counts = {}
    for const, m in mapdata.attributes().items():
        counts[m['label']] = mapdata.parse_map(m['label'])['objects']
    over = {k: v for k, v in counts.items() if v >= total}
    full = {k: v for k, v in counts.items() if v >= follower}
    tight = {k: v for k, v in counts.items() if v == follower - 1}
    ctx.expect(not over, f'maps with {total}+ object events overflow the object table: {over}')
    ctx.note(f'maps with no follower slot ({follower}+ events): {full}; one event from full: {tight}')
    src = open(os.path.join(ROOT, 'engine/overworld/follower.asm')).read()
    m = re.search(r'CanHaveFollower:.*?cp (FOLLOWER_OBJECT[^\n;]*?)\s*\n\s*jr nc, \.no', src, re.S)
    ctx.expect(m and m.group(1).strip() == 'FOLLOWER_OBJECT',
               'CanHaveFollower must refuse at FOLLOWER_OBJECT events, not FOLLOWER_OBJECT - 1 (the Lake of Rage off-by-one)')


@qa_test(suites=('general', 'battle', 'regression', 'full'), covers=('battle.hud', 'battle.switching'),
         provenance='static: engine/battle/core.asm')
def party_menu_users_restore_enemy_pic(ctx):
    """The party menu draws over the enemy's pic tiles (vTiles2 $00-$0f). Every routine
    that opens it in battle must reload the pic (GetMonFrontpic) before returning to
    the battle screen. OfferSwitch is exempt: the enemy is sent out again straight after."""
    exempt = {'OfferSwitch': 'the enemy sends out a new Pokemon (loading its pic) right after'}
    text = open(os.path.join(ROOT, 'engine/battle/core.asm')).read().split('\n')
    label, start = None, 0
    spans = []
    for i, line in enumerate(text):
        m = re.match(r'^([A-Za-z_]\w*)::?', line)
        if m:
            if label:
                spans.append((label, start, i))
            label, start = m.group(1), i
    spans.append((label, start, len(text)))
    users = []
    for name, a, b in spans:
        body = '\n'.join(text[a:b])
        if re.search(r'^\s+call SetUpBattlePartyMenu(_NoLoop)?\b', body, re.M) and name not in ('SetUpBattlePartyMenu_NoLoop',):
            users.append(name)
            if name in exempt:
                continue
            ctx.expect('GetMonFrontpic' in body or 'jmp BattleMenu' in body or 'BattleMenuPKMN' in body,
                       f'{name} opens the party menu in battle but never reloads the enemy pic')
    ctx.note('routines that open the in-battle party menu: ' + ', '.join(users))


@qa_test(suites=('general', 'regression', 'hardware', 'full'), covers=('follower', 'hw.memory_guard'), backends=('pyboy',),
         provenance='unit: calls ApplyMovementToFollower directly (injected), reads memory')
def follower_queue_cannot_overrun(ctx):
    """wFollowMovementQueue is 5 bytes and wObjectStructs follows it. Queue many steps
    with no follower consuming them: the queue must stop at its capacity and
    wPlayerStruct must be untouched."""
    from qa.gb.emu import Game
    g = ctx.game()
    g.tick(900)
    queue = g.sym['wFollowMovementQueue'][1]
    struct = g.sym['wPlayerStruct'][1]
    ctx.expect(struct == queue + 5, 'layout assumption changed: wPlayerStruct no longer directly follows the 5-byte queue; re-audit the bound')
    before = bytes(g.mem[1, struct + i] for i in range(16))
    g.mem[0xff70] = 1                       # WRAMX bank 1, where these variables live
    g.wr('wObjectFollow_Leader', 0)
    g.wr('wObjectFollow_Follower', 1)
    g.wr('wFollowerMovementQueueLength', 255)
    g.wr('wFollowInSync', 0)
    g.mem[g.sym['hMapObjectIndexBuffer'][1]] = 0
    for _ in range(40):
        g.call('ApplyMovementToFollower', a=C['movement_step_up'])
    after = bytes(g.mem[1, struct + i] for i in range(16))
    ctx.expect(before == after, 'queueing 40 steps changed wPlayerStruct: %s -> %s' % (before.hex(), after.hex()))
    qlen = g.rd('wFollowerMovementQueueLength')
    ctx.expect(qlen <= 4, f'queue length {qlen} exceeds capacity')


@qa_test(suites=('general', 'regression', 'hardware', 'full'), covers=('data.maps', 'hw.memory_guard'),
         provenance='static: maps/*.asm (checkout, not the ROM)')
def map_callbacks_end_with_endcallback(ctx):
    """A map callback runs via CallCallback, which saves the caller's script position. `end`
    pops that position and resumes executing from it (stale data: on a GBA it ran data as
    code and locked up). Every path out of a callback must use endcallback."""
    from qa.gb import scriptlint
    bad = scriptlint.lint_all()
    for fname, probs in bad.items():
        for kind, label, line in probs:
            ctx.expect(False, f'maps/{fname}:{line}: {kind} callback {label} reaches `end`, not `endcallback`')
    ctx.note('callbacks scanned in %d map files' % len(__import__('glob').glob(os.path.join(ROOT, 'maps', '*.asm'))))
