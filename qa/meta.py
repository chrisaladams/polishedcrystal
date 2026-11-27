"""Run metadata: everything needed to reproduce a result."""
import datetime
import os
import platform
import re
import shutil
import subprocess

from qa.gb.emu import ROOT, default_rom, sha1


def _run(cmd, cwd=None):
    try:
        return subprocess.check_output(cmd, cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return 'unavailable'


def rom_header(path):
    d = open(path, 'rb').read()
    cart = {0x1b: 'MBC5+RAM+BATTERY', 0x19: 'MBC5', 0x1a: 'MBC5+RAM', 0x10: 'MBC3+TIMER+RAM+BATTERY',
            0x13: 'MBC3+RAM+BATTERY'}
    return {
        'title': d[0x134:0x143].rstrip(b'\0').decode('ascii', 'replace'),
        'cgb_flag': d[0x143], 'cartridge_type': d[0x147], 'cartridge': cart.get(d[0x147], hex(d[0x147])),
        'rom_size_code': d[0x148], 'rom_bytes': len(d), 'ram_size_code': d[0x149],
        'header_checksum': d[0x14d], 'global_checksum': d[0x14e] << 8 | d[0x14f],
    }


def collect(rom=None, seed=None, extra=None):
    rom = rom or default_rom()
    gb = os.environ.get('GBDEV_DIR', '/home/user/gbdev')
    sameboy = os.environ.get('SAMEBOY_DIR', os.path.join(gb, 'SameBoy'))
    gearboy = os.environ.get('GEARBOY_DIR', os.path.join(gb, 'Gearboy'))
    try:
        import importlib.metadata as im
        pyboy_version = im.version('pyboy')
    except Exception:
        pyboy_version = 'unavailable'
    rgbasm = shutil.which('rgbasm') or '/opt/rgbds/bin/rgbasm'
    meta = {
        'time_utc': datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z',
        'rom': {'path': os.path.relpath(rom, ROOT), 'sha1': sha1(rom), 'header': rom_header(rom)},
        'git': {'commit': _run(['git', '-C', ROOT, 'rev-parse', 'HEAD']),
                'branch': _run(['git', '-C', ROOT, 'rev-parse', '--abbrev-ref', 'HEAD']),
                'dirty': bool(_run(['git', '-C', ROOT, 'status', '--porcelain', '--untracked-files=no']))},
        'tools': {'python': platform.python_version(), 'pyboy': pyboy_version,
                  'sameboy': _run(['git', '-C', sameboy, 'rev-parse', '--short', 'HEAD']),
                  'gearboy': _run(['git', '-C', gearboy, 'describe', '--always', '--tags']),
                  'rgbds': _run([rgbasm, '--version'])},
        'host': {'platform': platform.platform(), 'cpus': os.cpu_count()},
        'seed': seed,
        'hardware_configuration': 'emulated only: no physical console results are included',
    }
    if extra:
        meta.update(extra)
    return meta
