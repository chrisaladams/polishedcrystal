"""Regression: Rising Cup hardware report 2 (status symbols beside the enemy sprite
after the player's Pokemon faints and a replacement is sent in).

Root cause (confirmed): the party menu loads GFX_StatusIcons (16 tiles) to
vTiles2 tile $00, which is also where the enemy's front pic lives. The voluntary
switch paths reload the pic afterwards (GetMonFrontpic); the forced switch after a
faint (GetPlayerSwitchTarget) did not, so the icons stayed drawn over the enemy's
pic until the enemy was replaced. Not hardware-specific; it reproduces in PyBoy.
The Rising Cup is only where it was noticed: the code path is every battle.

Provenance: party, position and the faint (HP set to 0 at the first battle menu)
are INJECTED; the cup dialogue, team selection, battle, and replacement are real
button input through the game's own routines.
"""
from qa.gb import battle as B, fixtures as F, saves
from qa.gb.consts import C, map_ids
from qa.framework import qa_test

PROVENANCE = 'cup entry/battle/replacement: gameplay input; party+position+faint: injected'
PIC_TILES = 0x31          # a 7x7 front pic


def build(g):
    """Totodile, Pidgey, Rattata (lvl 20) beside the Rising Star Cup organiser"""
    for sp in ('TOTODILE', 'PIDGEY', 'RATTATA'):
        F.give_mon(g, C[sp], 20)
    F.teleport(g, *map_ids('ROUTE_36_NATIONAL_PARK_GATE'), 7, 3)


def run(g, shots=None):
    B.cup_select_three(g)
    # press through the round-1 intro until the first battle menu appears
    menu = [0]
    g.hook('BattleMenu', lambda _: menu.__setitem__(0, menu[0] + 1))
    for _ in range(60):
        if menu[0]:
            break
        g.press('a', 4, 26)
    assert menu[0], 'never reached the first battle menu'
    g.tick(30)
    before = B.vtiles2_tiles(g, 0, PIC_TILES)
    if shots:
        g.screenshot('before_faint')
    # INJECTED: the lead has fainted; the game runs its own faint and replacement flow
    for name in ('wBattleMonHP', 'wPartyMon1HP'):
        g.wr(name, 0)
        g.wr(name, 0, 1)
    pick = [0]
    g.hook('ForcePickSwitchMonInBattle', lambda _: pick.__setitem__(0, pick[0] + 1))
    for _ in range(80):
        if pick[0]:
            break
        g.press('a', 4, 26)
    assert pick[0], 'the forced-switch menu never appeared'
    g.tick(40)
    g.press('down', 4, 20)           # second Pokemon (Pidgey)
    g.press('a', 4, 30)
    g.press('a', 4, 30)              # Switch
    # let the send-out finish and the next battle menu come back
    menu[0] = 0
    for _ in range(80):
        if menu[0]:
            break
        g.press('a', 4, 26) if _ % 3 == 0 else g.tick(26)
    assert menu[0], 'the battle menu never returned after the replacement'
    g.tick(60)
    after = B.vtiles2_tiles(g, 0, PIC_TILES)
    if shots:
        g.screenshot('after_replacement')
    return before, after


def check(before, after):
    notes, ok = [], True
    diff = [i for i in range(PIC_TILES) if before[i * 16:(i + 1) * 16] != after[i * 16:(i + 1) * 16]]
    if diff:
        ok = False
        notes.append('enemy pic tiles changed after the replacement: %s' % diff)
    return ok, notes


@qa_test(suites=('regression', 'battle', 'full'), covers=('battle.hud', 'battle.switching', 'cups.rising_star'),
         backends=('pyboy', 'sameboy'), provenance=PROVENANCE)
def rising_cup_replacement_hud(ctx):
    g = ctx.boot('rising_cup_start', build)
    before, after = run(g, shots=True)
    ok, notes = check(before, after)
    for n in notes:
        ctx.note(n)
    ctx.expect(ok, '; '.join(notes))
