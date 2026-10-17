# Three-family Riemann–Roch determinant on the N41 public point

**An exact target-conditioned determinant retained one of 50,653 three-code families on the frozen N41 panel, and an independent Sage group join identified the same signed-state triple.** The panel leaves source slots 0–2 free while fixing one archived relation state in each of slots 3–5. The one compatible triple contains states `(12,122,116)`. Its public-target relation was independently checked by elliptic-curve addition. The exact screen used 3,241,792 determinant evaluations, exposing the cost of literal three-family elimination.

## Method

The field is `GF(2)[t]/(t^41+t^3+1)`, the curve is `y²+xy=x³+1`, and the subgroup order is `549756390943`. The archived raw public point is `Q=(2026560328086,1928332930914)`. Each of the six slots uses the frozen W8 source with seed 56; every source code has four signed pair-sum states. The three fixed states in slots 3–5 have IDs `(47,128,34)`. The [protocol](protocol.json) binds these inputs, code, source geometry, N131 census, one-worker envelope and checked-Sage runtime.

For a point `P=(x,y)`, let `v(P)=(1,x,y,x²,xy,x³,x²y)`, a basis evaluation row for `L(7O)`. The three fixed points and `−Q` give four independent rows. Their right kernel has dimension three. Project each state in the three free slots into that kernel to obtain `s₀,s₁,s₂∈GF(2^41)^3`. Seven distinct evaluation points sum to the identity exactly when `det(s₀,s₁,s₂)=0`, by the degree-seven elliptic divisor criterion. [Verification](verification.json) checks distinctness across the frozen eligible point domains; [the independent group join](audit_result.json) checks the resulting relation on the actual curve.

For each ordered three-code family `(c₀,c₁,c₂)`, the finite eliminant is the product of `det(s₀,s₁,s₂)` over its `4³=64` signed-state choices. It vanishes exactly when some state choice has determinant zero. The implementation reuses all 16 cross products for a `(c₀,c₁)` pair, then evaluates them against the four third-family states. A zero family is expanded and checked for folded-column conflicts.

| Frozen N41 stage | Result |
| --- | ---: |
| Eligible families / states in each free slot | 37 / 148 |
| Three-family combinations | 50,653 |
| Combinations with some distinct-column state choice | 45,990 |
| Nonzero / zero finite eliminants | 50,652 / **1** |
| Determinant evaluations / determinant-zero state triples | 3,241,792 / **1** |
| Independently checked group matches | `(12,122,116)` |
| Producer interval / monitored parent wall | 41.913 s / 42.196 s |
| Sampled parent-plus-child peak RSS | 48,529,408 B |

The monitored run completed below the frozen 600-second and 4-GiB caps. The producer interval includes kernel construction, eligibility, signatures, cross products, determinant evaluations and family classification. The [checked-Sage audit](audit_sage.py) independently builds 21,216 valid first-two-slot group sums, subtracts each of the 148 third-slot states from the public residual, and obtains the same sole match. Those operations are different units, so their counts alone are not a wall-time speedup comparison. The three fixed states come from the archived relation; this is a conditional component measurement with `candidate_id: null`.

## Proof map

| Result | Lean declaration / verification | Remaining bridge |
| --- | --- | --- |
| A finite three-family product is zero iff a state triple has determinant zero, under `mul x y = 0 ↔ x=0 ∨ y=0` | `ThreeFamilyProduct.familyProduct_zero_iff`; Lean 4.34.1 build passed; `#print axioms` gave `propext, Quot.sound` | Instantiate `Nat` encoding with the actual finite-field multiplication and determinant implementation |
| The projected 3×3 determinant represents dependence modulo the four fixed rows | Written row-reduction argument; kernel rank and witness checked by the runner | Formalize finite-field row equivalence and full-rank assumptions |
| Seven distinct points have a vanishing evaluation determinant iff their group sum is the identity | Standard elliptic divisor argument; all eligible N41 points are pairwise distinct; independent checked-Sage group join agrees across the entire finite panel | Formalize the `L(7O)` divisor criterion and connect the repository curve model to it in Lean |

The original mathematical statement and proof obligation remain open at the curve level. The [Lean module](ThreeFamilyProduct.lean) has no claim-encoding axioms, `sorry`, `admit`, or native evaluation; the pinned toolchain is in [lean-toolchain](lean-toolchain). `lean4checker --fresh` was unavailable locally. The finite-product theorem preserves the three families and the no-zero-divisors hypothesis, while the group criterion keeps the seven-distinct-point condition explicit. For the underlying genus-one Riemann–Roch dimensions, see [Milne's elliptic-curve notes](https://jmilne.org/math/Books/ectext6.pdf). For index-calculus context, see the [SAC 2020 preproceedings](https://sacworkshop.org/SAC20/files/preproceedings/18-IndexCalculus.pdf).

## N131 transfer and next experiment

The independently audited W23 source has 1,049,218 usable edge-code families per slot. Literal three-family enumeration for even one fixed three-state suffix requires **1,155,040,460,822,388,232 family triples** and **73,922,589,492,632,846,848 determinant evaluations**. Finishing those evaluations within 600 seconds would require at least **123,204,315,821,054,745 evaluations/s**. The three fixed suffix slots have `(4×1,049,218)³` signed assignments of their own. [Projection](projection.json) derives these integers from the frozen source census; it does not rule out an implicit symbolic representation.

The next useful design gate is an **implicit constraint on source-code bits and the public point** that avoids enumerating code triples or fixed suffixes, followed by an unpinned N41 ordinary-query solve under the same caps. The direct bilinear S3 pair leaf reduced N41 circuit AND count by 37.44% in the preceding experiment, so combining that leaf with a target-dependent multi-slot constraint is a more concrete next test than another explicit family table. Preserve every solver status and check any candidate relation by independent group addition before carrying it to the frozen N131 ordinary query.
