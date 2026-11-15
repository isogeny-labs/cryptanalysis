# Proof map

| Mathematical statement | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| The two point equations and a chord slope that is tangent at the second point imply `m²+a₁m=a₂+x₁+2x₂` | `XedniIntegralChord.monic_relation_of_tangent` | All coordinates and coefficients over `ℚ`; distinct x coordinates; exact chord, point-incidence, and tangent equations. Pinned `lake build IntegralChord` passed; `#print axioms` lists only the standard Lean foundations. |
| A rational root `m` of `X²+aX−b` with `a,b∈ℤ` is integral | `XedniIntegralChord.integer_slope_of_monic_relation` | Exact rational equation `m²+a m=b`; uses Mathlib's integral closure of `ℤ` in `ℚ`. Pinned `lake build IntegralChord` passed; `#print axioms` lists only the standard Lean foundations. |
| An integral-coordinate two-point chord satisfying the tangent equation has integral slope | `XedniIntegralChord.integer_slope_of_tangent` | `x₁,y₁,x₂,y₂,a₁,a₂∈ℤ`, `a₃,a₄,a₆,m∈ℚ`, distinct x coordinates, chord equation, both curve equations, tangent equation. Pinned `lake build IntegralChord` passed; `#print axioms` lists only the standard Lean foundations. |
| `U+2V=O` on the nonsingular elliptic curve forces the monic slope equation | `XedniIntegralChord.monic_relation_of_group_relation` | Exact Mathlib affine elliptic-curve group law over `ℚ`, nonsingular points, distinct x coordinates, and the relation `U+V+V=O`. The proof uses the point doubling and negation formulas, with no assumed tangent equation. Pinned build and axiom audit passed. |
| The elliptic-curve group relation forces an integral chord slope | `XedniIntegralChord.integer_slope_of_group_relation` | Same exact group-law hypotheses, plus `a₁,a₂,x₁,x₂` in the image of `ℤ→ℚ`; the y coordinates and remaining coefficients are rational. Pinned build and axiom audit passed. This is the central filter theorem. |

The frozen panel audit independently replays the eight field records and raw
rows. It checks the filter's necessary implication on every saved rational
relation, while the central group-law theorem supplies the general proof.
