# Squared Hasse predicate proof map

Pinned toolchain: `leanprover/lean4:v4.34.1`. Module:
`HasseSquareBounds.lean`, importing the existing `HasseUnique.lean` lemma.
This is a new partial formalization of the large-field curve-audit certificate,
not a complete proof of either concrete curve order.

| Declaration | Exact scope | Status |
| --- | --- | --- |
| `CurveAudit.squared_deviations_have_short_sum` | For natural `p,r,d₁,d₂`, if each `dᵢ² ≤ 4p` and `16p < r²`, then `d₁+d₂ < r`. | Lean proof; source-bound build and independent review in the dated report. |
| `CurveAudit.unique_multiple_from_squared_center_bounds` | Two multiples of `r` with explicit center bounds and those squared deviation checks coincide. | Lean proof, conditional on the supplied bounds and divisibility. |
| `CurveAudit.unsignedDelta_center_bounds` | The piecewise natural subtraction matching the Rust unsigned difference supplies both center inequalities. | Lean proof. |
| `CurveAudit.unique_multiple_from_hasse_squared_checks` | Two multiples of `r`, each with unsigned difference from `p+1` whose square is at most `4p`, coincide when `r²>16p`. | Lean proof of the verifier's arithmetic uniqueness implication. |

The first proof avoids an unformalized square root. Each `dᵢ²≤4p` yields
`(2dᵢ)²≤16p<r²`; monotonicity of natural squaring gives `2dᵢ<r`,
so `d₁+d₂<r`. The final proof uses the existing short-interval uniqueness
lemma. Its assumptions are satisfiable, e.g. `p=101, r=41, n=m=82,
k=l=2`: the center is `102`, each deviation is `20`, `400≤404`, and
`1681>1616`. The strict spacing is sharp as an abstract predicate: at
`p=1, r=4, n=0, m=4, k=0, l=1`, center `2`, both squared deviations equal
`4p`, and `r²=16p` while `n≠m`.

The Rust implementation's `hasse_unique_multiple` checks nonzero `r`,
`n % r == 0`, the piecewise unsigned difference squared against `4p`,
and `r*r > 16p`. This Lean module proves the *mathematical implication*
of the two squared checks and two divisibilities, including the natural
absolute-difference definition; it does not prove the Rust parser or BigUint
operations implement those predicates. It also does not supply a proof that
the *actual* elliptic-curve cardinality is a multiple of `r` or meets Hasse's
bound. Prime-field, nonsingular group, exact point-order, Lagrange,
Hasse-to-squared-bound, concrete certificate binding, trace, twist, and
performance claims remain outside this module.
