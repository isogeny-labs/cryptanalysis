# One-field-element root witness for the N41 target-conditioned gate

## Contribution

One free field element `w` now generates the normalized Bezout vector
`(1,w,w²,w³)` in the five-pair N41 Boolean circuit. This keeps every genuine
shared-root decomposition and removes 82 free input bits relative to the
three-coordinate kernel witness. The archived relation satisfied the circuit,
and all 32 frozen reachable controls were rejected. The resulting XCNF has
**140,627 variables and 386,839 total constraints**. A frozen four-arm solver
probe found only a **2.48% decision reduction** and paired wall ratios of
**1.380** and **1.336** against the normalized-kernel circuit at the fixed
conflict boundary. The predeclared full-query gate failed.

## Exact method and proof

The field is `GF(2)[u]/(u^41+u^3+1)` and the curve is `y²+xy=x³+1`, curve ID
`EC1N41Ckb1h7d5e80d3c4d0`, subgroup order `549756390943`. The public point
is `Q=(1936680952394,910597499030)`. The source has five aligned W9 pair
rotations `(0,0,12,12,24)`, 71 allowed codes per slot, and four signed states
per code. The circuit keeps five free eight-bit code words, the preceding
41-bit reciprocal `z`, and one free 41-bit shared-root witness `w`.
Its complete IC `candidate_id` is `null`.

Let `f` and `g` be the two source-valid final pair quartics and `B` their
symmetric four-by-four Bezout matrix. The new gate is
`B · (1,w,w²,w³)ᵀ = 0`. A shared root gives these four equations by the
quartic Bezout row identity. Conversely, a satisfying root vector gives
`det(B)=0` by the cofactor identity; the standard determinant/resultant
identity and the recorded four-root split of the final pair quartic yield a
common field root. The [proof map](PROOF_MAP.md) links the checked Lean
structural implications and states the remaining formalization bridge.

## Frozen circuit check

The [build protocol](build_protocol.json) froze the source, fixture, panel,
prior kernel audit and checked [Sage runtime](sage_runtime_info.json) before
the builder ran. The [builder](build.py) retained the first-three-pair F4 norm,
all allowed-code restrictions and folded-column collision clauses. It checked
all 33 frozen source-valid assignments, including a complete satisfying
assignment for the archived relation. Its [receipt](build_result.json) records
37.379 seconds including controls, 160,890,880 bytes self peak RSS under the
300-second/4-GiB envelope.

| Formula | Free field witness bits | AND gates | Variables | CNF clauses | Native XOR rows | Total constraints | Bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Normalized kernel | 123 | 123,078 | 141,260 | 371,134 | 17,978 | 389,112 | 12,710,695 |
| Structured root | **41** | **122,217** | **140,627** | **368,551** | 18,288 | **386,839** | **12,708,182** |

The [read-only verifier](verify.py) checks frozen hashes and all 33 decisions,
the exact formula counts, and that none of the 122 code, `z` or `w` input bits
is directly fixed by a unit clause.

## Frozen fixed-conflict comparison

The [probe protocol](probe_protocol.json) fixed one CryptoMiniSat worker,
20,000 requested conflicts, a 170-second solver limit, a 180-second parent
cap, 4-GiB sampled combined RSS and serial kernel/root/root/kernel order.
All arms ended `INDETERMINATE_CONFLICT_CAP`; no monitor or resource cap fired.
Every raw stream and per-arm result is retained with the
[aggregate receipt](probe_result.json).

| Arm | Gate | Wall seconds | Conflicts | Decisions | Propagations | Peak sampled combined RSS |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 0 | Kernel | 42.415 | 20,001 | 172,961 | 52M | 110,510,080 B |
| 1 | Root | 58.511 | 20,002 | 168,673 | 49M | 94,420,992 B |
| 2 | Root | 48.263 | 20,002 | 168,673 | 49M | 138,690,560 B |
| 3 | Kernel | 36.113 | 20,001 | 172,961 | 52M | 99,123,200 B |

The frozen promotion gate required every monitor to pass, both root arms to
use at most 80% of adjacent kernel decisions, and both paired root/kernel
wall ratios to be at most 1.25. The observed decision ratios were 0.975 in
both pairs, and wall ratios were 1.380 and 1.336. The gate therefore declined
a 600-second ordinary query. These fixed-conflict observations are a solver
stage diagnostic; their status remains `INDETERMINATE_CONFLICT_CAP`.

## Next discriminator

The structured Bezout vector still computes a complete matrix and four
matrix-vector products. The next exact circuit can impose the two source
quartic evaluations `f(w)=0` and `g(w)=0` directly on the same free `w`.
Freeze its source and panel, compare formula construction, and run the same
alternating fixed-conflict boundary before another ordinary N41 query. This
tests whether removing the intermediate Bezout matrix gives a materially
smaller and better propagating target-conditioned gate. N131 promotion still
requires the unpinned N41 relation and the source-bound 600-second/4-GiB gate.
