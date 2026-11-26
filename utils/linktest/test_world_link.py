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
- unplugging at either desk exchange returns both players to the desk,
  preserves the bracket records, and lets the next connection succeed;
- reconnecting cartridges with only one durable registration or final
  result recovers the same draw and each player's round;
- a session with heavy noise on the cable either changes nothing or leaves
  the two cartridges agreeing after a clean session, and a different clock
  on one Game Boy doesn't matter.

Every opponent is checked against the draw worked out here from the shared
seed, as WorldLinkDraw makes it.

Usage (from the repository root, after make):
  PYTHONPATH=/tmp/pyboy_cable python3 utils/linktest/test_world_link.py A.sav B.sav C.sav --out DIR
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
sys.path.insert(0, os.path.join(ROOT, 'utils', 'world_cup'))
from bracket import draw, winner  # noqa: E402

RECORD = 0x11d5  # sWorldLink's offset in the save (SRAM bank 0, $b1d5)
QF, SF, FINAL, OUT_QF, OUT_SF, CHAMPION, RUNNER_UP = range(7)
UNKNOWN = 0xff
fails = []


def record_bytes(sav):
    with open(sav, 'rb') as src:
        src.seek(RECORD)
        return src.read(20)


def record(sav):
    r = record_bytes(sav)
    if len(r) != 20 or r[:2] != b'WC':
        return None
    checksum = ord('C')
    for byte in r[3:]:
        checksum = (checksum + byte) & 0xff
        checksum = (checksum << 1 | checksum >> 7) & 0xff
    if r[2] != checksum:
        return None
    return {'id': r[3:5], 'seed': r[5] | r[6] << 8, 'half': r[7], 'partner': r[8:10],
            'name': r[10:18], 'status': r[18] & 0x7f, 'closed': bool(r[18] & 0x80), 'partner_status': r[19]}


def opponent(rec, round_):
    """Who the game should send out (WorldLinkOpponent), the trainers' own
    matches decided as WorldCupWinner does (utils/world_cup/bracket.py)."""
    seed = rec['seed']
    b, me = draw(seed), 4 * rec['half']
    other = me ^ 4
    if round_ == QF:
        return b[me + 1]
    if round_ == SF:
        return winner(seed, (me + 2) // 2, b[me + 2], b[me + 3])
    finalist = winner(seed, (other + 2) // 2, b[other + 2], b[other + 3])
    if rec['partner_status'] == OUT_QF:
        finalist = winner(seed, 4 + other // 4, b[other + 1], finalist)
    return finalist


def link(a, b, out, *extra, seconds=900, allow_failure=False):
    cmd = [sys.executable, os.path.join(ROOT, 'utils', 'linktest', 'linktest.py'), a, b,
           '--rules', 'world', '--turns', '400', '--seconds', str(seconds), '--out', out, *extra]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=1300)
    if res.returncode and not allow_failure:
        check(False, os.path.basename(out), res.stdout.strip() or res.stderr.strip())
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
        # where it was saved (the battle desk), for saving there again
        self.home = tuple(self.g.rd(n) for n in ('wMapGroup', 'wMapNumber', 'wXCoord', 'wYCoord'))
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
        for _ in range(16):
            if not self.g.rd('wScriptRunning'):
                break  # (once it's done: another press would talk again)
            self.g.press(answer, 40)
        self.settle()

    def withdraw(self):
        """Decline the round offered (or the wait) and leave the bracket."""
        self.talk()
        for _ in range(10):
            text = bytes(self.g.rd('wTilemap', i) for i in range(20 * 18))
            if bytes([0x98, 0xa4, 0xb2]) in text and self.g.rd('wMenuCursorY'):  # a Yes/No box
                break
            self.g.press('a', 40)
        self.g.press('down', 20)  # No: not now
        self.g.press('a', 60)
        for _ in range(10):  # "Leave the bracket?"
            text = bytes(self.g.rd('wTilemap', i) for i in range(20 * 18))
            if bytes([0x98, 0xa4, 0xb2]) in text:
                break
            self.g.press('a', 40)
        self.g.press('a', 60)  # Yes
        self.settle()

    def game_save(self):
        """Save the game in place (at the battle desk, where the link sessions
        start)."""
        self.g.warp(*self.home)
        self.g.tick(60)
        self.g.manual_save()
        self.g.tick(60)

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


def check_one_sided_commit(before, committed, outcome, step, stage):
    expected = [record(sav) for sav in committed]
    fields = ('id', 'seed', 'half', 'partner', 'status')
    for i, name in enumerate('AB'):
        where = f'{stage}_only_{name}'
        inputs = list(before)
        inputs[i] = committed[i]
        ra, rb, a, b = link(*inputs, step(where))
        check((ra, rb) == (outcome, outcome), where, f'after reconnect: {ra} / {rb}')
        for side, got, want in zip('AB', registered(a, b, where), expected):
            check(got and want and all(got[key] == want[key] for key in fields),
                  where, f'side {side} did not recover the same draw and round')


def check_interruptions(a, b, step):
    for exchange, retry_want in ((1, 'desk: registered'), (2, 'desk: synced')):
        where = f'unplug_exchange_{exchange}'
        before = (record_bytes(a), record_bytes(b))
        outcome_a, outcome_b, cut_a, cut_b = link(
            a, b, step(where), '--world-unplug', str(exchange), seconds=60)
        check((outcome_a, outcome_b) == ('desk: interrupted', 'desk: interrupted'), where,
              f'after disconnect: {outcome_a} / {outcome_b}')
        check((record_bytes(cut_a), record_bytes(cut_b)) == before, where,
              'the interrupted exchange changed a bracket record')

        outcome_a, outcome_b, a, b = link(cut_a, cut_b, step(f'{where}_retry'))
        check((outcome_a, outcome_b) == (retry_want, retry_want), where,
              f'after reconnect: {outcome_a} / {outcome_b}')
        ra, rb = registered(a, b, where)
        if exchange == 1 and ra and rb:
            check_one_sided_commit((cut_a, cut_b), (a, b), 'desk: registered', step, 'registration')
        elif exchange == 2 and ra and rb:
            for rec, old in zip((ra, rb), before):
                check(rec['status'] == rec['partner_status'] == QF
                      and rec['id'] == old[3:5] and rec['seed'] == int.from_bytes(old[5:7], 'little')
                      and rec['half'] == old[7], where, 'the retry changed the draw or lost a result')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('save_a')
    ap.add_argument('save_b')
    ap.add_argument('save_c', nargs='?', help='a third player, for a mismatched session')
    ap.add_argument('--out', default='world_link_out')
    ap.add_argument('--interruptions-only', action='store_true',
                    help='run the desk disconnect and retry cases only')
    args = ap.parse_args()
    if not args.interruptions_only and args.save_c is None:
        ap.error('the full suite needs a third save')
    os.makedirs(args.out, exist_ok=True)

    def step(name):
        d = os.path.join(args.out, name)
        os.makedirs(d, exist_ok=True)
        return d

    check_interruptions(args.save_a, args.save_b, step)
    if args.interruptions_only:
        return report()

    def keep(ind, name, save_game=False):
        if save_game:
            ind.game_save()
        return ind.save(os.path.join(args.out, name + '.sav'))

    def offline(sav, results, name):
        ind = Indigo(sav)
        ind.rounds(results, name)
        return keep(ind, name)

    def prizes(ind):
        return ind.items('ABILITYPATCH') + ind.items('BOTTLE_CAP')

    # 1. both finalists (B's clock on another day)
    ra_, rb_, a, b = link(args.save_a, args.save_b, step('both_register'), '--day-b', '77')
    check((ra_, rb_) == ('desk: registered', 'desk: registered'), 'both', f'registration: {ra_} / {rb_}')
    reg_a, reg_b = registered(a, b, 'both')
    a = offline(a, [True, True], 'both_A')
    b = offline(b, [True, True], 'both_B')
    check(record(a)['status'] == FINAL and record(b)['status'] == FINAL, 'both', 'not both qualified')
    finalists = (a, b)
    ra_, rb_, a, b = link(a, b, step('both_final'))
    check(ra_.startswith('battle over') and rb_.startswith('battle over'), 'both', f'final: {ra_} / {rb_}')
    sa, sb = record(a)['status'], record(b)['status']
    check({sa, sb} == {CHAMPION, RUNNER_UP}, 'both', f'after the final: {sa} {sb}')
    check(record(a)['partner_status'] == sb and record(b)['partner_status'] == sa, 'both',
          "each did not hear the other's result")
    check_one_sided_commit(finalists, (a, b), 'desk: synced', step, 'final_result')
    champ, other = (a, b) if sa == CHAMPION else (b, a)

    # the prize, and a power cut before saving: still unclaimed, so given again
    ind = Indigo(champ)
    before = prizes(ind)
    ind.visit()
    check(prizes(ind) == before + 1, 'prize', 'no prize for the champion')
    ind.visit()
    check(prizes(ind) == before + 1, 'prize', 'a second prize before saving')
    rec = ind.record()
    check(rec and not rec['closed'], 'prize', 'the bracket closed before the game was saved')
    keep(ind, 'prize_unsaved')  # (the cartridge as a power cut leaves it)
    ind = Indigo(os.path.join(args.out, 'prize_unsaved.sav'))
    before = prizes(ind)
    ind.visit()
    check(prizes(ind) == before + 1, 'prize', 'lost to a power cut before saving')
    # saved: closed, and no prize again
    champ = keep(ind, 'prize_saved', save_game=True)
    check(record(champ) and record(champ)['closed'], 'prize', 'saving did not close the bracket')
    ind = Indigo(champ)
    before = prizes(ind)
    ind.visit('b')
    check(prizes(ind) == before, 'prize', 'another prize after the saved claim')
    ind.save(os.path.join(args.out, 'prize_after.sav'))

    # the champion's closed record doesn't let the bracket start again
    ra_, rb_, x, y = link(champ, other, step('closed_vs_open'))
    check((ra_, rb_) == ('desk: synced', 'desk: synced'), 'closed', f'closed vs open: {ra_} / {rb_}')
    check(record(x)['id'] == reg_a['id'] and record(y)['id'] == reg_a['id'], 'closed', 'the bracket changed')
    ind = Indigo(y)
    ind.visit()
    check(ind.record()['closed'], 'closed', "the runner-up's bracket did not close")
    y = keep(ind, 'runner_up_closed')
    # both closed: a new bracket, with a new ID
    ra_, rb_, x, y = link(x, y, step('new_bracket'))
    check((ra_, rb_) == ('desk: registered', 'desk: registered'), 'closed', f'new bracket: {ra_} / {rb_}')
    nx, ny = registered(x, y, 'closed')
    check(nx and nx['id'] != reg_a['id'] and not nx['closed'], 'closed', 'the new bracket reused the old ID')

    # 2. one finalist; the eliminated partner hears the final result
    ra_, rb_, a, b = link(args.save_a, args.save_b, step('one_register'))
    registered(a, b, 'one')
    a = offline(a, [True, True], 'one_A')
    b = offline(b, [False], 'one_B')
    check(record(b)['status'] == OUT_QF, 'one', f'B status {record(b)["status"]}')
    ra_, rb_, a, b = link(a, b, step('one_sync'))
    check((ra_, rb_) == ('desk: synced', 'desk: synced'), 'one', f'sync: {ra_} / {rb_}')
    check(record(a)['partner_status'] == OUT_QF and record(b)['partner_status'] == FINAL, 'one',
          'not told how the other did')
    before = (record_bytes(a), record_bytes(b))
    ra_, rb_, a, b = link(a, b, step('one_sync_again'))
    after = (record_bytes(a), record_bytes(b))
    check(before == after, 'one', 'a second session changed the records')
    ind = Indigo(b)
    ind.visit('b')
    check(not ind.record()['closed'], 'one', 'the one out closed before hearing the end')
    b = keep(ind, 'one_B_wait')
    ind = Indigo(a)
    before = prizes(ind)
    ind.rounds([True], 'one_A_final')
    check(prizes(ind) == before + 1, 'one', 'no prize after the NPC final')
    a = keep(ind, 'one_A_champion', save_game=True)
    check(record(a)['closed'] and record(a)['status'] == CHAMPION, 'one', 'the NPC final champion not closed')
    ra_, rb_, a, b = link(a, b, step('one_hears'))
    check(record(b)['partner_status'] == CHAMPION, 'one', 'the one out did not hear the final result')
    ind = Indigo(b)
    ind.visit()
    check(ind.record()['closed'], 'one', 'the one out could not finish the bracket')
    ind.save(os.path.join(args.out, 'one_B_done.sav'))

    # 3. both out
    ra_, rb_, a, b = link(args.save_a, args.save_b, step('out_register'))
    registered(a, b, 'out')
    a = offline(a, [False], 'out_A')
    b = offline(b, [True, False], 'out_B')
    check(record(b)['status'] == OUT_SF, 'out', f'B status {record(b)["status"]}')
    ra_, rb_, a, b = link(a, b, step('out_sync'))
    check((ra_, rb_) == ('desk: synced', 'desk: synced'), 'out', f'sync: {ra_} / {rb_}')
    for name, sav in (('A', a), ('B', b)):
        ind = Indigo(sav)
        ind.visit()
        check(ind.record()['closed'], 'out', f'{name} bracket stayed open with both out')
        ind.save(sav + '.done')

    # 4. a withdrawal, heard as a forfeit; the survivor then loses the NPC final
    ra_, rb_, a, b = link(args.save_a, args.save_b, step('leave_register'))
    registered(a, b, 'leave')
    ind = Indigo(a)
    ind.withdraw()
    rec = ind.record()
    check(rec and rec['closed'] and rec['status'] == QF, 'leave', f'after leaving: {rec}')
    a = keep(ind, 'leave_A')
    b = offline(b, [True, True], 'leave_B')
    ra_, rb_, a, b = link(a, b, step('leave_sync'))
    check((ra_, rb_) == ('desk: synced', 'desk: synced'), 'leave', f'sync: {ra_} / {rb_}')
    check(record(b)['partner_status'] == OUT_QF, 'leave', f'B heard {record(b)["partner_status"]}')
    ind = Indigo(b)
    ind.rounds([False], 'leave_B_final')  # (checks the opponent: the other half's finalist)
    rec = ind.record()
    check(rec and rec['status'] == RUNNER_UP and rec['closed'], 'leave', f'after losing the NPC final: {rec}')
    ind.save(os.path.join(args.out, 'leave_B_done.sav'))

    # 5. a third player, while in a bracket with someone else
    ra_, rb_, a2, b2 = link(args.save_a, args.save_b, step('mismatch_register'))
    ra_, rb_, _, _ = link(a2, args.save_c, step('mismatch'))
    check((ra_, rb_) == ('desk: other brackets', 'desk: other brackets'), 'mismatch', f'{ra_} / {rb_}')
    check(record(os.path.join(args.out, 'mismatch', 'A.sav'))['id'] == record(a2)['id'], 'mismatch',
          'the bracket changed')

    # 6. noise at the desk, then a clean session
    # (a noisy session may be cut off rather than finish: either is checked
    # below, so it needn't wait out the usual limit)
    ra_, rb_, a, b = link(args.save_a, args.save_b, step('noisy'), '--noise-desk', '--corrupt', '4',
                          seconds=240, allow_failure=True)
    na, nb = record(a), record(b)
    ra_, rb_, a, b = link(a, b, step('noisy_clean'))
    check(ra_.startswith('desk:') and rb_.startswith('desk:'), 'noise', f'clean session: {ra_} / {rb_}')
    registered(a, b, 'noise')
    check(not (na and nb) or na['id'] == nb['id'], 'noise', 'the noisy session left different brackets')

    return report()


def report():
    print(f'{len(fails)} problems')
    for f in fails:
        print('  FAIL', f[0], '-', f[1])
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
