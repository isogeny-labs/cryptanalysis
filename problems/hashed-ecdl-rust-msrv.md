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
