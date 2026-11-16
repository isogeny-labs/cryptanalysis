# Proof map

| Result | Lean declaration | Hypotheses and verification |
| --- | --- | --- |
| An integer vertical shift exists when the shift modulus and x difference are coprime | `XedniPointLiftShift.exists_shift_of_gcd_one` | `p,d,dy∈ℤ` and `Int.gcd p d=1`; proves existence of `k∈ℤ` with `d ∣ dy+kp` using Bézout. Pinned build and `#print axioms` passed. |
| The saved prime-field centered-x setting admits a shift | `XedniPointLiftShift.exists_shift_of_prime` | `p,d∈ℕ`, `Nat.Prime p`, `0<d<p`, `dy∈ℤ`; proves existence of `k`. Pinned build and `#print axioms` passed. The finite row audit checks that every distinct-x centered pair has such a `d`. |
| The selected shift is the least `(|k|,k)` and its height is bounded by `|k|≤d/2` | — | Implemented in `run.py`; independently enumerated and checked for every distinct-x query by `audit.py`. The minimizer and height bound are not formalized in Lean. |
| An elliptic-curve relation with integral first coefficients and x coordinates requires integral slope | `XedniIntegralChord.integer_slope_of_group_relation` in the parent theorem module | Exact Mathlib affine group law over `ℚ`, nonsingular points, distinct x, `a₁,a₂,x₁,x₂` integral. Pinned parent Lean build and axiom audit passed. |

Both new declarations use Lean `v4.35.0-rc4` and pinned Mathlib
`021c46bdd042f67b538b9f9871d556a93713a9a9`. Their theorem module and
build output are retained in `formal/`.
