# Physical-hardware diagnostics: proposal (not implemented)

Status: **proposal, awaiting the owner's decision.** Nothing in this document is built. It
exists because the ROM has almost no spare RAM and strict save-compatibility rules, so any
diagnostic that records state is an architectural choice, and the brief asks for the owner to
be consulted first.

## What a diagnostic build would be for

Both defects reported from hardware (Lake of Rage, Rising Cup) turned out to reproduce in
emulation, so they did not need a diagnostic ROM. A diagnostic build is for the *next* defect
that does not reproduce: it would catch a corruption or an illegal state on the console and
report where, without a debugger.

## Constraints measured on the current ROM

`utils/memory_report.py` on `polishedcrystal-3.2.3.map`:

| Region | Free | Largest gap |
|---|---:|---:|
| WRAM0 | 9 B | 9 B |
| WRAMX (7 banks) | 3,561 B | 1,809 B |
| HRAM | 5 B | 5 B |
| SRAM (4 banks) | 923 B | 393 B (scattered over eight gaps) |
| ROM | about 2 MiB of the 4 MiB map | n/a |

* WRAM0 and HRAM cannot hold a log. WRAMX can, but only through bank switching.
* SRAM holds the saves. [`sram-allocation.md`](sram-allocation.md) requires any new record to
  carry its own marker and checksum and to be written interruption-safely. Writing diagnostics
  there risks the player's data; it needs explicit authorisation.
* Instrumentation changes timing (extra instructions per frame, bank switches). A defect that
  depends on timing may move or vanish in the diagnostic build, so a clean diagnostic run is weak
  evidence of absence.

## What already exists

The VBlank handler already detects stack overflow and underflow, execution from RAM, and a ROM
checksum mismatch, stores a code in `hCrashCode`, and shows the blue crash screen
(`engine/movie/bsod.asm`). If a console ever shows that blue screen, **photograph it**: it names
the error. That costs nothing and is in the release build today.

## Options

**A. On-screen diagnostics, no SRAM (recommended).** `make diag` defines `DIAG`; release builds
contain none of it (`if DEF(DIAG)` around every line, and the QA suite can assert the release ROM
is byte-identical with the flag off).
* A 32-event ring buffer (2 bytes each: checkpoint id, argument) in a `DIAG`-only WRAMX
  section, written by a `diag_log ID` macro that compiles to nothing otherwise.
* A per-frame overworld check of the invariants the QA suite found to matter: the player's
  object struct identity bytes, the follower queue length, the stack pointer's page, and the
  script position after a map callback returns.
* On the first violation, a diagnostic screen (hex, readable in a photograph) with the last
  events, the map, coordinates, ROM bank, WRAM bank and the failing check. Dismissed with a
  button; the game then carries on.
* No SRAM access, so no effect on saves. Cost: roughly 150 lines of assembly and about 1 KB of
  ROM, all `DIAG`-only.

**B. Add an SRAM export.** The same log, written to a dedicated record in the 393-byte gap
(marker + checksum + clear-then-write, as the Friend Teams do) **only** when the player chooses
"Save diagnostics" on the diagnostic screen, and readable with a save-file dumper. This lets
someone without a camera send the log, but it uses a sliver of the reserved maintenance SRAM and
needs the owner's approval for that allocation.

**C. Cable export.** Stream the log over the link cable to a PC. Needs hardware the owner may not
have and a protocol; not recommended unless A and B prove insufficient.

## Decisions needed from the owner

1. Is Option A approved as a `DIAG`-only build? (Nothing reaches release builds.)
2. Is any SRAM use for diagnostics acceptable (Option B), and if so which of the free gaps?
3. Which checks matter most on hardware: the player struct and follower queue (the defect class
   found here), script position after callbacks (L30), the stack page, or all three?

## Reproducing and reporting a hardware defect today (no instrumentation)

1. Note the ROM: the SHA-1 of the flashed file (`CHECKSUMS.txt`) and the console (GBC, GBA or SP).
2. Back up the save first. Test with a copy of the save, not the only one.
3. Reproduce from a known state: say where you started (map, coordinates, party, whether the
   follower option is on) and the exact steps.
4. If the screen goes blue, photograph it before powering off: it carries the error code.
5. If nothing visible happens (a freeze), say whether music and the menu still work (the Lake of
   Rage defect left the menu and Fly working, which pointed at object state, not a crash).
6. Photograph the screen at the failure, and say whether it repeats after a power cycle.
7. Run `make qa-regression` on the same commit: if it passes, the defect is probably timing- or
   hardware-specific, and Option A is what to build next.
