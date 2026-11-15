# Hecke 432 dual coordinate addendum: independent source-fidelity review

## Bound inputs and method

Reviewed producer commit `06335430add4198a2b82efe8db3f0f5c75f03043` in `/var/tmp/cryptanalysis-hecke432-dual-20261107` against archived base `890de0357`. The worktree HEAD equals the producer commit. The precommitted review plan is `45f21e2f1` at `/var/tmp/cryptanalysis-hecke432-review-20261107/reports/2026-11-07-hecke432-dual-map-formal-review/review-plan.yaml`. I read no sibling reviewer report or output before filing this review.

| Input | SHA-256 | Plan match |
| --- | --- | --- |
| `experiments/hecke-432-dual-map-formalization-20261107/formal/DualCurveEquation.lean` | `3028963daa2e9e6a068af99440ac1cc242dfde975d55bba17aaf3a6d277d4b26` | yes |
| `experiments/hecke-432-dual-map-formalization-20261107/formal/DEPENDENCIES.json` | `dced6afeb9c210df8891781827a72ab8c165f8937c8e6a2577c12f7935b60236` | yes |
| `experiments/hecke-432-map-identity-20261025/RESULT.md` | `c8bef40953cd7400ddf7863335215a9429cab2a60abe066ed754cbd11c115cc9` | yes |
| `experiments/hecke-432-map-identity-20261025/compare_qseries_sage.py` | `85001b63b51fbaf164a3c1af6cdba362c048ee14102957de3db3dc1876a0c92f` | yes |

The addendum toolchain file says `leanprover/lean4:v4.35.0-rc4`; `DEPENDENCIES.json` and the shared workspace `lakefile.toml` pin Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. This was a source-fidelity review. I did not run the exact Lean build or fresh axiom audit; the `#print axioms` lines in the source are instructions to Lean, not evidence of their output. Machine status is `not_verified` pending the exact build and CI evidence.

## Declaration-by-declaration finding

**`Hecke432DualCurve.numerator_identity` (lines 13–15): holds as a faithful scoped statement, machine status `not_verified`.** It quantifies over every commutative ring `R` and `x : R`. Its coefficients `16, 128, 64, 432`, exponents `3, 2, 3, 6`, and subtraction order match the rational identity asserted in the archived Sage program and the displayed addendum formula. The formula is a polynomial identity with no field or denominator assumptions. The proof text is `ring`; no conclusion is included among the hypotheses. Because the archive uses rational functions over `QQ`, this ring-general lemma is an algebraic strengthening of the numerator step, not a formalization of the full map.

**`Hecke432DualCurve.curve_equation` (lines 17–27): holds as a faithful scoped statement, machine status `not_verified`.** It universally quantifies over a field `K` and `x y : K`, with `x ≠ 0` and `y² = x³−16`. It concludes exactly that the archived `dual_y = y(x³+128)/x³` and `dual_x = (x³−64)/x²` satisfy `dual_y² = dual_x³+432`. The source hypothesis is precisely the affine equation of archived curve `B`, and the conclusion is precisely the affine equation of archived curve `E`. The coefficients, signs, powers and denominators match `RESULT.md` and `compare_qseries_sage.py`. The source curve equation is genuinely used at line 24, and the nonzero hypothesis is genuinely needed to clear denominators at line 26. Neither hypothesis assumes the target equation. The Lean theorem is algebraic over arbitrary fields, including characteristics in which these curves or their isogeny interpretation can degenerate; the archived modular/isogeny claim is over characteristic zero. Its stronger field quantifier does not establish geometric properties in every characteristic.

At `x = 0`, both displayed rational coordinate formulas have zero denominators. Lean's totalized field division would assign values to syntactic quotients, but `hx` excludes that case; the theorem must not be applied there as a rational-map assertion. Over `QQ`, `x=0` has no affine point on `B` because `y²=-16` has no rational solution; over an algebraic closure such points exist and an extension argument is still required. The point at infinity is outside the affine theorem as well.

## Bridges outside these declarations

1. **Exceptional points and morphism extension:** no theorem resolves `x=0` in relevant extensions, the point at infinity, or regularity of a global map between smooth projective curves.
2. **Isogeny structure:** no theorem proves a group homomorphism, finite surjectivity, separability, kernel, degree three, or that the coordinates are the cited dual isogeny `\widehat\pi`. Satisfying the target affine equation alone does not prove these properties.
3. **Modular source maps:** no Lean definition identifies the normalized `B` modular parametrization, the `C` quarter-shift points, their group difference, or the algebraic twist `H` with the affine coordinate formula.
4. **Differential and Sturm step:** no Lean theorem establishes the q-series calculations, the level-432 weight-two Sturm bound `144`, equality of global pullback differentials, or the characteristic-zero constant-map/cusp-normalization argument from `RESULT.md`.
5. **Archived finite-field/cusp claims:** the 883-point enumeration, cusp-field/torsion argument, image count `37`, and gap `894` are separate archived claims; these declarations neither restate nor prove them.

The README itself marks the first four bridges as open, so the addendum's stated scope is accurate. The archived `RESULT.md` gives a wider mathematical argument; its statement cannot be upgraded to a Lean-verified modular-map identity by these two declarations.

## Verdict and next evidence

Source-to-statement fidelity **holds** for the polynomial numerator identity and conditional affine target-curve equation. A global degree-three dual isogeny or quarter-shift modular-map identity remains **inconclusive from this formal addendum** because the listed bridges are absent. The exact source's machine status is **not_verified** in this review; obtain the pinned named-module build and fresh axiom output, with command, exit status, source hashes and run ID, before claiming kernel verification. No source mismatch or falsifying tuple satisfying the actual theorem hypotheses was found. This review did not perform the blind algebra derivation or its nearby-false controls; those belong to the independent `blind_algebra` joint.
