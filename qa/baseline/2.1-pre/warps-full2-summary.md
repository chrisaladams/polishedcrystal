# QA run

- ROM: `polishedcrystal-3.2.3.gbc` sha1 `5cdb8dc593574b373021c92e6c7aa4faf8081cda` (MBC5+RAM+BATTERY, 2097152 bytes)
- Commit: `7279d7469f891468c3c4708c5fb1c279e3ea0bdb` (working tree dirty) on `claude/sleepy-ramanujan-kc278b`
- Tools: python 3.13.18, pyboy 2.9.0, sameboy ea667ad, gearboy ad6fa70, rgbds rgbasm v1.0.4
- Seed: 1   Suite: map   Backend option: default   SameBoy models: per-test default
- Hardware: emulated only: no physical console results are included

| Result | Test | Backend | Seconds | Provenance |
|---|---|---|---|---|
| FAIL | test_warps.warps_0of4 | pyboy | 231.8 | walking onto each warp tile: gameplay input; party and the starting tile beside the warp: injected |
| FAIL | test_warps.warps_1of4 | pyboy | 229.9 | walking onto each warp tile: gameplay input; party and the starting tile beside the warp: injected |
| FAIL | test_warps.warps_2of4 | pyboy | 219.3 | walking onto each warp tile: gameplay input; party and the starting tile beside the warp: injected |
| FAIL | test_warps.warps_3of4 | pyboy | 243.7 | walking onto each warp tile: gameplay input; party and the starting tile beside the warp: injected |

## Failures

### test_warps.warps_1of4 (pyboy)
- LAV_RADIO_TOWER_2F#1 -> LAV_RADIO_TOWER_3F#1: arrived at (3, 0) on the first frame, the destination warp is at (15, 0)
Artifacts: test_warps.warps_1of4.pyboy/failure_0
### test_warps.warps_0of4 (pyboy)
- BLACKTHORN_GYM_1F#5 -> BLACKTHORN_GYM_2F#4: arrived at (7, 9) on the first frame, the destination warp is at (8, 7)
Artifacts: test_warps.warps_0of4.pyboy/failure_0
### test_warps.warps_2of4 (pyboy)
- LAV_RADIO_TOWER_3F#0: led to map (18, 18) (None), data says LAV_RADIO_TOWER_3F
Artifacts: test_warps.warps_2of4.pyboy/failure_0
### test_warps.warps_3of4 (pyboy)
- LAV_RADIO_TOWER_5F#0: destination LAV_RADIO_TOWER_4F is not a map constant
Artifacts: test_warps.warps_3of4.pyboy/failure_0

## Coverage (this run)

TESTED = every listed aspect has a passing test; PARTIAL = some; UNTESTED = none. Emulated runs only: nothing here is physical-hardware evidence.

| Area | Status | Covered | Not covered |
|---|---|---|---|
| Map traversal: connections, warps, collision | UNTESTED | - | map.connections, map.collision, map.smoke, map.warps (101 of 558 warps in shard 3 not taken) |
| NPC interactions and scripted movement | UNTESTED | - | npc.interaction, npc.scripted_movement |
| Story progression and event flags | UNTESTED | - | story.flags, story.progression |
| Sprite allocation and rendering | UNTESTED | - | sprites.player, sprites.oam_budget, sprites.objects |
| Battle HUD, switching and knockouts | UNTESTED | - | battle.hud, battle.switching, battle.knockout |
| Moves, abilities and status effects | UNTESTED | - | battle.moves, battle.abilities, battle.status |
| Tournaments and custom battle systems | UNTESTED | - | cups.rising_star, cups.whirl, cups.kimono, cups.dragon, cups.rental, cups.world, link.friend |
| Cinematics and environmental effects | UNTESTED | - | cinematic, weather |
| Roaming Pokemon and time-dependent events | UNTESTED | - | roaming, time.clock |
| Save integrity, SRAM allocation, clock | UNTESTED | - | save.roundtrip, save.sram_layout, clock.software |
| Trading, link battles, communication recovery | UNTESTED | - | link.trade, link.battle, link.recovery |
| Extended gameplay stress / fuzzing | UNTESTED | - | stress.fuzz, stress.long |
| Follower and object-struct integrity | UNTESTED | - | follower, follower.static |
| Cartridge / mapper / header compliance | UNTESTED | - | hw.header, hw.mapper |
| Hardware rules: OAM, VRAM access, power-on RAM | UNTESTED | - | hw.oam_lines, hw.vram_access, hw.memory_guard, hw.startup_ram |
| Static data validation | UNTESTED | - | data.maps, data.tables, data.layout |
| Graphics: frames, VRAM, OAM, flicker, PPU timing | UNTESTED | - | av.frames, av.vram, av.oam, av.flicker, av.ppu_timing |
| Graphics before/after: menus, battles, map transitions, cinematics | UNTESTED | - | av.menus, av.battle_gfx, av.transitions, av.cinematics |
| Audio: PCM scan, silence, music loops, sound effects | UNTESTED | - | av.audio_pcm, av.silence, av.music_loops, av.sfx |
| Audiovisual cross-emulator comparison and approved references | UNTESTED | - | av.cross_emulator, av.audio_cross, av.references |
| Hardware models CGB-0 / CGB-E / AGB for audiovisual checks | UNTESTED | - | av.models |
