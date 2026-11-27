# QA run

- ROM: `../../../tmp/claude-0/qa/mut/control/polishedcrystal-3.2.3.gbc` sha1 `5cdb8dc593574b373021c92e6c7aa4faf8081cda` (MBC5+RAM+BATTERY, 2097152 bytes)
- Commit: `855b959a5b247e9a8c8eb2fe4322db9034b9b20e` (working tree dirty) on `claude/sleepy-ramanujan-kc278b`
- Tools: python 3.13.18, pyboy 2.9.0, sameboy ea667ad, gearboy ad6fa70, rgbds rgbasm v1.0.4
- Seed: 1   Suite: map   Backend option: default   SameBoy models: per-test default
- Hardware: emulated only: no physical console results are included

| Result | Test | Backend | Seconds | Provenance |
|---|---|---|---|---|
| PASS | test_connections.cross_connections_0of4 | pyboy | 116.8 | walking across each connection: gameplay input; party, start map and position: injected |
| PASS | test_connections.cross_connections_1of4 | pyboy | 115.6 | walking across each connection: gameplay input; party, start map and position: injected |
| PASS | test_connections.cross_connections_2of4 | pyboy | 120.2 | walking across each connection: gameplay input; party, start map and position: injected |
| PASS | test_connections.cross_connections_3of4 | pyboy | 113.4 | walking across each connection: gameplay input; party, start map and position: injected |

## Coverage (this run)

TESTED = every listed aspect has a passing test; PARTIAL = some; UNTESTED = none. Emulated runs only: nothing here is physical-hardware evidence.

| Area | Status | Covered | Not covered |
|---|---|---|---|
| Map traversal: connections, warps, collision | UNTESTED | - | map.warps, map.collision, map.smoke, map.connections (17 of 53 in shard 2 not crossed on foot) |
| NPC interactions and scripted movement | UNTESTED | - | npc.interaction, npc.scripted_movement |
| Story progression and event flags | UNTESTED | - | story.flags, story.progression |
| Sprite allocation and rendering | PARTIAL | sprites.player | sprites.oam_budget, sprites.objects |
| Battle HUD, switching and knockouts | UNTESTED | - | battle.hud, battle.switching, battle.knockout |
| Moves, abilities and status effects | UNTESTED | - | battle.moves, battle.abilities, battle.status |
| Tournaments and custom battle systems | UNTESTED | - | cups.rising_star, cups.whirl, cups.kimono, cups.dragon, cups.rental, cups.world, link.friend |
| Cinematics and environmental effects | UNTESTED | - | cinematic, weather |
| Roaming Pokemon and time-dependent events | UNTESTED | - | roaming, time.clock |
| Save integrity, SRAM allocation, clock | UNTESTED | - | save.roundtrip, save.sram_layout, clock.software |
| Trading, link battles, communication recovery | UNTESTED | - | link.trade, link.battle, link.recovery |
| Extended gameplay stress / fuzzing | UNTESTED | - | stress.fuzz, stress.long |
| Follower and object-struct integrity | PARTIAL | follower | follower.static |
| Cartridge / mapper / header compliance | UNTESTED | - | hw.header, hw.mapper |
| Hardware rules: OAM, VRAM access, power-on RAM | PARTIAL | hw.memory_guard | hw.oam_lines, hw.vram_access, hw.startup_ram |
| Static data validation | UNTESTED | - | data.maps, data.tables, data.layout |
| Graphics: frames, VRAM, OAM, flicker, PPU timing | UNTESTED | - | av.frames, av.vram, av.oam, av.flicker, av.ppu_timing |
| Graphics before/after: menus, battles, map transitions, cinematics | UNTESTED | - | av.menus, av.battle_gfx, av.transitions, av.cinematics |
| Audio: PCM scan, silence, music loops, sound effects | UNTESTED | - | av.audio_pcm, av.silence, av.music_loops, av.sfx |
| Audiovisual cross-emulator comparison and approved references | UNTESTED | - | av.cross_emulator, av.audio_cross, av.references |
| Hardware models CGB-0 / CGB-E / AGB for audiovisual checks | UNTESTED | - | av.models |
