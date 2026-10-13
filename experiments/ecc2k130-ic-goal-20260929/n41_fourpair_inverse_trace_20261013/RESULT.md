# Exact inverse-trace N41 four-pair search boundary

**The inverse-trace gate preserves the full N41 W8 source and the known eight-column public relation, but its unpinned four-pair query reached the 190-second parent cap.** The resulting XCNF has 16,755 variables and 814,459 bytes. On this same source and public point, the prior BDD formula has 14,803 variables and 712,086 bytes. This narrows the useful domain of the inverse-trace substitution: it compresses the W18 N131 support, whereas the 125-mask W8 N41 BDD is already smaller.

The exact curve is `EC1N41Ckb1h7d5e80d3c4d0`, `GF(2)[t]/(t^41+t^3+1)`, `y²+xy=x³+1`, subgroup order `549756390943`, cofactor four. The public point is `(920359962848,755404565011)`, with frozen raw-chart target reciprocal `344545435656`. Four signed diagonal-pair slots use Frobenius rotations `(0,7,14,21)` and eight distinct folded columns. This is a point-decomposition stage with `candidate_id: null`.

## Exact gate and control

For each source mask `m`, the endpoint is `w=m·t`. The replacement gate chooses `v` and enforces `wv=1` and `Tr(v)=0`. Independent binary-field enumeration tested all 255 nonzero W8 masks and found exactly the 125 masks in the frozen source table. The [earlier checked-Sage census](../n131_common_frob_inverse_trace_20261012/n41_control_result.json) checked the same support and all masks in a previously audited public relation. The remaining pair-output equations, three upper S3 links, and folded-column shield come unchanged from the [four-pair builder](../n131_w18_allseed_fourpair_20261012/fourpair_v2.py).

The [builder](build.py) checked every clause and native-XOR row against the frozen known public relation before writing the unpinned [formula](public.xcnf). The control passed 42,564 clauses and 2,372 XOR rows. The control assignment is a correctness check; the ordinary solver received no pinned masks, pair outputs, or branch choices. The first preflight run compared four builder hashes to five protocol hashes and stopped before formula construction; its [failure receipt](preflight_failure.json) is separate from the corrected frozen run.

| Same-point source formula | BDD | Inverse trace |
| --- | ---: | ---: |
| Variables | 14,803 | 16,755 |
| AND gates | 11,601 | 13,745 |
| CNF clauses | 35,804 | 42,564 |
| Native-XOR rows | 2,892 | 2,372 |
| XCNF bytes | 712,086 | 814,459 |
| Complete known-relation assignment | pass | pass |
| Unpinned public query, 190-second parent cap | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |

## Frozen unpinned query

The [build protocol](protocol.json) fixes source, fixture, builder, solver, and resource envelope by hash. The [query protocol](query_protocol.json) fixes the exact XCNF hash, one CryptoMiniSat worker, `--maxtime=180`, a 190-second parent wall cap, and a 4-GiB combined RSS cap. The [receipt](query_result.json) records `BOUNDED_UNKNOWN`, `WALL_CAP`, 190.012611041 seconds parent wall, 134.619974 child user seconds, 6.141912 child system seconds, and 320,126,976 bytes sampled peak combined RSS. The [raw solver stream](solver.stdout) ends during active search after 2.096 million logged conflicts and 2,346 restarts, without a SAT/UNSAT terminal line. The [read-only verifier](verify.py) checks all frozen hashes, complete control status, support count, solver terminal lines, and the receipt classification.

The prior BDD query also reached its 190-second cap under one worker. These are same-point algorithmic diagnostics on a host without an isolation receipt, so the table compares exact formula size and bounded status, not a controlled CPU speed ratio.

## Next iteration

The exact source substitution alone did not make the four-output compatibility search tractable at N41. The next gate should condition **two unresolved partial sums jointly on the public point** before source-mask expansion. A candidate constraint must preserve the existing unpinned N41 eight-column witness, reject complete incompatible seed or partial-sum families, and report all target-dependent proposal work. The W18 N131 transfer needs a source-bound one-worker 600-second/4-GiB projection before another public query. The [proof map](PROOF_MAP.md) identifies inherited formal and checked-arithmetic controls.
