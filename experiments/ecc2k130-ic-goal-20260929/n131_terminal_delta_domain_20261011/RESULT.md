# Terminal-32 leaves a broad N131 pair-product difference domain

The frozen 32-state terminal pool contains eight distinct source edges with four point-sign choices each. For every terminal edge, a second same-seed W18 pair with disjoint folded columns still has **33,188–33,190 distinct unrotated product differences**. Across the eight terminal edges, the union contains **118,107 of 131,072** possible 17-bit difference codes, or **90.10848999%**. Terminal-state selection alone therefore gives no narrow difference domain for a call-per-difference algorithm.

The [protocol](protocol.json) fixes curve EC1N131Ckb1heb5f1998f20b over GF(2)[t]/(t^131+t^13+t²+t+1), seed mask 212, the archived W18 folded-column source, the exact terminal pool, one worker, 120 seconds, and 4 GiB. The 33,191 eligible source edges are the same input counted by the [terminal source receipt](../n131_w18_terminal_fiber_20261011/source_count.json). No target point or proposed four-point output is supplied to this source-domain census; its candidate ID remains null.

For a canonical source code c, the pair product is an F₂-linear map L(c). If q is a selected terminal code, the product difference is L(c)+L(q)=L(c XOR q). The producer excludes edges that share either terminal folded column, then counts the surviving difference codes. Its exact domain counts are:

| Terminal code | 4 | 10 | 17 | 18 | 22 | 24 | 28 | 29 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Allowed differences | 33,188 | 33,188 | 33,190 | 33,189 | 33,189 | 33,189 | 33,188 | 33,188 |

The eight domains contain **265,509** allowed edge–terminal pairings in total. Their multiplicity histogram has 34,204 codes present in one domain, 40,591 in two, 27,764 in three, 11,655 in four, 3,220 in five, 601 in six, 71 in seven, and one code in all eight. The intersection code is 52,475. Four sign choices of one terminal edge do not change its pair product, so they do not shrink or expand these code domains.

The [producer result](result.json) completed in 2.234 seconds with 80,904,192 B peak RSS. The [independent field audit](audit.json) used the frozen pair-product implementation to verify all **33,191** actual field products against w²+sw, proved the 17-vector product basis has full rank, and checked all **265,509** allowed field differences against the code-XOR representation. It independently rebuilt the domain histogram with a 131,072-entry counter in 42.015 seconds and 47,284,224 B peak RSS. Both intervals are local arithmetic diagnostics on an unisolated host. The [terminal verifier](verification.json) binds source, protocols, counts, resource caps, and independent result.

At least 33,188 difference candidates remain for **one** selected terminal edge before upper-chain target information is used. A simple call-per-difference strategy would have at most 18.08 milliseconds per call inside a 600-second query, even if every other target-dependent phase were free. That is a workload requirement, not a lower bound on a future implementation.

The terminal slot is rotated by 128 while the first free slot is at rotation zero. The [equal-rotation fixed-difference quotient](../n131_fixed_difference_root_20261011/RESULT.md) therefore cannot be inserted directly between those two slots. The next exact operator should use the [general rotated resultant](../n131_w15_rotated_fouratom_inverse_20261010/RESULT.md): fix the terminal product, solve its degree-at-most-eight polynomial in the other product for a proposed four-point output, and charge the generation of that output from the public target. Test it on an unpinned N41 relation before projecting complete N131 one-worker work and memory.
