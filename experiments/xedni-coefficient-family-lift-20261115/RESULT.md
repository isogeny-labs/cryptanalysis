# Rational-lift replay for the bounded two-point coefficient family

The frozen CRT lift laws produce 4 centered and 11 shifted rational relation
rows across the eight-field, 14-vector panel. All 15 occur for `(1,2)` or
`(2,1)`; the other 11 nonzero-sum directions have zero rational hits in
these accepted curves. The centered `(2,1)` rows are point-order swaps of
the two existing `(1,2)` rows at `p=47`. The shifted arm adds `(2,1)` hits
at `p=101` and `p=211`, where its `(1,2)` arm has none.

| Base prime | Subgroup `r` | Accepted reduced-family rows per arm | Centered rational rows | Shifted rational rows |
| ---: | ---: | ---: | ---: | ---: |
| 47 | 43 | 408 | 4 | 6 |
| 101 | 53 | 504 | 0 | 2 |
| 191 | 53 | 496 | 0 | 0 |
| 211 | 79 | 744 | 0 | 1 |
| 251 | 61 | 568 | 0 | 2 |
| 281 | 73 | 664 | 0 | 0 |
| 347 | 47 | 448 | 0 | 0 |
| 349 | 71 | 672 | 0 | 0 |
| **Total** |  | **4,504** | **4** | **11** |

Each arm retains 30,008 ordered queries, 400,176 public-group vector tests,
6,136 reduced-family relation rows, and 4,504 accepted curves on those rows.
The centered arm charges all 5,282,834 archived auxiliary coefficient probes;
the shifted arm charges 5,328,943. Each of the 4,504 accepted reduced rows
receives one rational group test per arm. Candidate curve reconstruction by
saved ordinal is a replay operation and does not replace the archived probe
cost. The original fixed `(1,2)` positive controls reproduce exactly: two
centered rows and six shifted rows, including their first query indices.

The first extra `(2,1)` hit in the centered arm is at `p=47`, query 503,
after 87,349 within-field auxiliary probes. It is the swapped point order of
the `(1,2)` hit at query 1,259. In the shifted arm, `(2,1)` first hits at
`p=101`, query 205 after 35,452 within-field probes, and at `p=211`, query
5,369 after 981,192 within-field probes. Each relation's exact curve,
lifted points, coefficients, query, vector, and scalar replay is retained in
`result.json`.

## Method and verification

`protocol.json` freezes the input result and arithmetic-source digests, the
14 vectors, both lift laws, row order, original probe charges, and caps. The
pure-Python runner verifies every archived uncompressed row hash. On each
accepted row with a public reduced-family relation, it selects the CRT
residues at the saved search ordinals, reconstructs the rational curve,
checks nonsingularity, point incidence, and reduction at `p`, 7, and 11,
then tests the rational group equation. Positive hits replay the scalar
against the public `Q`. The full archived auxiliary probe totals include
failed attempts and rows without a reduced relation.

The independent audit uses the repository's checked Sage launcher and saved
runtime receipt. It rebuilds every accepted reduced-family curve from the
archived rows, performs all 9,008 rational group tests in Sage, checks every
positive witness and the fixed-vector control, and returns `PASS` with empty
stderr. The Python result and Sage audit are sealed by `SEAL.sha256`.

This is a retrospective test of the two frozen curve-choice laws. It does not
choose new curves or a coefficient-dependent lift for the additional vectors,
and it makes no isolated wall-time comparison. The next falsifier is a
vector-dependent lift rule with its extra construction probes and failed rows
charged explicitly, tested on the same public points and ordered query law.
