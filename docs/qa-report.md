# QA report: hardware reliability and automated testing

Branch `claude/sleepy-ramanujan-kc278b`. Framework: [`qa/`](../qa/README.md); run it with `make qa` or `make qa-full`.
Findings are tracked in the [issue ledger](issue-ledger.md) as L28-L32.

Canonical run: ROM `polishedcrystal-3.2.3.gbc` SHA-1 `5cdb8dc593574b373021c92e6c7aa4faf8081cda`, commit `9a56d20f81` (clean tree), seed 1,
RGBDS 1.0.4, PyBoy 2.9.0, SameBoy `ea667ad`, Gearboy `ad6fa70`: **41 test runs, 41 passed** (`make qa-full`,
about 17 minutes on 3 workers). Report files: `qa/reports/runs/<time>/summary.md` and `results.json`.

**Everything below is from emulation (PyBoy, SameBoy, Gearboy) or static analysis. No result is
evidence about a physical console, and nothing is marked hardware-verified.** The two defects
reported from hardware are reproduced and fixed in emulation; whether the fixes cure the
cartridge is for the owner to confirm ([checklist section 8](release-2.0/hardware-checklist.md)).

## 1. Summary

| | |
|---|---|
| Confirmed defects fixed | 3 (L28 Lake of Rage, L29 Rising Cup HUD, L30 Battle Factory Hallway callback) |
| Behaviour change to confirm | 1 (L31: followers now appear in Lake of Rage and Cerulean Cape) |
| Regression tests | one per defect, each shown to **fail on the pre-fix ROM** and pass on the fixed one |
| Maps entered and checked | 612 of 613 (1 has no walkable tile) on PyBoy; on SameBoy CGB-E and AGB with an execution guard |
| Map connections crossed on foot | 131 of 213 (82 not crossable by walking; listed in §5) |
| Power cuts inside a save | 44 cut points across a 7,340-write save: all loaded the old or the new state, none corrupt |
| Not tested | large parts of the game (§6) |
| Not available | BGB, Emulicious, any physical console |

## 2. Environment

| Tool | Version | Use |
|---|---|---|
| RGBDS | 1.0.4 (built from source; the repo's INSTALL.md version) | build |
| PyBoy | 2.9.0 | high-volume input-driven tests, routine calls, snapshots |
| SameBoy | `LIJI32/SameBoy` master (commit in each run's `results.json`) | accuracy reference: real CGB boot ROMs, models CGB-0, CGB-E, AGB, seeded power-on RAM, write watchpoints, native execution guard |
| Gearboy | 3.8.x, headless `--mcp-stdio` | independent cartridge/symbol cross-check; its MCP debugger (breakpoints, trace, profiler) is wired in `qa/gb/gearboy_mcp.py` |
| SDL3 | 3.2.8 (built from source; Gearboy needs it) | |

Install everything with `sh qa/setup.sh`. Emulators run with no compatibility hacks: SameBoy uses
the real boot ROM of each model; PyBoy runs without a boot ROM, which is a stated difference.

**Cartridge facts, checked three ways** (header parse, Gearboy, PyBoy/SameBoy boot): MBC5+RAM+BATTERY
(`$1B`), 2 MiB ROM file (128 banks; the layout reserves 4 MiB), 32 KiB SRAM in 4 banks, CGB flag
`$80` (enhanced: also boots on a DMG), no real-time clock (the world clock is software), header and
global checksums valid. Speed modes: the emulators boot and run in normal speed; **double-speed
operation is not separately tested.**

**Tools not available.** BGB (closed source, Windows-only; `bgb.bircd.org` is blocked here and there
is no Wine) and Emulicious (`emulicious.net` blocked) could not be installed, so none of their
strict-exception checks were run. SameBoy's write watchpoint (`SBGame.write_watch`) and the native
execution guard (`qa/native/execguard.c`: NOP slides, illegal opcodes, code fetched from
VRAM/OAM/IO) cover part of the same ground, not all of it. Symbols are loaded into Gearboy; RGBDS
`.sym` files drive PyBoy and SameBoy through the framework. RGBDS `.map` files feed the memory audit.

## 3. Confirmed defects

### L28 Lake of Rage: the player vanishes or freezes (fixed in emulation)

* **Reproduced** by walking (real input) from Route 43 north across the map connection into Lake of
  Rage with a Pokemon in the party. Warping into the map does not trigger it, which is why the first
  attempts failed.
* **Evidence.** The player's object struct changes from Sprite 4, MapObjectIndex 0, SpriteTile 128
  to 13, 13, 13 as the follower queue length climbs past 5. A SameBoy write watchpoint on those
  bytes named `ApplyMovementToFollower` as the writer. The OAM then draws the player from garbage
  tiles; the menu and Fly keep working because they do not use that struct, matching the report.
* **Root cause.** Lake of Rage has 19 object events; `CanHaveFollower` refused a follower at
  19 or more (an off-by-one: the follower's slot, object 20, is only taken at 20). The follow link
  from Route 43 stayed on across the connection with no follower to consume the queue, so each step
  appended to `wFollowMovementQueue`, a 5-byte array directly before `wObjectStructs`. Entries 6, 7
  and 8 landed on the player's Sprite, MapObjectIndex and SpriteTile.
* **Fix** (`engine/overworld/follower.asm`, `map_objects.asm`): drop a stale follow link in
  `SpawnFollower`; never queue past the queue's end; correct the threshold.
* **Not specific to hardware**: it reproduces on PyBoy and on SameBoy CGB-0, CGB-E and AGB.
* **Tests**: `test_lake_of_rage` (both emulators, three revisions), `test_static.follower_queue_cannot_overrun`,
  `test_static.follower_slot_budget`, and `test_connections` (every connection).
* **Pre-fix ROM** (commit `52dff64`, SHA-1 `e28d623e0a8a`): all of the above fail, as the mutation run in §4 shows.

### L29 Rising Cup: status symbols beside the enemy sprite (fixed in emulation)

* **Reproduced** with real input: enter the Rising Star Cup, let the lead faint, send in the next
  Pokemon. A column of status icons appears over the enemy's sprite. (The faint itself is produced by
  setting the lead's HP to 0 at the first battle menu; the rest is the game's own flow.)
* **Root cause.** The party menu loads `GFX_StatusIcons` (16 tiles) over `vTiles2` tile `$00`, where
  the enemy's front pic lives. The voluntary switch paths reload the pic afterwards;
  `GetPlayerSwitchTarget`, used after a faint (and for Baton Pass and U-turn), did not. The icons stayed
  until the enemy was replaced, which is exactly what was reported.
* **Not specific to the cup or to hardware.** The code path is every battle.
* **Fix** (`engine/battle/core.asm`): `GetPlayerSwitchTarget` calls `GetMonFrontpic` after the menu.
* **`OfferSwitch` has the same omission and is left alone**: the enemy sends out a new Pokemon, loading
  its pic, immediately afterwards, and the enemy's tilemap is cleared meanwhile. This is analysis,
  not a test (`party_menu_users_restore_enemy_pic` records the exemption).
* **Tests**: `test_rising_cup_hud` (both emulators, three revisions), `test_static.party_menu_users_restore_enemy_pic`.

### L30 Battle Factory Hallway: a map callback that ends with `end` (found by the suite; fixed)

* **Not one of the two reported defects.** Found by entering every map on SameBoy: on **AGB (a Game
  Boy Advance in Game Boy Color mode) the hallway hard-locks** ("Illegal Opcode. Halting"), on CGB-0
  and CGB-E it runs a WRAM NOP slide and happens to recover.
* **Root cause.** `BattleFactoryHallway`'s `MAPCALLBACK_OBJECTS` script ended with `end`.
  `CallCallback` saves the caller's script position; `end` pops it and resumes executing from that
  stale position, running garbage commands, until a command index jumps into WRAM
  (`$CDCD`, a NOP slide to `$CEB4`) and a `ret` returns into whatever the stack holds. Where that
  lands is luck: valid code on CGB, data on AGB. **The same code is in upstream Polished Crystal.**
* **Fix**: both `end`s are `endcallback`. A static lint (`qa/gb/scriptlint.py`) follows every
  callback's control flow in all map files and finds no other instance.
* **Caveat: reached by an injected warp.** The callback runs on every entry to the hallway in real
  play, with whatever script position the previous script left, so a real run could hit it; that is
  *unverified*. On a GBA it is worth testing (checklist 8.4).
* **Tests**: `test_static.map_callbacks_end_with_endcallback` (fails on the pre-fix source),
  `test_map_smoke.enter_maps_exec_guard_*` (fails on the pre-fix ROM on CGB-E and AGB).

### L31 Behaviour change to confirm

With the threshold corrected, **Lake of Rage and Cerulean Cape (19 object events) now have a
follower** (seen in Lake of Rage; Cerulean Cape follows from the same rule and was crossed by the
connection test, not looked at); previously they had none. Ilex Forest (20 events) still has none because the map itself
uses the follower's slot. If the owner would rather these two maps stay follower-free, the fix is to
keep the old threshold and rely on the stale-link and queue-bound fixes; say so and it is a
one-line change.

## 4. Do the tests have teeth? (mutation check)

Every regression test was run on the **pre-fix ROM** and fails; on the fixed ROM it passes.

| Test | Pre-fix ROM | Fixed ROM |
|---|---|---|
| `lake_of_rage_approach` (PyBoy; SameBoy CGB-0, CGB-E, AGB) | FAIL (all) | PASS (all) |
| `rising_cup_replacement_hud` (same four) | FAIL (all) | PASS (all) |
| `follower_queue_cannot_overrun` | FAIL | PASS |
| `cross_connections` (the shard containing Route 43 to Lake of Rage) | FAIL | PASS |
| `enter_maps_exec_guard` (the shard containing the hallway; CGB-E and AGB) | FAIL (NOP slide; AGB also illegal opcode) | PASS |
| `map_callbacks_end_with_endcallback` (source lint) | FAIL on the pre-fix source | PASS |

The source-pattern lints read the checkout, not the ROM, so `--rom` does not change them.

## 5. What the broader tests found

* **Maps (612 entered, 1 skipped).** No crash handler ran, no hard lock, no illegal opcode, no
  corrupted player struct on the fixed ROM, on PyBoy, SameBoy CGB-E and SameBoy AGB. Largest sprite
  load on one scanline: 10 (`CELADON_HOME_DECOR_STORE_4F`), at the hardware limit but not over it.
  Maps were entered by injected warp and the player stood still: this checks map loading and standing
  state, not play.
* **Connections.** 131 of 213 crossed on foot, with the object-engine guards on for 8 further steps
  each, with no violation. The other 82 could not be crossed by walking: roughly 55 have no walkable
  tile aligned on the connection edge (sea routes needing Surf, ledges, trees), about 25 were tried
  and not crossed (a hazard or a blocked tile), 1 is a placeholder map (`FAKE_ROUTE_36`), 1 was
  interrupted by a battle. Those are **untested** and the coverage table says so.
* **Power-on RAM.** Five noise seeds on PyBoy and SameBoy: New Game reaches the bedroom in the same
  number of presses every time.
* **Saves.** Round trip loads identical state; flipping three bytes of the primary save recovers the
  identical state from the backup each time; **power cuts** at 44 points across a save of 7,340
  cartridge-RAM writes all load either the old or the new state intact (19 old, 25 new). This is
  emulated (SameBoy, snapshots between writes): **power loss on real flash/SRAM carts is still the
  open roadmap item.**
* **Fuzz.** Seeded random input (6,000 frames) from 10 starting points, watching the guards, on PyBoy
  and SameBoy CGB-E: no findings. It reaches wild battles (457 and 396 frames in battle) but not deep content.
* **Gearboy** agrees on the mapper, battery, RAM size, bank counts and symbol addresses.

## 6. Coverage: tested, partial, untested

The table below is generated by `qa/coverage.py` from the canonical run. The rules: TESTED = every listed aspect has a passing test; PARTIAL = some do; UNTESTED = none.
**Visiting a map or running code does not earn a tag**; a test must assert something.

TESTED = every listed aspect has a passing test; PARTIAL = some; UNTESTED = none. Emulated runs only: nothing here is physical-hardware evidence.

| Area | Status | Covered | Not covered |
|---|---|---|---|
| Map traversal: connections, warps, collision | UNTESTED | - | map.warps, map.collision, map.connections (21 of 53 in shard 3 not crossed on foot), map.smoke (1 of 153 maps in this shard had no walkable tile) |
| NPC interactions and scripted movement | UNTESTED | - | npc.interaction, npc.scripted_movement |
| Story progression and event flags | UNTESTED | - | story.flags, story.progression |
| Sprite allocation and rendering | PARTIAL | sprites.player, sprites.oam_budget | sprites.objects |
| Battle HUD, switching and knockouts | PARTIAL | battle.hud, battle.switching | battle.knockout |
| Moves, abilities and status effects | UNTESTED | - | battle.moves, battle.abilities, battle.status |
| Tournaments and custom battle systems | PARTIAL | cups.rising_star | cups.whirl, cups.kimono, cups.dragon, cups.rental, cups.world, link.friend |
| Cinematics and environmental effects | UNTESTED | - | cinematic, weather |
| Roaming Pokemon and time-dependent events | UNTESTED | - | roaming, time.clock |
| Save integrity, SRAM allocation, clock | PARTIAL | save.roundtrip, save.sram_layout | clock.software |
| Trading, link battles, communication recovery | UNTESTED | - | link.trade, link.battle, link.recovery |
| Extended gameplay stress / fuzzing | PARTIAL | stress.fuzz | stress.long |
| Follower and object-struct integrity | TESTED | follower, follower.static | - |
| Cartridge / mapper / header compliance | TESTED | hw.header, hw.mapper | - |
| Hardware rules: OAM, VRAM access, power-on RAM | PARTIAL | hw.oam_lines, hw.memory_guard, hw.startup_ram | hw.vram_access |
| Static data validation | TESTED | data.maps, data.tables, data.layout | - |

A test that only partly exercised an aspect withdraws that tag (`ctx.uncover`), so "Map traversal"
reads UNTESTED even though 612 maps were entered and 131 of 213 connections crossed: some connections
could not be crossed on foot and one map has no walkable tile, so the claim is withheld rather than rounded up.

Known gaps, in plain words:

* **Not tested at all:** NPC interactions and scripted movement; story progression and event
  flags; moves, abilities and status effects in the ROM (the simulator oracles under `meta_sim/`
  test the maths, not wired here); cinematics and weather; roaming and time-dependent events;
  extended multi-hour play.
* **Only the Rising Star Cup** of the six cups is driven; Whirl, Kimono, Dragon, Rental and World
  are not.
* **Link, trade and recovery:** `utils/linktest/` exists and is not wired into this runner (it needs
  a Cython build of a modified PyBoy serial layer and the family saves).
* **Hardware rules:** the 10-sprites-per-scanline limit and executed-code region checks run on every
  map; VRAM-access timing, DMA/interrupt interplay, VBlank workload, stack depth and double-speed
  mode are **not measured**. The VBlank handler's built-in stack check exists in the ROM; its
  headroom was not measured.
* **Fixture realism.** Most scenarios start from an injected party and position (marked in every
  test's provenance). Only New Game to the bedroom, the walks, and the cup/battle input are real play.

## 7. Outstanding risks

1. **Hardware.** Neither reported defect, nor the hallway lock, has been re-tested on a console.
   Checklist section 8 lists what to do.
2. **Unknown unknowns.** The suite found a latent bug nobody reported (L30) by looking for
   illegal execution; the same style of guard has covered maps but not battles, menus or link play.
3. **Upstream.** L28's stale-link/queue hazard is specific to the Link Edition follower; L29 and
   L30 are in upstream's code too (the party-menu and callback code is identical there).
   Suggest reporting L29 and L30 upstream.
4. **Injected-state findings.** Anything reached only by injection is labelled; the hallway lock
   is the main one.
5. **Instrumentation.** The planned diagnostic build is a proposal only
   ([`diagnostics-proposal.md`](diagnostics-proposal.md)); a decision is needed on SRAM use.

## 8. Test inventory

| Test | Suites | Backends |
|---|---|---|
| `test_connections.cross_connections_0of4` | map,full | pyboy |
| `test_connections.cross_connections_1of4` | map,full | pyboy |
| `test_connections.cross_connections_2of4` | map,full | pyboy |
| `test_connections.cross_connections_3of4` | map,full | pyboy |
| `test_map_smoke.enter_maps_0of4` | map,full | pyboy |
| `test_map_smoke.enter_maps_1of4` | map,full | pyboy |
| `test_map_smoke.enter_maps_2of4` | map,full | pyboy |
| `test_map_smoke.enter_maps_3of4` | map,full | pyboy |
| `test_map_smoke.enter_maps_exec_guard_0of4` | hardware,full | sameboy |
| `test_map_smoke.enter_maps_exec_guard_1of4` | hardware,full | sameboy |
| `test_map_smoke.enter_maps_exec_guard_2of4` | hardware,full | sameboy |
| `test_map_smoke.enter_maps_exec_guard_3of4` | hardware,full | sameboy |
| `test_fuzz.random_input_fuzz` | general,full | pyboy,sameboy |
| `test_gearboy.gearboy_agrees_on_cartridge` | hardware,general,full | pyboy |
| `test_hardware.rom_header_and_mapper` | hardware,general,full | pyboy |
| `test_hardware.power_on_ram_noise` | hardware,full | pyboy,sameboy |
| `test_lake_of_rage.lake_of_rage_approach` | regression,map,full | pyboy,sameboy |
| `test_rising_cup_hud.rising_cup_replacement_hud` | regression,battle,full | pyboy,sameboy |
| `test_save.save_round_trip` | general,full | pyboy,sameboy |
| `test_save.corrupted_primary_save_recovers_from_backup` | general,full | sameboy |
| `test_save.power_cut_during_save` | full,hardware | sameboy |
| `test_static.sram_layout_unchanged` | general,hardware,regression,full | pyboy |
| `test_static.text_and_palette_tables` | general,full | pyboy |
| `test_static.memory_regions_within_hardware` | general,hardware,full | pyboy |
| `test_static.follower_slot_budget` | general,regression,full | pyboy |
| `test_static.party_menu_users_restore_enemy_pic` | general,battle,regression,full | pyboy |
| `test_static.follower_queue_cannot_overrun` | general,regression,hardware,full | pyboy |
| `test_static.map_callbacks_end_with_endcallback` | general,regression,hardware,full | pyboy |

## 9. Reproducing

```sh
sh qa/setup.sh && make qa-full          # everything; reports in qa/reports/runs/<time>/
make qa                                 # the quick gate
python3 qa/run.py regression --rom /path/to/older.gbc   # mutation check against an older ROM
```

Each run's `results.json` records the ROM SHA-1 and header, git commit and dirty flag, tool versions,
host, seed, suite and backend options; failures include screenshots, registers, banks, OAM and VRAM
dumps. The runs below used seed 1.
