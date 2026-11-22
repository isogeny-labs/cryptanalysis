# N41 W11 target-conditioned block span: exact rejection boundary

**An affine enclosure rejected all 109 width-eight source-code blocks on
each of 24 frozen public-target residuals while retaining the verified
positive relation.** On that positive residual it retained one block and
rejected the other 108. The test identifies a selective whole-block
constraint for the exact two-pair oracle, and it also locates the point
where this particular linear relaxation loses selectivity: width-32 blocks
rejected only 8–13 of 32 on the 24 residuals.

The current construction evaluates every first-pair state before building
the enclosure. Its 25 queries each evaluated 1,124 target-conditioned
second products, so this experiment measures *selectivity*, not saved
online work. The next algorithmic step is to compute the width-eight
enclosure directly from a compact source-code description at less cost
than 32 point differences and product inversions per block.

## Instance and frozen input law

The field is `GF(2)[u]/(u^41+u³+1)` and the curve is
`y²+xy=x³+1`, ID `EC1N41Ckb1h7d5e80d3c4d0`, subgroup order
549,756,390,943 with cofactor four. The W11 fixed-seed source has
281 valid codes and four signed pair points per code. The tested slots
are Frobenius rotations 12 and 24 from the prior
[independently audited public relation](../n41_w11_fivepair_native_join_20261018/RESULT.md).
The positive residual is `R=(1434452595080,1460136977354)`, with
source codes `(253,63)` and exact first-state ID 278. The 24 other
residuals use deterministic Python seed `411153141`: choose three
uniform state IDs from slots 0, 1, and 2, retry until the three codes
are distinct, then subtract those three points from the frozen public
raw point `Q=(1936680952394,910597499030)`. The [protocol](protocol.json)
pins source hashes and a 300-second cap. All 25 target points are
distinct.

## Block gate

For each first state `P` and target residual `R`, put `V=R−P` and
compute the rotated second source product

`p_R(P)=C^(2^24)/x(V)+H^(2^24)x(V)`.

The possible second source products occupy an exact 10-dimensional
binary linear space `U`: with source parameter `a`, fixed seed `s`,
and source product `a(a+s)=a²+as`, both terms are binary-linear in
`a`. The checked run enumerated all 1,024 parameter codes and verified
rank 10. For a prefix block of first source codes, let `p0` be its
first product and let `D` be the XOR span of all `p_R(P)+p0` in the
block. If `p0+D` does not intersect `U`, no first state in that entire
block can produce a valid second pair. The Lean
[soundness theorem and proof map](PROOF_MAP.md) cover this implication;
the field and group evaluations are the frozen checked-Sage finite
calculation. The gate deliberately allows invalid second codes and
signs in `U`, so it cannot discard a valid witness through those filters.

Blocks are indexed by `code >> free_code_bits`. A first state with
`R−P` equal to the identity or `x=0` cannot match a valid second pair
and is omitted. The table counts a block rejected only when its affine
enclosure is disjoint from `U`.

| Free low code bits | Nonempty source-code blocks | Rejected on positive residual | Rejected on each of 24 ordinary residuals | Mean full-rank blocks on ordinary residuals |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 281 | 280 | 281 | 0 |
| 1 | 238 | 237 | 238 | 0 |
| 2 | 174 | 173 | 174 | 0 |
| 3 | 109 | 108 | 109 | 0 |
| 4 | 62 | 59 | 58–61; mean 59.71 | 1.88 |
| 5 | 32 | 11 | 8–13; mean 10.54 | 19.46 |

The positive residual had exactly one product in `U`; the 24 sampled
ordinary residuals had zero. Thus the positive block was retained at
every width, and every rejected block is consistent with the exact
membership scan. At width five, many block direction spaces together
with `U` have full rank 41; the enclosure then cannot reject that
block. This is the measured rank barrier for this grouping and input
panel, not a bound on every possible nonlinear block constraint.

## Work, proof, and next gate

The [checked-Sage run](result.json) spent 6.299 seconds loading and
preparing the source and 191.235 seconds on all target-dependent queries
and six rank levels, including every failed membership attempt. Mean
ordinary-residual query cost was 7.708 seconds on this ordinary host.
These intervals include 1,124 group differences and product inversions
per residual, plus rank construction; they are stage diagnostics rather
than a reduced-cost relation collector. The Sage runtime receipt is
[recorded](sage_runtime_info.json), and the
[verification receipt](verification_result.json) checks frozen hashes,
row counts, rank accounting and positive retention. The Lean module
builds with the pinned 4.34.1 toolchain and its `#print axioms` output
appears in [lean_check.log](lean_check.log).

The exact W20 subset of the proposed N131 W33 source already contains
132,045 valid pair codes and 528,180 signed states. Even a hypothetical
constant-cost width-eight prefix gate would have at least
`ceil(132045/8)=16,506` nonempty blocks to consider on that subset.
The current enumerative gate still touches every state, so it does not
change the prior [serial work boundary](../n41_w11_exact_two_pair_oracle_20261018/RESULT.md).
`candidate_id` remains `null` until a complete measured IC pipeline is
specified.

The next experiment should derive the width-eight affine enclosure
from a symbolic description of the three free code bits and the two
signed branch bits, measure its per-block target cost against scanning
all states, and retain the positive residual. If its construction still
requires the 32 point differences or if its enclosure has rank 41 on
the frozen controls, this gate is exhausted for the present method.
