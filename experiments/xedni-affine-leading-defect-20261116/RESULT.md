# Five probes reconstruct leading defects across a 2,401-model grid

On a fresh 32-target panel, five measured `Qp` models per public hit reconstructed **both** first-order `[q]P_i` leading residues for every model in a four-coordinate, seven-value shift grid. Independent modular Jacobian arithmetic found zero discrepancies across **55,223 candidate models**. The resulting vector-aware selector chose a depth-two exact rational residual on **22 of 23** public relation hits, improving 22 minimum-model choices. The remaining hit had no cancellation candidate in the grid. The [audit](audit.py) independently checked every predicted residue and every exact rational residual with `Fraction` group arithmetic.

## Frozen method and result

The [protocol](protocol.json) fixes eight field/subgroup records, a new target law `xedni-affine-defect-v1|p|j` with four targets per field, 16 public queries per target, 13 predeclared short vectors, and shifts `[-3,3]^4`. There were 512 queries, 6,656 public vector tests, and 23 public hits. Each hit had distinct image x-coordinates and 2,401 candidate rational models.

For each hit, evaluate `[q]P1` and `[q]P2` only at shifts `0,e1,e2,e3,e4`. Let `c_i(s)` be the residue of `t([q]P_i)/p` modulo `p`, where `t=-x/y` is the formal parameter. The frozen predictor is

`c_i(s) = c_i(0) + Σ_j s_j (c_i(e_j) - c_i(0)) mod p`.

All 2,401 model scores are constructed, then the selector chooses the smallest model whose predicted `a*c_1(s)+b*c_2(s)` vanishes for the known public-hit vector `(a,b)`. If none qualifies, it chooses the minimum-model baseline. Exact rational residuals are evaluated only after selection, for the selected model and baseline. A separate audit evaluates all candidates independently.

| Recorded item | Result |
| --- | ---: |
| Fresh targets / queries / vector tests | 32 / 512 / 6,656 |
| Public hits / full-grid candidate models | 23 / 55,223 |
| `Qp` probe models used by selector | 115 (five per hit) |
| Selected-model `Qp` confirmations | 23 models |
| Independent full-grid leading-residue checks | 55,223 models; zero mismatches |
| Predicted cancellation candidates | 101 |
| Hits with a cancellation candidate | 22 / 23 |
| Exact rational checks in producer | 45 distinct selected or baseline models |
| Baseline / selected depth-two residuals | 0 / 22 hits |
| Selected choices improved / worsened | 22 / 0 hits |
| Exact rational relations in full-grid audit | 0 |

The one uncovered hit was event 13, vector index 1. All 101 predicted cancellation candidates had exact rational residual depth two in the independent audit; the other 55,122 had depth one. The producer checked all selected leading residues with a separate `Qp` call and all selected depth predictions against exact rational group operations. Its candidate and prediction failure counts were zero. The [result manifest](run-result.json) indexes every candidate row and raw query/vector part. The [audit receipt](audit.json) is `PASS`.

The checked-Sage producer completed in **1.878 seconds** on an ordinary host. Exclusive stage timers were 0.634 seconds for all model constructions, 0.129 seconds for 115 probe-model `Qp` evaluations, 0.094 seconds for affine prediction over 55,223 rows, 0.024 seconds for selected-model `Qp` confirmations, and 0.064 seconds for 45 distinct rational group checks. The selected rational checks account for 0.054 seconds within the last stage; the baseline checks account for 0.010 seconds. Startup, finite-field query work, packing, and control flow occupy the remaining interval. The [checked Sage runtime](sage-runtime.json) was recorded before the run. Probe counts on this fresh panel and the earlier exhaustive search time come from different target panels, so they are not a paired timing ratio or an end-to-end IC speedup.

## Mathematical status and next test

First-order deformation predicts the affine rule: coordinate shifts change the rational lift and interpolated curve coefficients only at order `p`; reduction of the curve and image points stays fixed. The first graded formal-group coordinate is linear in those first-order changes. The frozen panel and independent audit establish the stated equality for every model in this finite grid. A general theorem for all admissible lifts would need a proof that the interpolated curve is integral and smooth at `p`, that the first-order deformation calculation applies to `[q]P_i`, and that the rational first graded coordinate agrees with the modular projective computation. That elliptic bridge is not yet formalized in Lean. The parent [Lean module](../xedni-leading-defect-selector-20261116/formal/LeadingDefect.lean) proves the downstream additive cancellation implication under an explicit leading-map hypothesis; this experiment makes no broader theorem claim.

The next test should derive the first-order affine coefficients directly from tangent and interpolation formulas, then measure that implementation on fresh targets. It should separately attempt the missing elliptic formal-group proof in Lean. Reproduce this evidence with `python3 verify.py`; new Sage runs use `/Volumes/SSD990/cryptanalysis/sage --runtime-info` before `/Volumes/SSD990/cryptanalysis/sage -python /absolute/path/to/run.py`.
