# Fresh N41 public-point relation from an exact target-conditioned join

The two-plus-one indexed join found and independently verified a ten-leaf
factor-base relation for a **fresh subgroup point** under the frozen W9 source.
The target came from an independently seeded scalar fixture dated before
this join experiment; its scalar was outside the worker input and clock.
The native worker found the relation at Frobenius orientation 0 after
19,651,865 target-conditioned probes, in **9.423 s parent wall** with
35,799,040 B sampled combined RSS. The [checked-Sage audit](audit_result.json)
reconstructed every leaf, checked ten distinct folded columns, and verified
the raw sum and cofactor-four subgroup point.

## Frozen inputs and exact join

The curve is `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[u]/(u^41+u^3+1)`, with equation `y²+xy=x³+1` and subgroup order
`549756390943`. The [protocol](protocol.json) pins the exact 5×284 W9
signed-pair source, existing native binary and source, fresh target fixture,
input TSV, one worker, 600-second parent cap and 4-GiB combined-RSS cap.
The raw target is `(1476947961888,1253336411133)` and its subgroup point
is `(339942650206,165641111719)`. The independent input law was one
`random.Random(202610152219)` scalar in `[1,r)`; the prior
[fresh-target protocol](../n41_target_root_join_20261015/fresh_protocol.json)
fixes that point and its validation-only scalar sidecar. The
[checked Sage runtime](sage_runtime_info.json) was saved before execution.

The native join hashes 79,424 disjoint-column sums from slots 0–1 and
precomputes 79,424 sums from slots 3–4. For every slot-2 state and right
sum, it probes `T − slot2 − right` in the left hash, expands a left witness
only on a hit, checks all ten folded columns distinct, and recomputes the
exact group sum. Frobenius orientations are tried in order. This is the
same hash-pinned worker used by the archived-target control, now with only
the TSV target header changed. Its exactness implication is covered by the
previous [Lean proof](../n41_target_conditioned_2p1_join_20261018/TwoPlusOneJoin.lean).

| Fresh public-point run | Recorded value |
| --- | ---: |
| State rows validated | 1,420 |
| Left and right pair entries | 79,424 each |
| Target-conditioned probes to hit | 19,651,865 |
| Column-rejected `(slot2,right)` combinations | 623,744 |
| Raw left-key matches through hit | 1 |
| Frobenius orientation and state IDs | `0`, `(122,219,255,80,188)` |
| Native left/right table completion | 0.0345 s / 0.0638 s |
| Native hit time from worker start | 9.394 s |
| Parent wall, including launch and input loading | 9.423 s |
| Sampled parent-plus-worker peak RSS | 35,799,040 B |

The [independent audit](audit_result.json) used Sage field and group
arithmetic rather than the native worker arithmetic. It reconstructed the
five signed pairs from the 10 masks and signs, matched every stored rotated
state point, checked the ten folded columns, summed to the oriented raw
target, transported back to the supplied raw point, checked cofactor-four
transport, and replayed the validation-only scalar against the frozen
generator. [verify.py](verify.py) checks all source hashes, monitoring and
result receipts and returned `REPLAY_PASS`.

The first wrapper launch used system Python and exited before starting the
worker because `psutil` was absent; [its receipt](attempt1_failure.json)
preserves that environment failure. Running the unchanged frozen wrapper
through the repository's checked Sage Python supplied the monitor dependency.

This is one ordinary-host relation-collection measurement. The source
tables were prepared before the measured interval, and the displayed parent
wall includes native loading and index construction. `candidate_id` remains
`null` because this component does not specify relation-matrix and target
recovery stages. The fresh target was previously used in a smaller N41
seven-slot root-join control, where that different source found zero
coordinate hits; this W9 result measures a distinct, larger source policy.

## Next construction gate

The W9 direct pair table does not fit the N131 W29 source projection:
the prior [N41 indexed-join result](../n41_target_conditioned_2p1_join_20261018/RESULT.md)
estimates about 273 million signed states per N131 slot and roughly
`7.47×10^16` pair entries before filtering. The next test should replace
the explicit two-code pair index with a **target-conditioned algebraic
membership oracle** that preserves exact witnesses while code rectangles
remain unresolved. On N41, freeze the same fresh point, positive witness,
and negative probe panel; compare oracle answers to exhaustive pair keys,
including all misses and work per query. Promote only an oracle with a
measured source-size and 600-second/4-GiB N131 cost envelope. For the
Q1358 15-leaf N131 workload, the separate need remains a joint constraint
across several middle partial sums, as the exact pair lookup alone supplies
too few target-compatible probes.
