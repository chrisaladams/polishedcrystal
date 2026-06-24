"""Shared species-pool eligibility filter for matrix.py and teams.py."""


def eligible(m, args):
    if 'stats' not in m or 'types' not in m:
        return False
    if not args.include_unevolved and not m.get('fully_evolved'):
        return False
    if not args.include_legendary and m.get('legendary'):
        return False
    return True
