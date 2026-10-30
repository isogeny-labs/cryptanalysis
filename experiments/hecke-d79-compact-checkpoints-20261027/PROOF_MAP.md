# Proof and audit map

The mathematical cancellation identities used by the pair index are the Lean-checked `PairIndexCancellation.two_cancel_iff`, `.three_cancel_iff`, and `.four_cancel_iff` in the pinned parent experiment. The append-only prefix recurrence is Lean-checked as `IncrementalPrefix.prefix_step` and `.prefix_mono` in the preceding rank-stopped collector. This change introduces a checkpoint representation and exclusive timing partition, not a new mathematical theorem.

| Property | Verification |
| --- | --- |
| Each journal appends one source step and only the rows first available at that step | `audit_sage.py` checks increasing source indices, row maximum source, exact static pair-index set, and source group equations |
| Incremental rank and stop rule | Independent Sage matrices at each of 355 source steps; rank-39 control stops at 35 and all fresh full caps stay below 39 |
| Anchored class logs | Sage q-projection and pointwise scalar replay for all 40 p103357 points |
| Charged wall partition | `audit_sage.py` recomputes lift, index, rank, checkpoint, and loop sums from sealed journals and case summaries |
| Frozen identity | `pre-run.json`, `post-selection.json`, `post-run.json`, `post-audit.json`, checked Sage runtime and `verify.py` |

The Python journal and elliptic-curve arithmetic are not encoded in Lean. Their exact execution bridge is the independent Sage audit and sealed outputs. The inherited Lean theorem modules state the group and finite-prefix facts with their original hypotheses and standard axiom audits.
