# QA run

- ROM: `polishedcrystal-3.2.3.gbc` sha1 `53dc05aafe9a2e325f13044d6c4bfe2bcc7d6aeb` (MBC5+RAM+BATTERY, 2097152 bytes)
- Commit: `749902a1e0a62d1f94aff29d612065019b658153` (working tree dirty) on `claude/sleepy-ramanujan-kc278b`
- Tools: python 3.13.18, pyboy 2.9.0, sameboy ea667ad, gearboy ad6fa70, rgbds rgbasm v1.0.4
- Seed: 1   Suite: regression   Backend option: default   SameBoy models: per-test default
- Hardware: emulated only: no physical console results are included

| Result | Test | Backend | Seconds | Provenance |
|---|---|---|---|---|
| PASS | test_boundaries.map_edges_0of4 | pyboy | 45.9 | walking outward at each map edge: gameplay input; map, party and the starting tile: injected |
| PASS | test_boundaries.map_edges_1of4 | pyboy | 46.7 | walking outward at each map edge: gameplay input; map, party and the starting tile: injected |
| PASS | test_boundaries.map_edges_2of4 | pyboy | 46.3 | walking outward at each map edge: gameplay input; map, party and the starting tile: injected |
| PASS | test_boundaries.map_edges_3of4 | pyboy | 44.8 | walking outward at each map edge: gameplay input; map, party and the starting tile: injected |
| PASS | test_interactions.autobattle_party_flags | pyboy | 13.4 | harness regression: party memory edited directly |
| PASS | test_interactions.objects_callbacks_survive_warp_entry | pyboy | 22.3 | injected: warp entry into every map that declares an objects callback |
| PASS | test_interactions.violet_outskirts_house_warp_entry | pyboy | 16.8 | injected: warp entry (MAPSETUP_WARP, as the `warp` script command and Fly do it) |
| PASS | test_interactions.violet_outskirts_house_warp_entry | sameboy CGB-E | 17.8 | injected: warp entry (MAPSETUP_WARP, as the `warp` script command and Fly do it) |
| PASS | test_interactions.violet_outskirts_house_warp_entry | sameboy AGB | 1.8 | injected: warp entry (MAPSETUP_WARP, as the `warp` script command and Fly do it) |
| PASS | test_lake_of_rage.lake_of_rage_approach | pyboy | 27.5 | walk: gameplay input; party/position/save: injected fixture |
| PASS | test_lake_of_rage.lake_of_rage_approach | sameboy CGB-E | 16.3 | walk: gameplay input; party/position/save: injected fixture |
| PASS | test_lake_of_rage.lake_of_rage_approach | sameboy CGB-0 | 20.6 | walk: gameplay input; party/position/save: injected fixture |
| PASS | test_lake_of_rage.lake_of_rage_approach | sameboy AGB | 3.1 | walk: gameplay input; party/position/save: injected fixture |
| PASS | test_rising_cup_hud.rising_cup_replacement_hud | pyboy | 53.0 | cup entry/battle/replacement: gameplay input; party+position+faint: injected |
| PASS | test_rising_cup_hud.rising_cup_replacement_hud | sameboy CGB-0 | 56.7 | cup entry/battle/replacement: gameplay input; party+position+faint: injected |
| PASS | test_rising_cup_hud.rising_cup_replacement_hud | sameboy CGB-E | 55.3 | cup entry/battle/replacement: gameplay input; party+position+faint: injected |
| PASS | test_rising_cup_hud.rising_cup_replacement_hud | sameboy AGB | 5.8 | cup entry/battle/replacement: gameplay input; party+position+faint: injected |
| PASS | test_static.follower_queue_cannot_overrun | pyboy | 2.2 | unit: calls ApplyMovementToFollower directly (injected), reads memory |
| PASS | test_static.follower_slot_budget | pyboy | 0.4 | static: maps/*.asm and engine/overworld/follower.asm |
| PASS | test_static.map_callbacks_do_not_wait | pyboy | 0.3 | static: maps/*.asm (checkout, not the ROM) |
| PASS | test_static.map_callbacks_end_with_endcallback | pyboy | 0.3 | static: maps/*.asm (checkout, not the ROM) |
| PASS | test_static.party_menu_users_restore_enemy_pic | pyboy | 0.0 | static: engine/battle/core.asm |
| PASS | test_static.sram_layout_unchanged | pyboy | 0.1 | static: symbol file and map file of the built ROM |

## Coverage (this run)

TESTED = every listed aspect has a passing test; PARTIAL = some; UNTESTED = none. Emulated runs only: nothing here is physical-hardware evidence.

| Area | Status | Covered | Not covered |
|---|---|---|---|
| Map traversal: connections, warps, collision | PARTIAL | map.connections, map.warps, map.collision | map.smoke |
| NPC interactions and scripted movement | UNTESTED | - | npc.interaction, npc.scripted_movement |
| Story progression and event flags | UNTESTED | - | story.flags, story.progression |
| Sprite allocation and rendering | PARTIAL | sprites.player | sprites.oam_budget, sprites.objects |
| Battle HUD, switching and knockouts | PARTIAL | battle.hud, battle.switching | battle.knockout |
| Moves, abilities and status effects | UNTESTED | - | battle.moves, battle.abilities, battle.status |
| Tournaments and custom battle systems | PARTIAL | cups.rising_star | cups.whirl, cups.kimono, cups.dragon, cups.rental, cups.world, link.friend |
| Cinematics and environmental effects | UNTESTED | - | cinematic, weather |
| Roaming Pokemon and time-dependent events | UNTESTED | - | roaming, time.clock |
| Save integrity, SRAM allocation, clock | PARTIAL | save.sram_layout | save.roundtrip, clock.software |
| Trading, link battles, communication recovery | UNTESTED | - | link.trade, link.battle, link.recovery |
| Extended gameplay stress / fuzzing | UNTESTED | - | stress.fuzz, stress.long |
| Follower and object-struct integrity | TESTED | follower, follower.static | - |
| Cartridge / mapper / header compliance | UNTESTED | - | hw.header, hw.mapper |
| Hardware rules: OAM, VRAM access, power-on RAM | PARTIAL | hw.memory_guard | hw.oam_lines, hw.vram_access, hw.startup_ram |
| Static data validation | PARTIAL | data.maps, data.layout | data.tables |
| Graphics: frames, VRAM, OAM, flicker, PPU timing | UNTESTED | - | av.frames, av.vram, av.oam, av.flicker, av.ppu_timing |
| Graphics before/after: menus, battles, map transitions, cinematics | UNTESTED | - | av.menus, av.battle_gfx, av.transitions, av.cinematics |
| Audio: PCM scan, silence, music loops, sound effects | UNTESTED | - | av.audio_pcm, av.silence, av.music_loops, av.sfx |
| Audiovisual cross-emulator comparison and approved references | UNTESTED | - | av.cross_emulator, av.audio_cross, av.references |
| Hardware models CGB-0 / CGB-E / AGB for audiovisual checks | UNTESTED | - | av.models |
