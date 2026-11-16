# Full IC pipeline build exceeds its measurement preparation cap

- **Status:** investigating
- **Kind:** resource limit in experiment preparation
- **Affected work:** [S3 fixed-instance protocol](../experiments/ic-s3-pipeline-20261115/PROTOCOL.md)
- **Next action owner:** current IC optimization session
- **Last updated:** 2026-11-15 America/Los_Angeles

## Problem

The full-framework release reference binary did not finish within the frozen
330-second build allowance, leaving no budgeted algorithm comparison output.

## Evidence and uncertainty

[pcc:unverified] Job20261116-053102-5ead on4CPU8GiB L4 terminated its reference
build process group at330seconds and exited1 after330.7seconds. Zero pipeline
pairs and zero rho runs were attempted. The final compiler output is retained
in experiments/ic-s3-pipeline-20261115/run-001/reference-build.log. The locally
built driver and independent base rebuilds pass their focused checks. The
cause of the longer cloud build is not established; no algorithm runtime is
inferred from compilation time. No measurement is promoted.

## What would unblock it

- [ ] Produce both default/direct release executables from the same pinned
      source, lockfile and toolchain, with complete build logs and hashes.
- [ ] Run the existing frozen matrix in a separate timing allocation, verifying
      hashes before execution and retaining caps, counts, answers and rho.

[pcc:unverified] Successful compilation resolves preparation only. Host qualification and a
verified complete IC improvement remain separate obligations.

## Next discriminating step

Use a bounded build-only job with no algorithm measurements, then a separate
900-second L4 timing allocation. The preparation protocol states its resource
limits before launch; the original330-second failure remains immutable. Do
not lower the optimization level to fit the original cap or replace fresh
single-target runs with amortized repetitions.

## Resolution and history

Unresolved. First build-only preparation and measured execution are pending.
