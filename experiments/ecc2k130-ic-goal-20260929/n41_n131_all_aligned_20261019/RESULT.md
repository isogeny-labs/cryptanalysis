# Five equal-rotation pair slots: verified N41 relation and bounded N131 query

Five W11 pair slots drawn from one source-point domain produced a verified
decomposition of the frozen N41 public point after 3,172,943 native join
probes. The same layout gives an exact ten-column N131 W29 circuit with
20,446 fewer clauses, 1,755 fewer native XOR rows, and a 33.0% smaller XCNF
than the earlier `(0,0,36,36,72)` layout. A constructed N131 witness passes
every circuit row and an independent Sage group replay. The frozen public
N131 query reached its 600-second wall cap with `BOUNDED_UNKNOWN`.

## Exact inputs and construction

N41 uses `GF(2)[u]/(u^41+u^3+1)`, `y²+xy=x³+1`, subgroup order
549756390943, cofactor 4, and raw public point
`(1936680952394,910597499030)` on `EC1N41Ckb1h7d5e80d3c4d0`.
The transformed [native input](n41_join_input.tsv) retains 281 valid W11
source codes, 1,124 signed pair states per slot, the fixed seed mask 56,
and ten distinct folded source columns per accepted relation. Its five pair
rotations are `(0,0,0,0,0)`. The [frozen native query](n41_query_protocol.json)
used one worker, seed 411153130, at most 20 million probes, a 600-second
wall cap, and a 4-GiB combined RSS cap. The [join receipt](n41_join_result.json)
records a hit in 4.812 seconds of parent wall time and 140,017,664 B
sampled peak combined RSS. The independent [Sage audit](n41_audit_result.json)
rebuilds all ten source points, checks their folded columns, sums their five
pair points to the raw target, and checks the fourfold subgroup projection.
Its canonical source codes are `[425,527,650,672,947]`.

N131 uses `GF(2)[u]/(u^131+u^13+u²+u+1)` and the same curve equation on
`EC1N131Ckb1heb5f1998f20b`. The frozen raw public point is
`(877610862732227974378969808549299291499,
2063336771837286479337213121437715536874)`; its fourfold subgroup
point is in the [public protocol](../n131_w23_sixpair_public_sat_20261017/protocol.json).
Each pair uses the same W29 source domain with seed mask 898618 and 28
canonical code bits. The separately recorded full W29 census contains
67,109,836 valid codes. The exact 2,093 valid cross-code folded-orbit
collision pairs are excluded for every pair of slots. Strictly increasing
source codes make all ten same-code exclusions and the reverse orientation
of each collision pair redundant. This is a permutation symmetry argument
because all five slots have the same source predicate and rotation.

| N131 circuit diagnostic | Paired-aligned `(0,0,36,36,72)` | All-aligned `(0,0,0,0,0)` |
| --- | ---: | ---: |
| Variables | 121,268 | 119,677 |
| CNF clauses | 274,794 | 254,348 |
| Native XOR rows | 42,402 | 40,647 |
| XCNF bytes | 20,644,230 | 13,825,116 |
| Encoded collision exclusions | 41,860 | 20,930 |
| Strict ordering constraints | 2 | 4 |
| Constructed assignment | Pass | Pass |

The [build protocol](build_protocol.json) pins source hashes, the collision
table, public point, constructed control, and checked Sage runtime. The
[build receipt](build_result.json) contains the exact formula and wire hashes.
The [constructed group control](n131_all_aligned_control.json) was derived
from previously audited pair points; [independent replay](control_replay.json)
rebuilds the leaves from masks, checks ten distinct folded columns, and
checks the raw group sum. This control is a circuit correctness test, not an
ordinary-query yield estimate.

## Bounded public search

The [paired stage protocol](probe_protocol.json) fixes the same N131 public
point, solver binary, one worker, a 60-second cap per encoding, a 4-GiB RSS
cap, and paired-aligned then all-aligned order. Both rows in the
[probe receipt](probe_result.json) ended at their wall cap:

| 60-second stage diagnostic | Paired-aligned | All-aligned |
| --- | ---: | ---: |
| Wall seconds | 60.031 | 60.013 |
| Sampled peak combined RSS | 638,271,488 B | 468,975,616 B |
| Last flushed restart / reported conflicts | 1,009 / 521K | 897 / 414K |
| Status | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |

The all-aligned encoding reduced sampled memory in this pair. Conflict
counts are solver diagnostics; the two source schedules define different
search spaces, and neither bounded row supplies relation yield or a
single-target DLP time. The [first](probe_first_attempt_failure.json),
[second](probe_second_attempt_failure.json), and
[third](probe_third_attempt_failure.json) attempts preserve disk-full
failures separately from solver outcomes. Their streams and partial receipt
remain beside the successful pair.

The [public query protocol](query_protocol.json) fixes one worker, a
590-second solver limit, a 600-second parent wall cap, and 4-GiB sampled
combined RSS. The [query receipt](query_result.json) and raw solver streams
record 600.059 seconds, 738,902,016 B sampled peak combined RSS, a wall-cap
stop, and no SAT or UNSAT terminal line. The last flushed restart reported
approximately 4.791 million conflicts. Its `BOUNDED_UNKNOWN` status is a
censored search result. [Terminal audit](terminal_audit.json) rechecks the
source, formula, stream, and proof hashes. The N131 independent public-model
replay is prepared in [replay_model_sage.py](replay_model_sage.py) for a future
SAT model.

## Formal proof map and next experiment

[AllAlignedOrder.lean](AllAlignedOrder.lean) is pinned to Lean 4.34.1.
`sort_preserves_sum` proves that sorting any finite list of distinct-coded
points produces a strictly ordered permutation with the same commutative
group sum. `sort_preserves_validity` proves that every sorted point retains
a shared per-slot validity predicate. These theorems justify ordering all
five equal-domain, equal-rotation pair states; the exact folded-column
collision exclusion and Sage group model remain implementation checks.
`lean AllAlignedOrder.lean` passed, and `#print axioms` reported only
`propext` and `Quot.sound` for both results. `lean4checker --fresh` was
unavailable on this host.

The next layout test is `(0,0,0,36,36)` at N131, with the corresponding
`(0,0,0,12,12)` N41 control. It keeps an ordered triple and pair while
restoring a second Frobenius source span. Test the frozen N41 public point
first, then build and cap the N131 public circuit only if the ordinary N41
control is independently verified. `candidate_id` stays `null` while the
factor-base log system, target descent, and same-point rho comparison are
unmeasured.
