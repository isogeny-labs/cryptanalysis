# Structured-consumer CI follow-up

2026-11-15. Claim `PCC-20261115-113f0f` is an unsigned producer observation.
The [scoped validator](consumer-lock-validator.json) and retained
[original partial report](producer-checks.json) record the integration outcome:
the consumer lock is corrected; full CI and merge remain blocked.
No performance or independent-execution result is claimed. [pcc:unverified]

## Correction

`crates/hashed-ecdl-tensor/Cargo.lock` still selected getrandom 0.2 for the
native path package after that package's manifest selected 0.4. The hosted
[consumer job](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43767412389/job/132975526165)
stopped at its locked Clippy step. The exact command reproduced exit 101
locally. The updated lock adds getrandom 0.4.3 and r-efi 6.0.0 while retaining
every prior package version and checksum. An offline resolver initially
selected cached libc 0.2.190; restoring the original 0.2.191 pin kept that
unrelated downgrade out of the commit. Both attempts are retained.
[pcc:unverified]

The lock change is source commit `0f6f1045`. Main `53bb82ac` was then
integrated in `fcd78dcb`, preserving both histories and the exact canonical
main ledger prefix. Only unmerged claim events were appended with the PCC
writer; claim/proof payloads were unchanged. [pcc:unverified]

| Check | Source | Observed result |
|---|---|---|
| Locked all-target Clippy | 0f6f1045 | exit 0 |
| Locked release library and structured CLI | 0f6f1045 | 33 library + 3 CLI checks pass |
| Locked all-target Clippy after main integration | fcd78dcb | exit 0 |
| Locked structured CLI after main integration | fcd78dcb | 3 checks pass |
| Locked all-target Rust 1.78 check | corrected graph | exit 101: getrandom edition2024 manifest |

These are producer software checks. The two runtime test rows refer to
different source revisions and are not pooled into a current-head test count.
The native SDK gained upstream joint-target code during the main merge; its
consumer was checked again afterward. All `--locked`, lint and correctness
flags remain enabled. [pcc:unverified]

## Inherited blockers

The hosted [corpus job](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43767412540/job/132975526584)
failed before native proof additions: the GLV source controls expect curve
hash `e1d624e58c54f25f9225be97481b50c0ed406cedcfdffa8ba66f01a5fbed7f63`,
while current main and PR curve bytes hash to
`6d120872c2020870a7fed1f8c28af644a7e31667e7b202986dddbca34772125b`.
The actual binding checker from base `58c86ef4` and head `54e4331a` refuses
the same inputs. Main `53bb82ac` retains the same mismatch. Neither the
source pin nor the controls were changed here. See the
[named GLV binding problem](../../../../problems/live-glv-source-pin-drift.md).
[pcc:unverified]

The workflow's later minimum-version steps were not reached in the hosted
failed job. A local locked Rust 1.78 check rejects getrandom 0.4.3's
edition2024 manifest. The existing
[native Rust-floor problem](../../../../problems/hashed-ecdl-rust-msrv.md)
and proposed [PR #1586](https://github.com/isogeny-labs/cryptanalysis/pull/1586)
cover that inherited graph incompatibility. No declared version was raised,
dependency silently downgraded or minimum-version check skipped.
[pcc:unverified]

The initial current-head read still had three unresolved CodeQL bot review
threads and no human review. Alert-management API access was not retried.
The frozen 2,473-file archive and previous unsigned evidence remain intact.
The snapshot inventory, benchmark-record and artifact checks pass; those
checks do not establish new timing or cryptanalytic performance.
[pcc:unverified]

## Evidence and next step

The two hosted decoded UTF-8 logs are retained completely in gzip files;
[the inventory](hosted-log-inventory.json) pins both compressed bytes and
decoded text. Local failures, resolver correction, successful checks,
base/head source comparisons and ledger reconciliation are retained beside
this note. Source-only pin reproductions do not substitute for a complete
native corpus build. [pcc:unverified]

Publish the lock correction, inspect the new head at the normal follow-up
cadence, and wait for the properly reviewed GLV binding and Rust-floor repairs.
Merge only when all applicable exact-head checks pass and no blocking review
remains. New research timing still requires the previously stated checkpoint,
admitted runner, frozen panel/accounting and signed-replay gates.

## Receipt metadata correction

The first observation report used `status: partial` to describe the blocked
integration. The recompute proof format requires `status: pass`, so attaching
that whole integration report as a validator was a metadata error. Its failed
format check, the original report and the original claim bytes are retained.
The corrected validator checks only the scoped consumer correction and
explicitly keeps `overall_ci_status: blocked`; no command result, requirement
or validation flag changes. Claim 113f0f has an explicit amendment, and the
ledger appends both the corrected claim digest and a correction note while
preserving the earlier event. The active proof now returns `not_covered`
because it is unsigned, rather than a report-format failure.
[pcc:unverified]
