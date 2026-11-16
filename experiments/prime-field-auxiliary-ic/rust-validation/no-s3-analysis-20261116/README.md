# Source-only analysis CI without S3

The user instructed **Proceed without S3** after the N83 analysis job failed
at historical-data restoration, before its unit tests. Source `f7d0e2c8`
removes this unnecessary prerequisite from `analysis-gate-tests`, with a test
fixture correction on `2ce59d8a261308cec218cc4fd7829b5c8b7fcbb1`.
Claim `PCC-20261116-c91136` is unsigned/unverified. This is a CI dependency
correction, not a solver or performance improvement. [pcc:unverified]

The existing eight tests generate temporary records and mock historical
archive reads. The job now checks out nine exact tracked files: the pinned
analyzer/test, imported Python sources, frozen protocol/schedule and checksum
file. It retains the original SHA-256 pins, test cases, job/check name and
triggers. Running the test file directly invokes its existing `unittest.main`.
The experiment job retains its original non-PR condition, analysis dependency,
runtime environment and historical-data restoration. [pcc:unverified]

`# artifacts-scope: job` opts this workflow into per-job dependency inference.
Global metadata remains an input to every job; an actual moved-data reference
still requires restoration. Generated pull steps are excluded from dependency
inference so a stale bootstrap cannot manufacture its own dependency. Their
formatting and checkout conditions are preserved. Unsupported scoped layout
fails; unmarked workflows retain their original behavior. [pcc:unverified]

On source `2ce59d8a`, all 37 artifact regression tests pass, including seven
new job-scope controls. The actual production analysis commands pass all eight
existing tests in a fresh directory with no archived inputs or manifests,
with AWS/artifact/checkpoint environment prefixes removed and Python audit
hooks denying network, child processes and historical-artifact reads.
Network/archive probes, a missing protocol and a changed checksum-pinned
analyzer all fail as expected. [The source-only receipt](source-only-final/source-only-receipt.json)
pins every input and command. Global wiring passes on `f7d0e2c8`; workflow and
wiring bytes remain identical on the corrected source. The
[validator](validator.json) preserves these exact scopes. None is independent
execution or signed replay evidence. [pcc:unverified]

Initial development failures remain intact: the first harness used the wrong
repository parent, and the first full artifact run found a malformed new
conditional-checkout fixture. Corrected source adds a fixture precondition;
no assertion was removed. [Development attempts](development-attempts.json)
links their original scripts, command receipts and complete outputs. The
earliest wiring separator diagnostic is explicitly a transcript summary,
rather than a captured subprocess log. [pcc:unverified]

[Source controls](source-scope.json) retain IC core/CLI/timing/checker source,
native curve source, the 2,473-file frozen snapshot and earlier evidence.
Historical failed S3 admission and CI logs are not rewritten. The user's
authorization removes S3 upload as a continuation prerequisite; Git/PR retain
this work. Admitted measurement resources, a frozen fresh panel, complete
accounting and independent signed replay remain open. No new benchmark or
auxiliary-map speedup is established. Hosted CI must still validate the new
head, and every applicable check/review continues to govern merge.
[pcc:unverified]

To repeat the source-only control without overwriting any evidence, run from
the repository root with a new output directory:

```sh
python3 experiments/prime-field-auxiliary-ic/rust-validation/no-s3-analysis-20261116/source_only_check.py \
  --source-ref 2ce59d8a261308cec218cc4fd7829b5c8b7fcbb1 \
  --output-dir /tmp/n83-source-only-new-replay
```

The harness refuses an existing output directory. Fresh replay logs keep
their own source and runner digests; they do not replace this receipt.
