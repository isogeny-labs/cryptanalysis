# N131 W18 sparse product-space proof map

| Result | Lean declaration or evidence | Status and exact assumptions |
| --- | --- | --- |
| Target-root enumeration composed with exact product-fiber membership | [`TargetFiber.query_iff_exists_source_witness`](../n41_target_derived_fiber_gcd_20261013/TargetFiber.lean) | Checked in pinned Lean 4.34.1 with no axioms. Assumes exact upper-root enumeration and exact fiber oracle. |
| Full-product-space roots filtered to usable source products | [`SupersetFilter.filtered_hit_iff_usable_hit`](../n41_linearized_superset_fiber_20261013/SupersetFilter.lean) | Checked in pinned Lean 4.34.1 with no axioms. Assumes the usable-product list is contained in the full list and the source predicate is exact. |
| Each nonzero W18 seed has a 17-dimensional full product image | Open concrete field bridge | In characteristic two, `L_s(w)=w²+sw` is `F₂`-linear with kernel `{0,s}`. The source domain has dimension 18, so rank-nullity gives 17. The independent [GF(2^131) preflight](result.json) checked rank 17 for seeds `7,3,5,1` in the exact polynomial basis. A Lean definition of this finite field and source subspace is still missing. |
| The constructed N131 witness satisfies the pair, four-atom, and upper equations | Open concrete curve/resultant bridge | The independent Python field implementation checked all four pair equations, both 266-term four-atom resultants, both pair-to-block upper equations, and the block-to-target upper equation. It binds the previously checked Sage group fixture by hash. The general equivalence of the resultant to the curve group law is still open in Lean. |
| Native full-bin GCD hit corresponds to a usable source pair | Open polynomial-GCD bridge | The native worker scanned every one of 32,947 usable first products against the 17-dimensional full second-product space. The checked-Sage auditor decoded the single degree-one GCD root, checked that it is the product of the usable masks `(17,18)`, and re-evaluated the four-atom polynomial. A faithful Lean polynomial-GCD implementation and root bridge remain open. |

Readable proof of the dimension claim: for a nonzero seed `s`, the map
`L_s(w)=w²+sw` is additive because squaring is additive in characteristic
two. Its kernel solves `w(w+s)=0`, hence consists exactly of `0` and `s`
in the field. Restricting to the 18-dimensional W18 source subspace,
which contains `s`, gives a one-dimensional kernel and a
17-dimensional image. The full product-space vanishing polynomial is
therefore linearized and has degree `2^17`; the native oracle evaluates
its 18 coefficient terms modulo each degree-at-most-eight four-atom
polynomial. Every usable pair product lies in that image, and the
checked Lean source-filter theorem explains why verifying a recovered
root against exact source codes preserves and rejects the right cases.

The two Lean modules above are built in their own pinned directories and
their `#print axioms` logs are retained there. The N131-specific finite
field and curve-resultant formalization is partial; the precise missing
objects are an exact polynomial-basis `GF(2^131)` model, the W18 support
predicate, the diagonal-point curve map, and the four-atom resultant
identity in Lean.
