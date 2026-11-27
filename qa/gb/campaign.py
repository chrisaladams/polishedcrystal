"""A resumable, independent exploration run (no Claude in the loop).

    python3 -m qa.gb.campaign --out DIR --seconds 1800 [--seed N] [--resume DIR/ckpt.state]

Plays from New Game (or a checkpoint) with the Explorer, writes checkpoints, a JSON
summary and failure artifacts to DIR, and exits non-zero if it recorded failures."""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--seconds', type=int, default=600)
    ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--resume', default=None, help='a checkpoint .state to continue from')
    ap.add_argument('--label', default='run')
    ap.add_argument('--rom', default=None)
    a = ap.parse_args(argv)
    from qa.gb import fixtures as F
    from qa.gb.emu import Game
    from qa.gb.explorer import Explorer
    os.makedirs(a.out, exist_ok=True)
    g = Game(rom=a.rom, workdir=a.out, seed=a.seed)
    if a.resume:
        g.tick(30)
        g.load_state_file(a.resume)
        provenance = 'branched from ' + os.path.basename(a.resume)
    else:
        F.new_game_to_bedroom(g)
        provenance = 'gameplay'
    ex = Explorer(g, a.out, seed=a.seed, label=a.label, provenance=provenance)
    s = ex.run(budget_seconds=a.seconds)
    s['seed'] = a.seed
    s['gated'] = ex.gated
    s['visited'] = sorted(ex.visited)
    s['timeline'] = ex.timeline[-200:]
    s['blocked_edge_events'] = [e for e in ex.nav.events][:200]
    json.dump(s, open(os.path.join(a.out, f'{a.label}_summary.json'), 'w'), indent=1, default=str)
    json.dump(ex.nav.log, open(os.path.join(a.out, f'{a.label}_inputs.json'), 'w'))
    print(json.dumps({k: s[k] for k in ('label', 'stopped', 'seconds', 'maps_visited', 'interactions', 'flags', 'badges',
                                         'levels', 'battles', 'checkpoints')}))
    return 1 if s['failures'] else 0


if __name__ == '__main__':
    sys.exit(main())
