# Native hashed-EC dependency graph exceeds the declared Rust floor

- **Status:** open
- **Kind:** inherited dependency compatibility gap
- **Affected work:** native `bindings/rust/hashed-ecdl-tensor` compatibility qualification
- **Next action owner:** native dependency-maintenance lane
- **Last updated:** 2026-11-15

## Problem

The native crate still declares Rust 1.78, but current main selects getrandom
0.4.3, whose package requires Rust 1.85 and edition 2024. This blocks an actual
Rust 1.78 check of the dependency graph. The prepared point-table feature itself
uses the compatible common API/syntax; the counterpart Crypto graph passes
Rust 1.78 all-target checking. These are producer observations. [pcc:unverified]

## Evidence and uncertainty

Main `9f467175fd5a0fe8fe6623a8715f9cb80e987305` already selected getrandom 0.4
while calling removed `getrandom::getrandom`. The integration updates that call
to `getrandom::fill`, without changing its dependency version. Modern Rust
checks then run; Cargo 1.78 rejects the dependency's edition2024 manifest. Raw
baseline/MSRV bodies, source and actual workspace-lock hashes are retained in
[the prepared-pair receipts](../experiments/prepared-point-tables-20261115/README.md).
These software observations establish no runtime or cryptanalytic result.
[pcc:unverified]

## What would unblock it

- Restore and qualify an approved dependency graph compatible with the stated
  floor, or review/document an intentional minimum-version change.
- Re-run locked all-target compilation and the original native correctness
  controls at that actual declared minimum, retaining source and lock identities.

A modern compiler pass alone does not satisfy the old minimum-version claim.
The native feature's modern-build qualification and this compatibility gap
are recorded separately.

## Next discriminating step

Review the native-only RNG dependency requirement against other Rust workspace
users, then validate the proposed graph in an isolated checkout. Do not silently
lower validation or describe a newer-compiler build as a 1.78 pass. No cloud
experiment or new spending is required for that development check.

## Resolution and history

Unresolved. Initial current-main API failure, modern API correction and actual
1.78 dependency rejection remain retained; historical receipts are unchanged.

## 2026-11-16 five-lead integration observation

The current native manifest now declares Rust 1.85, but the inherited workspace
lock selects sha2 0.11.1, whose declared floor is 1.88. The actual locked 1.85
all-target check therefore still fails before native compilation. No dependency
version was upgraded by the five-lead port; its generated lock repair removes
only orphan version_check/wasi nodes. Current stable native tests and strict
all-target clippy are separate development controls. The original compatibility
problem stays open, with the declared-floor failure retained in
`research/point_hash_five_leads_20261116/development.tar.xz`. [pcc:unverified]

- **Status:** open, narrowed after reviewed floor update


At the original diagnosis, the native crate declared Rust 1.78, but main selected getrandom
Rust 1.78 check of that dependency graph. The prepared point-table feature itself

Upstream PR #1586 has since merged an owner-reviewed Rust 1.85 floor. Source
`bbdf695d` integrates that repair: the native and structured-consumer graphs
both pass locked all-target Rust 1.85 compilation. Their stable correctness
controls also pass. This narrows the compatibility obstruction; exact-head
hosted qualification and the original requirement for correctness controls at
the declared minimum remain open. The standalone prime-field IC core retains
its separate Rust 1.78 floor. See
[the new scoped receipt](../experiments/prime-field-auxiliary-ic/rust-validation/ci-msrv-followup-20261115/),
claim `PCC-20261116-f7dd33`. [pcc:unverified]








The dependency-floor decision is now reviewed and merged. Next, finish the
exact-head hosted checks and qualify the original native correctness controls
on the accepted minimum. Preserve the earlier Rust 1.78 rejection as history.


2026-11-16, auxiliary IC integration of main `d9ee51f2`: SHA-2 0.11.1
requires Rust 1.88 and refuses the selected 1.85 graph. Compatible 0.11.0 is
pinned explicitly in the native tensor and curve-audit packages; affected
consumer locks and both uses of the removed digest formatter are corrected.
The [integration receipt](../experiments/prime-field-auxiliary-ic/random-vs-special/main-integration-20261116/README.md),
claim `PCC-20261116-62ae45` (unverified), retains the actual lock/API/MSRV
failures and a timed-out native library run. Selected native all-target 1.85
checking passes on `f748c746`, and wrapper checking passes on `5b9f7050`;
neither changes the declared floor or establishes full hosted qualification.

Not fully resolved. Initial main API failure, modern API correction and actual


2026-11-15, PR #1536 follow-up: the structured-consumer lockfile was
synchronized without changing dependency versions or the declared floor.
The local locked Rust 1.78 all-target check still rejects getrandom 0.4.3's
edition2024 manifest. The hosted job stopped at the earlier stale-lock
failure, so its later minimum-version steps have not been reported passing.
The original graph qualification requirement remains open. See
[the retained follow-up logs](../experiments/prime-field-auxiliary-ic/rust-validation/ci-consumer-followup-20261115/).

A proposed upstream minimum-version repair is tracked in
[PR #1586](https://github.com/isogeny-labs/cryptanalysis/pull/1586); it was open
at that earlier check and merged on 2026-11-15. This follow-up preserves the existing minimum-version tests
and does not treat a modern-compiler pass as Rust 1.78 compatibility.
