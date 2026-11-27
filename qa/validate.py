"""Detector validation: run the detectors against ROMs with known faults and measure what they miss.

    python3 -m qa.validate run [--mutants a,b] [--detectors x,y] [--jobs 3] [--out DIR]
    python3 -m qa.validate table [--out DIR]

For every (mutant, detector) cell the detector runs on the faulty ROM with no knowledge of where the
fault is. `control` (the unmodified tree) measures false positives: any detector that fires on it is wrong.
`blind` detectors look at one build; `diff` detectors compare a build with `control` and so find any
change, whether or not it is a defect. A cell result is DETECTED / MISSED; the table also lists, for each
mutant, which detectors are *expected* to be able to see its class, so a miss is a measured false negative.
Results are cached per cell in DIR/cells.json (rerun only what is missing; delete a key to redo it).
"""
import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from qa import mutants as M            # noqa: E402

DEFAULT_OUT = os.path.join(ROOT, 'qa/reports/validation')

PY = sys.executable
# name: (kind, argv template with {rom} {base} {out}, env, what it is)
DETECTORS = {
    'smoke-pyboy': ('blind', [PY, 'qa/run.py', 'map', '--only', 'test_map_smoke.enter_maps_0of4', '--rom', '{rom}', '--out', '{out}'], {},
                    'enter a quarter of all maps, guards on player struct / follower queue / crash handler'),
    'conn': ('blind', [PY, 'qa/run.py', 'map', '--only', 'test_connections', '--rom', '{rom}', '--out', '{out}'], {},
             'walk across every map connection on foot'),
    'execguard': ('blind', [PY, 'qa/run.py', 'hardware', '--only', 'enter_maps_exec_guard', '--models', 'CGB-E', '--rom', '{rom}', '--out', '{out}'], {},
                  'SameBoy native execution guard over every map'),
    'fuzz': ('blind', [PY, 'qa/run.py', 'general', '--only', 'random_input_fuzz', '--backend', 'pyboy', '--rom', '{rom}', '--out', '{out}'], {},
             'seeded random input with the overworld guards'),
    'oam-maps': ('blind', [PY, 'qa/run.py', 'av', '--only', 'oam_vram_integrity', '--rom', '{rom}', '--out', '{out}'], {},
                 'every map: object-to-OAM, blank sprites per object, tilemap attributes'),
    'battle-pic': ('blind', [PY, '-m', 'qa.gb.scenarios', '--count', '40', '--seed', '11', '--stages', 'goldenrod', '--jobs', '1', '--rom', '{rom}', '--out', '{out}'], {},
                   'seeded wild battles with KO/switch policies: state oracles and enemy-pic tile watch'),
    'battle-menus': ('blind', [PY, 'qa/run.py', 'av', '--only', 'battle_menus_keep_enemy_sprite', '--models', 'CGB-E', '--rom', '{rom}', '--out', '{out}'], {},
                     'every battle menu leaves the enemy sprite tiles intact'),
    'ppu-timing': ('blind', [PY, 'qa/run.py', 'av', '--only', 'ppu_timing_in_gameplay', '--models', 'CGB-E', '--rom', '{rom}', '--out', '{out}'], {},
                   'SameBoy: illegal VRAM/OAM access and VBlank length while playing'),
    'audio-scan': ('blind', [PY, 'qa/run.py', 'av', '--only', 'audio_boot_scan', '--rom', '{rom}', '--out', '{out}'], {},
                   'PCM analysis over boot and intro: silence, clipping, DC, glitches'),
    'music-loops': ('blind', [PY, 'qa/run.py', 'av', '--only', 'music_loops_0of4', '--rom', '{rom}', '--out', '{out}'], {'QA_AUDIO_LIMIT': '6', 'QA_MUSIC_MAX_FRAMES': '7200'},
                    'engine-state music loop validation (6 songs)'),
    'sfx-music': ('blind', [PY, 'qa/run.py', 'av', '--only', 'sfx_keeps_music_0of4', '--rom', '{rom}', '--out', '{out}'], {'QA_AUDIO_LIMIT': '8'},
                  'sound effects leave the music engine in place (8 effects)'),
    'apu': ('blind', [PY, 'qa/run.py', 'av', '--only', 'apu_channels_0of4', '--models', 'CGB-E', '--rom', '{rom}', '--out', '{out}'], {'QA_AUDIO_LIMIT': '10'},
            'APU channel monitor: voiced channels audible, engine frequency equals an independent note/octave model (10 songs)'),
    'x-frames': ('diff', [PY, '-m', 'qa.av.diffbuild', 'frames', '{base}', '{rom}', '--every', '5', '--out', '{out}'], {},
                 'screenshot every 5th map, compare with the control build'),
    'x-audio': ('diff', [PY, '-m', 'qa.av.diffbuild', 'audio', '{base}', '{rom}', '--songs', '30', '--frames', '480', '--out', '{out}'], {},
                'PCM of 30 songs, compare with the control build'),
}

# which detector families can in principle see which fault class (used to label misses as expected / unexpected)
CAN_SEE = {
    'memory/object-struct': ['smoke-pyboy', 'conn', 'fuzz', 'execguard'],
    'graphics/vram-clobber': ['battle-pic', 'battle-menus', 'x-frames'],
    'crash/script': ['execguard', 'smoke-pyboy'],
    'graphics/missing-tile': ['x-frames'],
    'graphics/sprite-missing': ['oam-maps', 'x-frames'],
    'audio/pitch': ['apu', 'x-audio'],
    'audio/channel-dropout': ['apu', 'x-audio'],
    'memory/overflow': ['battle-pic'],
    'hardware/ppu-timing': ['ppu-timing', 'execguard'],
    'hardware/vblank-workload': ['ppu-timing'],
}


def run_cell(mutant, det, out_root, base_rom):
    kind, argv, env, _ = DETECTORS[det]
    rom = M.rom_path(mutant)
    out = os.path.join(out_root, mutant, det)
    os.makedirs(out, exist_ok=True)
    cmd = [a.format(rom=rom, base=base_rom, out=out) for a in argv]
    e = dict(os.environ, PATH='/opt/rgbds/bin:' + os.environ['PATH'], **env)
    t0 = time.time()
    try:
        r = subprocess.run(cmd, cwd=ROOT, env=e, capture_output=True, text=True, timeout=5400)
        rc, text = r.returncode, r.stdout[-3000:] + r.stderr[-1500:]
    except subprocess.TimeoutExpired:
        rc, text = 99, 'timeout'
    ev = text.strip().splitlines()[-6:]
    # failure details from the report, when there is one
    rj = os.path.join(out, 'results.json')
    if os.path.exists(rj):
        try:
            res = json.load(open(rj))['results']
            bad = [x for x in res if x['status'] in ('fail', 'error')]
            ev = ['%s: %s' % (x['name'].split('.')[-1], (x['failures'] or [x.get('error') or ''])[0][:160]) for x in bad[:3]]
        except Exception:
            pass
    return dict(mutant=mutant, detector=det, detected=rc != 0, rc=rc, seconds=round(time.time() - t0), evidence=ev)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['run', 'table'])
    ap.add_argument('--mutants', default=None)
    ap.add_argument('--detectors', default=None)
    ap.add_argument('--jobs', type=int, default=3)
    ap.add_argument('--out', default=DEFAULT_OUT)
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    cells_path = os.path.join(a.out, 'cells.json')
    cells = json.load(open(cells_path)) if os.path.exists(cells_path) else {}
    muts = a.mutants.split(',') if a.mutants else [m for m in M.MUTANTS]
    dets = a.detectors.split(',') if a.detectors else list(DETECTORS)
    if a.cmd == 'run':
        base = M.rom_path('control')
        todo = [(m, d) for m in muts for d in dets if f'{m}/{d}' not in cells]
        print('%d cells to run' % len(todo), flush=True)
        with cf.ThreadPoolExecutor(a.jobs) as ex:
            futs = {ex.submit(run_cell, m, d, a.out, base): (m, d) for m, d in todo}
            for f in cf.as_completed(futs):
                r = f.result()
                cells[f'{r["mutant"]}/{r["detector"]}'] = r
                json.dump(cells, open(cells_path, 'w'), indent=1)
                print('%-18s %-13s %-8s %4ds' % (r['mutant'], r['detector'], 'DETECTED' if r['detected'] else 'quiet', r['seconds']), flush=True)
    table(cells, muts, dets, a.out)


def table(cells, muts, dets, out):
    lines = ['| mutant (class) | ' + ' | '.join(dets) + ' |', '|---|' + '---|' * len(dets)]
    fp, fn, tp = [], [], 0
    for m in muts:
        row = []
        for d in dets:
            c = cells.get(f'{m}/{d}')
            if not c:
                row.append('.')
                continue
            if m == 'control':
                row.append('FALSE ALARM' if c['detected'] else 'ok')
                if c['detected']:
                    fp.append((d, c['evidence']))
                continue
            cls = M.MUTANTS[m]['cls']
            sees = d in CAN_SEE.get(cls, [])
            if c['detected']:
                row.append('**found**' if sees else 'found (unplanned)')
                tp += 1
            else:
                row.append('MISSED' if sees else '-')
                if sees:
                    fn.append((m, d))
        lines.append('| %s (%s) | %s |' % (m, M.MUTANTS[m]['cls'], ' | '.join(row)))
    text = '\n'.join(lines)
    text += '\n\nFalse alarms on the control build: %d' % len(fp)
    for d, ev in fp:
        text += '\n- %s: %s' % (d, '; '.join(ev))
    text += '\nMissed although the detector family was expected to see the class: %d' % len(fn)
    for m, d in fn:
        text += '\n- %s by %s' % (m, d)
    open(os.path.join(out, 'matrix.md'), 'w').write(text + '\n')
    print(text)


if __name__ == '__main__':
    main()
