# Triple-plus-pair W29 layout: verified N41 relation and capped N131 search

An ordered three-pair block plus an ordered two-pair block produced a verified
relation on the frozen N41 public point after 6,320,834 native join probes.
At N131 it gives a 266,665-clause, 41,826-XOR-row W29 circuit with exact
ten-column collision exclusions; a constructed relation satisfies the circuit
and passes independent Sage group replay. The ordinary N131 public query
reached its frozen 600-second cap with status `BOUNDED_UNKNOWN`.

## Exact layout and controls

The N41 control is on `EC1N41Ckb1h7d5e80d3c4d0` over
`GF(2)[u]/(u^41+u^3+1)`, `y²+xy=x³+1`, subgroup order 549756390943,
cofactor 4, and raw public point `(1936680952394,910597499030)`.
Its five W11 pair rotations are `(0,0,0,12,12)`. The
[source transform](transform_result.json) retains 281 valid codes and
1,124 signed pair states per slot. The [frozen join](n41_query_protocol.json)
used one worker, seed 411153130, 20 million probes, a 600-second wall cap,
and a 4-GiB combined RSS cap. It found one hit in 8.885 seconds of parent
wall time, with 139,886,592 B sampled peak combined RSS. The
[independent Sage replay](n41_audit_result.json) reconstructs ten source
points, verifies ten distinct folded columns, sums the rotated pair outputs
to the raw public point, and checks the fourfold subgroup projection.

The N131 circuit is on `EC1N131Ckb1heb5f1998f20b` over
`GF(2)[u]/(u^131+u^13+u²+u+1)` with the same curve equation. Its frozen
public raw point is
`(877610862732227974378969808549299291499,
2063336771837286479337213121437715536874)`; the fourfold subgroup
point is fixed in the [public protocol](../n131_w23_sixpair_public_sat_20261017/protocol.json).
The W29 pair source uses seed mask 898618 and 28 canonical code bits; the
separately recorded full census contains 67,109,836 valid codes. Pair
rotations are `(0,0,0,36,36)`. The first three and last two codes are
strictly ordered separately. Six cross-block same-code exclusions and
33,488 oriented cross-code clauses enforce ten distinct Frobenius-folded
source columns using the exact 2,093-pair collision table.

| Exact circuit diagnostic | Paired-aligned `(0,0,36,36,72)` | Triple-plus-pair `(0,0,0,36,36)` | All-aligned `(0,0,0,0,0)` |
| --- | ---: | ---: | ---: |
| Variables | 121,268 | 120,774 | 119,677 |
| CNF clauses | 274,794 | 266,665 | 254,348 |
| Native XOR rows | 42,402 | 41,826 | 40,647 |
| XCNF bytes | 20,644,230 | 18,008,905 | 13,825,116 |
| Exact collision clauses | 41,860 | 33,488 | 20,930 |
| Same-code clauses | 10 | 6 | 0 |
| Strict-order clauses | 2 | 3 | 4 |

The [build protocol](build_protocol.json) pins source code, exact collision
table, public point, checked Sage runtime, and constructed control. Its
[receipt](build_result.json) records the formula and wire hashes and a
5.006-second construction and assignment check. The
[constructed group control](n131_triple_pair_control.json) was transported
from audited W29 pair states. [Independent replay](control_replay.json)
rebuilds its ten leaves from masks and verifies their folded columns and
raw group sum. These construction checks do not estimate ordinary-query
yield.

## Frozen search results

The [three-way probe protocol](probe_protocol.json) fixes one public point,
the same solver binary, one worker, a 60-second cap per arm, 4-GiB RSS cap,
and the order paired-aligned, triple-plus-pair, all-aligned. All three rows
in the [probe receipt](probe_result.json) ended at the wall cap:

| 60-second solver diagnostic | Paired-aligned | Triple-plus-pair | All-aligned |
| --- | ---: | ---: | ---: |
| Wall seconds | 60.008 | 60.089 | 60.082 |
| Sampled peak combined RSS | 746,995,712 B | 508,985,344 B | 528,072,704 B |
| Last flushed restart / reported conflicts | 1,166 / 592K | 1,098 / 566K | 1,002 / 505K |
| Status | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |

This one ordered ordinary-host probe measures SAT-stage behavior under
different source schedules. Its conflict counts do not establish relative
relation yield or a full IC speedup.

The [public query protocol](query_protocol.json) pins one worker, a
590-second solver limit, 600-second parent wall cap, and 4-GiB combined RSS
cap. The [query receipt](query_result.json) and raw streams record
600.051 seconds, 645,496,832 B sampled peak combined RSS, a wall-cap stop,
and no SAT or UNSAT terminal line. The last flushed restart reported about
4.716 million conflicts. `BOUNDED_UNKNOWN` records the capped public search.
The [terminal audit](terminal_audit.json) checks source and stream hashes and
keeps this status distinct from the verified constructed control. The
[public-model replay](replay_model_sage.py) is ready to independently verify
any future SAT witness.

## Proof map and next target-conditioned test

[TriplePairOrder.lean](TriplePairOrder.lean) is pinned to Lean 4.34.1 and
imports the committed [all-aligned ordering proof](../n41_n131_all_aligned_20261019/AllAlignedOrder.lean)
from `e542afb22`. For lists of code-point records in a commutative group
with distinct codes within each block, `sort_groups` proves strict
within-block ordering, permutation of all records, and preservation of the
combined group sum. Given per-record validity in each input block,
`sort_groups_preserve_domains` proves that each sorted block retains its own
source-validity predicate, allowing the two blocks to use different
Frobenius rotations. `sh check_lean.sh` builds both actual theorem modules;
`#print axioms` reports only `propext` and `Quot.sound` for the new theorems.
The implementation's folded-column exclusions and curve witnesses are
checked by the exact collision table and Sage replays. `lean4checker --fresh`
was unavailable on this host.

The next experiment should compile an exact target-conditioned filter from
the fixed-seed pair quadratic: two reciprocal roots differ by the source
product divided by the leading coefficient. Test on frozen N41 queries
whether quotienting that branch-difference span rejects whole candidate
families before pair combinations, then measure its full N131 build and
ordinary-query cost if the N41 filter preserves the audited relation.
`candidate_id` remains `null` while relation collection, the factor-base
log system, target descent, and the paired same-point rho solve are open.
