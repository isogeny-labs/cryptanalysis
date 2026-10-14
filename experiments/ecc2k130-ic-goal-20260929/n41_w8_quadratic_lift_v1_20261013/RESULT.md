# Quadratic lift exactly screens the width-16 witness roots

For the frozen N41 W8 width-16 witness region, the 128 right-hand reciprocal coordinates are independent after a degree-two Boolean lift into 862 features. The lifted-span test accepted **one of 240** target-conditioned S3 root proposals; direct membership in the 128-value right set accepted that same one. Independent checked Sage rebuilt the partial sums, lift rank, roots, and pass counts.

The lift maps a 41-bit reciprocal `d` to `(1, d_i, d_i d_j)` for all `0 ≤ i < j < 41`. Its 862 coordinates are exactly one constant, 41 linear, and 820 squarefree quadratic features. The native worker constructs the width-16 left and right two-pair partials from the pinned 30,952-state-per-slot table and uses the raw public target at preimage index 1. It builds a GF(2) basis of lifted right reciprocals, solves the target-conditioned S3 quadratic for each distinct left reciprocal, and tests each root against the lifted span and exact set. The control retains the known relation at slot IDs `(17678,155,6169,16990)`.

| Quantity | Native | Independent Sage |
| --- | ---: | ---: |
| Left/right distinct reciprocals | 120 / 128 | 120 / 128 |
| Right quadratic-lift rank | 128 | 128 |
| S3 root proposals | 240 | 240 |
| Lift passes / exact-set hits | 1 / 1 | 1 / 1 |
| Lift false positives among proposals | 0 | 0 |
| Monitored wall | 1.745292291 s | 35.166016083 s |

Both runs used one worker and 120 s / 4 GiB caps. Native sampled combined RSS was 32,686,080 bytes; Sage sampled combined RSS was 263,651,328 bytes with intact monitoring. `protocol.json` and `audit_protocol.json` bind the code, binary, source table, earlier census, and checked Sage runtime. `python3 -B verify.py` checks hashes and both result records. This is a component screen with `candidate_id: null`.

The lift demonstrates an exact filter for this selected root set, but its basis is built by enumerating all 128 right reciprocals and its online query evaluates all 240 root proposals. In this case a direct hash set performs the same membership decision with less work. The next useful experiment is therefore a **region-level symbolic test** that avoids forming the right partials or iterating the left roots. Without such a procedure, larger quadratic feature spaces by themselves do not reduce the W8 search cost.

No new general theorem is asserted. The Boolean one-hot structural theorem and its Lean proof are in the preceding quadratic-family experiment; this result is a finite audited computation.
