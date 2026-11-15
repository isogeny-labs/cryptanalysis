# T-1806: source-to-statement fidelity review, round 2

## Scope and verdict

**Verdict: holds for source-to-statement fidelity and identification of missing geometric bridges.** This is a source review of the exact Git objects below, not a Lean build or an independent algebra rederivation. The machine status of these declarations remains **not verified in this review**. I did not read the round-2 blind output or earlier round reports before filing this report.

The frozen claim is accurate at its stated scope: `Hecke432DualCurve.numerator_identity` expresses the numerator polynomial identity, and `Hecke432DualCurve.curve_equation` expresses the target equation for the archived rational coordinates under the source equation and `x ≠ 0`. Neither declaration asserts an isogeny or the modular identity in the archived `RESULT.md`.

## Exact inputs and source comparison

Reviewed producer commit: `06335430add4198a2b82efe8db3f0f5c75f03043`; archived result commit: `890de0357b0a2f76db8f3fe2e5504132af4ee845`; frozen review-plan commit: `bda2f489b631aff48860e12fa2616c3d4cdbd068`. I read the listed files with `git show <revision>:<path>` and hashed those blob bytes with SHA-256. The three hashes in the plan match:

| Input | SHA-256 |
| --- | --- |
| `experiments/hecke-432-dual-map-formalization-20261107/formal/DualCurveEquation.lean` | `3028963daa2e9e6a068af99440ac1cc242dfde975d55bba17aaf3a6d277d4b26` |
| `experiments/hecke-432-map-identity-20261025/RESULT.md` | `c8bef40953cd7400ddf7863335215a9429cab2a60abe066ed754cbd11c115cc9` |
| `experiments/hecke-432-map-identity-20261025/compare_qseries_sage.py` | `85001b63b51fbaf164a3c1af6cdba362c048ee14102957de3db3dc1876a0c92f` |

The Lean numerator has `(x^3-16)(x^3+128)^2-(x^3-64)^3=432x^6`, exactly the Sage script's rational assertion after multiplication by `t^6`. Its `CommRing` quantification makes this a polynomial identity in any commutative ring, including positive characteristic; it makes no nonsingularity or map claim. The target theorem uses `y^2=x^3-16`, `x ≠ 0`, and the same ordered coordinates `((x^3-64)/x^2, y(x^3+128)/x^3)` as both the script's `dual_x, dual_y` and the displayed formula in `RESULT.md`. Its conclusion is only `Y_target^2=X_target^3+432`. The source hypothesis is supplied, not derived. The `x ≠ 0` condition is the necessary affine denominator guard. The proof text invokes `ring`, substitution of `hB`, and `field_simp [hx]`; this is a source inspection, not confirmation that those tactics compiled at the pin.

The producer README maps the same two expressions to those same declarations and explicitly calls the target result a field-element equation. Its statement that extension at `X=0` and infinity, group homomorphism, degree three, dual-isogeny identification, quarter-shift modular parametrization and Sturm formalization remain open is consistent with the Lean source. The source file's own header is also scoped to the affine equation.

The producer `formal/lean-toolchain` and the shared build workspace `lean-toolchain` both specify `leanprover/lean4:v4.35.0-rc4`. `formal/DEPENDENCIES.json`, the shared `lakefile.toml`, and the shared `lake-manifest.json` all specify Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9`. The producer README names the shared workspace and an explicit `lake env lean -R ../.. .../DualCurveEquation.lean` command. I checked these pinned source files; I did not run that command, check installed dependency cleanliness, inspect an elaborated theorem type, or authenticate a build/axiom audit. The `#print axioms` lines in the source are requests for output, not output evidence.

## Missing bridges, one by one

1. **Exceptional affine points and infinity.** The rational expression is undefined at `X=0`; the Lean theorem excludes it. To obtain a map of complete curves one must prove extension at those points and at the point at infinity, including the images and regularity in suitable local/projective coordinates. The Lean statement does not handle characteristic restrictions or nonsingularity required for an elliptic-curve interpretation.
2. **Point-map and group law.** Satisfaction of the target equation on a dense affine domain does not prove a globally defined morphism preserving the identity or addition. Those facts require a geometric construction or a theorem applying to a completed morphism of elliptic curves.
3. **Degree, kernel, and dual identity.** The rational coordinate identity alone does not prove degree three, separability in the intended characteristic, a kernel, or equality to the dual of a specified isogeny. The normalization/sign and the relation to the named source/target models must be fixed.
4. **Modular construction.** No Lean object denotes `X_0(432)`, the quarter-shift points on `C=X_0(27)`, their subtraction, the twist to `E`, or the normalized modular parametrization to `B`. Thus neither claimed map has been constructed in the theorem's language, and rationality/descent of the quarter-shift construction is not established there.
5. **Differentials and Sturm.** The Lean declarations contain no q-series, invariant-differential pullbacks, agreement through `q^207`, level/weight identification, or proof of the Sturm bound 144 and its applicable hypotheses. The archived Sage script performs finite Laurent-series and bound assertions; transporting those computations to equality of global weight-two forms is separate from the affine equation.
6. **Cusp and constant-map step.** Even equality of pullback differentials would leave a constant difference of maps to an elliptic curve in characteristic zero. One must prove the morphisms exist on the connected complete domain, identify their values at the infinity cusp, and use those values to show the constant is zero. Pole-order claims and cusp normalization in `RESULT.md` are not consequences of either Lean declaration.

The archived script's finite-field `GF(883)` enumeration and the result's image/gap claims are also outside these two declarations. They are not needed to establish source fidelity of the two affine identities.

## Outcome boundary

`holds` here means the source and README faithfully state the two limited algebraic claims and leave the enumerated bridges open. It does not certify successful Lean elaboration, axiom status, the archived Sage execution, the degree-three isogeny, or the level-432 modular-map equality. The assigned blind algebra and nearby false controls belong to T-1805 and were not read or re-performed here.
