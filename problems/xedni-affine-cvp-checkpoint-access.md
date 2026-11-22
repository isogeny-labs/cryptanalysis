# Xedni affine-CVP checkpoint access

- **Status:** open (p=67 toy run completed 2026-11-12 under owner waiver; credentials still missing)
- **Kind:** access/tool limit
- **Affected work:** [frozen xedni affine-lift protocol](../research/xedni_lift_optimizer_20261101/PROTOCOL.md)
- **Next action owner:** environment operator for checkpoint credentials; research agent for the frozen run
- **Last updated:** 2026-11-12

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
- **Observed on 2026-11-02:** The managed runtime reported current, ready AWS
  variables and enforced unrestricted HTTP policy.  The installed token again
  returned HTTP 403.  With AWS CLI 2.39.3 installed outside the repository and
  the token file deliberately left untouched but not selected, the supported
  ambient-key transport reached S3 and `PutObject` returned `AccessDenied` for
  `checkpoints/cryptanalysis/codex__xedni-affine-cvp-eval-20261102/20261102T171849Z-318b27bf3427/checkpoint.tar.gz`.
  `scripts/checkpoint.sh status` then reported `last push: stale or none` and
  the gate exited nonzero.  The evaluator was not launched.
- **Observed after the direct-discriminant change on 2026-11-02:** A gate for
  branch `codex/xedni-step8-20261102` attempted the supported AWS upload at
  key `20261102T181246Z-e264f71189ff/checkpoint.tar.gz` and failed with
  `AWS_IO_TLS_ERROR_NEGOTIATION_FAILURE`.  The gate exited nonzero and the
  frozen evaluator again was not launched.  This transient transport error
  does not supersede the independently observed HTTP 403 and `AccessDenied`
  authorization failures.
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

2026-11-02: reproduced token HTTP 403 and directly isolated ambient AWS
`PutObject AccessDenied` despite runtime credential readiness.  The exact
authorization blocker remains unresolved; no frozen row was run.

2026-11-02: the post-direct-discriminant gate also failed, this time during
TLS negotiation.  No frozen row was run and the gate remains mandatory.


2026-11-12: the owner waived the S3 resume-checkpoint requirement for toy-size
xedni runs, verbatim: "for this toy-size run only, the S3 resume-checkpoint
requirement is waived because no upload credential exists in this container."
(given in the crypto session; scope: the frozen p=67 run and
`research/xedni_lift_success_20261112/`; bench records, the frozen protocol and
certificates are not waived).  The frozen p=67 comparison then ran once, as
specified, with the checkpoint gate not run; result and amendment are in the
protocol's "Amendment 2026-11-12" and `runs/run-20261112/`.  The credential
blocker itself is not resolved, so this record stays open for runs that are
not toy-size.
