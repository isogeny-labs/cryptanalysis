# Restricted Jacobian classifies all measured level-432 chain collisions

At **6,120** verified rational `(C,E,B)` triples across p883, p887, p919, p997, and p1231, the number of recovered source chains exceeds one exactly when the explicit B-coordinate equation `P_B(C,x_B)=0` has zero derivative in **both** tangent directions of `C×B`. There are **152** double fibers and **5,968** singleton fibers; the restricted-Jacobian classifier has zero mismatches. This is an exact classification of the declared finite-field datasets, with its initial narrower prediction and all correction steps retained.

| Prime | Triples | Double fibers | Restricted-Jacobian critical triples | Other tangent behavior |
| ---: | ---: | ---: | ---: | --- |
| 883 | 864 | 0 | 0 | — |
| 887 | 864 | 8 | 8 | Four critical points have `y_B=0`; four have both `∂_T P_B=0` and `D_C P_B=0` |
| 919 | 1,224 | 72 | 72 | All 72 have both `∂_T P_B=0` and `D_C P_B=0` |
| 997 | 1,800 | 0 | 0 | 72 have `D_C P_B=0` alone |
| 1231 | 1,368 | 72 | 72 | All 72 have both `∂_T P_B=0` and `D_C P_B=0` |

## The two tangent derivatives

Write `C:y_C²+y_C=x_C³−7`, `B:y_B²=x_B³−16`, and `T=x_B`. Tangent vectors on the two smooth curves in odd characteristic are

`v_C=(2y_C+1, 3x_C²)`, `v_B=(2y_B, 3x_B²)`.

Because `P_B` depends on `(x_C,y_C,T)` and not `y_B`, its derivatives restricted to `C×B` are

`D_C P_B=(2y_C+1)∂_{x_C}P_B+3x_C²∂_{y_C}P_B`,

`D_B P_B=2y_B ∂_T P_B`.

Thus the explicit hypersurface is critical exactly when `D_C P_B=0` and `2y_B∂_T P_B=0`. The second factor can vanish either because the x-coordinate equation is singular in T or because B lies at a fixed point of the sign involution, `y_B=0`. The pinned Lean theorem `SignBranch.restricted_jacobian_zero_iff` proves this product-zero algebra over a field with `2≠0`; `negation_fixed_iff_y_zero` proves the affine sign-branch identity. The written tangent calculation supplies the exact link to these curves. Whether every critical point has two modular source preimages uniformly in characteristic zero remains open.

The [initial protocol](protocol.json) had predicted that doubles would occur exactly when **both** `∂_T P_B` and `D_C P_B` vanished. Its [first result](initial_result.json) failed at three generic p887 double fibers with nonzero `∂_T P_B`; a fourth p887 double was on a special source model. All four have `B=(484,0)` and `E=(322,0)`. The corrected j-based source classifier in [`screen.py`](screen.py) also recognizes p883's `base` and `quadratic_twist` models as generic j rather than treating their labels as special. The failed prediction remains `FAIL_GENERIC_SINGULARITY_PREDICTION` in [`result.json`](result.json).

The [post hoc refinement](refinement_protocol.json) added the `y_B=0` branch and yielded zero mismatches in [`refined_result.json`](refined_result.json). The separately frozen [restricted-Jacobian replay](jacobian_protocol.json) then tested the actual tangent criterion; [`jacobian_result.json`](jacobian_result.json) records zero mismatches. These are exploratory classifications of previously measured primes, not a prospective holdout of the refined condition.

## Verification and proof boundary

All 6,120 candidate rows and the 89-term exact characteristic-zero B polynomial were bound by SHA-256 before the first gradient screen. [`gradient_rows.json`](gradient_rows.json) records the specialized equation and tangent derivatives. The independent [`audit.py`](audit.py) recomputes both derivatives using truncated dual-number multiplication rather than the producer's explicit derivative formulas, checks every source triple against the frozen candidate shards, and verifies both the failed and refined classifications. Its [receipt](audit.json) has zero gradient discrepancies and zero restricted-Jacobian mismatches.

The Lean module [`formal/SignBranch.lean`](formal/SignBranch.lean) checks the sign-branch and product-zero implications for any field with `2≠0`, along with the observed count identities. The toolchain and Mathlib revision are pinned in [`formal/DEPENDENCIES.json`](formal/DEPENDENCIES.json); [`formal/build-output.txt`](formal/build-output.txt) records the actual build and `#print axioms`. Only standard Lean foundations occur. The complete modular-curve morphism, normalization, and its source-fiber multiplicities are checked by the frozen finite-field producers and audits rather than formalized in Lean.

This is an index-calculus stage diagnostic with `candidate_id: null`. The next experiment is a prospective prime selected from source-free restricted-Jacobian candidates, followed by a complete direct source-chain inverse and independent all-j census, to test whether the critical-point equivalence persists beyond these five primes.

Replay from the repository root:

```sh
python3 experiments/hecke-432-collision-singular-locus-20261026/screen.py
python3 experiments/hecke-432-collision-singular-locus-20261026/refined_screen.py
python3 experiments/hecke-432-collision-singular-locus-20261026/jacobian_screen.py
python3 experiments/hecke-432-collision-singular-locus-20261026/audit.py
cd experiments/hecke-432-formal-ci-20261025
lake env lean ../hecke-432-collision-singular-locus-20261026/formal/SignBranch.lean
cd ../hecke-432-collision-singular-locus-20261026 && shasum -a 256 -c SEAL.sha256
```
