#!/usr/bin/env python3
"""Build the Link Edition release files into build/link-edition-VERSION/:

- the Default and Faithful ROMs (the cartridges' .gbc), with their .sym;
- BPS patches from upstream Polished Crystal v3.2.3 (Default and Faithful)
  to each, made by utils/release/bps.py and checked by applying them;
- CHECKSUMS.txt: size, CRC-32, MD5, SHA-1 and SHA-256 of every file, and the
  commit they were built from.

The upstream base ROMs are built from the v3.2.3 tag in a temporary git
worktree (they come out byte for byte the same as the official release's
files with RGBDS 1.0.x), unless --base-dir names a folder that has them.

Run from a clean checkout (the commit is recorded); it runs `make tidy`
between the builds.

Usage:
  python3 utils/release/build_release.py --version 2.0 [--base-dir DIR]
"""
import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import bps  # noqa: E402

UPSTREAM_TAG = 'v3.2.3'
BUILDS = [  # (make goal, built name, release name, upstream base name)
    ([], 'polishedcrystal-3.2.3', 'polished-crystal-link-edition-{v}', 'polishedcrystal-3.2.3'),
    (['faithful'], 'polishedcrystal-faithful-3.2.3', 'polished-crystal-link-edition-faithful-{v}',
     'polishedcrystal-faithful-3.2.3'),
]


def run(cmd, cwd):
    print('+', ' '.join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def digest(data):
    return (f'{len(data):>9}  crc32 {zlib.crc32(data):08x}  md5 {hashlib.md5(data).hexdigest()}  '
            f'sha1 {hashlib.sha1(data).hexdigest()}  sha256 {hashlib.sha256(data).hexdigest()}')


def build_bases(jobs):
    tmp = Path(tempfile.mkdtemp(prefix='pc-upstream-'))
    wt = tmp / 'upstream'
    run(['git', 'worktree', 'add', '--detach', str(wt), UPSTREAM_TAG], ROOT)
    try:
        out = tmp / 'bases'
        out.mkdir()
        for goals, _, _, base in BUILDS:
            run(['make', f'-j{jobs}', *goals], wt)
            shutil.copy(wt / f'{base}.gbc', out / f'{base}.gbc')
            run(['make', 'tidy'], wt)
        return out
    finally:
        run(['git', 'worktree', 'remove', '--force', str(wt)], ROOT)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--version', required=True)
    ap.add_argument('--base-dir', type=Path, help='folder with the upstream v3.2.3 ROMs')
    ap.add_argument('-j', '--jobs', type=int, default=4)
    args = ap.parse_args()
    commit = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True,
                            check=True).stdout.strip()
    dirty = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no'], cwd=ROOT,
                           capture_output=True, text=True, check=True).stdout.strip()
    out = ROOT / 'build' / f'link-edition-{args.version}'
    out.mkdir(parents=True, exist_ok=True)
    bases = args.base_dir or build_bases(args.jobs)
    lines = [f'Pokemon Polished Crystal: Link Edition {args.version}',
             f'commit {commit}{" (with uncommitted changes)" if dirty else ""}', '']
    for goals, built, release, base in BUILDS:
        run(['make', 'tidy'], ROOT)
        run(['make', f'-j{args.jobs}', *goals], ROOT)
        name = release.format(v=args.version)
        rom = (ROOT / f'{built}.gbc').read_bytes()
        (out / f'{name}.gbc').write_bytes(rom)
        shutil.copy(ROOT / f'{built}.sym', out / f'{name}.sym')
        source = (Path(bases) / f'{base}.gbc').read_bytes()
        patch = bps.make(source, rom)
        if bps.apply(source, patch) != rom:
            sys.exit(f'{name}.bps does not reproduce the ROM')
        (out / f'{name}.bps').write_bytes(patch)
        lines.append(f'{base}.gbc (upstream {UPSTREAM_TAG}, the patch source)')
        lines.append('  ' + digest(source))
        for ext in ('gbc', 'bps', 'sym'):
            lines.append(f'{name}.{ext}')
            lines.append('  ' + digest((out / f'{name}.{ext}').read_bytes()))
        lines.append('')
    run(['make', 'tidy'], ROOT)
    run(['make', f'-j{args.jobs}'], ROOT)  # (leave the Default build in place for the tests)
    (out / 'CHECKSUMS.txt').write_text('\n'.join(lines))
    print('\n'.join(lines))


if __name__ == '__main__':
    main()
