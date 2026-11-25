# SRAM allocation plan

The cartridge has 32 KiB of battery-backed SRAM in four 8 KiB banks. Older
saves are read at fixed addresses, so nothing that is already saved may move.
`utils/sram_layout/check_sram_layout.py` (run by `make test`) compares every
SRAM label in the build with `utils/sram_layout/sram_layout.txt` and fails if
one has moved or gone.

## Free SRAM

Measured with `utils/memory_report.py` (after the padding change below):

| Bank | Gap | Bytes | Was |
|---:|---|---:|---|
| 0 | `$bd84-$bf0c` | 393 | backup save padding (`ds 393`) |
| 0 | `$bfac-$bfff` | 84 | after Friend Team 2 |
| 0 | `$a5e9-$a5ff` | 23 | before "SRAM Mail" |
| 0 | `$b1e9-$b1ff` | 23 | after the World Link record |
| 1 | `$ab84-$ad0b` | 392 | main save padding (`ds 392`) |
| 1 | `$bffc-$bfff` | 4 | |
| 2, 3 | `$bff7-$bfff` | 9 each | end of the box database banks |
| | **Total** | **937** | 152 before |

The two padding blocks sat between the end of each save's data and its
checksum. Nothing read or wrote them: the save writes named fields, the
checksum covers only `sGameData`-`sGameDataEnd`, and the save upgrader copies
named fields. The "Save" and "Backup Save" sections now end at `sOptions3`
and `sBackupOptions3`. Their checksums and check values are in their own
sections, "Save Checksum" and "Backup Save Checksum". `layout.link` (`org`)
and asserts keep those at `$ad0c` and `$bf0d`, so the linker sees the padding
as free.

## Rules for a new allocation

1. **Its own integrity check.** Each record has a marker and a checksum, as
   the Friend Teams and the World Link record do. A save from an older version
   has whatever was left in that space: upstream has shrunk this padding each
   time it grew the save, so these bytes can hold old save data, or zeros or
   `$ff` on a fresh cartridge. An unmarked or failing record reads as empty.
2. **Interruption-safe writes.** Clear the marker first, then write the data
   and the checksum, and write the marker last. A reset partway through leaves
   the record empty, never half-written.
3. **A named section.** Give it a fixed address (`SECTION "Name", SRAM[$addr],
   BANK[n]`) or let the linker place it. Then run `check_sram_layout.py --write`
   so its address is guarded from then on.
4. **Say how long it lives.** Some records belong to the cartridge and survive
   a new adventure: Friend Teams, the link card, the World Link record. Others
   belong to one adventure and are cleared by `ErasePreviousSave` when a new
   game is saved. Write it next to the section.
5. **A version byte**, if its format might change. A record whose version it
   doesn't know reads as empty.

## Cost to future upstream merges

Upstream grows the save by taking bytes from this padding. On this branch,
a new section placed in the padding takes those bytes first, so an upstream
change that grows `wPlayerData`, `wCurMapData` or `wPokemonData` then fails to
link, because "Save" would overlap the record. That failure is the warning: the
merge then needs a save migration, or the record moves elsewhere. While the
padding is still empty, an upstream merge that grows the save links as before.

## Records today

| Record | Bank:address | Bytes | Lifetime | Check |
|---|---|---:|---|---|
| Friend Team 1 | `0:$b14d` | 136 | cartridge | marker, checksum, field validation |
| World Link | `0:$b1d5` | 20 | cartridge | status byte, receipt checks |
| Friend Team 2 | `0:$bf24` | 136 | cartridge | as Friend Team 1 |
| Link Card Records | `0:$bf10` | 20 | cartridge | marker |
| Link Card Players | bank 1 (linker) | | cartridge | tag |
