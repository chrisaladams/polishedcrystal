"""Honest coverage accounting.

Tests declare `covers=(tag, ...)`. A feature area is

    TESTED    - every tag the area lists has a passing test in this run
    PARTIAL   - some, not all, of its tags do
    UNTESTED  - none do

Passing a tag means "a test exercising that aspect ran and found nothing wrong
under the stated provenance", never "the feature is bug-free". Visiting a map or
executing code does not by itself earn a tag: a test must assert something.
"""

AREAS = [
    ('Map traversal: connections, warps, collision',
     ['map.connections', 'map.warps', 'map.collision', 'map.smoke']),
    ('NPC interactions and scripted movement', ['npc.interaction', 'npc.scripted_movement']),
    ('Story progression and event flags', ['story.flags', 'story.progression']),
    ('Sprite allocation and rendering', ['sprites.player', 'sprites.oam_budget', 'sprites.objects']),
    ('Battle HUD, switching and knockouts', ['battle.hud', 'battle.switching', 'battle.knockout']),
    ('Moves, abilities and status effects', ['battle.moves', 'battle.abilities', 'battle.status']),
    ('Tournaments and custom battle systems',
     ['cups.rising_star', 'cups.whirl', 'cups.kimono', 'cups.dragon', 'cups.rental', 'cups.world', 'link.friend']),
    ('Cinematics and environmental effects', ['cinematic', 'weather']),
    ('Roaming Pokemon and time-dependent events', ['roaming', 'time.clock']),
    ('Save integrity, SRAM allocation, clock', ['save.roundtrip', 'save.sram_layout', 'clock.software']),
    ('Trading, link battles, communication recovery', ['link.trade', 'link.battle', 'link.recovery']),
    ('Extended gameplay stress / fuzzing', ['stress.fuzz', 'stress.long']),
    ('Follower and object-struct integrity', ['follower', 'follower.static']),
    ('Cartridge / mapper / header compliance', ['hw.header', 'hw.mapper']),
    ('Hardware rules: OAM, VRAM access, power-on RAM',
     ['hw.oam_lines', 'hw.vram_access', 'hw.memory_guard', 'hw.startup_ram']),
    ('Static data validation', ['data.maps', 'data.tables', 'data.layout']),
    ('Graphics: frames, VRAM, OAM, flicker, PPU timing',
     ['av.frames', 'av.vram', 'av.oam', 'av.flicker', 'av.ppu_timing']),
    ('Graphics before/after: menus, battles, map transitions, cinematics',
     ['av.menus', 'av.battle_gfx', 'av.transitions', 'av.cinematics']),
    ('Audio: PCM scan, silence, music loops, sound effects',
     ['av.audio_pcm', 'av.silence', 'av.music_loops', 'av.sfx']),
    ('Audiovisual cross-emulator comparison and approved references',
     ['av.cross_emulator', 'av.audio_cross', 'av.references']),
    ('Hardware models CGB-0 / CGB-E / AGB for audiovisual checks', ['av.models']),
]


def table(results):
    passed = set()
    attempted = set()
    partial = {}
    for r in results:
        for tag, why in (r.get('partial') or {}).items():
            partial[tag] = why
    for r in results:
        for tag in r['covers']:
            attempted.add(tag)
            if r['status'] == 'pass':
                passed.add(tag)
    passed -= set(partial)          # a test that withdrew a tag outranks another test that merely names it
    lines = ['## Coverage (this run)', '',
             'TESTED = every listed aspect has a passing test; PARTIAL = some; UNTESTED = none. '
             'Emulated runs only: nothing here is physical-hardware evidence.', '',
             '| Area | Status | Covered | Not covered |', '|---|---|---|---|']
    for name, tags in AREAS:
        have = [t for t in tags if t in passed]
        miss = [t for t in tags if t not in passed]
        status = 'TESTED' if not miss else ('PARTIAL' if have else 'UNTESTED')
        notes = ['%s (%s)' % (t, partial[t]) for t in miss if t in partial]
        lines.append('| %s | %s | %s | %s |' % (name, status, ', '.join(have) or '-',
                                              ', '.join([t for t in miss if t not in partial] + notes) or '-'))
    return '\n'.join(lines)
