# Xedni affine-CVP checkpoint access

- **Status:** open
- **Kind:** access/tool limit
- **Affected work:** [frozen xedni affine-lift protocol](../research/xedni_lift_optimizer_20261101/PROTOCOL.md)
- **Next action owner:** environment operator for checkpoint credentials; research agent for the frozen run
- **Last updated:** 2026-11-01

## Problem

The frozen one-coset p=67 diagnostic for the xedni affine-CVP optimizer cannot
run because the required pre-run S3 resume checkpoint cannot be uploaded from
this managed environment.

The exact workload is the four-radius deterministic search in the linked
protocol, using four balanced lifts on `y^2=x^3+28` over `F_67`.  The
repository requires `scripts/checkpoint.sh gate` to pass before any evaluation
run.  An uncheckpointed local run would violate that acceptance criterion and
would not discharge the user's requested algorithm investigation.

## Evidence and uncertainty

- **Observed:** Implementation and protocol commit `2a1147147` builds under
  Rust 1.87.0.  Four focused library tests and the `ca-icx` CLI integration
  test pass in release mode.  `scripts/checkpoint.sh push` first found no
  supported transport.  After installing AWS CLI 2.39.3 in `/tmp`, the ambient
  identity authenticated as account `590183823895` user `adam`; direct
  checkpoint upload did not complete.  `presign-upload --days 1 --install`
  produced a token, but using it to upload the checkpoint archive returned
  HTTP 403.  No evaluation command was run and no p=67 result exists.
- **Derived or proved:** No mathematical conclusion follows from the access
  failure.  The code-level invariant checks and synthetic positive/negative
  controls establish only their tested cases.
- **Suspected explanation:** The ambient IAM user lacks `s3:PutObject` on the
  checkpoint prefix, so a URL signed by the same user is also unauthorized.
  This is consistent with the observed 403 but has not been confirmed by an
  IAM policy read.
- **Missing capability:** A valid repository checkpoint upload token or AWS
  profile authorized for
  `s3://setec-astronomy-artifacts/checkpoints/cryptanalysis/`.
- **What this evidence does not establish:** Whether LLL/Babai is stable on
  the frozen skew Smith basis, whether the exact neighborhood improves on
  Babai, whether the method improves the 2000 HMM-HNF implementation, or any
  dependence/ECDLP result.

## What would unblock it

- [ ] `scripts/checkpoint.sh push` uploads the current branch state under the
  xedni branch key and `scripts/checkpoint.sh gate` exits zero without a gate
  bypass.
- [ ] The four frozen rows run once, retain all raw JSON, and satisfy every
  exact incidence, congruence, nonsingularity, and candidate-cap check in the
  protocol.

The first condition is necessary to start.  The second completes only the
one-coset algorithmic diagnostic; it still cannot establish ECDLP success or
transfer to binary/Koblitz curves.

## Next discriminating step

- **Action or proof obligation:** Provision the scoped checkpoint transport,
  push the current checkpoint, then run the exact reproduction command in the
  protocol without changing the fixture, radii, or caps.
- **Inputs and controls:** Frozen p=67 fixture, raw exact solution, Babai
  control, exact-discriminant candidate, synthetic known-short positive
  control, and invalid-direction negative controls.
- **Execution limits and stop condition:** Four rows at radii 0, 1, 2, and 4;
  caps 1, 27, 125, and 729.  Stop and retain evidence on any invariant failure.
- **Outcomes and next actions:** A smaller exact discriminant than Babai is a
  one-coset stage improvement; equality is a bounded null result; invariant
  failure returns to implementation repair; another checkpoint failure keeps
  this access record open.
- **Recheck trigger:** A valid token/profile is attached to a managed session.

A planned step is not a completed experiment.  The required gate remains in
force.

## Resolution and history

2026-11-01: opened after both ambient and presigned-token checkpoint uploads
failed before the frozen evaluation.  Unresolved.

