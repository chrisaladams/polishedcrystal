"""Disposable faulty ROMs for validating the detectors.

A detector that has never seen a fault proves nothing. This builds ROMs from the current tree with one
deliberate fault each (or with one past fix reverted), in a scratch copy: the repository is never changed.

    python3 -m qa.mutants list
    python3 -m qa.mutants build [NAME ...]        # -> $QA_MUT/NAME/polishedcrystal-*.gbc (+ .sym/.map)

Each mutant has a class (what kind of defect it imitates) so the validation matrix can be read by class.
`replace` entries must match exactly once; a mutant that cannot be applied is an error, not a silent skip.
"""
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get('QA_MUT', '/tmp/claude-0/qa/mut')
SCRATCH = os.path.join(OUT, '_tree')

# name -> dict(cls, doc, replace=[(file, old, new)]) or revert=(commit, [paths])
MUTANTS = {
    'control': dict(cls='none', doc='unmodified tree built the same way (false-positive control)', replace=[]),
    # --- past defects, reintroduced by reverting their fixes -------------------------------------
    'rev-lake': dict(cls='memory/object-struct', doc='Lake of Rage fix reverted (L28)', revert=('d7350cf', ['engine/overworld/follower.asm', 'engine/overworld/map_objects.asm'])),
    'rev-rising': dict(cls='graphics/vram-clobber', doc='Rising Cup HUD fix reverted (L29)', revert=('cdc6337', ['engine/battle/core.asm'])),
    'rev-hall': dict(cls='crash/script', doc='Battle Factory Hallway callback fix reverted (L30)', revert=('61efc70', ['maps/BattleFactoryHallway.asm'])),
    # --- injected faults ---------------------------------------------------------------------------
    'gfx-tile-trunc': dict(cls='graphics/missing-tile', doc='tileset group 1/2 loads one tile too few', replace=[
        ('home/map.asm', '_DoLoadTilesetGFX:\n\tld c, $7f', '_DoLoadTilesetGFX:\n\tld c, $7e')]),
    'spr-npc3-gone': dict(cls='graphics/sprite-missing', doc='object 3 is never given an OAM slot', replace=[
        ('engine/overworld/map_objects.asm',
         '\tcall DoesObjectHaveASprite\n\tjr z, .skip\n\tld hl, OBJECT_FACING\n\tadd hl, bc\n\tld a, [hl]\n\tcp STANDING',
         '\tcall DoesObjectHaveASprite\n\tjr z, .skip\n\tld a, d\n\tcp 3\n\tjr z, .skip\n\tld hl, OBJECT_FACING\n\tadd hl, bc\n\tld a, [hl]\n\tcp STANDING')]),
    'aud-pitch-octave': dict(cls='audio/pitch', doc='every note one octave too low', replace=[
        ('audio/engine.asm', '.loop\n\t; [7 - octave] loops\n\tcp $7\n', '.loop\n\t; [7 - octave] loops\n\tcp $6\n')]),
    'aud-ch1-silent': dict(cls='audio/channel-dropout', doc='channel 1 envelope is never written', replace=[
        ('audio/engine.asm', '.ch1_noise_sampling\n\tld a, [wCurTrackDuty]\n\tldh [rAUD1LEN], a\n\tld a, [wCurTrackIntensity]\n\tldh [rAUD1ENV], a',
         '.ch1_noise_sampling\n\tld a, [wCurTrackDuty]\n\tldh [rAUD1LEN], a\n\tld a, [wCurTrackIntensity]\n\tand a ; fault: envelope not written')]),
    'mem-party-overrun': dict(cls='memory/overflow', doc='adding a party member copies three bytes too many', replace=[
        ('engine/pokemon/move_mon.asm',
         '\tld hl, wTempMonSpecies\n\tld bc, PARTYMON_STRUCT_LENGTH\n\trst CopyBytes\n\n\tld hl, wPartyMonOTs',
         '\tld hl, wTempMonSpecies\n\tld bc, PARTYMON_STRUCT_LENGTH + 3\n\trst CopyBytes\n\n\tld hl, wPartyMonOTs')]),
    'hw-vram-mode3': dict(cls='hardware/ppu-timing', doc='overworld writes VRAM at line 60 of every frame', replace=[
        ('engine/overworld/map_objects.asm',
         '\tld a, 1\n\tldh [hOAMUpdate], a\n\tcall InitSprites\n',
         '\tld a, 1\n\tldh [hOAMUpdate], a\n.fault_wait\n\tldh a, [rLY]\n\tcp 60\n\tjr nz, .fault_wait\n\txor a\n\tld [vTiles0 + $7f0], a\n\tcall InitSprites\n')]),
    'hw-vblank-long': dict(cls='hardware/vblank-workload', doc='VBlank handler spends ~1000 extra cycles', replace=[
        ('home/vblank.asm',
         '\tldh a, [hWX]\n\tldh [rWX], a\n\n\t; At CGB double speed',
         '\tldh a, [hWX]\n\tldh [rWX], a\n\tld bc, 150\n.fault_delay\n\tdec bc\n\tld a, b\n\tor c\n\tjr nz, .fault_delay\n\n\t; At CGB double speed')]),
}


def _run(cmd, cwd, env=None):
    r = subprocess.run(cmd, cwd=cwd, env=env, shell=isinstance(cmd, str), capture_output=True, text=True)
    return r


def prepare():
    """Scratch copy of the tree with its object files, so each mutant rebuilds only what it touches."""
    if not os.path.isdir(SCRATCH):
        os.makedirs(OUT, exist_ok=True)
        shutil.copytree(ROOT, SCRATCH, symlinks=True, ignore=shutil.ignore_patterns('.git', '.claude', 'reports', '.cache', '__pycache__'))
        _run(['git', 'init', '-q'], SCRATCH)


def _restore(paths):
    for p in paths:
        dst = os.path.join(SCRATCH, p)
        shutil.copyfile(os.path.join(ROOT, p), dst)
        os.utime(dst, None)                    # newer than the objects built from the faulty source, so make rebuilds it


def apply(name):
    m = MUTANTS[name]
    touched = []
    if 'replace' in m:
        for f, old, new in m['replace']:
            path = os.path.join(SCRATCH, f)
            s = open(path, encoding='utf-8').read()
            if s.count(old) != 1:
                raise SystemExit('%s: pattern for %s matches %d times (need exactly 1)' % (name, f, s.count(old)))
            open(path, 'w', encoding='utf-8').write(s.replace(old, new))
            touched.append(f)
    else:
        commit, paths = m['revert']
        diff = subprocess.run(['git', 'show', commit, '--', *paths], cwd=ROOT, capture_output=True, text=True).stdout
        r = subprocess.run(['git', 'apply', '-R'], cwd=SCRATCH, input=diff, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit('%s: cannot reverse-apply %s: %s' % (name, commit, r.stderr))
        touched = paths
    return touched


def build(name):
    prepare()
    touched = apply(name)
    env = dict(os.environ, PATH='/opt/rgbds/bin:' + os.environ['PATH'])
    try:
        r = _run('make -j4 2>&1 | tail -5', SCRATCH, env)
        out = os.path.join(OUT, name)
        os.makedirs(out, exist_ok=True)
        roms = [f for f in os.listdir(SCRATCH) if f.endswith('.gbc')]
        if not roms:
            raise SystemExit('%s: build produced no ROM:\n%s' % (name, r.stdout + r.stderr))
        for f in os.listdir(SCRATCH):
            if f.startswith('polishedcrystal-') and f.endswith(('.gbc', '.sym', '.map')):
                shutil.copy2(os.path.join(SCRATCH, f), out)
        return os.path.join(out, roms[0])
    finally:
        _restore(touched)                      # the next mutant starts from the clean tree again


def rom_path(name):
    d = os.path.join(OUT, name)
    for f in sorted(os.listdir(d)):
        if f.endswith('.gbc'):
            return os.path.join(d, f)
    raise FileNotFoundError(name)


def main(argv):
    cmd = argv[1] if len(argv) > 1 else 'list'
    if cmd == 'list':
        for n, m in MUTANTS.items():
            print('%-18s %-26s %s' % (n, m['cls'], m['doc']))
    elif cmd == 'build':
        for n in (argv[2:] or MUTANTS):
            print(n, '->', build(n), flush=True)
    else:
        raise SystemExit(__doc__)


if __name__ == '__main__':
    main(sys.argv)
