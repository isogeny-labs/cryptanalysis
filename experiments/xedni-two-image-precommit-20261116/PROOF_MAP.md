# Proof map for precommitted two-image interpolation

| Mathematical result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| First centered pair lies on the interpolated equation | `first_point_equation` | Any field and any four coordinates; checked. |
| Second pair lies on the same equation | `second_point_equation` | Any field; `x₁ ≠ x₂`; checked. |
| The `x` coefficient is forced by two point equations | `interpA_eq_of_two_equations` | Any field; `x₁ ≠ x₂`; both specified curve equations; checked. |
| The constant coefficient is forced | `interpB_eq_of_two_equations` | Same hypotheses; checked. |
| Distinct same-`x` points have opposite `y` | `same_x_opposite` | Any field; equal squared `y` and unequal `y`; checked. |
| Rational relation transfers to public points | `relation_transfer` | Additive commutative groups, an additive reduction homomorphism, both image equalities, and a rational relation; checked. |
| Actual reduction map for these elliptic curves | no Lean declaration | Partial formalization: construction of the good-reduction point-group homomorphism for rational `A,B` with denominator prime to `p`, and its action on the two named points, remains open. The independent arithmetic audit checks every named instance. |

The source contains no `sorry`, `admit`, custom axiom, or unverified native evaluation. The pinned `lean-toolchain`, `lakefile.toml`, and `lake-manifest.json` identify the actual build. The six `#print axioms` outputs contain only standard Lean foundations. The full xedni impossibility claim would require a quantified bound over all admissible lift choices and relation algorithms; these declarations establish the interpolation and reduction implications used by this frozen experiment.
