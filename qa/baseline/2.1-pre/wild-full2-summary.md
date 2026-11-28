# QA run

- ROM: `polishedcrystal-3.2.3.gbc` sha1 `53dc05aafe9a2e325f13044d6c4bfe2bcc7d6aeb` (MBC5+RAM+BATTERY, 2097152 bytes)
- Commit: `749902a1e0a62d1f94aff29d612065019b658153` (working tree dirty) on `claude/sleepy-ramanujan-kc278b`
- Tools: python 3.13.18, pyboy 2.9.0, sameboy ea667ad, gearboy ad6fa70, rgbds rgbasm v1.0.4
- Seed: 1   Suite: map   Backend option: default   SameBoy models: per-test default
- Hardware: emulated only: no physical console results are included

| Result | Test | Backend | Seconds | Provenance |
|---|---|---|---|---|
| FAIL | test_wild.wild_zones_1of4 | sameboy CGB-E | 190.3 | standing on the zone: injected warp and clock; the encounters are drawn by calling the game's own ChooseWildEncounter (injected call) |
| FAIL | test_wild.wild_zones_2of4 | sameboy CGB-E | 183.3 | standing on the zone: injected warp and clock; the encounters are drawn by calling the game's own ChooseWildEncounter (injected call) |
| PASS | test_wild.wild_zones_0of4 | sameboy CGB-E | 155.5 | standing on the zone: injected warp and clock; the encounters are drawn by calling the game's own ChooseWildEncounter (injected call) |
| PASS | test_wild.wild_zones_3of4 | sameboy CGB-E | 112.2 | standing on the zone: injected warp and clock; the encounters are drawn by calling the game's own ChooseWildEncounter (injected call) |

## Failures

### test_wild.wild_zones_2of4 (sameboy)
- SCARY_CAVE_B1F:grass:morn: species [72, 73, 171] are not in the table ['GOLBAT', 'KINGLER', 'CORSOLA', 'CORSOLA', 'HAUNTER', 'KINGLER', 'KINGLER']
- SCARY_CAVE_B1F:grass:day: species [72, 73, 171] are not in the table ['GOLBAT', 'KINGLER', 'CORSOLA', 'CORSOLA', 'HAUNTER', 'KINGLER', 'KINGLER']
- SCARY_CAVE_B1F:grass:nite: species [72, 73, 171] are not in the table ['GOLBAT', 'KINGLER', 'CORSOLA', 'CORSOLA', 'HAUNTER', 'KINGLER', 'KINGLER']
- SEAFOAM_ISLANDS_B4F:grass:morn: species [80, 116] are not in the table ['GOLBAT', 'DEWGONG', 'GOLDUCK', 'JYNX', 'PSYDUCK', 'SEEL', 'DEWGONG']
- SEAFOAM_ISLANDS_B4F:grass:day: species [80, 116] are not in the table ['GOLBAT', 'DEWGONG', 'GOLDUCK', 'JYNX', 'PSYDUCK', 'SEEL', 'DEWGONG']
- SEAFOAM_ISLANDS_B4F:grass:nite: species [80, 116] are not in the table ['GOLBAT', 'DEWGONG', 'GOLDUCK', 'JYNX', 'PSYDUCK', 'SEEL', 'DEWGONG']
- SHAMOUTI_SHRINE_RUINS:grass:morn: species [72, 73] are not in the table ['KRABBY', 'LEDIAN', 'PONYTA', 'HYPNO', 'PONYTA', 'RAPIDASH', 'RAPIDASH']
- SHAMOUTI_SHRINE_RUINS:grass:day: species [72, 73] are not in the table ['KRABBY', 'WEEPINBELL', 'PONYTA', 'HYPNO', 'PONYTA', 'RAPIDASH', 'RAPIDASH']
- SHAMOUTI_SHRINE_RUINS:grass:nite: species [72, 73] are not in the table ['KRABBY', 'ARIADOS', 'PONYTA', 'HYPNO', 'PONYTA', 'RAPIDASH', 'RAPIDASH']
- SILVER_CAVE_OUTSIDE:grass:morn: species [61, 62] are not in the table ['TANGELA', 'PONYTA', 'ARBOK', 'RAPIDASH', 'DODRIO', 'SKARMORY', 'URSARING']
- SILVER_CAVE_OUTSIDE:grass:day: species [61, 62] are not in the table ['TANGELA', 'PONYTA', 'ARBOK', 'RAPIDASH', 'DODRIO', 'SKARMORY', 'URSARING']
- SILVER_CAVE_OUTSIDE:grass:nite: species [62] are not in the table ['TANGELA', 'POLIWHIRL', 'GOLBAT', 'POLIWHIRL', 'HOUNDOOM', 'SNEASEL', 'SNEASEL']
- SLOWPOKE_WELL_B2F:grass:morn: species [80] are not in the table ['ZUBAT', 'ZUBAT', 'ZUBAT', 'SLOWPOKE', 'GOLBAT', 'SLOWPOKE', 'SLOWPOKE']
- SLOWPOKE_WELL_B2F:grass:day: species [80] are not in the table ['ZUBAT', 'ZUBAT', 'ZUBAT', 'SLOWPOKE', 'GOLBAT', 'SLOWPOKE', 'SLOWPOKE']
- SLOWPOKE_WELL_B2F:grass:nite: species [80] are not in the table ['ZUBAT', 'ZUBAT', 'ZUBAT', 'SLOWPOKE', 'GOLBAT', 'SLOWPOKE', 'SLOWPOKE']
- TOHJO_FALLS:grass:morn: species [118, 119] are not in the table ['ZUBAT', 'RATICATE', 'GOLBAT', 'SLOWPOKE', 'RATTATA', 'SLOWPOKE', 'SLOWPOKE']
- TOHJO_FALLS:grass:day: species [118, 119] are not in the table ['ZUBAT', 'RATICATE', 'GOLBAT', 'SLOWPOKE', 'RATTATA', 'SLOWPOKE', 'SLOWPOKE']
- TOHJO_FALLS:grass:nite: species [118, 119] are not in the table ['ZUBAT', 'RATICATE', 'GOLBAT', 'SLOWPOKE', 'RATTATA', 'SLOWPOKE', 'SLOWPOKE']
- UNION_CAVE_B1F_NORTH:grass:morn: species [194, 195] are not in the table ['GEODUDE', 'ZUBAT', 'ZUBAT', 'ONIX', 'RATTATA', 'RATTATA', 'RATTATA']
- UNION_CAVE_B1F_NORTH:grass:day: species [194, 195] are not in the table ['GEODUDE', 'ZUBAT', 'ZUBAT', 'ONIX', 'RATTATA', 'RATTATA', 'RATTATA']
- UNION_CAVE_B1F_NORTH:grass:nite: species [195] are not in the table ['GEODUDE', 'ZUBAT', 'WOOPER', 'ONIX', 'RATTATA', 'RATTATA', 'RATTATA']
- UNION_CAVE_B2F:grass:morn: species [72, 73, 195] are not in the table ['ZUBAT', 'GOLBAT', 'ZUBAT', 'RATICATE', 'GEODUDE', 'ONIX', 'ONIX']
- UNION_CAVE_B2F:grass:day: species [72, 73, 195] are not in the table ['ZUBAT', 'GOLBAT', 'ZUBAT', 'RATICATE', 'GEODUDE', 'ONIX', 'ONIX']
- UNION_CAVE_B2F:grass:nite: species [72, 73] are not in the table ['ZUBAT', 'GOLBAT', 'QUAGSIRE', 'RATICATE', 'GEODUDE', 'ONIX', 'ONIX']
- WHIRL_ISLAND_B2F:grass:morn: species [73, 116, 224] are not in the table ['KRABBY', 'ZUBAT', 'SEEL', 'KRABBY', 'GOLBAT', 'SHELLDER', 'SHELLDER']
- WHIRL_ISLAND_B2F:grass:day: species [73, 116, 224] are not in the table ['KRABBY', 'ZUBAT', 'SEEL', 'KRABBY', 'GOLBAT', 'SHELLDER', 'SHELLDER']
- WHIRL_ISLAND_B2F:grass:nite: species [73, 116, 224] are not in the table ['KRABBY', 'ZUBAT', 'KRABBY', 'KRABBY', 'GOLBAT', 'GOLBAT', 'GOLBAT']
- WHIRL_ISLAND_SW:grass:morn: species [72, 116, 224] are not in the table ['KRABBY', 'ZUBAT', 'SEEL', 'KRABBY', 'GOLBAT', 'SHELLDER', 'SHELLDER']
- WHIRL_ISLAND_SW:grass:day: species [72, 116, 224] are not in the table ['KRABBY', 'ZUBAT', 'SEEL', 'KRABBY', 'GOLBAT', 'SHELLDER', 'SHELLDER']
- WHIRL_ISLAND_SW:grass:nite: species [72, 116, 224] are not in the table ['KRABBY', 'ZUBAT', 'KRABBY', 'KRABBY', 'GOLBAT', 'GOLBAT', 'GOLBAT']
Artifacts: test_wild.wild_zones_2of4.sameboy.CGB-E/failure_0.png
### test_wild.wild_zones_1of4 (sameboy)
- SCARY_CAVE_1F:water:day: species [41, 42, 98, 99, 222] are not in the table ['TENTACOOL', 'TENTACRUEL', 'LANTURN']
- SCARY_CAVE_SHIPWRECK:water:day: species [24, 42, 222] are not in the table ['MISDREAVUS', 'HAUNTER', 'LANTURN']
- SLOWPOKE_WELL_B1F:water:day: species [41] are not in the table ['SLOWPOKE', 'SLOWPOKE', 'SLOWPOKE']
- UNION_CAVE_1F:water:day: species [19, 27, 41, 74, 95] are not in the table ['WOOPER', 'QUAGSIRE', 'QUAGSIRE']
- UNION_CAVE_B1F_SOUTH:water:day: species [20, 41, 42, 74, 95] are not in the table ['WOOPER', 'QUAGSIRE', 'QUAGSIRE']
- YELLOW_FOREST:water:day: species [46, 161, 172, 209] are not in the table ['MARILL', 'PIKACHU', 'PSYDUCK']
Artifacts: test_wild.wild_zones_1of4.sameboy.CGB-E/failure_0.png

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
