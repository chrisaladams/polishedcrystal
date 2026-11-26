#!/usr/bin/env python3
"""Check how the linked World Championship's session decides what to do
(WorldLinkPlan, engine/link/world_link.asm) from the two desk messages, on
one cartridge (PyBoy, no cable): the plan is worked out from what this side
has (wWorldLinkMine) and what the other sent (wWorldLinkTheirs), so every
case, including corrupt or hostile messages, can be given directly.

Both sides only change anything when their plans agree (the echo exchange),
so "no plan" (0) for a bad message means neither side changes:

- the normal cases: neither in a bracket (register), the same bracket
  (sync, open or one side closed), a registration one side didn't keep
  (join, named the same way on both sides: the clock side's view);
- injected values out of range (state, bracket half, status), each alone:
  no plan;
- a bracket that isn't the same one (ID, draw seed, the same half, either
  partner ID): a mismatch, never a sync;
- a closed bracket against no bracket: a new one (register), not a sync.

Usage (from the repository root, after make):
  python3 utils/linktest/test_world_plan.py SAVE.sav
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'anime_events'))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_friend_records import Caller  # noqa: E402
from test_wild_mons import Game, rgbasm_values  # noqa: E402


def world_link_constants():
    """The message layout (WLMSG_*), states (WLSTATE_*) and plans (WLPLAN_*),
    from engine/link/world_link.asm."""
    src = open(os.path.join(ROOT, 'engine', 'link', 'world_link.asm')).read()
    K = rgbasm_values(['PLAYER_NAME_LENGTH', 'WORLD_LINK_MESSAGE_LENGTH', 'WORLDLINK_QUARTERFINAL',
                       'WORLDLINK_SEMIFINAL', 'WORLDLINK_RUNNER_UP', 'USING_INTERNAL_CLOCK',
                       'USING_EXTERNAL_CLOCK'], None)
    block = src[src.index('rsreset'):src.index('DEF WLMSG_CHECK')]
    offset = 0
    for name, size in re.findall(r'DEF (WLMSG_\w+)[ \t]+rb[ \t]*([^\n;]*)', block):
        K[name] = offset
        size = size.split(';')[0].strip()
        offset += 1 if not size else (K[size] if size in K else int(size))
    states = src[src.index('const WLSTATE_NONE') - 20:]
    for n, name in enumerate(re.findall(r'const (WLSTATE_\w+)', states)[:3]):
        K[name] = n
    for name, value in re.findall(r'DEF (WLPLAN_\w+)\s+EQU (\d+)', src):
        K[name] = int(value)
    return K


K = world_link_constants()
NAMES = {v: k for k, v in K.items() if k.startswith('WLPLAN_')}
NAMES[0] = 'no plan'


def message(state, bracket=0x4321, seed=0x1234, half=0, me=0x1111, partner=0x2222,
            status=None):
    m = [0] * K['WORLD_LINK_MESSAGE_LENGTH']
    m[K['WLMSG_STATE']] = state
    if state != K['WLSTATE_NONE']:
        m[K['WLMSG_ID']:K['WLMSG_ID'] + 2] = [bracket & 0xff, bracket >> 8]
        m[K['WLMSG_SEED']:K['WLMSG_SEED'] + 2] = [seed & 0xff, seed >> 8]
        m[K['WLMSG_HALF']] = half
        m[K['WLMSG_PARTNER_ID']:K['WLMSG_PARTNER_ID'] + 2] = [partner & 0xff, partner >> 8]
        m[K['WLMSG_STATUS']] = K['WORLDLINK_QUARTERFINAL'] if status is None else status
    m[K['WLMSG_MY_ID']:K['WLMSG_MY_ID'] + 2] = [me & 0xff, me >> 8]
    return m


def main():
    g = Game(open(sys.argv[1], 'rb').read())
    g.boot()
    caller = Caller(g)
    fails = []
    OPEN, CLOSED, NONE = K['WLSTATE_OPEN'], K['WLSTATE_CLOSED'], K['WLSTATE_NONE']
    status_addr = g.sym['hSerialConnectionStatus'][1]

    def plan(mine, theirs, clock='internal'):
        for k in range(K['WORLD_LINK_MESSAGE_LENGTH']):
            g.wr('wWorldLinkMine', mine[k], k)
            g.wr('wWorldLinkTheirs', theirs[k], k)
        g.m[status_addr] = K['USING_INTERNAL_CLOCK' if clock == 'internal' else 'USING_EXTERNAL_CLOCK']
        caller.call('WorldLinkPlan')
        return caller.out['A']

    def expect(what, mine, theirs, want, clock='internal'):
        got = plan(mine, theirs, clock)
        if got != K[want] if want != 'no plan' else got != 0:
            fails.append(f'{what}: {NAMES.get(got, got)}, not {want}')

    me_a = dict(me=0x1111, partner=0x2222, half=0)  # this side: half 0
    me_b = dict(me=0x2222, partner=0x1111, half=1)  # the partner: half 1

    # the normal cases
    expect('neither in a bracket', message(NONE, me=0x1111), message(NONE, me=0x2222), 'WLPLAN_REGISTER')
    expect('the same bracket, both open', message(OPEN, **me_a), message(OPEN, **me_b), 'WLPLAN_SYNC')
    expect('the same bracket, mine closed', message(CLOSED, **me_a), message(OPEN, **me_b), 'WLPLAN_SYNC')
    expect('the same bracket, theirs closed', message(OPEN, **me_a), message(CLOSED, **me_b), 'WLPLAN_SYNC')
    expect('both closed', message(CLOSED, **me_a), message(CLOSED, **me_b), 'WLPLAN_REGISTER')
    expect('a closed one against none', message(CLOSED, **me_a), message(NONE, me=0x2222), 'WLPLAN_REGISTER')
    # a registration one side didn't keep, named as the clock side sees it
    expect('theirs, I am their partner (clock side)', message(NONE, me=0x1111),
           message(OPEN, **me_b), 'WLPLAN_JOIN_THEIRS')
    expect('theirs, I am their partner (other side)', message(NONE, me=0x1111),
           message(OPEN, **me_b), 'WLPLAN_JOIN_MINE', clock='external')
    expect('mine, they are my partner', message(OPEN, **me_a), message(NONE, me=0x2222), 'WLPLAN_JOIN_MINE')
    expect('mine, someone else', message(OPEN, **me_a), message(NONE, me=0x3333), 'WLPLAN_MISMATCH')

    # values out of range in what the other sent: no plan
    expect('their state out of range', message(OPEN, **me_a), [CLOSED + 1] + message(OPEN, **me_b)[1:],
           'no plan')
    expect('their state $ff', message(NONE, me=0x1111), [0xff] + message(NONE, me=0x2222)[1:], 'no plan')
    bad_half = message(OPEN, **me_b)
    bad_half[K['WLMSG_HALF']] = 2
    expect('their half out of range', message(OPEN, **me_a), bad_half, 'no plan')
    expect('their status out of range', message(OPEN, **me_a),
           message(OPEN, status=K['WORLDLINK_RUNNER_UP'] + 1, **me_b), 'no plan')
    expect('their status $ff', message(OPEN, **me_a), message(OPEN, status=0xff, **me_b), 'no plan')
    # (no bracket: the rest of their message isn't read)
    junk = message(NONE, me=0x2222)
    junk[K['WLMSG_HALF']], junk[K['WLMSG_STATUS']] = 0x77, 0x99
    expect('no bracket, junk after the state', message(NONE, me=0x1111), junk, 'WLPLAN_REGISTER')

    # not the same bracket: a mismatch, never a sync
    for what, change in (('another bracket ID', dict(bracket=0x4322)), ('another draw seed', dict(seed=0x1235)),
                         ('the same half', dict(half=0)), ('another partner ID', dict(partner=0x3333)),
                         ('another player', dict(me=0x3333))):
        theirs = message(OPEN, **{**me_b, **change})
        expect(f'both open, {what}', message(OPEN, **me_a), theirs, 'WLPLAN_MISMATCH')

    g.pb.stop(save=False)
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
