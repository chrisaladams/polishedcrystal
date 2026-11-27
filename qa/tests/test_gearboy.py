"""Cartridge facts and symbol loading as seen by a third, independent emulator (Gearboy,
driven over its MCP server). Skipped, not passed, when Gearboy is not installed."""
import os

from qa.framework import qa_test
from qa.gb.emu import load_sym


@qa_test(suites=('hardware', 'general', 'full'), covers=('hw.mapper', 'hw.header'),
         provenance='static + Gearboy headless via MCP; no gameplay')
def gearboy_agrees_on_cartridge(ctx):
    import json
    from qa.gb import gearboy_mcp
    if not os.path.exists(gearboy_mcp.GEARBOY):
        ctx.skip('Gearboy not built (qa/setup.sh)')
    from qa import meta as M
    h = M.rom_header(ctx.rom)
    sym = load_sym(ctx.rom[:-4] + '.sym')
    with gearboy_mcp.Gearboy(ctx.rom) as gb:
        info = json.loads(gb.call('get_media_info'))
        ctx.expect(info['valid_rom'], 'Gearboy says the ROM is not valid')
        ctx.expect(info['active_mapper'] == 'MBC5', f'mapper {info["active_mapper"]}, expected MBC5')
        ctx.expect(info['has_battery'], 'no battery-backed RAM detected')
        ctx.expect(not info['is_rtc'], 'a real-time clock was detected; the world clock is software')
        ctx.expect(info['is_cgb'], 'not detected as a Game Boy Color game')
        ctx.expect(info['rom_bank_count'] * 0x4000 == h['rom_bytes'], 'ROM bank count disagrees with the file size')
        ctx.expect(info['ram_bank_count'] == 4, f'RAM banks {info["ram_bank_count"]}, expected 4 (32 KiB)')
        ctx.note('Gearboy %s: %s, %d ROM banks, %d RAM banks, battery=%s, rtc=%s' % (
            info['emulator_version'], info['active_mapper'], info['rom_bank_count'], info['ram_bank_count'],
            info['has_battery'], info['is_rtc']))
        for name in ('wMapGroup', 'hROMBank', 'DelayFrameHalt'):
            got = json.loads(gb.call('lookup_symbol_by_name', name=name))
            text = json.dumps(got).lower()
            addr = '%04x' % sym[name][1]
            ctx.expect(addr in text, f'symbol {name}: expected address {addr}, Gearboy says {text[:120]}')
        for _ in range(120):
            gb.call('debug_step_frame')
        cpu = gb.call('get_cpu_status')
        ctx.note('after 120 frames Gearboy CPU: ' + str(cpu)[:160].replace('\n', ' '))
