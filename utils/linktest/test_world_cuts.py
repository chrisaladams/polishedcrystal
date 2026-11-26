#!/usr/bin/env python3
"""Cut the cable at each commit boundary of a linked World Championship
session, then link up cleanly, and check the two cartridges end up agreeing.

A session (Special_WorldLinkSession) is two exchanges and a commit: what
each side has (session bytes 1-55, counted on side A), then the plan each
worked out with the other's check echoed (56-118, its message data ending
near byte 110 and padding after), then both commit and save if, and only if,
each got the other's whole message and the plans agree. A cut in the second
exchange is the dangerous one: one side may get everything and commit while
the other doesn't. That is what the next session's join plans are for.

Each case unplugs the cable as one session byte starts (linktest.py
--unplug-desk), either pulled out (600 frames, past every timeout) or bumped
(4 frames), then runs a clean session from the cartridges the cut left:

- registration (two unregistered saves): the cut session either registers
  both in one bracket or leaves at least one side able to join; after the
  clean session both are in the same bracket, one in each half;
- results (both registered, side A has won its quarterfinal offline): after
  the clean session both are in the same bracket, side B has heard A's
  result, and A's own result is unchanged (a cut never loses or repeats it).

Every session must end at the desk (registered, synced or interrupted),
never stuck, and a cut session never leaves two different brackets.

Usage (from the repository root, after make):
  PYTHONPATH=/tmp/pyboy_cable python3 utils/linktest/test_world_cuts.py A.sav B.sav --out DIR [--quick]
"""
import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from test_world_link import Indigo, link, record, QF, SF  # noqa: E402

PULLED, BUMPED = 600, 4
# session bytes: the first exchange's start, middle and end; the second's
# start and middle; its last data bytes; the padding after; the last byte
REGISTER_CUTS = [(1, PULLED), (28, PULLED), (55, PULLED), (56, PULLED), (85, PULLED), (109, PULLED),
                 (110, PULLED), (111, PULLED), (118, PULLED), (28, BUMPED), (85, BUMPED), (111, BUMPED)]
RESULT_CUTS = [(56, PULLED), (85, PULLED), (110, PULLED), (111, PULLED), (118, PULLED), (110, BUMPED)]
QUICK = {(56, PULLED), (110, PULLED), (111, PULLED), (85, BUMPED)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('save_a')
    ap.add_argument('save_b')
    ap.add_argument('--out', default='world_cuts_out')
    ap.add_argument('--quick', action='store_true', help='four cut points per scenario')
    ap.add_argument('--jobs', type=int, default=2)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    fails = []

    def step(name):
        d = os.path.join(args.out, name)
        os.makedirs(d, exist_ok=True)
        return d

    def at_desk(r):
        return r in ('desk: registered', 'desk: synced', 'desk: interrupted')

    def same_bracket(a, b):
        ra, rb = record(a), record(b)
        return ra and rb and ra['id'] == rb['id'] and ra['seed'] == rb['seed'] and {ra['half'], rb['half']} == {0, 1}

    def case(name, a, b, cut, after):
        n, frames = cut
        where = f'{name} byte {n} ({"pulled" if frames == PULLED else "bumped"})'
        ra, rb, ca, cb = link(a, b, step(f'{name}_{n}_{frames}'), '--unplug-desk', f'{n},{frames}', seconds=300)
        problems = []
        if not (at_desk(ra) and at_desk(rb)):
            problems.append(f'the cut session: {ra} / {rb}')
        ka, kb = record(ca), record(cb)
        if ka and kb and ka['id'] != kb['id']:
            problems.append('the cut session left two different brackets')
        ra2, rb2, a2, b2 = link(ca, cb, step(f'{name}_{n}_{frames}_clean'), seconds=300)
        if not (ra2.startswith('desk:') and rb2.startswith('desk:') and 'interrupted' not in ra2 + rb2):
            problems.append(f'the clean session after: {ra2} / {rb2}')
        if not same_bracket(a2, b2):
            problems.append(f'not one bracket after the clean session: {record(a2)} {record(b2)}')
        problems += after(ka, kb, a2, b2)
        return where, f'cut: {ra} / {rb}; clean: {ra2} / {rb2}', problems

    jobs = []
    pick = (lambda cuts: [c for c in cuts if c in QUICK]) if args.quick else (lambda cuts: cuts)

    # registration
    for cut in pick(REGISTER_CUTS):
        jobs.append(('register', args.save_a, args.save_b, cut, lambda ka, kb, a2, b2: []))

    # results: register cleanly, A wins its quarterfinal offline (saved)
    ra, rb, a, b = link(args.save_a, args.save_b, step('results_register'), seconds=300)
    if (ra, rb) != ('desk: registered', 'desk: registered') or not same_bracket(a, b):
        fails.append(('results', f'the clean registration: {ra} / {rb}'))
    else:
        ind = Indigo(a)
        ind.rounds([True], 'results A')
        ind.game_save()
        a = ind.save(os.path.join(args.out, 'results_A_won.sav'))
        if record(a)['status'] != SF:
            fails.append(('results', f"A's quarterfinal win not recorded: {record(a)}"))

        def heard(ka, kb, a2, b2):
            got = []
            if record(a2)['status'] != SF:
                got.append(f"A's own result changed: {record(a2)['status']}")
            if record(b2)['status'] != QF:
                got.append(f"B's own result changed: {record(b2)['status']}")
            if record(b2)['partner_status'] != SF:
                got.append(f"B didn't hear A's result: {record(b2)['partner_status']}")
            return got

        for cut in pick(RESULT_CUTS):
            jobs.append(('results', a, b, cut, heard))

    with ThreadPoolExecutor(args.jobs) as pool:
        for where, said, problems in pool.map(lambda j: case(*j), jobs):
            print(f'{where}: {said}' + (' -- ' + '; '.join(problems) if problems else ''))
            fails += [(where, p) for p in problems]

    print(f'{len(fails)} problems')
    for where, what in fails:
        print('  FAIL', where, '-', what)
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
