#
# License: See LICENSE.md file
# GitHub: https://github.com/Baekalfen/PyBoy
#

import threading
import multiprocessing
from multiprocessing import shared_memory
import pyboy
from pyboy.utils import MAX_CYCLES, PyBoyInvalidOperationException

import cython

logger = pyboy.logging.get_logger(__name__)


CYCLES_8192HZ = 128


class Serial:
    def __init__(self, cgb_mode, emulate=True):
        self.cgb_mode = cgb_mode  # Indicates if we are CGB hardware, running in CGB or DMG mode
        self.emulate = emulate
        self.SB = 0xFF  # Always 0xFF for a disconnected link cable
        if self.cgb_mode:
            self.SC = 0b01111100
        else:
            self.SC = 0b01111110
        self.transfer_enabled = 0
        self.internal_clock = 0
        self._cycles_to_interrupt = MAX_CYCLES if not self.emulate else 0
        self.last_cycles = 0
        self.clock = 0
        self.clock_target = MAX_CYCLES

    def set_SB(self, value):
        if not self.emulate:
            return
        # Always 0xFF when cable is disconnected. Connecting is not implemented yet.
        self.SB = 0xFF

    def set_SC(self, value):  # cgb, double_speed
        if not self.emulate:
            return
        if self.cgb_mode:
            self.SC = value | 0b01111100  # Mask out read-only bits
        else:
            self.SC = value | 0b01111110  # Mask out read-only bits
        self.transfer_enabled = self.SC & 0x80
        # TODO:
        # if cgb and (self.SC & 0b10): # High speed transfer
        #     self.double_speed = ...
        self.internal_clock = self.SC & 1  # 0: external, 1: internal
        if self.internal_clock:
            self.clock_target = self.clock + 8 * CYCLES_8192HZ
            self._cycles_to_interrupt = self.clock_target - self.clock
        else:
            # Will never complete, as there is no connection
            self.transfer_enabled = 0  # Technically it is enabled, but no reason to track it.
            self.clock_target = MAX_CYCLES
            # The clock keeps counting, so the distance to the MAX_CYCLES
            # sentinel would eventually go negative and stall the
            # coordinator loop at the minimum cycle target.
            self._cycles_to_interrupt = MAX_CYCLES

    def tick(self, _cycles):
        cycles = _cycles - self.last_cycles
        if cycles == 0:
            return False
        self.last_cycles = _cycles

        if not self.emulate:
            self._cycles_to_interrupt = MAX_CYCLES
            return False

        self.clock += cycles

        interrupt = False
        if self.transfer_enabled and self.clock >= self.clock_target:
            # Clear bit 7 (transfer in progress). Games poll this bit to
            # detect transfer completion.
            self.SC &= 0b01111111
            self.transfer_enabled = 0
            # self._cycles_to_interrupt = MAX_CYCLES
            self.clock_target = MAX_CYCLES
            interrupt = True

        if self.transfer_enabled:
            self._cycles_to_interrupt = self.clock_target - self.clock
        else:
            # The clock keeps counting, so the distance to the MAX_CYCLES
            # sentinel would eventually go negative and stall the
            # coordinator loop at the minimum cycle target.
            self._cycles_to_interrupt = MAX_CYCLES
        return interrupt

    def save_state(self, f):
        f.write(self.SB)
        f.write(self.SC)
        f.write(self.transfer_enabled)
        f.write(self.internal_clock)
        f.write_64bit(self.last_cycles)
        f.write_64bit(self._cycles_to_interrupt)
        f.write_64bit(self.clock)
        f.write_64bit(self.clock_target)

    def load_state(self, f, state_version):
        self.SB = f.read()
        self.SC = f.read()
        self.transfer_enabled = f.read()
        self.internal_clock = f.read()
        self.last_cycles = f.read_64bit()
        self._cycles_to_interrupt = f.read_64bit()
        self.clock = f.read_64bit()
        self.clock_target = f.read_64bit()
        if not self.emulate:
            self.SB = 0xFF
            self.SC = 0b01111100 if self.cgb_mode else 0b01111110
            self.transfer_enabled = 0
            self.internal_clock = 0
            self._cycles_to_interrupt = MAX_CYCLES
            self.clock = 0
            self.clock_target = MAX_CYCLES

    def stop(self):
        pass


class SerialSharedMemory(Serial):
    """A lockstep link cable with real clock semantics.

    Two emulators (one per process) share a small memory block. Each side
    publishes its cycle count and waits whenever it gets more than
    `sync_window` cycles ahead of the other, so the two run in lockstep.

    Only the side using the internal clock drives a transfer. When its 8 bits
    have been clocked out, it exchanges bytes with the other side if that side
    is waiting with the external clock and the transfer bit set; otherwise it
    reads $FF (nothing on the other end). An external-clock side never
    completes on its own: it completes when the clock side delivers a byte.

    Layout of each side's 64-byte slot: +0 cycles (u64), +8 armed for an
    external transfer, +9 SB, +10 delivery pending, +11 delivered byte,
    +12 alive.
    """

    def __init__(self, cgb_mode, shared_memory, serial_interrupt_based):
        super().__init__(cgb_mode)
        self.shared_memory = shared_memory
        self.shared_slot = shared_memory.slot
        self.me = lk_ptr(shared_memory.address + 64 * self.shared_slot)
        self.other = lk_ptr(shared_memory.address + 64 * (1 - self.shared_slot))
        self.interrupt_based = serial_interrupt_based
        self.bits_transferred = 0
        self.sync_step = 64
        self.sync_window = 128
        self.SB = 0xFF
        lk_set8(self.me + 9, 0xFF)
        lk_set8(self.me + 8, 0)
        lk_set8(self.me + 10, 0)
        self._cycles_to_interrupt = self.sync_step

    def save_state(self, f):
        raise PyBoyInvalidOperationException("Save state is not supported with serial connection")

    def load_state(self, f, state_version):
        raise PyBoyInvalidOperationException("Load state is not supported with serial connection")

    def set_SB(self, value):
        self.SB = value
        lk_set8(self.me + 9, value)

    def set_SC(self, value):
        if self.cgb_mode:
            self.SC = value | 0b01111100
        else:
            self.SC = value | 0b01111110
        self.transfer_enabled = self.SC & 0x80
        self.internal_clock = self.SC & 1
        lk_set8(self.me + 10, 0)
        if self.transfer_enabled and self.internal_clock:
            if self.cgb_mode and (self.SC & 0b10):
                self.clock_target = self.clock + 8 * CYCLES_8192HZ // 32
            else:
                self.clock_target = self.clock + 8 * CYCLES_8192HZ
            lk_set8(self.me + 8, 0)
        else:
            self.clock_target = MAX_CYCLES
            lk_set8(self.me + 8, 1 if self.transfer_enabled else 0)
        self._cycles_to_interrupt = self.sync_step

    def tick(self, _cycles):
        cycles = _cycles - self.last_cycles
        if cycles == 0:
            return False
        self.last_cycles = _cycles
        self.clock += cycles
        lk_set64(self.me, self.clock)

        # lockstep: wait while we are too far ahead of a live partner
        spins = 0
        while lk_get8(self.other + 12) and lk_get64(self.other) + self.sync_window < self.clock:
            spins += 1
            if spins > 200:
                lk_yield()

        interrupt = False
        if self.transfer_enabled:
            if self.internal_clock:
                if self.clock >= self.clock_target:
                    if lk_get8(self.other + 8):
                        lk_set8(self.other + 8, 0)
                        lk_set8(self.other + 11, lk_noise(self.other, self.SB))
                        lk_set8(self.other + 10, 1)
                        self.SB = lk_noise(self.me, lk_get8(self.other + 9))
                    else:
                        self.SB = 0xFF
                    lk_set8(self.me + 9, self.SB)
                    self.SC &= 0b0111_1111
                    self.transfer_enabled = 0
                    self.clock_target = MAX_CYCLES
                    interrupt = True
            elif lk_get8(self.me + 10):
                lk_set8(self.me + 10, 0)
                self.SB = lk_get8(self.me + 11)
                lk_set8(self.me + 9, self.SB)
                self.SC &= 0b0111_1111
                self.transfer_enabled = 0
                interrupt = True

        if self.transfer_enabled and self.internal_clock and self.clock_target - self.clock < self.sync_step:
            self._cycles_to_interrupt = self.clock_target - self.clock
        else:
            self._cycles_to_interrupt = self.sync_step
        return interrupt

    def stop(self):
        lk_set8(self.me + 12, 0)


class SerialSharedMemoryBuffer:
    def __init__(self, name=None):
        self.connected = True
        self.barrier = multiprocessing.Barrier(2)
        self._owner = name is None
        self._shared_memory = (
            shared_memory.SharedMemory(create=True, size=2) if name is None else shared_memory.SharedMemory(name=name)
        )

    def write(self, slot, value):
        if self.connected:
            self._shared_memory.buf[slot] = value

    def read(self, slot):
        if self.connected:
            return self._shared_memory.buf[slot]
        else:
            return 1

    def synchronize(self):
        if self.connected:
            try:
                self.barrier.wait(timeout=30)
            except threading.BrokenBarrierError:
                logger.error("Connection lost to the other emulator")
                self.connected = False  # TODO: Reconnect?

    def __del__(self):
        self.close()

    def close(self):
        self._shared_memory.close()
        try:
            self._shared_memory.unlink()
        except FileNotFoundError:
            pass
