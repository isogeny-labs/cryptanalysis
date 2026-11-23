# Target-translated quadratic norm rejects sign-closed N41 source blocks

**An exact quotient-coordinate predicate retained the archived N41
left-pair witness and rejected frozen miss blocks without enumerating
their signed states inside the predicate.** Across block widths of 1, 2,
4, 8, 16, and 32 distinct x-roots, the known positive had a degree-one
norm gcd; each of two target-derived miss keys had degree zero. A separate
integer-field implementation replayed both curve signs at every one of
the 18 block/key cases and matched every gcd zero set and direct source
candidate. The tested source blocks are sign-closed: each x-root represents
exactly two rotated first-slot points.

For a target-conditioned key `K` and first source point `A=(X,Y)`, the
second candidate is `V=K−A`. In the quotient coordinate algebra defined
by the block polynomial `f(X)` and curve equation
`Y²+XY=X³+1`, compute `x(V)` symbolically and infer its rotated second
source product

`p(V)=C_rot/x(V)+H_rot x(V)`.

The rotated product subspace has a nine-term linearized annihilator
`L_rot`, computed once from the eight-dimensional source-product basis.
Reduce `L_rot(p(V))` in the block algebra and take its quadratic norm over
the two possible `Y` signs. If this norm is coprime to `f`, neither sign
at any block x-root can produce an admissible second-source product.
The [proof map](PROOF_MAP.md) gives the checked Lean norm and conditional
Bézout implications. Roots where the translation denominator or `x(V)`
is zero require direct fallback; no tested block had such a root.

| Distinct x-roots per block | Positive gcd degree | Miss gcd degrees | Symbolic seconds, two misses | Direct seconds, two misses |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 1 | 0, 0 | 0.0184 | 0.000224 |
| 2 | 1 | 0, 0 | 0.2237 | 0.075956 |
| 4 | 1 | 0, 0 | 0.6328 | 0.000602 |
| 8 | 1 | 0, 0 | 1.0600 | 0.002512 |
| 16 | 1 | 0, 0 | 3.2218 | 0.002183 |
| 32 | 1 | 0, 0 | 4.1690 | 0.006267 |

Each row is two frozen target-derived miss keys from the earlier W9
implicit-oracle panel, applied to the block containing first-slot state
zero. These are checked-Sage ordinary-host component intervals, with
cache and runtime noise visible in the width-two direct timing. The
symbolic path includes block polynomial construction, quotient-ring
translation, product-span evaluation, norm, and gcd. The direct path
enumerates both signs, subtracts each point, and tests product-span
membership. At width 32, the measured symbolic path took 4.169 seconds
for the two misses, versus 0.00627 seconds for direct enumeration.
The present quotient implementation therefore offers an exact
whole-block rejection rule but no charged search-work advantage on this
panel. Its degree-32 block representation also requires explicit block
x-roots; that construction would not satisfy the N131 600-second/4-GiB
promotion gate without a compact source-code representation.

The first prototype completed all mathematical assertions and failed
while serializing a Sage integer; `first_failure.json` retains its
`PRODUCER_FAILURE_SERIALIZATION` status and source hash. The corrected
three-case prototype, six-width sweep, independent integer-field replay,
checked Sage runtime receipt, pinned protocols, Lean build logs, and
`python3 verify.py` are preserved here. `candidate_id` remains null.

The next representation test must keep the target-translated annihilator
factored **in still-free source-code bits**, so a large code region can be
rejected without first listing its x-roots or constructing a degree-sized
quotient. It must preserve the N41 public witness, charge exceptional
fallbacks and all failed regions, and show a source-bound path into the
frozen N131 public-point envelope before promotion.
