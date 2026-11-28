# QA campaign progress

**Status: the QA phase is closed.** Development moved to content-first (Johto expansion, then the living Pokemon world). This file is the
short record; the details are in:

- [`qa-baseline.md`](qa-baseline.md): the pre-expansion baseline (build hash, resource use, results, gaps, how to reproduce);
  raw summaries in [`../qa/baseline/2.1-pre/`](../qa/baseline/2.1-pre/), tag `qa-baseline-2.1-pre`
- [`issue-ledger.md`](issue-ledger.md): confirmed defects (L28 to L34 fixed) and unresolved findings (L35 to L41)
- [`qa-av.md`](qa-av.md): audiovisual validation
- [`qa-inventory.md`](qa-inventory.md): content coverage against the repository inventory
- [`qa-report.md`](qa-report.md): the first-phase report

## Policy from here (owner's direction)

During development, fix immediately: build failures, save corruption and data loss, memory corruption, critical crashes and
progression blockers, fundamental shared-engine defects, hardware resource violations that stop a feature, and architecture that
would make later work much harder. Everything else (minor graphics and audio, performance, cinematic timing, collision nits, dialogue
and interface polish, incomplete regression coverage) is recorded in the ledger and deferred to the stabilization phase.
Keep the game buildable and playable. `make qa-regression` is the quick check that nothing critical regressed (23 tests).

## To resume QA work later

```sh
make qa-regression                       # critical suite
python3 qa/run.py map --only test_boundaries --jobs 4       # map edges
python3 -m qa.inventory report           # coverage table
python3 -m qa.gb.world_scenarios --start 0 --count 4000 --seed 1 --jobs 8 --out DIR
python3 -m qa.mutants build && python3 -m qa.validate run   # detector validation (partial so far)
```
