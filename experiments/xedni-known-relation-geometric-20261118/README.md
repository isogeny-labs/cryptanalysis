# Lean geometric bridge for known-relation lifts

The interpolated short Weierstrass curve through an integral representative of a public point **reduces to the prescribed source curve and is elliptic over `Q` whenever the source discriminant is nonzero**. The checked Lean module proves that the chosen rational coordinates form a nonsingular affine point. This supplies the curve-model and rational-point part of the construction in [`xedni-known-relation-lifts-20261118`](../xedni-known-relation-lifts-20261118/README.md).

## Statement and mathematical proof

Let `f : Z → S` be a ring homomorphism into a commutative ring. Fix integers `A,B₀,x,y` whose images satisfy

`f(y)² = f(x)³ + f(A)f(x) + f(B₀)`.

Set `B = y²−x³−Ax` and let `W` be the short Weierstrass model with coefficients `A,B`. Applying `f` to the displayed identity gives `f(B)=f(B₀)`, so `W.map f` is exactly the source short model with coefficients `f(A),f(B₀)`. The discriminant commutes with the coefficient map. Thus a nonzero discriminant on the source implies `W.Δ ≠ 0` over `Z`. Its image in `Q` is also nonzero, so the rational model is elliptic. By construction `y²=x³+Ax+B` over `Q`, giving a rational affine point with coordinates `(x,y)`. For the experiments, `S=ZMod p`, `A=−1`, and `B₀=−2`.

## Proof map

| Result | Lean declaration in [`GeometricKnownRelation.lean`](GeometricKnownRelation.lean) | Status |
| --- | --- | --- |
| Short model commutes with a coefficient homomorphism | `shortCurve_map` | Checked |
| Explicit discriminant polynomial | `shortCurve_discriminant` | Checked |
| Interpolated coefficient maps to `B₀` under the on-curve hypothesis | `interpolated_coefficient_map` | Checked |
| The entire interpolated Weierstrass model maps to the source model | `interpolated_curve_reduction` | Checked |
| Source nonzero discriminant implies integral model nonzero discriminant | `interpolated_curve_nonsingular` | Checked |
| Chosen integer coordinates satisfy the rational curve equation | `interpolated_rational_equation` | Checked |
| The rational model is elliptic | `interpolated_rational_elliptic` | Checked |
| Chosen coordinates form a nonsingular rational affine point | `interpolated_rational_nonsingular_point` | Checked |
| Reduction of arbitrary rational point multiples and the exact subgroup identifications | Prior [`run.py`](../xedni-known-relation-lifts-20261118/run.py) and [`audit.py`](../xedni-known-relation-lifts-20261118/audit.py) on 13 models | Concrete replay passed; a point-level reduction homomorphism and its compatibility with scalar multiplication remain outside this Lean module |

The group algebra, including derivation of the common public point from a known relation and a Bézout inverse, is checked in [`KnownRelationLifts.lean`](../xedni-known-relation-lifts-20261118/KnownRelationLifts.lean). Taken together, the two Lean modules formalize the group and curve-model implications; the point-level reduction bridge is still partial and is stated as such.

## Reproduction

The pinned toolchain is Lean `v4.35.0-rc4`, with Mathlib revision `021c46bdd042f67b538b9f9871d556a93713a9a9` in [`lakefile.toml`](lakefile.toml) and [`lake-manifest.json`](lake-manifest.json). From this directory run:

```sh
lake build GeometricKnownRelation
```

[`build-output.txt`](build-output.txt) records the successful build and `#print axioms` for all eight declarations. They use only `propext`, `Classical.choice`, and `Quot.sound`. The module has no `sorry`, `admit`, `sorryAx`, custom research axiom, or native-evaluation shortcut. `lean4checker --fresh` was unavailable on this host.
