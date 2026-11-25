# Complete-panel acceptance correction

The frozen `opcounts.py` analysis can accept a truncated ledger containing only
one valid rank row as `counts_identical`. It also constructs `band.md` before
checking whether archive identity and validity checks passed. Neither behavior
satisfies the original protocol's complete-panel acceptance rule.

`analyze_v2.py` is a separate analysis version. It preserves the pinned producer,
`PROTOCOL.md`, `PINS.sha256`, `opcounts.py`, `band.py`, and historical reports.
It requires all 62 rows in their frozen order, with the exact serial, arm,
point, seed, archived twin, and block. Diagnostic subsets cannot pass this gate.
The existing validity, archive identity, and scalar checks must also pass before
the unchanged band arithmetic is called.

New outputs are `counts-v2.json`, `opcounts_result-v2.json`, and `band-v2.md`.
A failing analysis removes any prior v2 band at that output location and leaves
historical `band.md` untouched. A failed run retains its available raw counts
and failure checks; it cannot publish a new band. The workflow verifies
`ANALYSIS_V2.sha256` and runs the acceptance regressions. PR events run only
these tests; they do not dispatch the experiment.

The eight regression cases cover a complete panel, a single rank row, a missing
last target, a duplicate replacing a target, a changed seed, an invalid row,
a mismatch against its archived twin, and malformed input with stale outputs. They test analysis acceptance, not
the producer's operation counters. The archived numerical band arithmetic is
unchanged. No full-panel result or new performance ranking is established by
this repair; already-running jobs still use their original checkout and need
this analysis applied to their saved receipts before acceptance.

Run from the repository root:

```sh
sha256sum -c experiments/koblitz-n83-opcounts-20261023/ANALYSIS_V2.sha256
python3 -m unittest discover -s experiments/koblitz-n83-opcounts-20261023 -p test_analyze_v2.py -v
python3 experiments/koblitz-n83-opcounts-20261023/analyze_v2.py --receipt-dir /path/to/panel
```

## Chronology (added 2026-11-06, sheriff case SHF-20261106-a114e7, CAN-4)

This analyzer postdates the data it accepts. Times are UTC, from the git
objects and the archived `runs.jsonl` (`finished_unix_s` minus
`process_wall_ms`):

| event | time | commit or record |
| --- | --- | --- |
| protocol frozen | 2026-10-23 01:11:19 | `765061e1b`, parent of run head `1a6067f63` |
| first run (serial 1, kS) | 01:23:55 to 01:26:49 | `run_github_39882571652/panel/runs.jsonl` |
| last run (serial 62, rT) | 01:56:40 to 01:56:42 | the same |
| this analyzer | 02:59:00 | `ad1fbc64d` |

It is stricter only (complete-panel gate before the unchanged band
arithmetic), and its counts and band are byte-identical to the in-run v1
output, so there is no forking-path effect on any number. The protocol,
run and analyzer commits are not on `main` (squash merge of #1077); the
ancestry is provable from `refs/pull/1077/head` (`8b205273`) and
`claude/n83-opcounts-run` (`1a6067f63`). `ARTIFACT.json` is an archived
receipt and is not edited; see `CORRECTIONS-20261106.md`.
