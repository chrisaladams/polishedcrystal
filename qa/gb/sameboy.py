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
        self.lib.GB_set_turbo_mode(self.gb, True, True)   # no real-time pacing
        self._regs = self.lib.GB_get_registers(self.gb)
        self._access = {}
        self._exec_hooks = {}
        self._exec_keep = None

    # ---- time and input
    def tick(self, n=1, render=True):
        for _ in range(n):
            self.lib.GB_run_frame(self.gb)
            self.frame += 1

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

    # ---- instruction / memory hooks (slow in Python: use sparingly)
    def exec_hook(self, label, fn):
        bank, a = self.sym[label]
        self._exec_hooks[a] = (bank, fn)
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

    def screenshot(self, name):
        from PIL import Image
        path = os.path.join(self.workdir, name if name.endswith('.png') else name + '.png')
        im = Image.frombuffer('RGBA', (160, 144), bytes(self.pixels), 'raw', 'RGBA', 0, 1)
        im.convert('RGB').save(path)
        return path

    def save_sram(self):
        n = self.lib.GB_save_battery_size(self.gb)
        buf = C.create_string_buffer(n)
        self.lib.GB_save_battery_to_buffer(self.gb, buf, n)
        return buf.raw

    def close(self):
        pass
