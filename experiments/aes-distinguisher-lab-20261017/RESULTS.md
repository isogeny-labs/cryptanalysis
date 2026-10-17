# First recorded AES laboratory suite

Classification: engineering and bounded observations. Preferred report:
[PDF](reports/run-20261017T1846Z-v2/report.pdf),
[Markdown](reports/run-20261017T1846Z-v2/REPORT.md), and
[machine-readable summary](reports/run-20261017T1846Z-v2/summary.json).
The [protocol](README.md) and `run.sh` remain frozen as committed before execution.

## Observations

The raw run in `runs.tar.xz` records 41 successful commands. Extract it as
described below to inspect `runs/20261017-first-suite/`. Two
events passed every tested fresh key at one round and two at two rounds. None
passed in the other ten finite search families, including standard full-round
AES-128/192/256 and both PRP controls. All matched random-control families passed.
Each family evaluated two frozen events on eight fresh fixed keys with 4,096
pairs/event/key; the twelve predeclared alpha allocations sum to 0.006.

Known three-round integrals balanced all output bytes in all 16 structures for
each of the four three-round configurations. The four-round configuration had
zero all-byte-balanced structures. The quartet component check accepted 64,552
of 65,536 generated quartets. Inversion and output-affine-undone each matched in
64,552 cases, raw AES S-box in 277, and the random byte bijection in 243.

These measurements are restricted to the recorded predicates and keys. They do
not constitute a new distinguisher beyond known reduced-round effects, a
full-AES attack, a security bound, or official campaign admission. No hardware
performance comparison or complete key-recovery cost was measured. Existing
ECDLP scoreboards and canonical curve graphs remain current because no result
here changes a curve identity, ECDLP measurement or accepted frontier.

## Source and execution checks

The engine, tests, lockfile and protocol were published at
`8a3ee1d85cbb32b0fb78aa8b92cc363e3e0caffd` before the run. Receipts record exact
argv, source and binary SHA-256, seeds, environment, dirty state, timestamps,
stdout/stderr, statuses and a byte-identical validation replay. Source, protocol
and executable hashes were rechecked against the exercised files. The current
engine sources still match. A preliminary launch failed before any trial because
the output parent was missing; after creating that parent the unchanged card
completed once. No scientific rerun was used to select an outcome.

The Rust tests cover all three FIPS vectors, supported roundtrip conventions,
24 independently generated OpenSSL comparisons, exact component tables,
MixColumns cancellation, consistent PRP forward/inverse maps, fresh-key positive
and null checks, integral mutation, and frozen-byte binding. Twelve library and
two integration tests passed on stable and Rust 1.87. Formatting and release
Clippy with warnings denied passed. Logs are in [checks](checks/).

An advisory software review found and corrected the frozen-byte binding,
parameter/overflow validation, sensitivity wording, and receipt provenance
issues before the scientific suite. It also caught misleading completed-mirror
wording and a report generator that initially embedded this suite's outcomes.
The renderer now derives outcomes, source revision, settings, control results
and alpha accounting from its inputs. A deliberately altered temporary fixture
with empty candidate lists, failed controls, a failed process and a different
revision produced those negative outcomes in its report. This was a software
fixture check, not an additional cryptanalytic trial. No critical mathematical
defect remained in the reviewed finite instrument; that review is not an
independent scientific campaign review.

## Reproduce the report

From the repository root, with Rust installed:

```sh
(cd experiments/aes-distinguisher-lab-20261017 && \
  sha256sum -c runs.tar.xz.sha256 && tar -xJf runs.tar.xz)
cargo run --release --locked --manifest-path tools/aes-discover/Cargo.toml \
  --example summarize -- \
  experiments/aes-distinguisher-lab-20261017/runs/20261017-first-suite \
  /path/to/NEW-report-directory
# In that new directory:
typst compile report.typ report.pdf
```

The renderer launches no trial or new significance test. It binds its source
artifacts by SHA-256. It does not independently certify a recorded receipt.
The PDF was compiled with Typst 0.15.0, and both pages were visually inspected.
The earlier accurate, suite-specific report is preserved in
`reports/run-20261017T1846Z`; the generic renderer's `-v2` report is preferred.

Receipts retain original absolute paths. In another checkout, replace only the
original `/workspace/cryptanalysis/` prefix with that checkout's absolute path
when checking receipt files; do not edit the original receipts. New scientific
runs require a new output directory and retain their own source identity.

The `crypto` mirror is prepared but not applied: its required Conductor service
is unreachable. See the companion
[access problem](https://github.com/aburan28/crypto-autoresearcher/blob/codex/aes-distinguisher-research/problems/aes-lab-conductor-and-campaign-admission.md).

Subsequent integration update: the current user authorized standalone
application in `crypto`. The source mirror is now applied; eleven native/Cargo
files match this companion and fourteen native tests pass there. Repository
verification and PR delivery are tracked by the linked problem record. This
does not rerun or alter the frozen suite, its observations, or campaign status.
Delivery: [crypto PR #2105](https://github.com/aburan28/crypto/pull/2105).
The native mirror/backlog checks pass, while the required root library check
fails before tests on unchanged ecbench/Gaudry sources. The linked problem
record preserves that separate regression gap.
