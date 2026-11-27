"""Cartridge, header and power-on state checks."""
from qa import meta
from qa.framework import qa_test
from qa.gb import fixtures as F, saves
from qa.gb.consts import map_ids

NINTENDO_LOGO = bytes.fromhex('CEED6666CC0D000B03730083000C000D0008111F8889000EDCCC6EE6DDDDD999BBBB67636E0EECCCDDDC999FBBB9333E')


@qa_test(suites=('hardware', 'general', 'full'), covers=('hw.header', 'hw.mapper'),
         provenance='static: the built ROM file')
def rom_header_and_mapper(ctx):
    d = open(ctx.rom, 'rb').read()
    h = meta.rom_header(ctx.rom)
    ctx.expect(d[0x104:0x134] == NINTENDO_LOGO, 'Nintendo logo bytes are wrong')
    chk = 0
    for b in d[0x134:0x14d]:
        chk = (chk - b - 1) & 0xff
    ctx.expect(chk == d[0x14d], 'header checksum %02x != computed %02x' % (d[0x14d], chk))
    total = (sum(d) - d[0x14e] - d[0x14f]) & 0xffff
    ctx.expect(total == h['global_checksum'], 'global checksum mismatch')
    ctx.expect(h['cartridge_type'] == 0x1b, 'cartridge type %02x, expected 1b (MBC5+RAM+BATTERY)' % h['cartridge_type'])
    ctx.expect(h['cartridge_type'] not in (0x0f, 0x10), 'header claims a real-time clock; the world clock is software')
    ctx.expect(h['ram_size_code'] == 3, 'RAM size code %d, expected 3 (32 KiB)' % h['ram_size_code'])
    ctx.expect(h['rom_bytes'] == 0x8000 << h['rom_size_code'], 'ROM size code %d does not match %d bytes' % (h['rom_size_code'], h['rom_bytes']))
    ctx.expect(h['cgb_flag'] in (0x80, 0xc0), 'CGB flag %02x' % h['cgb_flag'])
    ctx.note('%s, %d KiB ROM, 32 KiB SRAM, CGB flag %02x (%s)' % (h['cartridge'], h['rom_bytes'] // 1024, h['cgb_flag'],
             'CGB only' if h['cgb_flag'] == 0xc0 else 'CGB enhanced: also boots on a DMG'))
    # MBC5 allows 9-bit ROM banking: the last bank referenced must exist
    last = max(b for b, a in [v for v in ctx.sym_banks()])
    ctx.expect(last < h['rom_bytes'] // 0x4000, 'symbols reference ROM bank %d beyond the file' % last)


@qa_test(suites=('hardware', 'full'), covers=('hw.startup_ram',), backends=('pyboy', 'sameboy'),
         provenance='power-on to bedroom by button input; RAM noise seeded', timeout=900)
def power_on_ram_noise(ctx):
    """Real consoles power on with arbitrary RAM. Boot with several noise seeds and
    require the same outcome as clean RAM: New Game reaches the bedroom."""
    outcomes = {}
    for seed in range(1, 6):
        if ctx.backend == 'sameboy':
            from qa.gb.sameboy import SBGame
            g = SBGame(rom=ctx.rom, workdir=ctx.out, model=ctx.model or 'CGB-E', seed=seed * 7919)
        else:
            from qa.gb.emu import Game
            g = Game(rom=ctx.rom, workdir=ctx.out, power_on_noise=seed)
        try:
            n = F.new_game_to_bedroom(g)
            outcomes[seed] = (n, F.where(g))
        except TimeoutError as e:
            outcomes[seed] = ('never reached the bedroom', str(e))
            ctx.snapshot(g, 'noise_seed_%d' % seed)
    ctx.note(str(outcomes))
    good = {v for v in outcomes.values() if isinstance(v[0], int)}
    ctx.expect(len(good) == 1 and len(good) == len(set(outcomes.values())),
               'power-on noise changed the outcome: %r' % outcomes)
