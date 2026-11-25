#!/usr/bin/env python3
"""Check the linked World Championship end to end, from two saves.

Link sessions run over the virtual cable (linktest.py, with the cable module
built: see README.md); the rounds against the visiting trainers are played
at the Indigo Plateau on each cartridge between them, and every session
starts from the cartridges the last one left. The scenarios:

- both finalists: register, both win their quarterfinal and semifinal, link
  up: the final is a link battle; one is champion and the other runner-up,
  and the Indigo Plateau's desk gives the champion the prize and closes
  both brackets;
- one finalist: one wins through, the other loses a quarterfinal; linking
  up tells each how the other did (twice: a second session changes
  nothing more), and the finalist plays the other half's finalist at the
  Indigo Plateau, while the other is told to wait;
- both out: they hear so, and both brackets close;
- a session with heavy noise on the cable either changes nothing or leaves
  the two cartridges agreeing after a clean session, and a different clock
  on one Game Boy doesn't matter.

Every opponent is checked against the draw worked out here from the shared
seed, as WorldLinkDraw makes it.

Usage (from the repository root, after make):
  PYTHONPATH=/tmp/pyboy_cable python3 utils/linktest/test_world_link.py A.sav B.sav --out DIR
"""
import argparse
import io
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'utils', 'wild_mons'))
from test_wild_mons import Game, rgbasm_values  # noqa: E402

RECORD = 0x11d5  # sWorldLink's offset in the save (SRAM bank 0, $b1d5)
QF, SF, FINAL, OUT_QF, OUT_SF, CHAMPION, RUNNER_UP = range(7)
UNKNOWN = 0xff
fails = []


def record(sav):
    r = open(sav, 'rb').read()[RECORD:RECORD + 20]
    if r[:2] != b'WC':
        return None
    return {'id': r[3:5], 'seed': r[5] | r[6] << 8, 'half': r[7], 'partner': r[8:10],
            'name': r[10:18], 'status': r[18], 'partner_status': r[19]}


def draw(seed):
    order = list(range(1, 8))
    s = seed
    for c in range(6, 0, -1):
        s = (s * 5 + 1) & 0xffff
        j = (s >> 8) % (c + 1)
        order[c], order[j] = order[j], order[c]
    return [0] + order[:3] + [0] + order[3:6]


def opponent(rec, round_):
    b, me = draw(rec['seed']), 4 * rec['half']
    other = me ^ 4
    if round_ == QF:
        return b[me + 1]
    if round_ == SF:
        return max(b[me + 2], b[me + 3])
    finalist = max(b[other + 2], b[other + 3])
    if rec['partner_status'] == OUT_QF:
        finalist = max(finalist, b[other + 1])
    return finalist


def link(a, b, out, *extra):
    cmd = [sys.executable, os.path.join(ROOT, 'utils', 'linktest', 'linktest.py'), a, b,
           '--rules', 'world', '--turns', '400', '--seconds', '900', '--out', out, *extra]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=1300)
    got = dict(re.findall(r'^([AB]): (.*?) \(', res.stdout, re.M))
    return got.get('A', '?'), got.get('B', '?'), os.path.join(out, 'A.sav'), os.path.join(out, 'B.sav')


class Indigo:
    """One cartridge at the Indigo Plateau's World Championship desk."""

    def __init__(self, sav):
        self.K = rgbasm_values(['GROUP_INDIGO_PLATEAU_POKECENTER_1F', 'MAP_INDIGO_PLATEAU_POKECENTER_1F',
                                'EVENT_GOT_MYSTICTICKET_FROM_RED', 'PARTYMON_STRUCT_LENGTH', 'ABILITYPATCH',
                                'EVENT_WORLD_CUP_PRIZE_PENDING', 'BOTTLE_CAP'], None)
        src = open(os.path.join(ROOT, 'engine', 'events', 'world_cup.asm')).read()
        table = src[src.index('WorldCupTrainers:'):src.index('assert_table_length', src.index('WorldCupTrainers:'))]
        names = re.findall(r'world_cup_trainer (\w+), (\w+),', table)
        values = rgbasm_values(sorted({n for pair in names for n in pair if not n.isdigit()}), None)
        self.trainers = [(values[c], int(i) if i.isdigit() else values[i]) for c, i in names]
        self.sav = sav
        self.g = Game(open(sav, 'rb').read())
        self.g.boot()
        # (saved at the battle desk: the boot's A presses talk to its
        # receptionist, so say no first)
        for _ in range(8):
            self.g.press('b', 30)
        self.g.tick(60)
        n = self.K['EVENT_GOT_MYSTICTICKET_FROM_RED']
        self.g.wr('wEventFlags', self.g.rd('wEventFlags', n // 8) | 1 << (n % 8), n // 8)

    def talk(self):
        g = self.g
        g.warp(self.K['GROUP_INDIGO_PLATEAU_POKECENTER_1F'], self.K['MAP_INDIGO_PLATEAU_POKECENTER_1F'], 6, 12)
        g.tick(30)
        g.face('left')
        g.tick(10)

    def battle(self, win, expect, where):
        g, L = self.g, self.K['PARTYMON_STRUCT_LENGTH']
        for _ in range(16):
            g.press('a', 40)
            if g.rd('wBattleMode'):
                break
        if not g.rd('wBattleMode'):
            fails.append((where, 'no battle'))
            return
        want = self.trainers[expect - 1]
        got = (g.rd('wOtherTrainerClass'), g.rd('wOtherTrainerID'))
        if got != want:
            fails.append((where, f'battled {got}, not {want} (draw slot value {expect})'))
        # end it the way test_orange_league.py does: when the game resolves a
        # faint, the losing side's whole team is down (items can't heal it)
        party, active = ('wOTParty', 'wEnemyMonHP') if win else ('wParty', 'wBattleMonHP')

        def faint_team(_):
            for k in range(g.rd(party + 'Count')):
                g.wr(party + 'Mon1HP', 0, k * L)
                g.wr(party + 'Mon1HP', 0, k * L + 1)
            g.wr(active, 0)
            g.wr(active, 0, 1)
            if win:
                g.wr('wBattleMonHP', g.rd('wBattleMonMaxHP'))
                g.wr('wBattleMonHP', g.rd('wBattleMonMaxHP', 1), 1)

        g.tick(300)
        faint_team(None)
        g.pb.hook_register(*g.sym['ResolveFaints'], faint_team, None)
        try:
            for _ in range(400):
                if not g.rd('wBattleMode'):
                    break
                g.press('a', 30)
        finally:
            g.pb.hook_deregister(*g.sym['ResolveFaints'])
        if g.rd('wBattleMode'):
            fails.append((where, 'the battle did not finish'))

    def settle(self):
        g = self.g
        for _ in range(60):
            g.tick(30)
            g.press('b', 10)
            if not g.rd('wScriptRunning') and not g.rd('wBattleMode'):
                g.tick(60)
                if not g.rd('wScriptRunning'):
                    return

    def rounds(self, results, where):
        """Play rounds in a row (True: win), checking each opponent."""
        self.talk()
        for k, win in enumerate(results):
            rec = self.record()
            self.battle(win, opponent(rec, rec['status']), f'{where} round {k + 1}')
            self.g.tick(200)
        self.settle()

    def visit(self, answer='a'):
        """Talk to the desk once, through whatever it says (answering any
        question with `answer`)."""
        self.talk()
        self.g.press('a', 40)
        for _ in range(12):
            self.g.press(answer, 40)
        self.settle()

    def record(self):
        ram = bytes(self.g.m[0, 0xb1d5 + i] for i in range(20))
        tmp = io.BytesIO(b'\0' * RECORD + ram)
        tmp.seek(0)
        path = self.sav + '.tmp'
        open(path, 'wb').write(tmp.getvalue())
        return record(path)

    def items(self, item):
        g = self.g
        for pocket in ('Items', 'Medicine', 'Balls'):
            for i in range(g.rd('wNum' + pocket)):
                if g.rd('w' + pocket, 2 * i) == self.K[item]:
                    return g.rd('w' + pocket, 2 * i + 1)
        return 0

    def save(self, path):
        g = self.g
        ram = bytes(g.m[bank, 0xa000 + i] for bank in range(4) for i in range(0x2000))
        tail = open(self.sav, 'rb').read()[len(ram):]
        open(path, 'wb').write(ram + tail)
        g.pb.stop(save=False)
        return path


def check(cond, where, what):
    if not cond:
        fails.append((where, what))


def registered(a, b, where):
    ra, rb = record(a), record(b)
    check(ra and rb, where, f'not both registered: {ra} {rb}')
    if ra and rb:
        check(ra['id'] == rb['id'] and ra['seed'] == rb['seed'], where, 'different brackets')
        check({ra['half'], rb['half']} == {0, 1}, where, f'halves {ra["half"]} {rb["half"]}')
    return ra, rb


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('save_a')
    ap.add_argument('save_b')
    ap.add_argument('--out', default='world_link_out')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    def step(name):
        d = os.path.join(args.out, name)
        os.makedirs(d, exist_ok=True)
        return d

    def offline(sav, results, name):
        ind = Indigo(sav)
        ind.rounds(results, name)
        return ind.save(os.path.join(args.out, name + '.sav'))

    # both finalists (with B's clock on another day)
    ra_, rb_, a, b = link(args.save_a, args.save_b, step('both_register'), '--day-b', '77')
    check((ra_, rb_) == ('desk: registered', 'desk: registered'), 'both', f'registration: {ra_} / {rb_}')
    registered(a, b, 'both')
    a = offline(a, [True, True], 'both_A')
    b = offline(b, [True, True], 'both_B')
    check(record(a)['status'] == FINAL and record(b)['status'] == FINAL, 'both', 'not both qualified')
    ra_, rb_, a, b = link(a, b, step('both_final'))
    check(ra_.startswith('battle over') and rb_.startswith('battle over'), 'both', f'final: {ra_} / {rb_}')
    sa, sb = record(a)['status'], record(b)['status']
    check({sa, sb} == {CHAMPION, RUNNER_UP}, 'both', f'after the final: {sa} {sb}')
    check(record(a)['partner_status'] == sb and record(b)['partner_status'] == sa, 'both',
          'each did not hear the other\'s result')
    champ = a if sa == CHAMPION else b
    ind = Indigo(champ)
    prizes = ind.items('ABILITYPATCH') + ind.items('BOTTLE_CAP')
    ind.visit()
    check(ind.record() is None, 'both', "the champion's bracket did not close")
    check(ind.items('ABILITYPATCH') + ind.items('BOTTLE_CAP') == prizes + 1, 'both', 'no prize for the champion')
    ind.save(os.path.join(args.out, 'both_champion_done.sav'))

    # one finalist; the sync session twice
    ra_, rb_, a, b = link(args.save_a, args.save_b, step('one_register'))
    registered(a, b, 'one')
    a = offline(a, [True, True], 'one_A')
    b = offline(b, [False], 'one_B')
    check(record(b)['status'] == OUT_QF, 'one', f'B status {record(b)["status"]}')
    ra_, rb_, a, b = link(a, b, step('one_sync'))
    check((ra_, rb_) == ('desk: synced', 'desk: synced'), 'one', f'sync: {ra_} / {rb_}')
    check(record(a)['partner_status'] == OUT_QF and record(b)['partner_status'] == FINAL, 'one',
          'not told how the other did')
    before = (open(a, 'rb').read()[RECORD:RECORD + 20], open(b, 'rb').read()[RECORD:RECORD + 20])
    ra_, rb_, a, b = link(a, b, step('one_sync_again'))
    after = (open(a, 'rb').read()[RECORD:RECORD + 20], open(b, 'rb').read()[RECORD:RECORD + 20])
    check(before == after, 'one', 'a second session changed the records')
    # (winning the final there, the desk gives the prize and closes the bracket)
    ind = Indigo(a)
    prizes = ind.items('ABILITYPATCH') + ind.items('BOTTLE_CAP')
    ind.rounds([True], 'one_A_final')
    check(ind.record() is None, 'one', f'after the NPC final the bracket is still open: {ind.record()}')
    check(ind.items('ABILITYPATCH') + ind.items('BOTTLE_CAP') == prizes + 1, 'one', 'no prize after the NPC final')
    a = ind.save(os.path.join(args.out, 'one_A_final.sav'))
    ind = Indigo(b)
    ind.visit('b')
    check(ind.record() is not None and ind.record()['status'] == OUT_QF, 'one',
          'the one out lost the bracket before hearing the end')
    ind.save(os.path.join(args.out, 'one_B_wait.sav'))

    # both out
    ra_, rb_, a, b = link(args.save_a, args.save_b, step('out_register'))
    registered(a, b, 'out')
    a = offline(a, [False], 'out_A')
    b = offline(b, [True, False], 'out_B')
    check(record(b)['status'] == OUT_SF, 'out', f'B status {record(b)["status"]}')
    ra_, rb_, a, b = link(a, b, step('out_sync'))
    check((ra_, rb_) == ('desk: synced', 'desk: synced'), 'out', f'sync: {ra_} / {rb_}')
    for sav in (a, b):
        ind = Indigo(sav)
        ind.visit()
        check(ind.record() is None, 'out', 'a bracket stayed open with both out')
        ind.pb_done = ind.save(sav + '.done')

    # noise at the desk, then a clean session
    ra_, rb_, a, b = link(args.save_a, args.save_b, step('noisy'), '--noise-desk', '--corrupt', '4')
    na, nb = record(a), record(b)
    ra_, rb_, a, b = link(a, b, step('noisy_clean'))
    check(ra_.startswith('desk:') and rb_.startswith('desk:'), 'noise', f'clean session: {ra_} / {rb_}')
    registered(a, b, 'noise')
    check(not (na and nb) or na['id'] == nb['id'], 'noise', 'the noisy session left different brackets')

    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
