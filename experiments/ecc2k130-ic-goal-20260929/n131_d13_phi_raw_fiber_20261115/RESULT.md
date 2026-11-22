# Expanded d13 source: exact raw cofactor distribution

The adjacent-Frobenius image `P + tau(P)` doubles the exact d13 source's
usable point count while keeping the original 4,134 subgroup-log unknowns.
This audit resolves its raw-lift geometry. At each of the ten proposed
Frobenius positions, the union supplies **16,536 raw point choices** and
reaches **all four** rational cofactor classes. Its ten-position ordered
tuple count is approximately balanced across the four raw target fibers.

The exact curve is `y²+xy=x³+1` over `GF(2^131)` in the repository's ONB
representation, with subgroup order
`r=680564733841876926932320129493409985129` and curve ID
`EC1N131Ckb1heb5f1998f20b`. The source is the frozen 13-dimensional
phi-subspace in `d13_exact_geometry_v1.json`. One valid selector gives a raw
point `P` and its negative; the new branch gives `P+tau(P)` and its negative.
All 4,134 valid selectors were enumerated. The prior expanded-base census
established 1,083,108 original and 1,083,108 image subgroup points with no
overlap; the union has 2,166,216 points and 4,134 independent log unknowns.

Let `T4=(1,1)`, a rational point of order four, with `2T4=(0,1)`.
The class of a raw point `R` is `[r]R` in `E[4]`, indexed by
`0,T4,2T4,3T4`. Since Frobenius fixes this rational torsion,
`[r](R+tau(R))=2[r]R`. The [Lean theorem](CofactorImage.lean) checks the
abstract additive implication and the resulting even-class restriction;
the [proof map](PROOF_MAP.md) records the concrete curve bridge and axiom
audit.

| Raw source per Frobenius position | Class 0 | Class 1 | Class 2 | Class 3 | Total |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original | 2,160 | 2,067 | 1,974 | 2,067 | 8,268 |
| `P+tau(P)` image | 4,134 | 0 | 4,134 | 0 | 8,268 |
| Union | **6,294** | **2,067** | **6,108** | **2,067** | **16,536** |

These are exact point counts, with both signs included. The image alone
cannot hit raw target fibers of classes 1 or 3. The union can hit each class.
Distinctness of the original and image projected bases implies distinct raw
point sets, and the previously checked Frobenius orbit geometry gives the
same class counts at each of the ten positions.

The following values divide exact **ordered tuple counts by `r`**. They are
conditional means for one specific raw endpoint under a uniform-distribution
assumption *within* each cofactor coset; they are not observed relation yield.

| Source policy | Leaves | Class 0 mean | Class 1 mean | Class 2 mean | Class 3 mean |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original | 9 | 0.0000663 | 0.0000663 | 0.0000663 | 0.0000663 |
| Union | 9 | 0.034025 | 0.033892 | 0.034025 | 0.033892 |
| Original | 10 | 0.548372 | 0.548372 | 0.548372 | 0.548372 |
| Union | 10 | **562.081269** | **560.984525** | **562.081269** | **560.984525** |

The exact integer counts and 40-digit conditional quotients are in
[`analysis_result.json`](analysis_result.json). The roughly 1,024-fold
ten-leaf combinatorial increase follows from doubling the raw choices at
each position. This is a source-design improvement; SAT encoding cost,
ordinary-query yield, rank, target descent, and paired online time require
measurements on the exact construction.

The primary ONB [census](census.py) finished in 43.492 s and 27,623,424
peak RSS bytes. It checked every original and image point's cofactor class,
the image `x` formula, and commutation with fourfold projection. The
independent polynomial-field [Sage replay](audit_sage.py) checked all 4,134
selectors and matched the ordered class-pair and image-x digests; it
finished in 166.689 s and 253,313,024 peak RSS bytes. Both runs used the
accepted local Sage runtime receipt where Sage was involved. These ordinary
host timings are diagnostics, not isolated IC/rho benchmark results.

The first census implementation reached its frozen 240-second cap by doing
redundant subgroup-order multiplications. Its source, protocol, stderr, and
`CAPPED_240_SECONDS` status remain here. The [v2 protocol](protocol_v2.json)
was frozen before the optimized census and derives sign/image classes by
group laws, retaining sampled direct image checks. The independent Sage
pass independently checked every selector. All caps, source hashes, and
input hashes are recorded in the protocols.

## Next gate

Encode the exact original-or-image raw source with a branch bit for each
leaf and a ten-leaf sum circuit. First test an unpinned ordinary relation
on the corresponding exact N41 construction, with planted correctness
control and full source-bound row verification. Then freeze one N131
ordinary-query run at one worker, 600 seconds, and 4 GiB, preserving all
timeouts and failed attempts. Promote `Q20261115082001` to a canonical
candidate only after the N41 source, N131 formula, complete stage policy,
and source digests are fixed. Its `candidate_id` remains `null` here.
