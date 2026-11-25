# Equal-rotation source ordering for the N41 two-quadratic gate

**Contribution.** An exact ordering rule for the first two equal-rotation
source slots adds 30 Boolean variables and 149 clauses to the frozen
two-quadratic five-pair circuit. Its complete eight-bit comparator
truth table and the archived positive control pass. At a frozen
20,000-conflict solver boundary, ordering reduced decisions from
31,602 to 28,136 in each paired arm, a ratio of **0.890**. The
one-worker public N41 query reached its 600-second wall cap with
recorded status `BOUNDED_UNKNOWN`, so the improvement remains a stage
diagnostic and is not promoted to N131.

## Exact construction and proof

The curve is `EC1N41Ckb1h7d5e80d3c4d0`, with
`GF(2)[u]/(u^41+u³+1)`, subgroup order `549756390943`, and public point
`(1936680952394,910597499030)`. The five W9 pair slots have rotations
`(0,0,12,12,24)`. The first two source code domains are identical;
their first-three-pair F4 equation is symmetric in the corresponding
pair roots. Swapping the complete first and second pair states preserves
the first-three group sum and later constraints. Distinct valid pair
states in those slots have distinct codes under the existing
disjoint-column rule, so every represented relation has an orientation
with `code0 < code1`. The [proof map](PROOF_MAP.md) gives the Lean-checked
F4 and ordering results and states the concrete curve bridge.

The [builder](build.py) appends a linear-size unsigned comparator to the
hash-pinned [reference formula](../n41_w9_final_pair_quadratics_20261018/formula.xcnf).
It exhaustively evaluates all 65,536 pairs of eight-bit inputs against
the generated gate clauses, then checks the 33 archived controls.
The archived positive has ordered codes `(93,228)` and remains admitted.
The [build protocol](build_protocol.json) pins source hashes before
execution.

| Circuit | Variables | Total CNF plus XOR constraints | Bytes |
| --- | ---: | ---: | ---: |
| Reference two-quadratic | 128,017 | 353,073 | 11,020,550 |
| [Ordered](build_result.json) | 128,047 | 353,222 | 11,023,787 |

## Frozen solver comparison and public query

The [probe protocol](probe_protocol.json) fixed serial
`quadratic/ordered/ordered/quadratic` arms on the same point, one
CryptoMiniSat 5.14.7 worker, a 20,000-conflict cap, 180-second parent
cap and 4-GiB sampled-RSS cap. All four arms ended
`INDETERMINATE_CONFLICT_CAP` with monitoring intact. The ordered arms
used 28,136 decisions versus 31,602 for each paired reference, and
wall ratios were 0.831 and 0.864. Both passed the predeclared
promotion gate of at most 90% paired decisions and 125% paired wall.
The [probe receipt](probe_result.json) retains raw solver streams.

The [query protocol](query_protocol.json) then froze the same public
point, ordered formula, solver binary and flags, one worker, a
590-second solver limit, 600-second parent cap and 4-GiB RSS cap.
All five source codes, the preceding reciprocal and both final
quadratic roots were unpinned apart from the exact first-code ordering.
The [query receipt](query_result.json) records:

| Measured component | Value |
| --- | ---: |
| Reference target-dependent build plus ordered build/audit | 53.083 s |
| Solver launch, search and parent stop | 600.024 s |
| Charged stage total | **653.108 s** |
| Sampled peak combined RSS | 311,787,520 B |
| RSS samples / monitor errors | 5,626 / 0 |
| Last flushed restart / approximate conflicts | 1,481 / 949,000 |
| Status / stop | `BOUNDED_UNKNOWN` / `WALL_CAP` |

The solver stream has no SAT, UNSAT or INDETERMINATE terminal line.
Conflict and decision counts measure search progress at bounded work;
they are not relation-yield observations. The build interval
conservatively includes the exhaustive 65,536-case comparator audit.
Independent model replay was conditioned on SAT and therefore was not
invoked. The [verifier](verify.py) passes source hashes, comparator
counts and controls, Lean output, probe gate, query streams, and the
resource receipt. These wall times are exploratory ordinary-host stage
measurements. `candidate_id` remains `null`.

## Next discriminator

The ordering saved about 11% of fixed-conflict decisions but left the
ordinary public query capped. The next search should change the
first-three-pair constraint itself, such as an exact partial-sum filter
or a lower-cost F4 encoding, and compare it against this frozen
two-quadratic reference. A favorable N41 gate must be followed by an
independently verified ordinary N131 public-point relation within
one worker, 600 seconds and 4 GiB.
