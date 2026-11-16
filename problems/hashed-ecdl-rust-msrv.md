# Native hashed-EC dependency graph exceeds the declared Rust floor

- **Status:** open, narrowed after reviewed floor update
- **Kind:** inherited dependency compatibility gap
- **Affected work:** native `bindings/rust/hashed-ecdl-tensor` compatibility qualification
- **Next action owner:** native dependency-maintenance lane
- **Last updated:** 2026-11-15

## Problem

At the original diagnosis, the native crate declared Rust 1.78, but main selected getrandom
0.4.3, whose package requires Rust 1.85 and edition 2024. This blocks an actual
Rust 1.78 check of that dependency graph. The prepared point-table feature itself
uses the compatible common API/syntax; the counterpart Crypto graph passes
Rust 1.78 all-target checking. These are producer observations. [pcc:unverified]

Upstream PR #1586 has since merged an owner-reviewed Rust 1.85 floor. Source
`bbdf695d` integrates that repair: the native and structured-consumer graphs
both pass locked all-target Rust 1.85 compilation. Their stable correctness
controls also pass. This narrows the compatibility obstruction; exact-head
hosted qualification and the original requirement for correctness controls at
the declared minimum remain open. The standalone prime-field IC core retains
its separate Rust 1.78 floor. See
[the new scoped receipt](../experiments/prime-field-auxiliary-ic/rust-validation/ci-msrv-followup-20261115/),
claim `PCC-20261116-f7dd33`. [pcc:unverified]

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

The dependency-floor decision is now reviewed and merged. Next, finish the
exact-head hosted checks and qualify the original native correctness controls
on the accepted minimum. Preserve the earlier Rust 1.78 rejection as history.

## Resolution and history

Not fully resolved. Initial main API failure, modern API correction and actual
1.78 dependency rejection remain retained; historical receipts are unchanged.


2026-11-15, PR #1536 follow-up: the structured-consumer lockfile was
synchronized without changing dependency versions or the declared floor.
The local locked Rust 1.78 all-target check still rejects getrandom 0.4.3's
edition2024 manifest. The hosted job stopped at the earlier stale-lock
failure, so its later minimum-version steps have not been reported passing.
The original graph qualification requirement remains open. See
[the retained follow-up logs](../experiments/prime-field-auxiliary-ic/rust-validation/ci-consumer-followup-20261115/).
[pcc:unverified]

A proposed upstream minimum-version repair is tracked in
[PR #1586](https://github.com/isogeny-labs/cryptanalysis/pull/1586); it was open
at that earlier check and merged on 2026-11-15. This follow-up preserves the existing minimum-version tests
and does not treat a modern-compiler pass as Rust 1.78 compatibility.
[pcc:unverified]
