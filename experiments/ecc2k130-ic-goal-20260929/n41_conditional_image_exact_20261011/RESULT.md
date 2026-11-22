# Exact conditional product-image gate for N41 two-pair completion

For each nonzero W6 pair seed, **six parity checks and a nonzero product clause describe exactly the 31 products of distinct nonzero source masks**. The product-image constraint can therefore be enforced in the target-conditioned two-pair XCNF without computing the bilinear source product inside the circuit. Exhaustive integer-field enumeration verified the identity for all 63 seeds at each of the two Frobenius rotations, and the frozen positive assignment satisfies the complete circuit.

Let the six-bit first mask be `a`, the second mask be `a xor s`, and `s != 0`. In the eleven-dimensional product span, `p = a² + sa` is the image of a binary linear map with kernel `{0,s}`. Its image has 32 elements, one of which is zero. Excluding `a=0` and `a=s` leaves exactly 31 admissible products. For each fixed `s`, a six-row annihilator of the image is computed once; a seed selector guards its six native-XOR checks. The two pair equations and the public-target `S3` equation are unchanged from the [derivative circuit](../n41_derivative_pair_sat_20261011/RESULT.md). The candidate remains a component design (`candidate_id: null`).

The [frozen protocol](protocol.json) binds the code, XCNF inputs, solver binary, one worker, 35-second parent cap, and 4-GiB RSS ceiling. The [audit](audit.json) verifies source and formula hashes, active solver search, the parent caps, and absence of terminal solver lines. The positive input is the known N41 public-row middle point; control 23 is a target-derived relaxed group hit that misses the exact source-pair domain. The exact positive full assignment was checked before search, and all 63 seed images at each rotation were enumerated independently of SAT.

| Circuit on positive input | Variables | AND gates | Clauses | Native XOR rows | XCNF bytes | Unpinned search |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Free-product derivative | 3,082 | 1,844 | 5,659 | 1,122 | 178,738 | `BOUNDED_UNKNOWN` at 35 s in prior gate |
| Bilinear source-image | 3,186 | 1,916 | 5,879 | 1,164 | 185,896 | `BOUNDED_UNKNOWN` at 35 s in prior gate |
| Conditional linear image, exact source policy | 3,602 | **1,844** | 7,299 | 1,516 | 213,370 | `BOUNDED_UNKNOWN` at 35.116 s |

The target-derived control also reached `BOUNDED_UNKNOWN` at 35.085 s. Both runs began active CryptoMiniSat search and stayed under 55 MB combined RSS. The exact conditional gate removes 72 AND gates compared with the bilinear source-image circuit, while adding 416 variables, 1,420 clauses, 352 XOR rows, and 27,474 XCNF bytes on the positive input. These ordinary-host runs are solver diagnostics; the shared cap does not establish a runtime ordering between the circuits.

The preceding [linear-image preflight](../n41_conditional_image_20261011/protocol.json) retained product zero and therefore represented the full 32-element image. It recorded the same capped search statuses. This follow-up enforces the actual nonzero source-mask policy and is the exact version of the method.

The next experiment should target **left-output generation** in the N131 W14 construction. A conditional image gate still leaves both pair-output coordinates free in SAT, while the [N41 inverse join](../n41_linearized_full_bucket_scan_20261011/RESULT.md) is already exact and complete when a middle point is supplied. A proposed N131 generator should be tested by counting its target-dependent left candidates, exact source-pair witnesses, preparation bytes, and ordinary relation yield within the frozen one-worker 600-second/4-GiB envelope before SAT encoding work is resumed.
