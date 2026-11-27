"""SameBoy backend (ctypes over libsameboy.so): accurate CGB revisions, a real boot
ROM, hardware-style randomised RAM, 10-sprite-per-line limit, VRAM/OAM access
blocking. Same surface as emu.Game for the parts tests share."""
import ctypes as C
import os
import random

from .emu import ROOT, default_rom, load_sym

SB_DIR = os.environ.get('SAMEBOY_DIR', '/home/user/gbdev/SameBoy')
MODELS = {'CGB-0': 0x200, 'CGB-A': 0x201, 'CGB-B': 0x202, 'CGB-C': 0x203,
          'CGB-D': 0x204, 'CGB-E': 0x205, 'AGB': 0x207}
BOOT = {'CGB-0': 'cgb0_boot.bin', 'AGB': 'agb_boot.bin'}
KEYS = {'right': 0, 'left': 1, 'up': 2, 'down': 3, 'a': 4, 'b': 5, 'select': 6, 'start': 7}
DIRECT = {'ROM': 0, 'RAM': 1, 'CART_RAM': 2, 'VRAM': 3, 'HRAM': 4, 'IO': 5, 'BOOTROM': 6, 'OAM': 7,
          'BGP': 8, 'OBP': 9, 'IE': 10}

RGB_ENCODE = C.CFUNCTYPE(C.c_uint32, C.c_void_p, C.c_uint8, C.c_uint8, C.c_uint8)
VBLANK_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_int)
EXEC_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_uint16, C.c_uint8)
READ_CB = C.CFUNCTYPE(C.c_uint8, C.c_void_p, C.c_uint16, C.c_uint8)
WRITE_CB = C.CFUNCTYPE(C.c_bool, C.c_void_p, C.c_uint16, C.c_uint8)


def _lib():
    path = os.path.join(SB_DIR, 'build/lib/libsameboy.so')
    if not os.path.exists(path):
        raise RuntimeError('libsameboy.so missing: run qa/setup.sh')
    lib = C.CDLL(path)
    lib.GB_alloc.restype = C.c_void_p
    lib.GB_init.restype = C.c_void_p
    lib.GB_init.argtypes = [C.c_void_p, C.c_int]
    lib.GB_load_rom.argtypes = [C.c_void_p, C.c_char_p]
    lib.GB_load_boot_rom.argtypes = [C.c_void_p, C.c_char_p]
    lib.GB_load_battery_from_buffer.argtypes = [C.c_void_p, C.c_char_p, C.c_size_t]
    lib.GB_save_battery_size.argtypes = [C.c_void_p]
    lib.GB_save_battery_to_buffer.argtypes = [C.c_void_p, C.c_char_p, C.c_size_t]
    lib.GB_run_frame.argtypes = [C.c_void_p]
    lib.GB_run_frame.restype = C.c_uint64
    lib.GB_run.argtypes = [C.c_void_p]
    lib.GB_run.restype = C.c_uint
    lib.GB_set_key_state.argtypes = [C.c_void_p, C.c_int, C.c_bool]
    lib.GB_set_pixels_output.argtypes = [C.c_void_p, C.c_void_p]
    lib.GB_set_rgb_encode_callback.argtypes = [C.c_void_p, RGB_ENCODE]
    lib.GB_set_vblank_callback.argtypes = [C.c_void_p, VBLANK_CB]
    lib.GB_set_execution_callback.argtypes = [C.c_void_p, EXEC_CB]
    lib.GB_set_read_memory_callback.argtypes = [C.c_void_p, READ_CB]
    lib.GB_set_write_memory_callback.argtypes = [C.c_void_p, WRITE_CB]
    lib.GB_read_memory.argtypes = [C.c_void_p, C.c_uint16]
    lib.GB_read_memory.restype = C.c_uint8
    lib.GB_write_memory.argtypes = [C.c_void_p, C.c_uint16, C.c_uint8]
    lib.GB_get_direct_access.argtypes = [C.c_void_p, C.c_int, C.POINTER(C.c_size_t), C.POINTER(C.c_uint16)]
    lib.GB_get_direct_access.restype = C.c_void_p
    lib.GB_get_registers.argtypes = [C.c_void_p]
    lib.GB_get_registers.restype = C.POINTER(C.c_uint16)
    lib.GB_random_seed.argtypes = [C.c_uint64]
    lib.GB_set_rendering_disabled.argtypes = [C.c_void_p, C.c_bool]
    lib.GB_set_color_correction_mode.argtypes = [C.c_void_p, C.c_int]
    lib.GB_set_turbo_mode.argtypes = [C.c_void_p, C.c_bool, C.c_bool]
    lib.GB_get_clock_rate.argtypes = [C.c_void_p]
    lib.GB_get_clock_rate.restype = C.c_uint32
    return lib


_GUARD = None


def exec_guard_lib():
    """Compile (once) and load qa/native/execguard.c."""
    global _GUARD
    if _GUARD is None:
        import subprocess
        src = os.path.join(ROOT, 'qa', 'native', 'execguard.c')
        so = os.path.join(ROOT, 'qa', '.cache', 'execguard.so')
        os.makedirs(os.path.dirname(so), exist_ok=True)
        if not os.path.exists(so) or os.path.getmtime(so) < os.path.getmtime(src):
            subprocess.check_call(['cc', '-O2', '-shared', '-fPIC', '-o', so, src])
        lib = C.CDLL(so)
        lib.execguard_fn.restype = C.c_void_p
        lib.execguard_count.restype = C.c_int
        lib.execguard_instructions.restype = C.c_uint64
        lib.av_vblank_ly.argtypes = [C.c_int]
        lib.av_vblank_ly.restype = C.c_uint64
        lib.av_vblank_count.restype = C.c_uint64
        lib.execguard_set_io.argtypes = [C.c_void_p]
        lib.av_write_fn.restype = C.c_void_p
        lib.av_audio_fn.restype = C.c_void_p
        lib.av_audio_init.argtypes = [C.c_size_t]
        lib.av_audio_count.restype = C.c_size_t
        lib.av_audio_data.restype = C.c_void_p
        lib.av_vram_writes.restype = C.c_uint64
        lib.av_vram_bad.restype = C.c_uint64
        lib.av_oam_writes.restype = C.c_uint64
        lib.av_oam_bad.restype = C.c_uint64
        lib.av_access_count.restype = C.c_int
        lib.av_access_get.argtypes = [C.c_int, C.POINTER(C.c_uint16), C.POINTER(C.c_uint16), C.POINTER(C.c_uint8),
                                      C.POINTER(C.c_uint8), C.POINTER(C.c_uint8), C.POINTER(C.c_uint8)]
        lib.execguard_watch.argtypes = [C.c_uint16, C.c_int]
        lib.execguard_watch_hits.argtypes = [C.c_int]
        lib.execguard_watch_hits.restype = C.c_uint64
        lib.execguard_set_hram.argtypes = [C.c_void_p]
        lib.execguard_coverage.argtypes = [C.c_int]
        lib.execguard_cover.restype = C.c_void_p
        lib.execguard_cover_size.restype = C.c_int
        lib.execguard_get.argtypes = [C.c_int, C.POINTER(C.c_uint16), C.POINTER(C.c_uint16),
                                      C.POINTER(C.c_uint8), C.POINTER(C.c_uint8)]
        _GUARD = lib
    return _GUARD


KIND = {1: 'NOP slide (running zeroed RAM)', 2: 'illegal opcode', 3: 'code fetched from VRAM/OAM/IO'}


class SBGame:
    """One SameBoy instance. model: 'CGB-0'...'CGB-E' or 'AGB'."""

    def __init__(self, rom=None, sav=None, sym=None, workdir='.', seed=1, model='CGB-E',
                 boot=True):
        self.lib = _lib()
        self.rom = rom or default_rom()
        self.sym = load_sym(sym or self.rom[:-4] + '.sym')
        self.workdir = workdir
        os.makedirs(workdir, exist_ok=True)
        self.model = model
        self.frame = 0
        self.lib.GB_random_seed(seed)          # RAM power-on noise, reproducible per seed
        self.gb = self.lib.GB_init(self.lib.GB_alloc(), MODELS[model])
        bootfile = BOOT.get(model, 'cgb_boot.bin')
        self.lib.GB_load_boot_rom(self.gb, os.path.join(SB_DIR, 'build/bin/BootROMs', bootfile).encode())
        if self.lib.GB_load_rom(self.gb, self.rom.encode()):
            raise RuntimeError('SameBoy could not load ' + self.rom)
        if sav:
            data = open(sav, 'rb').read()
            self.lib.GB_load_battery_from_buffer(self.gb, data, len(data))
        self.pixels = (C.c_uint32 * (160 * 144))()
        self._enc = RGB_ENCODE(lambda gb, r, g, b: r | g << 8 | b << 16 | 0xff000000)
        self._vb = VBLANK_CB(lambda gb, t: None)
        self.lib.GB_set_rgb_encode_callback(self.gb, self._enc)
        self.lib.GB_set_vblank_callback(self.gb, self._vb)
        self.lib.GB_set_pixels_output(self.gb, C.addressof(self.pixels))
        self.lib.GB_set_color_correction_mode(self.gb, 0)  # GB_COLOR_CORRECTION_DISABLED: raw 5-bit colours
        self.lib.GB_set_turbo_mode(self.gb, True, True)   # no real-time pacing
        self._regs = self.lib.GB_get_registers(self.gb)
        self._access = {}
        self.frame_hooks = []
        self._exec_hooks = {}
        self._exec_keep = None

    # ---- time and input
    def tick(self, n=1, render=True):
        for _ in range(n):
            self.lib.GB_run_frame(self.gb)
            self.frame += 1
            for h in self.frame_hooks:
                h(self)

    def press(self, button, hold=4, wait=6):
        self.lib.GB_set_key_state(self.gb, KEYS[button], True)
        self.tick(hold)
        self.lib.GB_set_key_state(self.gb, KEYS[button], False)
        self.tick(wait)

    def hold(self, button, frames):
        self.lib.GB_set_key_state(self.gb, KEYS[button], True)
        self.tick(frames)
        self.lib.GB_set_key_state(self.gb, KEYS[button], False)

    # ---- raw memory
    def _direct(self, kind):
        if kind not in self._access:
            size, bank = C.c_size_t(), C.c_uint16()
            ptr = self.lib.GB_get_direct_access(self.gb, DIRECT[kind], C.byref(size), C.byref(bank))
            self._access[kind] = (ptr, size.value)
        return self._access[kind]

    def _bytes(self, kind, off, n):
        ptr, size = self._direct(kind)
        return C.string_at(ptr + off, n)

    def read(self, addr, bank=None):
        """Byte at addr. WRAM 0xd000-0xdfff takes an explicit bank (1-7)."""
        if bank is not None and 0xd000 <= addr < 0xe000:
            return self._bytes('RAM', bank * 0x1000 + (addr - 0xd000), 1)[0]
        return self.lib.GB_read_memory(self.gb, addr)

    def read_rom(self, bank, addr):
        off = addr if addr < 0x4000 else bank * 0x4000 + (addr & 0x3fff)
        return self._bytes('ROM', off, 1)[0]

    def write(self, addr, value, bank=None):
        if bank is not None and 0xd000 <= addr < 0xe000:
            ptr, _ = self._direct('RAM')
            C.cast(ptr + bank * 0x1000 + (addr - 0xd000), C.POINTER(C.c_uint8))[0] = value
        else:
            self.lib.GB_write_memory(self.gb, addr, value)

    def _loc(self, name, k=0):
        bank, a = self.sym[name]
        a += k
        return (bank, a) if 0xd000 <= a < 0xe000 and bank >= 1 else (None, a)

    def rd(self, name, k=0):
        bank, a = self._loc(name, k)
        return self.read(a, bank)

    def wr(self, name, value, k=0):
        bank, a = self._loc(name, k)
        self.write(a, value, bank)

    def rd16(self, name, k=0):
        return self.rd(name, k) << 8 | self.rd(name, k + 1)

    def dump(self, start, length, bank=None):
        return bytes(self.read(a, bank) for a in range(start, start + length))

    def vram(self, vbk):
        return self._bytes('VRAM', vbk * 0x2000, 0x2000)

    def oam(self):
        return self._bytes('OAM', 0, 160)

    @property
    def pc(self):
        return self._regs[5]

    @property
    def sp(self):
        return self._regs[4]

    @property
    def regs(self):
        r = self._regs
        return {'af': r[0], 'bc': r[1], 'de': r[2], 'hl': r[3], 'sp': r[4], 'pc': r[5]}

    def where(self, pc=None):
        pc = self.regs['pc'] if pc is None else pc
        bank = self.read(0xff87) if 0x4000 <= pc < 0x8000 else 0
        best = None
        for n, (b, a) in self.sym.items():
            if (b == bank or (pc < 0x4000 and b == 0)) and a <= pc and not n.startswith('.'):
                if best is None or a > best[1]:
                    best = (n, a)
        return f'{best[0]}+{pc - best[1]}' if best else f'{bank:02x}:{pc:04x}'

    def frame_rgb(self):
        import numpy as np
        a = np.frombuffer(bytes(self.pixels), dtype=np.uint8).reshape(144, 160, 4)
        return a[:, :, :3].copy()

    # ---- audiovisual monitors (native)
    def enable_av(self, audio_seconds=30, guard=True):
        """Start PCM capture, PPU access-timing monitoring and VBlank-end-line sampling.
        Replaces any Python write watch. Also turns on the execution guard."""
        if guard and self._exec_keep is None:
            self.enable_exec_guard()
        lib = exec_guard_lib()
        io, _ = self._direct('IO')
        lib.execguard_set_io(io)
        lib.av_vblank_reset()
        lib.av_access_reset()
        if guard:
            self._av_write = C.cast(lib.av_write_fn(), WRITE_CB)
            self.lib.GB_set_write_memory_callback(self.gb, self._av_write)
        lib.av_audio_init(48000 * audio_seconds)
        self.lib.GB_set_sample_rate.argtypes = [C.c_void_p, C.c_uint]
        self.lib.GB_set_sample_rate(self.gb, 48000)
        SAMPLE_CB = C.CFUNCTYPE(None, C.c_void_p, C.c_void_p)
        self._av_audio = C.cast(lib.av_audio_fn(), SAMPLE_CB)
        self.lib.GB_apu_set_sample_callback.argtypes = [C.c_void_p, SAMPLE_CB]
        self.lib.GB_apu_set_sample_callback(self.gb, self._av_audio)
        self.lib.GB_set_highpass_filter_mode.argtypes = [C.c_void_p, C.c_int]
        self.lib.GB_set_highpass_filter_mode(self.gb, 1)      # GB_HIGHPASS_ACCURATE: like the hardware's output capacitor

    def vblank_lines(self):
        """{LY: count} of the PPU line when the VBlank handler returned."""
        lib = exec_guard_lib()
        return {i: lib.av_vblank_ly(i) for i in range(154) if lib.av_vblank_ly(i)}

    def access_report(self):
        """(vram_writes, vram_bad, oam_writes, oam_bad, [first illegal accesses])."""
        lib = exec_guard_lib()
        ev = []
        for i in range(min(lib.av_access_count(), 64)):
            a, pc, v, m, ly, k = (C.c_uint16(), C.c_uint16(), C.c_uint8(), C.c_uint8(), C.c_uint8(), C.c_uint8())
            lib.av_access_get(i, C.byref(a), C.byref(pc), C.byref(v), C.byref(m), C.byref(ly), C.byref(k))
            ev.append(dict(addr=a.value, pc=pc.value, value=v.value, mode=m.value, ly=ly.value,
                           kind='VRAM' if k.value == 1 else 'OAM'))
        return lib.av_vram_writes(), lib.av_vram_bad(), lib.av_oam_writes(), lib.av_oam_bad(), ev

    def audio_pcm(self, reset=False):
        """Captured audio so far as an int16 (n, 2) array at 48 kHz."""
        import numpy as np
        lib = exec_guard_lib()
        n = lib.av_audio_count()
        arr = np.frombuffer(C.string_at(lib.av_audio_data(), n * 4), dtype=np.int16).reshape(n, 2).copy() if n else np.zeros((0, 2), np.int16)
        if reset:
            lib.av_audio_reset()
        return arr

    # ---- native execution guard (fast: C callback on every instruction)
    def enable_exec_guard(self):
        lib = exec_guard_lib()
        lib.execguard_reset()
        hram, _ = self._direct('HRAM')
        lib.execguard_set_hram(hram)
        self._guard_cb = C.cast(lib.execguard_fn(), EXEC_CB)
        self.lib.GB_set_execution_callback(self.gb, self._guard_cb)
        self._exec_keep = 'native'

    def counter(self, label):
        """A callable returning how many times the ROM executed `label` (native guard on)."""
        lib = exec_guard_lib()
        bank, addr = self.sym[label]
        idx = lib.execguard_watch(addr, bank if 0x4000 <= addr < 0x8000 else -1)
        if idx < 0:
            raise RuntimeError('too many watched addresses')
        return lambda: lib.execguard_watch_hits(idx)

    def enable_coverage(self):
        lib = exec_guard_lib()
        lib.execguard_coverage(1)

    def coverage_bitmap(self):
        """Executed ROM addresses as bytes (bit per (bank, offset); see execguard.c)."""
        lib = exec_guard_lib()
        return C.string_at(lib.execguard_cover(), lib.execguard_cover_size())

    def exec_events(self):
        """Suspicious executions recorded so far: [(kind, pc, previous pc, opcode)]."""
        lib = exec_guard_lib()
        out = []
        for i in range(min(lib.execguard_count(), 32)):
            pc, prev, op, kind = C.c_uint16(), C.c_uint16(), C.c_uint8(), C.c_uint8()
            lib.execguard_get(i, C.byref(pc), C.byref(prev), C.byref(op), C.byref(kind))
            out.append((KIND.get(kind.value, '?'), pc.value, prev.value, op.value))
        return out

    # ---- instruction / memory hooks (slow in Python: use sparingly)
    def exec_hook(self, label, fn, replace=True):
        """Run fn(game) each time the instruction at `label` is about to execute. With
        replace=False the hook is added to any existing ones at that address."""
        bank, a = self.sym[label]
        if replace or a not in self._exec_hooks:
            self._exec_hooks[a] = (bank, fn)
        else:
            old = self._exec_hooks[a][1]
            self._exec_hooks[a] = (bank, lambda game, o=old, n=fn: (o(game), n(game)))
        if self._exec_keep is None:
            def cb(gb, addr, opcode):
                h = self._exec_hooks.get(addr)
                if h and (addr < 0x4000 or self.read(0xff87) == h[0]):
                    h[1](self)
            self._exec_keep = EXEC_CB(cb)
            self.lib.GB_set_execution_callback(self.gb, self._exec_keep)

    def write_watch(self, lo, hi, fn, wram_bank=None):
        """Call fn(game, addr, old, new, pc) for every CPU write to [lo, hi) (a strict
        memory-access watchpoint). With wram_bank set, 0xd000-0xdfff writes only
        count while that WRAM bank is mapped. fn returns False to block the write."""
        def cb(gb, addr, value):
            if addr < lo or addr >= hi:
                return True
            if wram_bank is not None and 0xd000 <= addr < 0xe000:
                io, _ = self._direct('IO')
                bank = (C.cast(io, C.POINTER(C.c_uint8))[0x70] & 7) or 1
                if bank != wram_bank:
                    return True
            old = self.lib.GB_read_memory(self.gb, addr)
            r = fn(self, addr, old, value, self.regs['pc'])
            return True if r is None else bool(r)
        self._wcb = WRITE_CB(cb)
        self.lib.GB_set_write_memory_callback(self.gb, self._wcb)

    # ---- calling a ROM routine from the main thread (injection; see emu.Game.call)
    def call(self, label, a=0, bc=0, de=0, hl=0, max_frames=600, mash=None):
        bank, entry = self.sym[label]
        halt = self.sym['DelayFrameHalt'][1]
        r = self._regs
        state = {'job': (entry, bank, a, bc, de, hl), 'saved': None, 'result': None, 'running': False}

        def on_halt(game):
            if state['running']:
                if r[4] != state['saved'][4]:
                    return                       # a nested DelayFrameHalt inside the routine
                state['result'] = (r[0] >> 8) & 0xff
                for i in range(6):
                    r[i] = state['saved'][i]
                self.lib.GB_write_memory(self.gb, 0x2000, state['rb'])
                self.lib.GB_write_memory(self.gb, 0xff87, state['rb'])
                state['running'] = False
            elif state['job']:
                e, bk, aa, bcc, dee, hll = state['job']
                state['job'] = None
                state['saved'] = [r[i] for i in range(6)]
                state['rb'] = self.read(0xff87)
                if 0x4000 <= e < 0x8000:
                    self.lib.GB_write_memory(self.gb, 0x2000, bk)
                    self.lib.GB_write_memory(self.gb, 0xff87, bk)
                sp = (r[4] - 2) & 0xffff
                self.lib.GB_write_memory(self.gb, sp, halt & 0xff)
                self.lib.GB_write_memory(self.gb, sp + 1, halt >> 8)
                r[4] = sp
                r[0] = aa << 8 | (r[0] & 0xff)
                r[1], r[2], r[3] = bcc, dee, hll
                r[5] = e
                state['running'] = True
        prev_hook = self._exec_hooks.get(halt)
        self.exec_hook('DelayFrameHalt', on_halt, replace=False)
        self._call_handlers = getattr(self, '_call_handlers', [])
        self._call_handlers.append(on_halt)
        try:
            for i in range(max_frames):
                if mash and i % 12 == 0:
                    self.lib.GB_set_key_state(self.gb, KEYS[mash], True)
                elif mash and i % 12 == 4:
                    self.lib.GB_set_key_state(self.gb, KEYS[mash], False)
                self.tick(1)
                if state['result'] is not None:
                    return state['result']
            raise AssertionError(f'{label} did not return (pc={r[5]:04x}, {self.where()})')
        finally:
            self._call_handlers.remove(on_halt)
            # drop our hook again: a Python callback on every instruction costs ~2/3 of the run time
            if self._exec_keep not in (None, 'native') and not state['running']:
                if prev_hook is None:
                    self._exec_hooks.pop(halt, None)
                else:
                    self._exec_hooks[halt] = prev_hook
                if not self._exec_hooks:
                    self.lib.GB_set_execution_callback(self.gb, EXEC_CB(0))
                    self._exec_keep = None

    hook = exec_hook   # same name as the PyBoy backend; fn receives the game

    def screenshot(self, name):
        from PIL import Image
        path = os.path.join(self.workdir, name if name.endswith('.png') else name + '.png')
        im = Image.frombuffer('RGBA', (160, 144), bytes(self.pixels), 'raw', 'RGBA', 0, 1)
        im.convert('RGB').save(path)
        return path

    def in_battle(self):
        return self.rd('wBattleMode') != 0

    def save_point(self):
        """Snapshot the machine; restore_point() returns to it."""
        self.lib.GB_get_save_state_size = getattr(self.lib, 'GB_get_save_state_size')
        self.lib.GB_get_save_state_size.argtypes = [C.c_void_p]
        self.lib.GB_get_save_state_size.restype = C.c_size_t
        self.lib.GB_save_state_to_buffer.argtypes = [C.c_void_p, C.c_char_p]
        n = self.lib.GB_get_save_state_size(self.gb)
        buf = C.create_string_buffer(n)
        self.lib.GB_save_state_to_buffer(self.gb, buf)
        self._point = buf

    def dump_state(self, path):
        self.save_point()
        open(path, 'wb').write(bytes(self._point))

    def load_state_file(self, path):
        data = open(path, 'rb').read()
        self.lib.GB_load_state_from_buffer.argtypes = [C.c_void_p, C.c_char_p, C.c_size_t]
        if self.lib.GB_load_state_from_buffer(self.gb, data, len(data)):
            raise RuntimeError('SameBoy refused the state file')

    def restore_point(self):
        self.lib.GB_load_state_from_buffer.argtypes = [C.c_void_p, C.c_char_p, C.c_size_t]
        if self.lib.GB_load_state_from_buffer(self.gb, self._point, len(self._point)):
            raise RuntimeError('SameBoy refused its own save state')

    def save_sram(self):
        n = self.lib.GB_save_battery_size(self.gb)
        buf = C.create_string_buffer(n)
        self.lib.GB_save_battery_to_buffer(self.gb, buf, n)
        return buf.raw

    def close(self):
        pass
