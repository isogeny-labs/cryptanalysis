# Prime-field IC Jacobian relation-walk protocol

## Request and scope

The requested change is to extend the native `ca-ic prime` CLI and its
prime-field index-calculus implementation with Jacobian coordinates for
relation collection.  This experiment is deliberately limited to the
single-large-prime relation collector; descent, rho, factor-base selection,
the relation equations, and certification remain unchanged.

| Requirement | Implementation evidence | Acceptance evidence |
| --- | --- | --- |
| Select Jacobian relation collection from the IC CLI | `--relation-coordinates jacobian` is parsed and reported in JSON | CLI integration test |
| Avoid one affine inversion per adding-walk step | independent walks are held in Jacobian form, batch-normalized once per lane round, and advanced by mixed Jacobian addition | field/group-law differential tests and source inspection |
| Preserve the existing result and accounting semantics | affine remains the default; each initialized lane and each probe step is charged under the existing operation model | deterministic known-answer tests for both backends |
| Make performance claims only from comparable evidence | compare the exact affine baseline and Jacobian candidate at the same revision, curve panel, seeds, budgets, target count, and build profile | paired timings with raw JSON and environment receipt |

## Frozen comparison

- Source baseline: `1ee4f47e962aac7f0f09781e34fccfaec1c6456e`.
- Control: `ca-ic prime --solver orbit --relation-coordinates affine`.
- Candidate: the same command with `--relation-coordinates jacobian` and
  the reported default Jacobian lane count.
- Primary measurement: `logs.seconds` and whole-command wall time.
- Correctness gates: no rejected relations, no inconsistent components,
  every certified column verifies, and every requested known-answer target
  is recovered.
- Accounting gate: the candidate does not receive an operation-count
  discount for projective arithmetic.  Lane scalar multiplications and one
  walk advance per processed probe retain the existing abstract group-op
  charges.

The first local run is exploratory unless its environment satisfies the
repository isolation contract.  It may establish correctness or reject a
candidate, but it cannot establish a baseline speedup.  A result here is a
relation-collection stage result, not an end-to-end index-calculus win.

Timing is currently blocked by the named
[checkpoint-access problem](../../problems/prime-ic-jacobian-checkpoint-access.md);
no timing run may start until the repository checkpoint gate succeeds.

## Representation obligations

Jacobian `(X:Y:Z)` represents affine `(X/Z^2, Y/Z^3)` and uses `Z = 0` for
the identity.  The candidate must pass differential tests for conversion,
doubling, mixed addition (including identity, inverse, and equal-point
branches), and seeded scalar multiples on generic, `j = 0`, and `j = 1728`
curves.  Batch normalization must be equivalent to individual affine
conversion for every lane.
