# QA run

- ROM: `../../../../tmp/old/polishedcrystal-3.2.3.gbc` sha1 `5cdb8dc593574b373021c92e6c7aa4faf8081cda` (MBC5+RAM+BATTERY, 2097152 bytes)
- Commit: `b28702997ac5fd6a1192dce88cad81b218005ed3` on `claude/sleepy-ramanujan-kc278b`
- Tools: python 3.13.18, pyboy 2.9.0, sameboy unavailable, gearboy unavailable, rgbds rgbasm v1.0.4
- Seed: 1   Suite: map   Backend option: default   SameBoy models: per-test default
- Hardware: emulated only: no physical console results are included

| Result | Test | Backend | Seconds | Provenance |
|---|---|---|---|---|
| FAIL | test_boundaries.map_edges_0of4 | pyboy | 28.9 | walking outward at each map edge: gameplay input; map, party and the starting tile: injected |
| FAIL | test_boundaries.map_edges_1of4 | pyboy | 28.5 | walking outward at each map edge: gameplay input; map, party and the starting tile: injected |
| FAIL | test_boundaries.map_edges_2of4 | pyboy | 28.9 | walking outward at each map edge: gameplay input; map, party and the starting tile: injected |
| FAIL | test_boundaries.map_edges_3of4 | pyboy | 28.0 | walking outward at each map edge: gameplay input; map, party and the starting tile: injected |

## Failures

### test_boundaries.map_edges_3of4 (pyboy)
- ROUTE_25: walking up off the north edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_25: walking down off the south edge at (15, 39) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
Artifacts: test_boundaries.map_edges_3of4.pyboy/failure_0
### test_boundaries.map_edges_1of4 (pyboy)
- ROUTE_23_SOUTH: walking down off the south edge at (0, 63) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_23_SOUTH: walking left off the west edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_23_SOUTH: walking right off the east edge at (23, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_28: walking up off the north edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_28: walking down off the south edge at (0, 17) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_28: walking right off the east edge at (39, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_3: walking up off the north edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_3: walking down off the south edge at (7, 25) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_44: walking up off the north edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_44: walking down off the south edge at (0, 17) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_44: walking right off the east edge at (59, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
Artifacts: test_boundaries.map_edges_1of4.pyboy/failure_0
### test_boundaries.map_edges_0of4 (pyboy)
- MAHOGANY_TOWN: walking down off the south edge at (0, 17) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_10_SOUTH: walking up off the north edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_10_SOUTH: walking left off the west edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_10_SOUTH: walking right off the east edge at (19, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_23_NORTH: walking left off the west edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_23_NORTH: walking right off the east edge at (23, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_8: walking up off the north edge at (5, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_8: walking down off the south edge at (5, 21) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- RUGGED_ROAD_SOUTH: walking left off the west edge at (0, 2) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- RUGGED_ROAD_SOUTH: walking right off the east edge at (33, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
Artifacts: test_boundaries.map_edges_0of4.pyboy/failure_0
### test_boundaries.map_edges_2of4 (pyboy)
- CERULEAN_CAPE: walking up off the north edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- CERULEAN_CAPE: walking down off the south edge at (0, 37) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- CERULEAN_CAPE: walking right off the east edge at (49, 23) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- LAVENDER_TOWN: walking right off the east edge at (19, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_10_NORTH: walking up off the north edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_10_NORTH: walking down off the south edge at (0, 57) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_22: walking up off the north edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_22: walking down off the south edge at (0, 17) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_22: walking left off the west edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_24: walking up off the north edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_24: walking left off the west edge at (0, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_45: walking down off the south edge at (0, 95) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_9: walking up off the north edge at (3, 0) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- ROUTE_9: walking down off the south edge at (7, 17) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
- SILVER_CAVE_OUTSIDE: walking down off the south edge at (0, 29) [tile reachable on foot] changed the map to (209, 240) (None) at (230, 65)
Artifacts: test_boundaries.map_edges_2of4.pyboy/failure_0

## Coverage (this run)

TESTED = every listed aspect has a passing test; PARTIAL = some; UNTESTED = none. Emulated runs only: nothing here is physical-hardware evidence.

| Area | Status | Covered | Not covered |
|---|---|---|---|
| Map traversal: connections, warps, collision | UNTESTED | - | map.connections, map.warps, map.collision, map.smoke |
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
