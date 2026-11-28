# QA run

- ROM: `polishedcrystal-3.2.3.gbc` sha1 `53dc05aafe9a2e325f13044d6c4bfe2bcc7d6aeb` (MBC5+RAM+BATTERY, 2097152 bytes)
- Commit: `c3d923d75685b79b72aad78b38aa458bfc885d83` on `claude/sleepy-ramanujan-kc278b`
- Tools: python 3.13.18, pyboy 2.9.0, sameboy ea667ad, gearboy ad6fa70, rgbds rgbasm v1.0.4
- Seed: 1   Suite: hardware   Backend option: default   SameBoy models: CGB-E,AGB
- Hardware: emulated only: no physical console results are included

| Result | Test | Backend | Seconds | Provenance |
|---|---|---|---|---|
| PASS | test_map_smoke.enter_maps_exec_guard_0of4 | sameboy AGB | 125.0 | injected warp into each map; no gameplay input (the player stands still); SameBoy with native execution guard |
| PASS | test_map_smoke.enter_maps_exec_guard_0of4 | sameboy CGB-E | 189.0 | injected warp into each map; no gameplay input (the player stands still); SameBoy with native execution guard |
| PASS | test_map_smoke.enter_maps_exec_guard_1of4 | sameboy CGB-E | 181.1 | injected warp into each map; no gameplay input (the player stands still); SameBoy with native execution guard |
| PASS | test_map_smoke.enter_maps_exec_guard_1of4 | sameboy AGB | 157.8 | injected warp into each map; no gameplay input (the player stands still); SameBoy with native execution guard |
| PASS | test_map_smoke.enter_maps_exec_guard_2of4 | sameboy AGB | 130.4 | injected warp into each map; no gameplay input (the player stands still); SameBoy with native execution guard |
| PASS | test_map_smoke.enter_maps_exec_guard_2of4 | sameboy CGB-E | 158.5 | injected warp into each map; no gameplay input (the player stands still); SameBoy with native execution guard |
| PASS | test_map_smoke.enter_maps_exec_guard_3of4 | sameboy CGB-E | 111.8 | injected warp into each map; no gameplay input (the player stands still); SameBoy with native execution guard |
| PASS | test_map_smoke.enter_maps_exec_guard_3of4 | sameboy AGB | 80.2 | injected warp into each map; no gameplay input (the player stands still); SameBoy with native execution guard |

## Coverage (this run)

TESTED = every listed aspect has a passing test; PARTIAL = some; UNTESTED = none. Emulated runs only: nothing here is physical-hardware evidence.

| Area | Status | Covered | Not covered |
|---|---|---|---|
| Map traversal: connections, warps, collision | PARTIAL | map.smoke | map.connections, map.warps, map.collision |
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
| Cartridge / mapper / header compliance | PARTIAL | hw.mapper | hw.header |
| Hardware rules: OAM, VRAM access, power-on RAM | PARTIAL | hw.memory_guard | hw.oam_lines, hw.vram_access, hw.startup_ram |
| Static data validation | UNTESTED | - | data.maps, data.tables, data.layout |
| Graphics: frames, VRAM, OAM, flicker, PPU timing | UNTESTED | - | av.frames, av.vram, av.oam, av.flicker, av.ppu_timing |
| Graphics before/after: menus, battles, map transitions, cinematics | UNTESTED | - | av.menus, av.battle_gfx, av.transitions, av.cinematics |
| Audio: PCM scan, silence, music loops, sound effects | UNTESTED | - | av.audio_pcm, av.silence, av.music_loops, av.sfx |
| Audiovisual cross-emulator comparison and approved references | UNTESTED | - | av.cross_emulator, av.audio_cross, av.references |
| Hardware models CGB-0 / CGB-E / AGB for audiovisual checks | UNTESTED | - | av.models |
