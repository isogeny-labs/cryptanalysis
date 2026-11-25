# Full quadratic feature rank for N41 width-11 right partial sums

**The width-11 two-pair right-partial family has full 862-dimensional
degree-at-most-two coordinate-feature rank.** A frozen sample reached rank
862 after 865 accepted distinct-code partial sums. An independent
integer-polynomial field implementation reconstructed all 862 basis
witnesses from their source codes and signed pair points, recomputed the
Frobenius-rotated group sums and reciprocal coordinates, and confirmed the
rank. Consequently, no nonzero Boolean polynomial of degree at most two
in the 41 reciprocal-coordinate bits vanishes on this entire family.

## Exact family and certificate

The field is `GF(2)[u]/(u^41+u^3+1)` and the curve is
`y²+xy=x³+1`, curve ID `EC1N41Ckb1h7d5e80d3c4d0`, subgroup order
549,756,390,943, cofactor four. The previously frozen width-11 fixed-seed
source has 281 valid canonical codes and 1,124 signed pair outputs. This
experiment forms the two rightmost pair slots of the five-pair N41 S3
tree: their Frobenius rotations are 12 and 24. It requires distinct source
codes, adds their rotated curve points, excludes the identity and zero-x
exceptional results, and records the reciprocal of the sum's x coordinate.

For a reciprocal coordinate `x` encoded as 41 polynomial-basis bits,
the feature vector is

`φ(x) = (1, x₀, …, x₄₀, x₀x₁, …, x₃₉x₄₀) ∈ GF(2)^862`.

The [protocol](protocol.json) pins the checked Sage runtime, source code,
previous exact code census, fixed sample seed, 4,000-attempt limit and
180-second cap. The [result](result.json) contains each rank-increasing
witness with two signed pair points, codes, branch indices, partial
reciprocal coordinate, and pivot. The [independent verifier](verify_rank.py)
uses its own integer `GF(2)[u]` multiplication, inversion, trace,
half-trace, curve addition, Frobenius, and feature-rank implementation;
its [receipt](verify_result.json) records the full replay.

| Measurement or check | Result |
| --- | ---: |
| Exact signed pair states / canonical codes | 1,124 / 281 |
| Frozen random attempts / accepted partials | 875 / 865 |
| Rank-increasing basis witnesses | 862 |
| Degree-at-most-two feature dimension / measured rank | 862 / 862 |
| Source construction / total checked-Sage arithmetic interval | 21.405 / 25.119 s |
| Sage raw maximum RSS | 264,962,048 B |
| Independent source-code and group-sum replay | 862/862 basis rows; 280 source codes reconstructed |
| Independent verifier interval | 8.698 s |

The coordinate-rank statement is exact once these 862 point witnesses are
accepted. Any degree-at-most-two Boolean polynomial has a unique 862-bit
coefficient vector and evaluates as its dot product with `φ(x)`. A
polynomial vanishing on every family member vanishes on the 862
independent witnesses, so its coefficient vector is zero. The
[proof map](PROOF_MAP.md) identifies the Lean-checked structural implication
and the independently replayed finite certificate.

This excludes an output-only quadratic equality for this exact raw-point
two-pair family. It does not evaluate conditions that retain the source
codes, couple several unresolved partial sums, or use higher-degree
features. The earlier [W6 suffix audit](../n41_suffix_quadratic_span_20261012/RESULT.md)
found full quadratic rank in a trace-zero coordinate hyperplane; this
width-11 family reaches the entire 862-dimensional quadratic feature
space.

## Next experiment and promotion gate

The next compact-filter experiment should keep source-product variables
and the public target residual in the same constraint, then measure
whole-family rejection before enumerating pair combinations. The
fixed-code two-quartic [joint equation](../n41_w9_two_quartic_resultant_20261017/RESULT.md)
is an exact starting point; the missing step is a compact free-code
representation whose query work fits the resource cap. This rank result
is a stage diagnostic, `candidate_id: null`. N131 promotion still requires
an ordinary unpinned N41 relation with independent replay, followed by
its own frozen one-worker, 600-second, 4-GiB query and full accounting.
