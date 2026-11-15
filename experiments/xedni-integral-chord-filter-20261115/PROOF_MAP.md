# Proof map

| Mathematical statement | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| The two point equations and a chord slope that is tangent at the second point imply `m²+a₁m=a₂+x₁+2x₂` | `XedniIntegralChord.monic_relation_of_tangent` | All coordinates and coefficients over `ℚ`; distinct x coordinates; exact chord, point-incidence, and tangent equations. Pinned `lake build IntegralChord` passed; `#print axioms` lists only the standard Lean foundations. |
| A rational root `m` of `X²+aX−b` with `a,b∈ℤ` is integral | `XedniIntegralChord.integer_slope_of_monic_relation` | Exact rational equation `m²+a m=b`; uses Mathlib's integral closure of `ℤ` in `ℚ`. Pinned `lake build IntegralChord` passed; `#print axioms` lists only the standard Lean foundations. |
| An integral-coordinate two-point chord satisfying the tangent equation has integral slope | `XedniIntegralChord.integer_slope_of_tangent` | `x₁,y₁,x₂,y₂,a₁,a₂∈ℤ`, `a₃,a₄,a₆,m∈ℚ`, distinct x coordinates, chord equation, both curve equations, tangent equation. Pinned `lake build IntegralChord` passed; `#print axioms` lists only the standard Lean foundations. |
| `U+2V=O` on the nonsingular elliptic curve implies the tangent equation when x coordinates differ | — | Standard chord-and-tangent group-law bridge. The report gives the readable derivation, while Lean group-law instantiation remains open. The conditional Lean theorem must not be read as an unconditional group-law theorem. |

The frozen panel audit independently replays the eight field records and raw
rows. It checks the filter's necessary implication on every saved rational
relation, but finite replay is not a replacement for the algebraic proof.
