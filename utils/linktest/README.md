# Link battle test harness

`linktest.py` links two emulated Game Boys with a virtual cable and plays a
link battle between two saves: both talk to the Pokémon Center 2F battle desk,
save, sit at the Colosseum table and fight (each picks its moves in rotation
and sends in the next healthy Pokémon when one faints). At the start of every
turn each side records both active Pokémon and both parties' HP; the two
records must agree, mirrored, or the battle has desynced.

`--corrupt N` adds line noise: about 1 in N bytes side B receives during the
battle gets one bit flipped. `--rom-b` runs side B on a different ROM.

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
