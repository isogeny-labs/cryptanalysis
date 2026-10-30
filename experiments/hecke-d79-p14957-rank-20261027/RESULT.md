# Four-term relations restore rank in the p14957 D79 class

For the prespecified first larger-q antipodal case, `p=14957`, the 40 conductor-four class points all map to residue 1 in the order-five quotient. All 40 degree-13 outside trace sums map to residue 2. The degree-13 neighbor polynomial has the predicted factor pattern `(1)(1)(12)` at every class point; each source yields one outside-class Frobenius trace. Signed relations of support at most three have zero yield in both the direct-point and outside-trace arms, as the order-five projection predicts. At support four, **272 direct-point relations** and **242 outside-trace cancellations** independently raise the base row rank from 20 to **39 over F1489** and **40 over Q**.

| Arm and support cap | Verified signed relations | Rank over F1489 with base | Rank over Q with base |
|---|---:|---:|---:|
| Degree-2/5 base rows | 20 rows | 20 | 20 |
| Direct points, support ≤3 | 0 | 20 | 20 |
| Degree-13 outside traces, support ≤3 | 0 | 20 | 20 |
| Direct points, support ≤4 | 272 | 39 | 40 |
| Degree-13 outside traces, support ≤4 | 242 | 39 | 40 |
| Both support-four arms | 514 | 39 | 40 |

All 40 class points have nonzero projection to the order-1489 subgroup in the independent audit. The rank 39 over F1489 is thus consistent with the scalar-log functional on valid relation rows; the rank certificates independently establish both the upper and lower numerical bounds. The full Q rank follows from an invertible minor modulo 3. The two support-four arms reach the same rank; this panel does not select a faster complete IC candidate.

## Frozen inputs and replay

`inputs.json` binds the earlier eight-prime class receipt by SHA-256, fixes the source digest, `p`, `q`, the predicted factor pattern and the 1800-second producer cap. `result.json` stores all class points, base rows, degree-13 factors, orbit sizes, modular-polynomial checks, outside traces, statuses and exclusive phase timings. `post_inputs.json` and `post_inputs4.json` separately freeze the support-three and support-four analyses against the producer receipt. The latter was written before support-four enumeration. Each arm enumerated **772,240** sign patterns through support four in three alternating repetitions, retaining every candidate and rank path.

The checked-Sage independent audits passed for both support limits. They reconstructed the 10/10/20 class strata from the conductor-1/2/4 Hilbert class polynomials, refactored every degree-13 neighbor polynomial, replayed all reported group identities, and recomputed ranks over Q and F1489. Class completeness in the audit is relative to those three ring-class strata. The structural Lean theorem proves the order-five obstruction for residues 1/4 and 2/3; the generated rank module checks exact F1489 kernels and minors and F3 full-rank minors. The proof map records the curve-specific formalization bridge.

The checked-Sage producer recorded 35.92 s for source construction and 1.335 s for all degree-13 fibers on this local host. The three direct support-four enumerations took 1.568–1.684 s; outside-trace enumerations took 4.121–4.205 s. These are exploratory stage diagnostics with different preparation requirements, not a complete pipeline or calibrated online comparison. `candidate_id` and `target_online_ms` remain null.

The next case to test is the second antipodal class, `p=36037`, with residues 1:20 and 4:20 and `q=1451`. It can test whether the support-four threshold and rank recovery persist when the class occupies both antipodal cosets.
