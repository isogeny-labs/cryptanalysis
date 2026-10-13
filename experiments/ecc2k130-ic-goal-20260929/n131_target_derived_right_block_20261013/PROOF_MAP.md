# Proof map for the target-derived right-block control

| Result | Proof or verification | Exact scope |
| --- | --- | --- |
| Deduplicating outputs cannot increase labelled input count | `FixedLeftCoverage.eraseDups_length_le` in `FixedLeftCoverage.lean` | Any list with a Boolean equality operation; checked in Lean 4.34.1. |
| A fixed-left source with at most `16ab` signed right choices reaches at most `16ab` distinct outputs | `FixedLeftCoverage.fixed_left_output_bound` | Any output map and explicit `choices.length ≤ 16ab` hypothesis. This includes group maps when supplied as `output`. |
| The right source supplies at most `16·32827·32842` labels | `verify_terminal.py` checks exact source counts and integer product against frozen N131 source bridge | Concrete mask enumeration remains a checked finite computation, not imported into Lean. Different sign choices or source exclusions may collapse labels. |
| Public-target roots preserve listed right-block witnesses | `TargetFiber.query_iff_exists_source_witness` in `../n41_target_derived_fiber_gcd_20261013/TargetFiber.lean` | Exact root enumeration and GCD oracle are explicit hypotheses. The concrete N131 field routines are checked by their frozen execution and group replay. |
| Linearized superset plus exact source filtering preserves usable hits | `SupersetFilter.filtered_hit_iff_usable_hit` in `../n41_linearized_superset_fiber_20261013/SupersetFilter.lean` | Requires containment of the usable list in the superset and an exact source predicate. The native root decoder checks this predicate in the N131 run. |
| The decoded masks satisfy the actual public group equation | `audit_sage.py`, `audit_result.json`, and `audit_run_status.json` | Checked Sage replays all 256 sign assignments on the exact N131 curve. A Lean model of this specific binary-curve group law and the finite source data remains open. |

For the counting proof, list every signed pair choice in each right slot.
There are at most four signs for each admissible mask pair, so the ordered
right-choice list has at most `16ab` entries. Fixing the left block makes
the public output a function of each right choice. The image has no more
elements than its input list. The Lean theorem proves this last implication
for any function and any list satisfying the count hypothesis. The finite
source bridge supplies `a=32827`, `b=32842`; the terminal verifier checks
the resulting product and exact subgroup denominator. Uniformity is used
only when converting the image-size bound into a target coverage fraction.

Build with `lean FixedLeftCoverage.lean` in this directory. The toolchain
is pinned in `lean-toolchain`; `lean_check.log` records `#print axioms` for
both declarations. They depend only on `propext` and `Quot.sound`, with no
research axioms, `sorry`, or native evaluation. The module uses Lean's
bundled Std and has no external package dependency. `lean4checker` was not
installed in this environment.
