# Link battle test harness

`linktest.py` links two emulated Game Boys with a virtual cable and plays a
link battle between two saves: both talk to the Pokémon Center 2F battle desk,
save, sit at the Colosseum table and fight (each picks its moves in rotation
and sends in the next healthy Pokémon when one faints). At the start of every
turn each side records both active Pokémon and both parties' HP; the two
records must agree, mirrored, or the battle has desynced.
The check fails if setup never reaches a shared action exchange, a side
times out, or a finished battle changes either real party. After a finished
battle each side must also have kept the other's team for Friend Battles
(sFriendTeam1 or 2: the species and forms sent, the format, a good
checksum), except after a Random Battle, where neither keeps one.

`--corrupt N` adds line noise: about 1 in N bytes side B receives during the
battle gets one bit flipped. `--rom-b` runs side B on a different ROM.

Use `--rules normal`, `random`, `rising`, or `unrestricted` to choose the
format. The harness checks the level on both ends and the fixed team sizes
for Random and Rising Star. Use `--rules rising --party-size 3` to test with
three Pokémon from each save. Use `--rules rising,unrestricted --party-size 3
--expect-rejection mismatch` to exercise the desk's format mismatch check.

`--trade` sends both sides to the trade desk instead, and passes when both
reach the Trade Center (held items are taken off in memory first: the desk
turns away Pokémon carrying mail). `--last-rules A,B` sets each cartridge's
last battle rules at boot, as a Championship session leaves them:
`--trade --last-rules world,normal` and `--trade --last-rules world` check
that a trade straight after the Championship neither starts a Championship
session nor is refused for different rules (the trade room checks neither).

## The cable

PyBoy's own shared-memory link swaps bytes whenever both sides finish a
transfer, even when neither drives the clock, which real hardware can't do.
In Pokémon that makes both games think they drive the clock, and their link
battles desync on the first speed tie. `pyboy_cable/` replaces PyBoy's serial
link with one that follows the hardware: only the internal-clock side drives a
transfer, an external-clock side completes only when the clock side delivers a
byte to it, and the two emulators run in lockstep (within 128 cycles).

`pyboy_cable/serial.py` and `serial.pxd` are modified from PyBoy 2.9
(LGPL-3.0, https://github.com/Baekalfen/PyBoy).

## Running

    pip install cython
    sh utils/linktest/pyboy_cable/build.sh /tmp/pyboy_cable
    make
    PYTHONPATH=/tmp/pyboy_cable python3 utils/linktest/linktest.py A.sav B.sav --turns 20

Run `python3 utils/linktest/test_link_card.py SAVE.sav` against a built ROM
to check the Trainer Card, per-opponent records, older saves, the yearly reset
and the full roster. The test uses an in-memory copy of the supplied save.

## Cutting the cable at the Championship desk

`--unplug-desk N,FRAMES` unplugs the cable as byte N of the linked
Championship session starts (counted on side A from `Special_WorldLinkSession`),
for FRAMES frames. A session is 118 bytes: the first exchange is bytes 1-55,
the second (the plans, each side's check echoed) 56-118, its data ending near
byte 110. `LINKTEST_TRACE=WorldLinkSwap,WorldLinkCommit` logs the byte count
at each step.

`test_world_cuts.py A.sav B.sav --out DIR [--quick]` cuts at each boundary in a
registration session and a results session, then links cleanly, and checks
that every session ends at the desk, no cut leaves two brackets, and the clean
session leaves both cartridges in one bracket with every result kept and
heard. The full run is 18 cuts (36 sessions, two at a time); `--quick` is 7.
