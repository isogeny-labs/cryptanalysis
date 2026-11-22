# Analysis amendment for the target-origin-pencil panel

Date: 2026-11-18

Status: prospective analysis-only correction, written before any natural panel
rows. This amendment does not change the frozen source-instance generator,
lift, candidate construction, ordering, coefficient bound, exact checks,
grid, master seed, release binary, or runner. `PROTOCOL.md`, `runner.py`,
`analyze.py`, and `FREEZE.json` remain the immutable version-1 record.
[pcc:unverified]

## Reason for the amendment

The version-1 analyzer can set `stage_improvement_observed` on an incomplete
file. It tests the recovery comparison and two named failure statuses, but it
does not require the exact 1,600-key roster and does not reject every other
certificate, source, group, lift, semantic, internal, or unknown failure.
Consequently its promotion boolean is not an admissible implementation of the
prospectively stated completeness boundary. [pcc:unverified]

`analyze-v2.py` is therefore authoritative for any future natural output. It
requires exactly one row for every frozen `(p, family, lift, r, idx)` key,
rejects missing, duplicate, unexpected, and malformed roster entries, and
checks all recorded paired-arm invariants before a result can be promoted.
[pcc:unverified]

## Frozen status classification

The following feasibility exclusions are admissible retained outcomes and do
not by themselves invalidate a complete panel:

```text
no_point
small_order
identity
no_integer_solution
rank_deficient
```

`ok` is the only analyzed paired-arm outcome. Every other status, including
`internal_not_on_curve`, `lift_error`, `lift_cert_failed`, `group_error`,
`relation_cert_failed`, either lost-baseline status,
`origin_pencil_internal_error`, and any unknown or missing status, is an
invalid outcome. This classification is fixed before observing natural rows.
[pcc:unverified]

## Corrected decision boundary

`stage_improvement_observed` is true only if the exact roster is complete,
there are no invalid statuses or analyzer invariant failures, at least one
valid row has a candidate-only correct target recovery, and no valid row has a
baseline-only correct target recovery. The summary retains counts overall, by
rank, and by full cell, and explicitly reports the roster defects and status
classification. [pcc:unverified]

This correction cannot turn a null result into a win: it only closes routes by
which incomplete or invalid evidence could have been promoted. It remains a
stage-level comparison, not an end-to-end ECDLP claim. [pcc:unverified]
