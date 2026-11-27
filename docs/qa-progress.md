# QA campaign progress (resume file)

Living record of the execution campaign: what was run, what it found, what is still untested. Written so work can
resume after a context reset. Numbers here are copied from run artifacts (paths given); nothing is estimated.
Everything is emulation. No result is evidence about a physical console.

Branch: `claude/sleepy-ramanujan-kc278b`. Tooling summary: [`qa/README.md`](../qa/README.md), AV: [`qa-av.md`](qa-av.md),
findings: [`issue-ledger.md`](issue-ledger.md), report: [`qa-report.md`](qa-report.md).

## How to resume

```
sh qa/setup.sh                                   # tools, once
python3 -m qa.mutants build                      # faulty ROMs (+ control) in /tmp/claude-0/qa/mut
python3 -m qa.validate run --jobs 3              # detector validation matrix -> qa/reports/validation/
python3 -m qa.gb.scenarios --count N --seed S --jobs 3 --out DIR [--backend sameboy --model AGB]   # resumable
python3 qa/run.py av                             # audiovisual suite
```

## 1. Detector validation (task C1)

Method: [`qa/mutants.py`](../qa/mutants.py) builds ROMs with one fault each from the current tree (and with each
fixed defect reverted); [`qa/validate.py`](../qa/validate.py) runs every detector on every ROM and on an unmodified
**control** build. Detectors have no knowledge of where a fault is. Results: `qa/reports/validation/cells.json`, `matrix.md`.

See section 1 of the detector-validation write-up once the matrix is complete (this file is updated after each run).

## 2. Scenario campaign (task C2)

Counts are kept strictly apart: *attempted* (a scenario started), *completed* (every battle ran to its end and the
checks ran), *skipped* (could not be set up), *not started* (the encounter never began a battle), *battles executed*.
Frames are never counted as scenarios.

(filled from `summary.json` of each campaign directory)

## 3. Gameplay sweep (task C3)

(see `docs/qa-report.md`; worker tracks A/B/C are reviewed before merging)

## 4. Audiovisual sweep (task C4)

(see `docs/qa-av.md` and the latest `av_review.md`)

## 5. Defects found in this campaign

(ledger entries L33 onwards)

## 6. Remaining untested / not verified

(maintained as the campaign proceeds)
