# M31 polynomial intersection on archived root sets

When a polynomial splits into known distinct linear factors, its common roots with a query polynomial can be found by evaluating the query on the known roots. A reusable subproduct tree supports fast multipoint evaluation. The Lean file proves the root predicate for any field polynomial GCD and specializes it to a known basis root.

Local arm64, FLINT 3.6.0, 12 deterministic dense monic queries per size, each of degree twice the number of roots. The inputs use the archived structured roots at depths 12 and 15. The queries have zero, one or two deliberately inserted basis factors, cycling by block. Each query was timed once per method with alternating order. Untimed verification checked the zero mask against the computed GCD on every basis root, including a check against its degree. All 24 masks agreed.

| Basis roots | Median GCD ms | Median evaluation ms | Median paired GCD/evaluation | Evaluation wins |
|---:|---:|---:|---:|---:|
| 4,096 | 4.925 | 3.749 | 1.582 | 9/12 |
| 32,768 | 82.291 | 39.408 | 2.039 | 12/12 |

The benchmark starts from the same explicit roots for both methods. At 32,768 roots, constructing the basis polynomial took 7.201 ms and building the evaluation tree took 5.752 ms. Adding the observed setup once to each query gives a derived median paired ratio of 1.950. These single setup observations include allocator and library state. The GCD timer ends at the returned polynomial, and the evaluation timer ends at the returned array of values. Output conversion and verification are outside both timers.

These measurements use generated query coefficients. They do not establish performance on actual resultants or charge the extra root materialization that a map-only caller would need. The earlier query panel and this arithmetic microbenchmark use different inputs and timings; their ratios cannot be combined into an observed speedup.

Reproduce with `bash replay.sh` in this directory, with a C compiler, pkg-config, FLINT 3.6.0 and Python 3. Replay RootIntersection.lean using mathlib with Lean 4.34.1.
