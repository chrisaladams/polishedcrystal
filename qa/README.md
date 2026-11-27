# QA framework

Automated tests that run the **built ROM** in emulators, plus static checks of the
repository. Used for Link Edition development through 2.1. The current results, findings
and open risks are in [`docs/qa-report.md`](../docs/qa-report.md).

Nothing here is evidence about a physical console. Every result is from emulation or static
analysis, and each test says how its starting state was reached (see *Provenance*).

## Quick start

```sh
sh qa/setup.sh               # once: RGBDS 1.0.4, PyBoy, SameBoy, Gearboy (+ SDL3)
make qa                      # regression + general suites (builds the ROM first)
make qa-full                 # everything
```

| Command | What runs |
|---|---|
| `make qa-general` | static checks, header/mapper, save round trip, fuzz, unit tests |
| `make qa-map` | all-map smoke (PyBoy), every map connection crossed on foot |
| `make qa-battle` | battle HUD / switching tests |
| `make qa-hardware` | header, mapper, power-on RAM, power-cut saves, SameBoy execution guard on every map (CGB-E and AGB), Gearboy cross-check |
| `make qa-regression` | one test per fixed defect, on every backend |
| `make qa-full` | all of the above |
| `make qa-list` | list tests, their suites and backends |

Options go in `QA_ARGS`: `make qa-map QA_ARGS="--seed 7 --jobs 2"`. Without make:
`python3 qa/run.py <suite> [--seed N] [--jobs N] [--backend pyboy|sameboy|all] [--models CGB-0,CGB-E,AGB] [--rom PATH] [--only SUBSTR] [--out DIR]`.
`make test` (the older build checks) is unchanged.

Exit status is non-zero if any test fails or errors. A skipped test is reported as skipped, never
as passed.

### Environment variables

`QA_ROM` (ROM to test), `QA_CACHE` (fixture cache), `QA_CONNECTION_LIMIT`, `QA_MAP_LIMIT`,
`QA_FUZZ_FRAMES`, `QA_FUZZ_STARTS` (shrink the long tests while developing), `GBDEV`,
`SAMEBOY_DIR`, `GEARBOY_BIN`, `SDL3_LIB` (tool locations).

## Layout

```
qa/run.py         runner: discovers tests, runs each in its own process, writes the report
qa/framework.py   @qa_test decorator and the per-test context (ctx.boot, ctx.expect, ctx.uncover)
qa/coverage.py    the coverage areas and the TESTED / PARTIAL / UNTESTED rules
qa/meta.py        run metadata: ROM hash and header, git commit, tool versions, seed
qa/report.py      results.json + summary.md
qa/tests/         the tests (test_*.py)
qa/gb/            the library
    emu.py          PyBoy backend: symbols, memory, input, hooks, routine calls, snapshots
    sameboy.py      SameBoy backend (ctypes): CGB-0..E / AGB, real boot ROM, seeded power-on RAM,
                    write watchpoints, native execution guard
    gearboy_mcp.py  Gearboy headless MCP client (debugger, symbols, trace, profiler)
    saves.py        save fixtures built by the game's own save routine, cached by ROM hash
    fixtures.py     New Game by button input, GivePoke, warps; labelled GAMEPLAY / INJECTED
    guards.py       player-struct / follower-queue / crash-handler guards
    collision.py    reads the loaded map's collision from RAM (as GetCoordTileCollision does)
    mapdata.py      maps, connections, object counts parsed from the repository
    scriptlint.py   static control-flow lint of map callbacks
    hw.py           OAM / sprites-per-scanline rules
qa/native/        execguard.c: C execution callback (NOP slides, illegal opcodes, code in VRAM/IO)
```

Symbol addresses always come from the `.sym` the build produces; constants are evaluated with
`rgbasm` against `includes.asm`, so tests survive code moving between banks.

## Writing a test

```python
from qa.framework import qa_test

@qa_test(suites=('regression', 'map'), covers=('map.connections', 'follower'),
         backends=('pyboy', 'sameboy'), provenance='walk: input; party: injected')
def my_test(ctx):
    g = ctx.boot('fixture_name', build_fn)      # Continue from a cached save (built once)
    ...
    ctx.expect(cond, 'what went wrong')         # collects failures; the test fails at the end
    ctx.uncover('map.connections', 'only 131 of 213')   # withdraw coverage you did not earn
```

* `covers` lists coverage tags (`qa/coverage.py`). A tag counts only if a test that declares it
  *passes*. If a run exercised only part of an aspect, call `ctx.uncover(tag, why)`.
* Failures write a screenshot, `state.json` (registers, ROM/WRAM/VRAM banks, LCD registers),
  `oam.bin`, `vram0.bin`, `vram1.bin` and any regions the test asks for under the test's report
  directory.
* Long tests are sharded (`..._0of4`) so `--jobs` spreads them across cores.

## Provenance

| Label | Meaning |
|---|---|
| gameplay | reached only by button presses from power-on |
| injected | memory writes, a direct routine call (`g.call`), or a warp were used to skip ahead |

Injection is how scenarios are reached quickly (a party, a position, an event flag, a KO), but it
can create states real play cannot. Each test states which parts are injected. Findings reached
only through injection are labelled as such in the report.

## Determinism

Everything is deterministic for a given ROM, backend, model and `--seed`: the emulators are
deterministic, SameBoy's power-on RAM comes from the seed, fuzz inputs come from `ctx.rng`.
Each run records the ROM SHA-1 and header, git commit (and whether the tree was dirty), tool
versions, host, seed and suite in `results.json` / `summary.md`. A failing fuzz run also writes its
input log so it can be replayed.

## Checking that a test can fail

A test that cannot fail proves nothing. For each regression test the report records the result
on the pre-fix ROM:

```sh
git worktree add /tmp/base <commit before the fix> && (cd /tmp/base && make)
python3 qa/run.py regression --rom /tmp/base/polishedcrystal-*.gbc
```

Source-pattern lints (`follower_slot_budget`, `party_menu_users_restore_enemy_pic`,
`map_callbacks_end_with_endcallback`) read the checkout, not the ROM, so `--rom` does not
affect them.

## Known limits

* PyBoy is not cycle-exact and its hooks are single-instruction patches. SameBoy is the
  accuracy reference; Gearboy is a third opinion. None replaces a real console.
* BGB and Emulicious are not available in the cloud environment (blocked hosts; BGB is
  Windows-only). SameBoy's write watchpoint and native execution guard stand in for BGB's
  exception/access-violation breakpoints; they do not cover every BGB check.
* The link cable tests in `utils/linktest/` need a Cython build of PyBoy's serial layer and
  family save files; they are not wired into this runner yet.
