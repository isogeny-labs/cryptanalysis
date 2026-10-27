# Direct support-five rows complete the p73757 rational matrix before degree-13 source lifting

For the prospectively selected `p=73757` D79 class, 154 direct signed support-five relations raise the frozen support-four baseline from rational rank 34 to rank 40. On that same support-four baseline, 133 degree-13 Hecke support-five relations also reach rank 40: the ascending source order first reaches it after 26 sources, while the order-five projection round-robin order takes 29. The direct-row-assisted prefix needs zero degree-13 sources. These are source-count and matrix-rank results for the frozen 40-point class and relation families.

## Frozen instance and execution

The selection rule took the first eligible odd `v` from 263 through 500 for `p=v²+316` prime, `5 | #E(F_p)`, `5 ∤ p−1`, and largest prime order factor at least 53. It selected `v=271`, `p=73757`, `#E(F_p)=73630`, and largest prime factor `q=199`. The curve is `y²+y=x³−x²−10x−20`. The 40 conductor-four class points split 20/20 across residues 0 and 1 under the order-five projection. The ascending and projection round-robin orders were sealed in `post_class.json` before any degree-13 lift. There was no case replacement.

All 40 degree-13 fibers were lifted with the checked repository Sage launcher and a hash-pinned function artifact. Each had factor pattern `(1)(1)(4)(4)(4)` and status `OUTSIDE_CLASS_TRACE`. The base degree-2/5 matrix has 20 rows and rational rank 20. The support-four census then found 203 direct and 196 Hecke relations, giving 419 baseline rows and rational/modulo-199 rank 34.

| Row family added to support-four baseline | Verified support-five relations | Rational rank | Rank over F199 |
| --- | ---: | ---: | ---: |
| Direct | 154 | 40 | 39 |
| Hecke | 133 | 40 | 39 |
| Direct and Hecke | 287 | 40 | 39 |

| Frozen source order | Support-four baseline: preceding rank | First rational-rank-40 source count | Direct-support-five baseline source count |
| --- | ---: | ---: | ---: |
| Ascending | 25 sources: 39 | 26 | 0 |
| Projection round-robin | 28 sources: 39 | 29 | 0 |

The order-five projection policy takes three more degree-13 source visits than ascending on this holdout. The direct-support-five baseline is already rationally complete before the source phase, so its zero-source gate is independent of either order. The rank over `F199` remains 39 in every completed row family here; the subgroup-log matrix requires a separate rank or kernel analysis.

The producer generated both support-five arms with a signed pair/triple index, group-checked every row, and retained each prefix including zero-yield prefixes. The independent Sage audit rebuilds the class and all fibers, exhaustively checks 10,528,128 signed five-source patterns per arm, and recomputes both prefix rank paths. Exact timings are stage diagnostics on this ordinary host; the experimental comparison is the frozen source count. `candidate_id` and `target_online_ms` are null because the measured object is relation preparation.

The first support-five output miscounted a preexisting rank-40 direct baseline as a one-source hit. `ATTEMPTS.json` and `result-attempt1.json` preserve that output; `support5_v2.py` reran the same census with source count zero and its own frozen hash. The audited result is `result.json`.

## Next experiment

The direct support-five rows now produce a full-rank rational matrix on this new field, while all three completed arms retain one modular dimension. Compute a basis for that `F199` right kernel, test its relation to the class action and order-five projection, and prespecify a row family that could remove it. The next ordering holdout should use a source policy with a mechanism tied to rank gain rather than projection round-robin alone.
