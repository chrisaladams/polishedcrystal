"""A symbol-aware PyBoy wrapper: input, memory, hooks, screenshots and
failure artifacts.

Everything resolves addresses from the .sym file the build produced, so tests
keep working when code moves between banks. A Game never edits ROM and never
touches a real save: SRAM comes from a copy the caller provides.
"""
import hashlib
import json
import os
import re
import subprocess
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
SYM_LINE = re.compile(r'^([0-9a-fA-F]{2,}):([0-9a-fA-F]{4})\s+(\S+)')

BUTTONS = ('a', 'b', 'start', 'select', 'up', 'down', 'left', 'right')


def load_sym(path):
    """{name: (bank, address)} from an rgblink .sym file."""
    sym = {}
    with open(path) as f:
        for line in f:
            m = SYM_LINE.match(line)
            if m:
                b, a, n = m.groups()
                sym.setdefault(n, (int(b, 16), int(a, 16)))
    return sym


def rom_version():
    """VERSION from the Makefile, so the default ROM path follows releases."""
    for line in open(os.path.join(ROOT, 'Makefile')):
        m = re.match(r'VERSION\s*:=\s*(\S+)', line)
        if m:
            return m.group(1)
    raise RuntimeError('VERSION not found in Makefile')


def default_rom():
    return os.environ.get('QA_ROM') or os.path.join(ROOT, f'polishedcrystal-{rom_version()}.gbc')


def sha1(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        h.update(f.read())
    return h.hexdigest()


class Game:
    """One emulated console running the ROM."""

    def __init__(self, rom=None, sav=None, sym=None, workdir='.', seed=1, speed=0, power_on_noise=None):
        from pyboy import PyBoy
        self.rom = rom or default_rom()
        self.sym = load_sym(sym or self.rom[:-4] + '.sym')
        self.workdir = workdir
        os.makedirs(workdir, exist_ok=True)
        self.seed = seed
        self.frame = 0
        kw = {}
        if sav:
            kw['ram_file'] = open(sav, 'rb')
        self.pb = PyBoy(self.rom, window='null', **kw)
        self.pb.set_emulation_speed(speed)
        self.mem = self.pb.memory
        self.reg = self.pb.register_file
        self.trace_hooks = {}
        if power_on_noise is not None:
            self.randomize_ram(power_on_noise)
        self.events = []          # (frame, label) from hooks, kept for artifacts

    def randomize_ram(self, seed):
        """Fill WRAM (all 8 banks), HRAM, VRAM (both banks) and OAM with seeded
        noise before the first instruction runs. Real consoles power on with
        arbitrary RAM; emulators usually zero it, which hides code that reads
        memory it never wrote."""
        import random
        rng = random.Random(seed)
        m = self.mem
        for a in range(0xc000, 0xd000):
            m[a] = rng.randrange(256)
        for bank in range(1, 8):
            for a in range(0xd000, 0xe000):
                m[bank, a] = rng.randrange(256)
        for a in range(0xff80, 0xffff):
            m[a] = rng.randrange(256)
        for bank in (0, 1):
            for a in range(0x8000, 0xa000):
                m[bank, a] = rng.randrange(256)
        for a in range(0xfe00, 0xfea0):
            m[a] = rng.randrange(256)

    # ---- time and input
    def tick(self, n=1, render=True):
        """Run n frames; only the last is rendered (screenshots need one)."""
        for i in range(n):
            self.pb.tick(1, render and i == n - 1)
            self.frame += 1

    def press(self, button, hold=4, wait=6):
        """Press and release one button, then let the game react."""
        self.pb.button(button, hold)
        self.tick(hold + wait)

    def hold(self, button, frames):
        self.pb.button_press(button)
        self.tick(frames)
        self.pb.button_release(button)

    def run_until(self, cond, max_frames=600, step=1):
        """Tick until cond() is truthy; returns frames used or raises TimeoutError."""
        for i in range(0, max_frames, step):
            if cond():
                return i
            self.tick(step)
        if cond():
            return max_frames
        raise TimeoutError('condition not met in %d frames' % max_frames)

    @property
    def pc(self):
        return self.reg.PC

    @property
    def sp(self):
        return self.reg.SP

    def read(self, addr, bank=None):
        return self.mem[bank, addr] if bank is not None and 0xd000 <= addr < 0xe000 else self.mem[addr]

    def write(self, addr, value, bank=None):
        if bank is not None and 0xd000 <= addr < 0xe000:
            self.mem[bank, addr] = value
        else:
            self.mem[addr] = value

    # ---- memory by symbol
    def _loc(self, name, k=0):
        bank, a = self.sym[name]
        a += k
        return (bank, a) if 0xd000 <= a < 0xe000 and bank >= 1 else (None, a)

    def rd(self, name, k=0):
        bank, a = self._loc(name, k)
        return self.mem[bank, a] if bank is not None else self.mem[a]

    def wr(self, name, value, k=0):
        bank, a = self._loc(name, k)
        if bank is not None:
            self.mem[bank, a] = value
        else:
            self.mem[a] = value

    def rd16(self, name, k=0):
        return self.rd(name, k) << 8 | self.rd(name, k + 1)

    def rd_bytes(self, name, n):
        return bytes(self.rd(name, i) for i in range(n))

    def dump(self, start, length, bank=None):
        if bank is not None:
            return bytes(self.mem[bank, a] for a in range(start, start + length))
        return bytes(self.mem[a] for a in range(start, start + length))

    def vram(self, vbk):
        """All 8 KiB of VRAM bank vbk (0 or 1)."""
        return bytes(self.mem[vbk, a] for a in range(0x8000, 0xa000))

    def oam(self):
        return bytes(self.mem[0xfe00 + i] for i in range(160))

    # ---- hooks and symbolisation
    def hook(self, label, fn):
        bank, a = self.sym[label]
        self.pb.hook_register(bank if a >= 0x4000 and a < 0x8000 else 0, a, fn, None)

    def where(self, pc=None):
        """Nearest preceding symbol for the CPU's PC in the currently mapped bank."""
        pc = self.reg.PC if pc is None else pc
        bank = self.mem[0xff87] if 0x4000 <= pc < 0x8000 else 0   # hROMBank
        best = None
        for n, (b, a) in self.sym.items():
            if (b == bank or (pc < 0x4000 and b == 0)) and a <= pc and not n.startswith('.'):
                if best is None or a > best[1]:
                    best = (n, a)
        return f'{best[0]}+{pc - best[1]}' if best else f'{bank:02x}:{pc:04x}'

    # ---- artifacts
    def screenshot(self, name):
        path = os.path.join(self.workdir, name if name.endswith('.png') else name + '.png')
        self.pb.screen.image.save(path)
        return path

    def snapshot(self, tag, names=(), regions=()):
        """Write screenshot, registers, selected symbols and raw regions for a failure.

        regions: iterable of (label, start, length, bank_or_None).
        """
        base = os.path.join(self.workdir, tag)
        os.makedirs(base, exist_ok=True)
        self.pb.screen.image.save(os.path.join(base, 'screen.png'))
        info = {
            'frame': self.frame,
            'pc': f'{self.reg.PC:04x}', 'sp': f'{self.reg.SP:04x}',
            'where': self.where(),
            'af': f'{self.reg.A:02x}{self.reg.F:02x}',
            'bc': f'{self.reg.B:02x}{self.reg.C:02x}',
            'de': f'{self.reg.D:02x}{self.reg.E:02x}',
            'hl': f'{self.reg.HL:04x}',
            'rom_bank': self.mem[0xff87], 'wram_bank': self.mem[0xff70] & 7,
            'vram_bank': self.mem[0xff4f] & 1, 'lcdc': self.mem[0xff40], 'stat': self.mem[0xff41],
            'ly': self.mem[0xff44], 'ie': self.mem[0xffff], 'if': self.mem[0xff0f],
            'symbols': {n: self.rd(n) for n in names if n in self.sym},
        }
        with open(os.path.join(base, 'state.json'), 'w') as f:
            json.dump(info, f, indent=1)
        with open(os.path.join(base, 'oam.bin'), 'wb') as f:
            f.write(self.oam())
        for bank in (0, 1):
            with open(os.path.join(base, f'vram{bank}.bin'), 'wb') as f:
                f.write(self.vram(bank))
        for label, start, length, bank in regions:
            with open(os.path.join(base, f'{label}.bin'), 'wb') as f:
                f.write(self.dump(start, length, bank))
        return base

    # ---- calling a routine directly (a controlled, non-gameplay shortcut)

    def _ensure_trap(self):
        """Hook DelayFrameHalt, which only the main thread runs (interrupts on).

        A pending call starts there: the hook saves the CPU, points it at the
        routine with DelayFrameHalt as the return address, and when the routine
        returns the hook fires again, records A and restores the saved CPU, so
        the game carries on as if nothing happened."""
        if getattr(self, '_trap_set', False):
            return
        _, self._trap_addr = self.sym['DelayFrameHalt']
        self._job = None          # (entry, bank, a, bc, de, hl) waiting to start
        self._running = False
        self._result = None
        self._saved = None

        def on_halt(_):
            r = self.reg
            if self._running:
                if r.SP != self._saved[0][1]:
                    return            # a nested DelayFrameHalt inside the routine
                self._result = r.A
                (r.PC, r.SP, r.A, r.F, r.B, r.C, r.D, r.E, r.HL), rb = self._saved
                self.mem[0xff87] = rb
                self.mem[0x2000] = rb
                self._running = False
            elif self._job:
                entry, bank, a, bc, de, hl = self._job
                self._job = None
                self._saved = ((r.PC, r.SP, r.A, r.F, r.B, r.C, r.D, r.E, r.HL), self.mem[0xff87])
                if 0x4000 <= entry < 0x8000:
                    self.mem[0x2000] = bank
                    self.mem[0xff87] = bank
                sp = (r.SP - 2) & 0xffff
                self.mem[sp], self.mem[sp + 1] = self._trap_addr & 0xff, self._trap_addr >> 8
                r.SP, r.A = sp, a
                r.B, r.C, r.D, r.E, r.HL = bc >> 8, bc & 0xff, de >> 8, de & 0xff, hl
                r.PC = entry
                self._running = True
        self.pb.hook_register(0, self._trap_addr, on_halt, None)
        self._trap_set = True

    def call(self, label, a=0, bc=0, de=0, hl=0, max_frames=600, mash=None):
        """Run a ROM routine to its `ret` from the main thread, then resume the game.

        This is injection, not gameplay: tests that use it must say so.
        The return address is pushed just below the live stack pointer, so no
        game data is touched; interrupts keep running as in normal play.
        mash='b' presses that button every 12 frames while it runs (to get past text).
        """
        self._ensure_trap()
        bank, entry = self.sym[label]
        self._result = None
        self._job = (entry, bank, a, bc, de, hl)
        for i in range(max_frames):
            if mash and i % 12 == 0:
                self.pb.button(mash, 4)
            self.pb.tick(1, False)
            self.frame += 1
            if self._result is not None:
                return self._result
        raise AssertionError(f'{label} did not return (PC={self.reg.PC:04x}, {self.where()})')

    def save_point(self):
        """Snapshot the whole machine (PyBoy only); restore_point() returns to it."""
        import io
        self._point = io.BytesIO()
        self.pb.save_state(self._point)

    def restore_point(self):
        self._point.seek(0)
        self.pb.load_state(self._point)

    def in_battle(self):
        return self.rd('wBattleMode') != 0

    def close(self):
        self.pb.stop(save=False)


def git_commit():
    try:
        return subprocess.check_output(['git', '-C', ROOT, 'rev-parse', 'HEAD'], text=True).strip()
    except Exception:
        return 'unknown'
