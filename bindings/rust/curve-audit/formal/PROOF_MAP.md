# Curve-audit interval proof map

Lean toolchain: `leanprover/lean4:v4.34.1` from `lean-toolchain`. Module:
`HasseUnique.lean`. This map distinguishes the checked natural-number lemmas
from the P-192/P-224 curve-order certificate still to be formalized.

| Declaration | Exact mathematical claim | Status |
| --- | --- | --- |
| `CurveAudit.unique_multiple_in_short_interval` | For arbitrary `r,width,n,m,k,l : Nat`, if `width<r`, `n=k*r`, `m=l*r`, `n≤m+width` and `m≤n+width`, then `n=m`. | Existing Lean proof; independent scoped review in [PR #1197](https://github.com/isogeny-labs/cryptanalysis/pull/1197). |
| `CurveAudit.unique_multiple_from_center_bounds` | For arbitrary `r,radius,center,n,m,k,l : Nat`, if `radius+radius<r`, both `n,m` are multiples of `r`, and both lie within `radius` of `center` in each natural-number direction, then `n=m`. | New Lean proof; source-bound native build and transitive axiom audit in the dated report for this change. Independent semantic review remains required before broader promotion. |

The second proof obtains `n≤m+radius+radius` from `n≤center+radius`
and `center≤m+radius`, and obtains the reverse inequality symmetrically.
It then applies the first theorem. The hypotheses are satisfiable, for
example `r=7`, `radius=1`, `center=n=m=14`, `k=l=2`. The strict diameter
bound is necessary: with `r=6`, `radius=center=3`, `n=0`, `m=6`, `k=0`,
`l=1`, all other premises hold, but `n≠m` when the diameter equals `r`.

The **full curve-order theorem remains open**. Neither lemma supplies a
formal prime-field model, Lucas certificate correctness, nonsingular
elliptic group, typed generator/exact point order, Lagrange divisibility,
Hasse bound for the actual cardinality, conversion from the checked squared
integer predicates to a suitable natural radius, or a Lean instantiation
with the actual P-192/P-224 cardinality. The Rust and independent Python
certificate replays are computational evidence and do not close these Lean
obligations. No trace, twist-order, performance, or security claim is
formalized by these declarations.
