# Complementary four-term rank at the second antipodal D79 class

At the prespecified `p=36037` holdout, the 40 conductor-four class points split evenly between residues 1 and 4 in the order-five quotient. Each of the 40 degree-13 Hecke sources has simple factor pattern `(1)(1)(3)(3)(3)(3)` and four outside-class Frobenius orbit traces. Their aggregate sums split evenly between residues 2 and 3. Signed supports one through three produce zero direct or outside-trace relations. At support four, **213 direct relations** and **198 outside-trace cancellations** provide complementary matrix rank.

| Row system | Verified support-four relations | Rank over F1451 | Rank over Q |
|---|---:|---:|---:|
| Degree-2/5 base | 20 rows | 20 | 20 |
| Base + direct | 213 | 37 | 37 |
| Base + degree-13 trace | 198 | 34 | 34 |
| Base + both | 411 | **39** | **40** |

The degree-13 trace rows add two F1451 dimensions beyond the direct system, while the direct rows add five beyond the degree-13 trace system. Over Q the respective gains are three and six. Thus the two relation families are complementary at this frozen support cap; neither alone reaches the combined rank. A separate checked-Sage subgroup audit constructed the order-1451 group from one projected class point, computed all 40 class-point logs in that group, and verified that those logs annihilate all 20 base, 213 direct and 198 trace rows. Every class-point log is nonzero. This supplies a curve-derived F1451 kernel witness for the observed rank-39 ceiling. The combined Q rank has an invertible 40-minor modulo 3.

In the earlier `p=14957` one-residue class, each support-four arm independently reached the combined rank. Here the 20/20 antipodal split accompanies a rank deficit in each separate arm and a complementary gain when the arms are joined. These are two frozen cases; the observed difference motivates a broader coset-balance panel, not a fitted law.

`inputs.json` fixes the parent class receipt SHA-256, source digest, curve, group order, factor prediction and 1800-second producer cap. `result.json` retains all points, rows, factors, orbit traces, modular-polynomial checks, statuses and phase timings. `post_inputs.json` binds the producer receipt by SHA-256 before the support-four census; each 40-source arm traversed 772,240 signed patterns in three alternating repetitions, preserving every relation and rank path. The first independent audit attempt stopped at a copied assumption of at most two outside traces per source; its stderr is retained. The corrected audit passed, reconstructing the 10/10/20 conductor strata, refactoring all 40 degree-13 polynomials, replaying every reported relation, and recomputing all ranks. Its class-completeness check is relative to the conductor-1/2/4 ring-class strata.

The checked-Sage producer measured 35.19 s for function construction and 0.825 s for degree-13 fibers on this local host. The three direct enumerations took 1.63–2.28 s, and the outside-trace enumerations took 10.51–10.82 s. These are exploratory stage diagnostics with different preparation requirements, not a calibrated online IC comparison. `candidate_id` and `target_online_ms` remain null.

The pinned Lean build passed for the structural order-five theorem and exact numerical kernel/minor certificates for all three row systems. Its axiom printout and generator regeneration check are retained in `formal/`. The proof map keeps the general rank implication and curve-specific Lean bridge open. The next useful comparison is the mixed-projection `p=26237` zero-triple case from the eight-prime panel: its absent direct triples are not explained by the antipodal condition, so a support-four census can separate projection and finite-group sparsity effects.
