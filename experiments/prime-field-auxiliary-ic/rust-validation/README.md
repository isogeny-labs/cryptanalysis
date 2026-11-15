# Native integration check receipt

The latest [field-fiber report](field-fibers-20261115/REPORT.md) and
[PDF](field-fibers-20261115/REPORT.pdf), claim `PCC-20261115-82ccdd`, pin source
`facaac33` and unsigned producer checks: 20 core tests on each toolchain and
four CLI tests. This adds power and norm-one trace encodings, an orbit-based
raw-fiber generator, pre-split terminals, and same-column direct controls.
The general terminal uses five field multiplication calls instead of eight;
torus preparation uses one square root instead of the inverse tree's
`2^depth-2` (none at depth one). These are source-operation counts; a runtime
improvement is unmeasured. Six Lean identity sources are supplied but unbuilt;
the finite-field structural proof and atlas update remain open.
[pcc:unverified]


The [kernel-fusion receipt](kernel-fusion-20261115/producer-checks.json), claim
`PCC-20261115-d2f58b`, records the subsequent arithmetic and candidate-index
changes in source commit `27fc983`. The intermediate shift uses two field
multiplications and four additions/subtractions, replacing three of each;
SIMD zero masks and inline scalar collection remove the second result scan.
The explicit-product controls include a 128-root, 58-coordinate fixture and
mixed/zero shifts. Fifteen core checks pass on stable and Rust 1.78, together
with three CLI checks. These are producer correctness checks and source-level
operation counts; a runtime improvement remains unmeasured. [pcc:unverified]

The timing-access checks still find no expected local checkpoint or Runpod
credentials. A read-only dispatch of the existing Cloud ECC2K-130 status action
returned HTTP 422 because that workflow is manually disabled. No runner or
benchmark job was started. The access question remains open. [pcc:unverified]

The [CI follow-up receipt](ci-followup-20261115/producer-checks.json), claim
`PCC-20261115-2a4d0d`, records the subsequent CI results and remaining blockers.
Both dependency-consumer jobs passed. The auxiliary workflow never started:
repository policy rejected `dtolnay/rust-toolchain@master`. The replacement
installs the same toolchains directly with `rustup`; local actionlint and both
toolchain checks pass, with the corrected remote workflow still pending.
[pcc:unverified]

CodeQL now reports 23 annotations: three archived scalar fixtures and 20 sinks
for the CLI's mathematical recovery-witness output. Alert-management access
still returns HTTP 403, so maintainer classification remains necessary. No
check or alert was disabled and the snapshot remains unchanged.
[pcc:unverified]

The follow-up receipt's failed local tooling attempt records the overall
install-and-lint exit code 127: `/usr/bin/go` was a board-game executable and
did not produce actionlint. The subsequent invocation of the missing binary
returned 127. The successful check used the official actionlint v1.7.7 release
after comparing its archive with the published checksum. [pcc:unverified]

The follow-up [consumer check receipt](consumer-checks.json), claim
`PCC-20261115-dc9cae`, retains the locked dependency graph diagnostics for the
safe bindings and binary-genus2 tool. It addresses the two early integration
CI failures by updating the tool's transitive lockfile and the sparse checkout
consumers. No registry package version was changed. [pcc:unverified]

[producer-checks.json](producer-checks.json) and its raw logs record unsigned
producer checks. Claim `PCC-20261115-c2f013` has no signed standing or execution
proof. The tested source bytes are retained in commit `073d5e4`; the following
manifest cleanup removes only an extra terminal blank line. No Rust algorithm
source or frozen snapshot changes in that cleanup. [pcc:unverified]

| Requested deliverable | Current status |
|---|---|
| Native Rust API and suite CLI | Implemented; safe re-exports and `ca-ic auxiliary` producer checked |
| Optimize polynomial/GCD stage | Centered exact resultant circuit ported; the complete known-root case avoids generic GCD construction; no new stage timing |
| Optimize relation recovery | Signed gain graph and certificate DAG implemented; compared with dense elimination in correctness tests |
| IC with and without auxiliary maps | Both implemented, with matching rows/certificates on matched small-field walks; arbitrary direct bases accepted |
| Compare against rho | Repository C batched negation-map reference exposed; small-field public-key check passes; new timing panel not run |
| Both requested prime fields | Arithmetic and exact relation circuits checked for `2^31-1` and `2^61-1`; fresh full Rust recoveries at those sizes not run |
| End-to-end speedup | Not established for the Rust integration; checkpoint upload access and compliant measurement allocation/panel remain outstanding |

The checks include 13 native tests including the documentation example on
stable and on Rust 1.78, two comparisons with C Montgomery arithmetic, three
CLI tests, and 26 archived Python tests. Core/bindings/suite lints and MSRV
builds are recorded separately. These are implementation checks on an ordinary
CPU host, not an admitted IC performance panel. [pcc:unverified]

The checkpoint upload gate reports no configured token or AWS profile. No new
research benchmark was launched; the original measurement requirement remains
open in [the problem record](../../../problems/prime-field-auxiliary-ic-validation.md).
[pcc:unverified]

The import's previous head also has three CodeQL clear-text-storage alerts at
`snapshot/prepare.py:193`, `snapshot/prepare61.py:57`, and
`snapshot/algebraic/end_to_end/prepare_runs.py:63`. These scripts intentionally
write public known-answer scalar fixtures to verification sidecars excluded
from solver input. The code-scanning API returned HTTP 403, so no alert was
dismissed or check disabled. Maintainer classification of those fixture alerts
remains necessary before merging. [pcc:unverified]
