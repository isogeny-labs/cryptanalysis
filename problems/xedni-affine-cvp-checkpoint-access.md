# Xedni experiment checkpoint access

- **Status:** open (two prior toy panels completed under narrow owner waivers; credentials still missing)
- **Kind:** access/tool limit
- **Affected work:** [frozen xedni affine-lift protocol](../research/xedni_lift_optimizer_20261101/PROTOCOL.md), [fresh target-bearing selector protocol](../research/xedni_target_relation_20261118/PROTOCOL.md), [target-origin-pencil protocol](../research/xedni_origin_pencil_20261118/PROTOCOL.md), draft PR #1768
- **Next action owner:** environment operator for checkpoint credentials; research agent for the frozen run
- **Last updated:** 2026-11-18

## Problem

New frozen Xedni experiments cannot run because the required pre-run S3 resume
checkpoint cannot be uploaded from this managed environment.  Prior narrow
owner waivers applied only to their exact toy commands and do not authorize a
modified fresh-seed panel. [pcc:unverified]

The current blocked workloads are the 1,600-row paired target-bearing selector
and the separately frozen 1,600-row target-origin-pencil comparison in the
linked November 18 protocols: four primes, two curve families, two lift
policies, ranks 6 through 9, and 25 trials per cell under distinct fresh master
seeds. The repository requires `scripts/checkpoint.sh gate` to pass before any
natural row is generated. [pcc:unverified]

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
- **Observed on 2026-11-18:** after the target-selector protocol, runner,
  analyzer, and `FREEZE.json` were committed and pushed at `10a28313a6`, a
  complete `.resume/RESUME.md` passed its content check.  `checkpoint.sh`
  then reported no permitted `ecc-challenges-new` profile, no
  `CHECKPOINT_UPLOAD_TOKEN`, and no token file.  Installing AWS CLI 1.46.3
  enabled the documented ambient-key fallback, but S3 rejected the exact
  checkpoint `PutObject` with `AllAccessDisabled`; the push and gate remained
  nonzero.  No fresh natural row was generated. [pcc:unverified]
- **Observed later on 2026-11-18:** the target-origin-pencil implementation
  was committed at `b31c01eb`, frozen and pushed at `422ea24b`, and all six
  frozen source hashes plus release-binary hash rechecked clean. A complete
  `.resume/RESUME.md` passed the content check, but `checkpoint.sh gate`
  reported no permitted `ecc-challenges-new` profile, no
  `CHECKPOINT_UPLOAD_TOKEN`, and no token file. It exited nonzero before any
  natural row was generated. [pcc:unverified]
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
- **What this evidence does not establish:** whether target-bearing ordering
  or the larger target-origin pencil improves recovery on fresh lifts, whether
  either changes complete work favorably, or any end-to-end ECDLP result.
  [pcc:unverified]

## What would unblock it

- [ ] `scripts/checkpoint.sh push` uploads the current branch state under the
  xedni branch key and `scripts/checkpoint.sh gate` exits zero without a gate
  bypass.
- [ ] The current frozen panel runs once, retains all rows, and satisfies every
  exact relation, shifted-source, paired-selection, and analyzer invariant in
  its protocol.

The first condition is necessary to start.  The second completes only the
one-coset algorithmic diagnostic; it still cannot establish ECDLP success or
transfer to binary/Koblitz curves.

## Next discriminating step

- **Action or proof obligation:** Provision scoped checkpoint transport, push
  the current checkpoint, then run one exact frozen November 18 panel at a
  time without changing its seed, grid, or cap.
- **Inputs and controls:** for the origin-pencil panel, fresh fixed seed,
  identical source/lift per paired row, complete baseline-origin box, complete
  target-origin pencil, fixed nine-point control, exact group certificates,
  source replay, and baseline candidate-set digest equality.
- **Execution limits and stop condition:** 1,600 sequential paired rows under
  the origin-pencil protocol's frozen 7,200-second cap; stop and retain
  evidence on any certificate or invariant failure.
- **Outcomes and next actions:** pencil-only recoveries with no baseline loss
  establish the specified stage improvement; equality is a bounded null; a
  gain still needs duplicate-aware full-work accounting and independent
  replay; certificate failure returns to implementation repair; another
  credential failure updates this record without running. [pcc:unverified]
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

2026-11-18: the owner separately waived the gate only for the exact frozen
November 17 1,600-row panel.  That panel completed, but its waiver explicitly
excluded larger or modified panels.  The fresh target-selector checkpoint
push and gate failed for absent transport before any natural row.  Unresolved.
[pcc:unverified]

2026-11-18: the separately frozen target-origin-pencil panel reached the same
mandatory gate at pushed head `422ea24b`. The resume capsule was complete, but
no supported upload transport existed; the gate exited nonzero and no natural
row was generated. Unresolved. [pcc:unverified]
