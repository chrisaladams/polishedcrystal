#!/usr/bin/env python3
"""Build and check the postgame using an in-memory copy of an existing save."""
import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('save', type=Path, help='compatible save with a healthy party')
    ap.add_argument('--full', action='store_true', help='also sweep every wild encounter map')
    ap.add_argument('--shots', type=Path, help='save character placement screenshots here')
    args = ap.parse_args()
    save = args.save.resolve()
    if not save.is_file():
        ap.error(f'save not found: {save}')
    try:
        import pyboy  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError as exc:
        ap.error(f'{exc}; install utils/anime_events/requirements.txt first')
    subprocess.run(['make', '-j4'], cwd=ROOT, check=True)
    checks = [['test/test_wild_reachability.py']]
    checks += [[f'utils/anime_events/test_{name}.py', str(save)]
              for name in ('story', 'quest_map', 'engine_cleanup', 'software_clock', 'orange_league',
                           'cameos', 'whirl_cup', 'movie_events', 'campaigns', 'shadow_encounters')]
    checks.append(['utils/wild_mons/test_wild_mons.py', str(save)]
                  + ([] if args.full else ['--quick']))
    audit = ['utils/audit/audit_reachability.py', str(save)]
    if args.full:
        audit.append('--wild')
    if args.shots:
        shots = args.shots.resolve()
        shots.mkdir(parents=True, exist_ok=True)
        audit += ['--shots', str(shots)]
    checks.append(audit)
    failures = []
    for command in checks:
        print(f'\nChecking {command[0]}', flush=True)
        try:
            result = subprocess.run([sys.executable, *command], cwd=ROOT, timeout=1800)
            if result.returncode:
                failures.append(command[0])
        except subprocess.TimeoutExpired:
            failures.append(command[0] + ' (timed out)')
    print(f'\n{len(checks) - len(failures)}/{len(checks)} checks passed', flush=True)
    for name in failures:
        print(f'  FAILED: {name}')
    return bool(failures)


if __name__ == '__main__':
    sys.exit(main())
