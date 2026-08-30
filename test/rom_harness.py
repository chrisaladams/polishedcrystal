"""Run individual ROM routines under PyBoy and inspect the result.

The trick these tests use is that most scoring helpers are pure functions of a
few RAM locations: page in the routine's bank, write its inputs, jump straight
at it, and read the answer back. That avoids needing a save file or driving the
game to a battle, so the tests stay fast and deterministic.

Addresses are resolved from the .sym file rgblink emits rather than hardcoded,
so the tests keep working when code moves between banks.
"""

import glob
import os
import re

SYM_LINE = re.compile(r'^([0-9a-fA-F]{2,}):([0-9a-fA-F]{4})\s+(\S+)')

# Scratch space. TRAP holds a `jr -2` we return into, so we can spot the routine
# finishing; STRUCT is spare WRAM bank 1 for building fake party structs.
TRAP = 0xff90
STRUCT = 0xd400
STACK = 0xdff0

MBC_ROM_BANK = 0x2000
H_ROM_BANK = 0xff87
SVBK = 0xff70
IE = 0xffff
IF = 0xff0f


def find_build(root='.'):
    """Locate the built ROM and its symbol file."""
    roms = sorted(
        r for r in glob.glob(os.path.join(root, '*.gbc'))
        if 'faithful' not in r and '_vc' not in r and 'debug' not in r)
    if not roms:
        raise SystemExit(
            'No ROM found. Build one first (make), then re-run the tests.')
    rom = roms[0]
    sym = rom[:-len('.gbc')] + '.sym'
    if not os.path.exists(sym):
        raise SystemExit(f'No symbol file beside {rom}; expected {sym}.')
    return rom, sym


def load_symbols(path):
    """Parse rgblink's .sym into {name: (bank, address)}."""
    symbols = {}
    with open(path) as handle:
        for line in handle:
            match = SYM_LINE.match(line)
            if match:
                bank, addr, name = match.groups()
                symbols.setdefault(name, (int(bank, 16), int(addr, 16)))
    return symbols


class Harness:
    def __init__(self, rom, symbols, boot_frames=900):
        from pyboy import PyBoy
        self.symbols = symbols
        self.pyboy = PyBoy(rom, window='null')
        # Boot far enough that the MBC and WRAM banking are in a sane state.
        for _ in range(boot_frames):
            self.pyboy.tick(1, False)
        self.mem = self.pyboy.memory
        self.reg = self.pyboy.register_file
        # Map in the WRAM bank the battle variables live in *before* any test
        # writes to them, and stop interrupts running game code behind our back.
        # Without this, a write aimed at e.g. wCurDamage lands in whichever bank
        # the booted game happened to leave mapped.
        self.prepare()

    def prepare(self):
        self.mem[SVBK] = 1
        self.mem[IE] = 0
        self.mem[IF] = 0

    def addr(self, name):
        """Address of a symbol, ignoring which bank it lives in."""
        return self.symbols[name][1]

    def bank(self, name):
        return self.symbols[name][0]

    def offset(self, base, member):
        """Byte offset of a struct member, e.g. offset('wPartyMon1', ...HP)."""
        return self.addr(member) - self.addr(base)

    def write16(self, address, value):
        """Write a big-endian 16-bit value, the convention this codebase uses."""
        self.mem[address] = (value >> 8) & 0xff
        self.mem[address + 1] = value & 0xff

    def read16(self, address):
        return (self.mem[address] << 8) | self.mem[address + 1]

    def call(self, routine, a=0, hl=0, max_frames=60):
        """Run `routine` to its ret. Returns the value left in A."""
        bank, entry = self.symbols[routine]

        self.prepare()
        self.mem[MBC_ROM_BANK] = bank
        self.mem[H_ROM_BANK] = bank   # keep farcall's bookkeeping consistent
        self.mem[TRAP] = 0x18         # jr -2
        self.mem[TRAP + 1] = 0xfe

        self.mem[STACK] = TRAP & 0xff
        self.mem[STACK + 1] = (TRAP >> 8) & 0xff
        self.reg.SP = STACK
        self.reg.HL = hl
        self.reg.A = a
        self.reg.PC = entry

        for _ in range(max_frames):
            self.pyboy.tick(1, False)
            if self.reg.PC in (TRAP, TRAP + 1):
                return self.reg.A
        raise AssertionError(
            f'{routine} did not return (PC={self.reg.PC:04x})')

    def stop(self):
        self.pyboy.stop(save=False)
