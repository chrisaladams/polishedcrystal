#!/usr/bin/env python3
"""Check the cartridge clock through Continue, VBlank, saves and scheduled events."""
import sys
from pathlib import Path

from test_orange_league import ROOT
from test_wild_mons import Game, rgbasm_values


CLOCK = ('wRTCDayLo', 'wRTCHours', 'wRTCMinutes', 'wRTCSeconds')


def clock(game):
    return tuple(game.rd(field) for field in CLOCK)


def set_clock(game, values):
    for field, value in zip(CLOCK, values):
        game.wr(field, value)


def word(game, name, value=None):
    if value is None:
        return game.rd(name) | game.rd(name, 1) << 8
    game.wr(name, value & 255)
    game.wr(name, value >> 8, 1)


def run_clock_code(game, name, *, seconds=0):
    """Call the assembled code on the emulated CPU. Restore a state before UI input."""
    memory, registers = game.m, game.pb.register_file
    bank, address = game.sym[name]
    memory[0xffff] = memory[0xff0f] = 0  # no interrupts during the injected call
    memory[0xff70] = 1
    if bank:
        memory[0x2000] = memory[game.addr('hROMBank')] = bank
    call = bytes((0xcd, address & 255, address >> 8))
    if seconds:
        # One real timer update per iteration, skipping the preceding idle frames.
        frame = game.addr('wGameTimeFrames')
        program = bytes((0x01, seconds & 255, seconds >> 8, 0xc5, 0x3e, 59,
                         0xea, frame & 255, frame >> 8)) + call
        program += bytes((0xc1, 0x0b, 0x78, 0xb1, 0x20, (-15) & 255))
    else:
        program = call
    start = 0xff90
    stop = start + len(program)
    for i, byte in enumerate(program + b'\x18\xfe'):
        memory[start + i] = byte
    registers.SP, registers.PC = 0xc0e0, start
    for _ in range(500):
        game.pb.tick(1, False)
        if registers.PC in (stop, stop + 1):
            return
    raise AssertionError(f'{name} did not return')


def legacy_save(game, original, *, hardware, bad_primary=False):
    """Construct an older valid save with disagreeing raw and saved display times."""
    data = bytearray(original[:0x8000])

    def offset(name):
        bank, ptr = game.sym[name]
        return bank * 0x2000 + ptr - 0xa000

    def player_field(prefix, name):
        return offset('s' + prefix + 'PlayerData') + game.addr(name) - game.addr('wPlayerData')

    for prefix in ('', 'Backup'):
        place = player_field(prefix, 'wRTC')
        data[place:place + 4] = bytes((6, 23, 59, 52))
        place = player_field(prefix, 'wRTCDayLo')
        data[place:place + 4] = bytes((100, 12, 0, 0))
        place = player_field(prefix, 'wSoftwareClockMarker')
        data[place:place + 4] = bytes(4)
        opt = offset('s' + prefix + 'Options') + game.addr('wInitialOptions2') - game.addr('wOptions')
        data[opt] = (data[opt] & ~8) | (8 if hardware else 0)
        base = offset('s' + prefix + 'GameData')
        end = offset('s' + prefix + 'GameDataEnd')
        checksum = offset('s' + prefix + 'Checksum')
        data[checksum:checksum + 2] = (sum(data[base:end]) & 65535).to_bytes(2, 'little')
    if bad_primary:
        checksum = offset('sChecksum')
        data[checksum] ^= 1
    # The old RTC overflow flag must not force a time reset.
    data[offset('sRTCStatusFlags')] = 0x80
    return bytes(data) + original[0x8000:]


def main(path):
    original = Path(path).read_bytes()
    rom = (Path(ROOT) / 'polishedcrystal-3.2.3.gbc').read_bytes()
    assert rom[0x147] == 0x1b  # MBC5 with battery-backed RAM: no RTC (Link Edition, 4 MiB carts)
    k = rgbasm_values(('MORN', 'DAY', 'EVE', 'NITE', 'SOFTWARE_CLOCK_MARKER', 'WORLD_CLOCK_DAYS',
                       'STATUSFLAGS2_BUG_CONTEST_TIMER_F', 'BUG_CONTEST_MINUTES', 'LIGHTNING_ROD',
                       'NORMAL', 'FAIRY'), None)
    game = Game(original)
    fixtures = [legacy_save(game, original, hardware=True),
                legacy_save(game, original, hardware=False, bad_primary=True)]
    game.pb.stop(save=False)
    for fixture in fixtures:
        game = Game(fixture)
        try:
            game.boot()
            assert word(game, 'wSoftwareClockMarker') == k['SOFTWARE_CLOCK_MARKER']
            day, hour, minute, second = clock(game)
            resumed = (day - 6) * 86400 + hour * 3600 + minute * 60 + second
            assert 86392 <= resumed < 86400 + 4 * 60, clock(game)
        finally:
            game.pb.stop(save=False)

    game = Game(fixtures[0])
    try:
        game.boot()
        base = game.state()
        game.wr('wGameLogicPaused', 0)
        game.wr('wGameTimerPaused', 1)
        game.wr('wGameTimeFrames', 0)
        game.wr('wClockFramePhase', 0)
        set_clock(game, (10, 10, 0, 0))
        word(game, 'wGameplaySeconds', 0)
        # 100 measured seconds through the unmodified VBlank path.
        game.pb.tick(5960, False)
        assert word(game, 'wGameplaySeconds') == 99
        game.pb.tick(13, False)
        assert word(game, 'wGameplaySeconds') == 100
        assert clock(game) == (10, 10, 26, 40)

        # Simulate complete periods through the real second-update routine.
        game.load(base)
        set_clock(game, (0, 6, 0, 0))
        run_clock_code(game, 'UpdateGameTimer', seconds=2700)
        assert clock(game) == (0, 18, 0, 0)
        run_clock_code(game, 'UpdateTime')
        assert game.rd('wTimeOfDay') == k['NITE']
        run_clock_code(game, 'UpdateGameTimer', seconds=2700)
        assert clock(game) == (1, 6, 0, 0)
        run_clock_code(game, 'UpdateTime')
        assert game.rd('wTimeOfDay') == k['MORN']
        run_clock_code(game, 'UpdateGameTimer', seconds=6 * 5400)
        assert clock(game) == (7, 6, 0, 0)
        run_clock_code(game, 'UpdateTime')
        run_clock_code(game, 'Var_DayOfWeek')
        assert game.rd('wStringBuffer2') == 0
        for hour, palette in ((8, 'MORN'), (9, 'DAY'), (14, 'DAY'), (15, 'EVE'), (17, 'EVE')):
            set_clock(game, (7, hour, 59, 59))
            run_clock_code(game, 'UpdateTime')
            assert game.rd('wTimeOfDay') == k[palette]

        # Advance past the day counter wrap and let the normal daily reset run.
        set_clock(game, (k['WORLD_CLOCK_DAYS'] - 1, 23, 59, 57))
        run_clock_code(game, 'KimonoCupToday')
        assert game.rd('wCupFoeType') == k['FAIRY']
        game.wr('wDailyResetTimer', 1)
        game.wr('wDailyResetTimer', k['WORLD_CLOCK_DAYS'] - 1, 1)
        game.wr('wDailyFlags', 255)
        game.wr('wFruitTreeFlags', 255)
        run_clock_code(game, 'UpdateGameTimer', seconds=1)
        assert clock(game) == (0, 0, 0, 13)
        run_clock_code(game, 'KimonoCupToday')
        assert game.rd('wCupFoeType') == k['NORMAL']
        run_clock_code(game, 'UpdateTime')
        run_clock_code(game, 'CheckDailyResetTimer')
        assert game.rd('wDailyFlags') == 0 and game.rd('wFruitTreeFlags') == 0
        run_clock_code(game, 'GetTodaysSightingNames')
        sighting_before = game.rd('wNamedObjectIndex')
        run_clock_code(game, 'UpdateGameTimer', seconds=5400)
        run_clock_code(game, 'GetTodaysSightingNames')
        assert game.rd('wNamedObjectIndex') != sighting_before

        # Continue a software-clock save with a day from the old 140-day cycle.
        set_clock(game, (139, 12, 34, 56))
        game.wr('wDailyResetTimer', 1)
        game.wr('wDailyResetTimer', 139, 1)
        game.wr('wDailyFlags', 255)
        run_clock_code(game, 'RestoreGameClock')
        assert clock(game) == (139 - k['WORLD_CLOCK_DAYS'], 12, 34, 56)
        run_clock_code(game, 'UpdateTime')
        run_clock_code(game, 'CheckDailyResetTimer')
        assert game.rd('wDailyFlags') == 255

        # The phone counts real gameplay seconds even across the 16-bit wrap.
        word(game, 'wGameplaySeconds', 65530)
        run_clock_code(game, 'GetLeadAbility')
        lightning_rod = game.pb.register_file.A == k['LIGHTNING_ROD']
        run_clock_code(game, 'InitCallReceiveDelay')
        assert word(game, 'wPhoneDelayRemaining') == 1200
        seconds = 600 if lightning_rod else 1200
        run_clock_code(game, 'UpdateGameTimer', seconds=seconds - 1)
        run_clock_code(game, 'CheckReceiveCallTimer')
        assert not game.rd('wTimeCyclesSinceLastCall')
        run_clock_code(game, 'UpdateGameTimer', seconds=1)
        run_clock_code(game, 'CheckReceiveCallTimer')
        assert game.rd('wTimeCyclesSinceLastCall') == 1
        assert word(game, 'wPhoneDelayRemaining') == 600

        # The 20-minute contest uses play seconds, including during a battle.
        game.wr('wStatusFlags2', game.rd('wStatusFlags2') | (1 << k['STATUSFLAGS2_BUG_CONTEST_TIMER_F']))
        game.wr('wBattleMode', 1)
        run_clock_code(game, 'StartBugContestTimer')
        assert game.rd('wBugContestMinsRemaining') == k['BUG_CONTEST_MINUTES']
        run_clock_code(game, 'UpdateGameTimer', seconds=20 * 60 - 1)
        assert game.rd('wBugContestMinsRemaining') == 0
        assert game.rd('wBugContestSecsRemaining') == 1
        run_clock_code(game, 'UpdateGameTimer', seconds=1)
        assert not game.rd('wBugContestSecsRemaining')

        # Link mode freezes both clocks, independently of the saved local time.
        for hour in (8, 23):
            set_clock(game, (2, hour, 0, 0))
            elapsed = word(game, 'wGameplaySeconds')
            game.wr('wLinkMode', 1)
            run_clock_code(game, 'UpdateGameTimer', seconds=60)
            assert clock(game) == (2, hour, 0, 0)
            assert word(game, 'wGameplaySeconds') == elapsed
        game.wr('wLinkMode', 0)
        game.wr('wGameTimeCap', 1)
        run_clock_code(game, 'UpdateGameTimer', seconds=1)
        assert clock(game) == (2, 23, 0, 16)

        # A manual save persists the time and counters, then Continue resumes.
        game.load(base)
        set_clock(game, (20, 18, 10, 0))
        word(game, 'wGameplaySeconds', 5700)
        game.manual_save()
        saved = game.sram()
        game.pb.stop(save=False)
        game = Game(saved)
        game.boot()
        assert clock(game)[:2] == (20, 18), clock(game)
        assert 5700 <= word(game, 'wGameplaySeconds') <= 5715
        print('Passed hardware-free clock, legacy and backup saves, day/night, week and day wrap, sightings, phone, contest, link pause and manual Continue.')
    finally:
        game.pb.stop(save=False)


if __name__ == '__main__':
    main(sys.argv[1])
