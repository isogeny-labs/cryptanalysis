# Prime IC Jacobian timing checkpoint access

- **Status:** `open`
- **Kind:** access/tool limit
- **Affected work:** [Prime-field IC Jacobian relation-walk protocol](../experiments/prime-ic-jacobian-relations-20261031/PROTOCOL.md)
- **Next action owner:** environment operator or benchmark runner with checkpoint upload access
- **Last updated:** 2026-10-31

## Problem

We cannot establish a relation-collection wall-time improvement for the new
`ca-ic prime --relation-coordinates jacobian` backend because repository policy
requires an uploaded resume checkpoint before an experiment, while this session
has neither the `ecc-challenges-new` AWS profile nor a
`CHECKPOINT_UPLOAD_TOKEN`.

The blocked comparison is the same-revision affine/Jacobian pairing defined in
the affected protocol.  Arithmetic and end-to-end known-answer correctness can
still be tested, but neither source-level inversion savings nor unisolated
timing intuition satisfies the requested speedup evidence.

## Evidence and uncertainty

- **Observed:** On branch `codex/prime-jacobian-relations` at base
  `1ee4f47e962aac7f0f09781e34fccfaec1c6456e`, `scripts/checkpoint.sh status`
  selected `s3://setec-astronomy-artifacts/checkpoints/cryptanalysis/codex__prime-jacobian-relations/`.
  After completing `.resume/RESUME.md`, `scripts/checkpoint.sh push` returned
  `no way to upload: no AWS profile 'ecc-challenges-new', no
  CHECKPOINT_UPLOAD_TOKEN` and uploaded nothing. No timing command was run.
- **Derived or proved:** The access failure blocks the repository's experiment
  gate; it says nothing about the candidate's performance.
- **Suspected explanation:** The managed session was provisioned without the
  repository checkpoint identity or a presigned upload token.
- **Missing capability:** A valid checkpoint upload token or configured AWS
  profile, followed by an isolation-qualified benchmark host for a promotable
  timing claim.
- **What this evidence does not establish:** It does not establish a speedup,
  slowdown, or equivalence between affine and Jacobian collection.

## What would unblock it

- [ ] `scripts/checkpoint.sh push` uploads the current branch state and
  `scripts/checkpoint.sh gate` succeeds without weakening the gate.
- [ ] The frozen paired protocol runs on a host satisfying the repository's
  isolation contract, retaining raw native JSON, commands, binary/source
  hashes, environment receipt, correctness checks, and uncertainty.

The first condition permits an experiment to start.  Both conditions are
needed to promote a measured relation-collection speedup; even then, a stage
win would not establish an end-to-end index-calculus improvement.

## Next discriminating step

- **Action or proof obligation:** Provision a presigned checkpoint upload token,
  rerun the gate, then execute the affine/Jacobian pairing in the linked
  protocol.
- **Inputs and controls:** Exact same release binary, curve type/parameters,
  seeds, target count, factor-base sizing, relation budget, and operation
  accounting; affine is the control.
- **Execution limits and stop condition:** Use the existing CLI budgets and
  repository isolated-benchmark contract; stop on any incorrect target,
  rejected relation, uncertified/inconsistent column, or gate failure.
- **Outcomes and next actions:** A robust paired win supports tuning and a
  default-switch proposal; a loss keeps affine as default and profiles field
  products versus saved inversions; inconclusive noise calls for stronger
  controls; another access failure updates this record without running.
- **Recheck trigger:** Checkpoint credentials or an isolation-qualified runner
  become available.

## Resolution and history

2026-10-31: opened after the checkpoint upload and gate failed before any
timing command. Functional release tests had passed, but performance remains
unmeasured. Unresolved.
