# Exact branch equation for the expanded N131 source

The adjacent-Frobenius image can enter the existing N131 phi-chart S3
circuit through **one exact Boolean branch equation per leaf**. This gives
a concrete ten-leaf formula design for the 2,166,216-point expanded d13
base. The equation has a sparse source-product implementation bounded by
**1,716 two-input AND gates per leaf**, or **17,160** across ten leaves,
before the S3 chain and XOR wiring. The complete ten-leaf formula and its
ordinary-query cost still require measurement.

On the exact curve `y²+xy=x³+1` over `GF(2^131)`, let
`phi=1/(x(P)+1)` for a valid raw source point and `y=phi²+phi`.
The previously audited adjacent image has `x(P+tau(P))=1/y`. Its phi chart
is therefore `phi_image=y/(1+y)`. For Boolean `b`, with zero selecting
`P` and one selecting `P+tau(P)`, constrain a full-field `phi_out` by

`(1+b*y)*phi_out = phi+b*phi²`.

At `b=0` this forces `phi_out=phi`; at `b=1` it forces
`(1+y)*phi_out=y`. Here `1+y` is nonzero: `Tr(y)=0` while
`Tr(1)=1` in the odd-degree field. The [Lean proof](BranchEquation.lean)
checks the branch equivalence and uniqueness with exact hypotheses. The
[proof map](PROOF_MAP.md) identifies the remaining concrete curve and
finite-field formalization bridge.

The frozen [ONB census](audit_result.json) checked both branches for all
**4,134 valid d13 source selectors**: 8,268 branch equations, 4,134
distinct image phi outputs, and no zero denominator. It completed in
5.418 seconds with 26,001,408 peak RSS bytes. The prior independently
checked Sage raw-fiber census established the same adjacent group map on
all selectors. A new independent polynomial-field replay in this directory
reached its frozen 180-second cap while scanning all 8,191 nonzero
subspace codes; its stdout, stderr, source, and protocol are retained with
status `CAPPED_180_SECONDS`. A replay restricted to the already enumerated
4,134 valid selectors is the next finite check of the new chart digest.

For the sparse product, write `phi=sum(c_j*basis_j)` with 13 selector bits.
Then `y=sum(c_j*(basis_j²+basis_j))`. Form `d_j=b*c_j` using 13 AND gates;
`b*y` is the linear combination of the 13 fixed y-basis vectors by `d_j`.
Multiplying full-field `phi_out` by this sparse combination uses at most
`13*131=1,703` pairwise AND terms followed by linear XOR maps. The same
`d_j` bits form `b*phi²` linearly, so the source branch needs at most
`13+1,703=1,716` AND gates. This is a constructive upper bound on the
new branch subcircuit. It does not price the S3 links: unlike the old
subspace leaves, `phi_out` can be a full-field image chart, so some former
sparse link multiplications may become generic.

The preceding d13/m12 formula had 232,244 variables, 228,629 clauses,
and 171,278 native-XOR rows. Those counts provide a source-bound reference
for the next ten-leaf build; they are not a prediction of its total size.
The next gate is to generate the exact ten-leaf formula, verify a complete
assignment through every leaf and S3 link, and price the changed internal
multipliers before a one-worker, 600-second, 4-GiB ordinary N131 query.
The proposal retains `candidate_id: null` until the full stage policy and
source are fixed.
