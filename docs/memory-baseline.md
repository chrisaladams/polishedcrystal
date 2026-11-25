# Memory baseline

Measured from the linker map, not estimated. Regenerate with
`python3 utils/memory_report.py polishedcrystal-3.2.3.map` (add
`--compare OLD.map` for a before/after report, `--markdown` for tables), and
`make freespace` for `bank_ends.txt`.

## Build

| | |
|---|---|
| Commit | `b47b74a31` (Phase 8: the linked World Championship) |
| Toolchain | RGBDS 1.0.4 (rgbasm, rgblink, rgbgfx), Python 3.13.18 |
| Cartridge | MBC3, 2 MiB ROM, 32 KiB SRAM (4 banks) |
| `make` (crystal) | `polishedcrystal-3.2.3.gbc`, SHA-1 `3591eceeb49141c84dbcd3f6062fc218ad4c69dc`, 12,992 bytes free |
| `make faithful` | `polishedcrystal-faithful-3.2.3.gbc`, SHA-1 `631750aadf5f0591517655e55167df29e3f30cbb`, 13,053 bytes free |

Each was built from a `make tidy` tree. The other targets (monochrome, noir,
hgss, debug, pocket, vc) weren't measured here; `make test` builds debug.

## Summary

| Resource | Free | Largest contiguous gap | Notes |
|---|---:|---:|---|
| ROM, total | 12,993 B | 12,741 B | 12,741 of it in ROMX bank $7f; every other ROMX bank has 0-4 B; ROM0 has 199 B at $3f39 |
| ROM, after the 7 KiB reserve | 5,825 B | | |
| SRAM | 152 B | 84 B | bank 0: 23 B at $a5e9, 23 B at $b1e9, 84 B at $bfac; bank 1: 4 B; banks 2-3: 9 B each |
| WRAM0 | 16 B | 16 B | at $cfe0; the "Misc 404" union is still 404 B (the Championship's buffers are inside it) |
| WRAMX | 3,718 B | 1,950 B | bank 1: 13 B; bank 2: 1,643 B (1,628 contiguous at $d9a4); bank 5: 2,062 B (1,950 at $d562); banks 3, 4, 6, 7 full |
| HRAM | 5 B | 5 B | at $ffef |
| VRAM | (static map: both banks allocated) | | the map shows the fixed vTiles/vBGMap layout; free tiles depend on the screen, so a per-screen audit is still to do |

## What the newest features cost

Measured by building each commit and comparing maps (`--compare`):

| Change | Commit | ROM | SRAM | WRAM0 |
|---|---|---:|---:|---:|
| Before them | `70ca5f0c5` | 17,489 B free | 444 B free | 18 B free |
| Bedroom achievements | `47a86b55f` | +815 B | 0 | 0 |
| Friend Battles | `d9466245e` | +1,544 B | +272 B | +2 B |
| Linked World Championship | `b47b74a31` | +2,138 B | +20 B | 0 |
| Total | | +4,497 B | +292 B | +2 B |

Before these, ROMX bank $7f was entirely empty; the achievements fit in
scattered space, and Friend Battles and the Championship took 3,643 B of it.

## crystal, in detail

### Totals

| Region | Banks | Used | Free | Largest gap | Empty banks |
|---|---:|---:|---:|---:|---:|
| ROM0 | 1 | 16184 | 200 | 199 | 0 |
| ROMX | 127 | 2067975 | 12793 | 12741 | 0 |
| VRAM | 2 | 16384 | 0 | 0 | 0 |
| SRAM | 4 | 32616 | 152 | 84 | 0 |
| WRAM0 | 1 | 4080 | 16 | 16 | 0 |
| WRAMX | 7 | 24954 | 3718 | 1950 | 0 |
| HRAM | 1 | 122 | 5 | 5 | 0 |

### SRAM by bank

| Bank | Used | Free | Gaps (start: bytes) |
|---:|---:|---:|---|
| 0 | 8062 | 130 | $a5e9: 23, $b1e9: 23, $bfac: 84 |
| 1 | 8188 | 4 | $bffc: 4 |
| 2 | 8183 | 9 | $bff7: 9 |
| 3 | 8183 | 9 | $bff7: 9 |

### WRAM0 by bank

| Bank | Used | Free | Gaps (start: bytes) |
|---:|---:|---:|---|
| 0 | 4080 | 16 | $cfe0: 16 |

### WRAMX by bank

| Bank | Used | Free | Gaps (start: bytes) |
|---:|---:|---:|---|
| 1 | 4083 | 13 | $dff3: 13 |
| 2 | 2453 | 1643 | $d4f1: 15, $d9a4: 1628 |
| 3 | 4096 | 0 | none |
| 4 | 4096 | 0 | none |
| 5 | 2034 | 2062 | $d562: 1950, $df90: 112 |
| 6 | 4096 | 0 | none |
| 7 | 4096 | 0 | none |

### HRAM by bank

| Bank | Used | Free | Gaps (start: bytes) |
|---:|---:|---:|---|
| 0 | 122 | 5 | $ffef: 5 |

### ROM0 by bank

| Bank | Used | Free | Gaps (start: bytes) |
|---:|---:|---:|---|
| 0 | 16184 | 200 | $00ff: 1, $3f39: 199 |

### VRAM by bank

| Bank | Used | Free | Gaps (start: bytes) |
|---:|---:|---:|---|
| 0 | 8192 | 0 | none |
| 1 | 8192 | 0 | none |

### The 12 ROMX banks with the most free space

| Bank | Free | Largest gap |
|---:|---:|---:|
| 127 | 12741 | 12741 |
| 99 | 4 | 4 |
| 85 | 4 | 4 |
| 60 | 4 | 4 |
| 122 | 3 | 3 |
| 83 | 3 | 3 |
| 80 | 3 | 3 |
| 75 | 3 | 3 |
| 62 | 3 | 3 |
| 97 | 2 | 2 |
| 92 | 2 | 2 |
| 90 | 2 | 2 |


## faithful, totals

### Totals

| Region | Banks | Used | Free | Largest gap | Empty banks |
|---|---:|---:|---:|---:|---:|
| ROM0 | 1 | 16170 | 214 | 213 | 0 |
| ROMX | 127 | 2067928 | 12840 | 12787 | 0 |
| VRAM | 2 | 16384 | 0 | 0 | 0 |
| SRAM | 4 | 32616 | 152 | 84 | 0 |
| WRAM0 | 1 | 4080 | 16 | 16 | 0 |
| WRAMX | 7 | 24954 | 3718 | 1950 | 0 |
| HRAM | 1 | 122 | 5 | 5 | 0 |

