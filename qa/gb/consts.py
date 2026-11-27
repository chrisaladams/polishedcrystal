"""Evaluate game constants (species, maps, flags...) with rgbasm, exactly as the build does."""
import os
import re
import shutil
import subprocess
import tempfile

from .emu import ROOT


def rgbasm():
    for p in (os.environ.get('RGBASM'), shutil.which('rgbasm'), '/opt/rgbds/bin/rgbasm'):
        if p and os.path.exists(p):
            return p
    raise RuntimeError('rgbasm not found; run qa/setup.sh')


def values(names, faithful=False):
    """{name: int} for each constant that is defined."""
    with tempfile.NamedTemporaryFile('w', suffix='.asm', delete=False) as f:
        for n in names:
            f.write(f'IF DEF({n})\nPRINTLN "{n}={{d:{n}}}"\nENDC\n')
        path = f.name
    try:
        flags = ['-DFAITHFUL'] if faithful else []
        r = subprocess.run([rgbasm(), *flags, '-P', 'includes.asm', '-o', os.devnull, path],
                           cwd=ROOT, capture_output=True, text=True)
    finally:
        os.unlink(path)
    out = {}
    for line in r.stdout.splitlines():
        k, _, v = line.partition('=')
        if v.lstrip('-').isdigit():
            out[k] = int(v)
    return out


class Consts(dict):
    """Lazy constant lookup: C['SPECIES_NAME'] evaluates it on first use."""

    def __missing__(self, key):
        v = values([key]).get(key)
        if v is None:
            raise KeyError(f'constant {key} is not defined')
        self[key] = v
        return v

    def preload(self, names):
        self.update(values(names))


C = Consts()


def map_ids(name):
    """(group, number) for a map constant such as 'LAKE_OF_RAGE'."""
    return C['GROUP_' + name], C['MAP_' + name]
