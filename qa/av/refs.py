"""Known-good reference images, with a human approval gate.

A reference is only trusted if a person approved it. Tests never approve anything:

  * `capture candidate` writes qa/av/reference/pending/<name>.png (git-ignored) with a manifest
    recording the ROM hash, commit, emulators and models that agreed, and the monitor results;
  * a person looks at it (python3 -m qa.av.refs show NAME  -> prints paths; open the PNG) and runs
      python3 -m qa.av.refs approve NAME --by "who" --note "why this is correct"
    which copies it to qa/av/reference/approved/ and records who approved it and when;
  * comparison tests use only approved references. With none, they report `unreferenced`
    (a skip, never a pass), and write a candidate.

A candidate is only produced when the emulators agree with each other and no monitor
fired during its capture: a reference from a build that already shows a defect would
bake the defect in.
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import sys

from . import frames

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = os.path.join(ROOT, 'qa', 'av', 'reference')
APPROVED = os.path.join(BASE, 'approved')
PENDING = os.path.join(BASE, 'pending')
MANIFEST = os.path.join(APPROVED, 'manifest.json')


def _manifest():
    return json.load(open(MANIFEST)) if os.path.exists(MANIFEST) else {}


def approved_path(name):
    p = os.path.join(APPROVED, name + '.png')
    return p if os.path.exists(p) and name in _manifest() else None


def load_approved(name):
    import numpy as np
    from PIL import Image
    p = approved_path(name)
    return np.asarray(Image.open(p).convert('RGB')) if p else None


def propose(name, frame, evidence):
    """Write a pending candidate. `evidence` is a dict (rom sha1, commit, emulators, agreement...)."""
    os.makedirs(PENDING, exist_ok=True)
    path = os.path.join(PENDING, name + '.png')
    frames.save(frame, path)
    json.dump(evidence, open(path[:-4] + '.json', 'w'), indent=1, default=str)
    return path


def compare(name, frame, evidence=None, tol=24, max_fraction=0.01):
    """Compare a frame with the approved reference. Returns (status, detail) where status is
    'match', 'mismatch' or 'unreferenced' (no approved reference: a candidate was written)."""
    ref = load_approved(name)
    if ref is None:
        if evidence is not None:
            propose(name, frame, evidence)
        return 'unreferenced', f'no approved reference for {name}; candidate written to reference/pending'
    d = frames.diff(ref, frame, tol)
    if d['fraction'] > max_fraction:
        return 'mismatch', d
    return 'match', d


def approve(name, by, note):
    src = os.path.join(PENDING, name + '.png')
    if not os.path.exists(src):
        raise SystemExit(f'no pending candidate {name}')
    if not by or not note:
        raise SystemExit('approval needs --by and --note')
    evidence = json.load(open(src[:-4] + '.json')) if os.path.exists(src[:-4] + '.json') else {}
    if evidence.get('emulators_agree') is False or evidence.get('monitor_anomalies'):
        raise SystemExit('refusing: the candidate was captured with emulator disagreement or monitor anomalies; '
                         'fix or explain first (edit the .json evidence if you have reviewed it)')
    os.makedirs(APPROVED, exist_ok=True)
    shutil.copy(src, os.path.join(APPROVED, name + '.png'))
    m = _manifest()
    m[name] = dict(sha256=hashlib.sha256(open(src, 'rb').read()).hexdigest(), approved_by=by, note=note,
                   approved_at=datetime.datetime.utcnow().isoformat(timespec='seconds') + 'Z', evidence=evidence)
    json.dump(m, open(MANIFEST, 'w'), indent=1, sort_keys=True)
    print('approved', name)


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('list')
    s = sub.add_parser('show')
    s.add_argument('name')
    a = sub.add_parser('approve')
    a.add_argument('name')
    a.add_argument('--by', required=True)
    a.add_argument('--note', required=True)
    args = ap.parse_args(argv)
    if args.cmd == 'list':
        pend = sorted(f[:-4] for f in os.listdir(PENDING) if f.endswith('.png')) if os.path.isdir(PENDING) else []
        print('approved:', ', '.join(sorted(_manifest())) or '(none)')
        print('pending :', ', '.join(pend) or '(none)')
    elif args.cmd == 'show':
        p = os.path.join(PENDING, args.name + '.png')
        print(p)
        print(open(p[:-4] + '.json').read() if os.path.exists(p[:-4] + '.json') else '(no evidence)')
    else:
        approve(args.name, args.by, args.note)


if __name__ == '__main__':
    main()
