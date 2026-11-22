# Shared XOR seed and source difference do not compress N41 four-point outputs

An exact N41 census shows that a four-point block with two source pairs sharing XOR seed `s` retains its full finite output family after the second source difference `u` is fixed. Among **378 `(s,u)` keys with multiple valid four-mask quartets**, zero keys had a common sign-zero output and zero had identical all-sign output sets. Every one of the **25,920** valid signed assignments produced a different group output *within its own `(s,u)` key*. An independent checked-Sage implementation matched every aggregate count and replayed an explicit two-quartet counterexample.

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over `GF(2)[t]/(t^41+t³+1)` on `y²+xy=x³+1`. The input is the previously audited W6 rotation-zero source with **32 rational masks**, **26 folded columns**, and projected prime-subgroup points. For a nonzero pair seed `s`, take two disjoint edges `(a,a+s)` and `(b,b+s)` with four distinct folded columns. Their canonical source difference is `u=min(a+b,a+b+s)` in the six-bit mask space. All sixteen point-sign choices are included. This is a factor-base geometry test with `candidate_id: null`; no target point is selected in the census.

The proposed compression would have made the group output depend only on `(s,u)`, allowing a whole family of quartets to share one upper-chain state. The census instead found:

| Exact rotation-zero quantity | Count |
| --- | ---: |
| Four-mask quartets after distinct-column filtering | **1,620** |
| Occupied `(s,u)` keys | 1,188 |
| Keys with 1 / 2 / 3 quartets | 810 / 324 / 54 |
| Keys with multiple quartets | **378** |
| Repeated keys with one sign-zero output | **0** |
| Repeated keys with identical sixteen-sign output sets | **0** |
| Signed assignments / distinct outputs summed within keys | **25,920 / 25,920** |

For example, `s=1, u=4` admits quartets `(2,3,6,7)` and `(58,59,62,63)`. Their sign-zero projected output points are respectively `(1499587031670,469641006212)` and `(861758057320,1698183614183)`. The [integer-field producer](../n41_same_seed_derivative_collapse_20261011/run_v2.py) enumerated all four-mask families, checked every group output on the curve, and cached the four signed sums of each source edge. Its [complete receipt](../n41_same_seed_derivative_collapse_20261011/result_v2.json) records 19.041 seconds and 19,808,256 B peak RSS under one worker, 120 seconds, and 4 GiB. The [independent Sage replay](sage_audit_v2.json) used separately constructed field and curve arithmetic, rebuilt every quartet and all sixteen signs, and matched every count in 21.289 seconds with 223,444,992 B peak RSS. Both intervals are local arithmetic diagnostics on an unisolated host.

The first producer recomputed each pair sum for every sign assignment and crossed its 120-second guard after completing rotation zero; its [failure receipt](../n41_same_seed_derivative_collapse_20261011/failure_v1.json) preserves the capped status. The cached-pair version uses the same source masks and exact output sets. The first Sage auditor reached the aggregate comparison but compared Python integer histogram keys with JSON string keys; its [failure receipt](failure_v1.json) and frozen source are retained. The versioned auditor normalizes only those keys. The [terminal verifier](verification.json) binds both frozen protocols, failures, complete producer and Sage results, source hashes, cap statuses, and checked Sage runtime.

This result rules out the proposed **source-difference-only** generator for the repeated-rotation geometry: the `(s,u)` label does not identify an upper-chain point or a small common output set even at N41. The next useful test must retain the finite output coordinate or couple two blocks to the *public target* before merging quartets. In particular, a target-conditioned block-pair operator should be compared against the exact N41 inverse join on the same unpinned positive and negative residuals, counting rejected seed families and complete failed-probe work before any N131 promotion.
