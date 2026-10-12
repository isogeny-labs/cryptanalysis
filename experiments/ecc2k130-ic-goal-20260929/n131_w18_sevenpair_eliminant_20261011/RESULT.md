# Seven-pair W18 eliminant circuit reaches a bounded public search

An exact first/terminal product eliminant can replace two explicit pair-output coordinates in a target-conditioned W18 decomposition circuit. The resulting circuit preserves a constructed nine-pair group witness: all **686,791 CNF clauses and 268,800 native-XOR rows** pass. On the frozen N131 public point, one-worker CryptoMiniSat entered active search and reached the 600-second parent limit with `BOUNDED_UNKNOWN`. The eliminant added enough Boolean multiplication that this first encoding is larger than the prior 32-state terminal-fiber circuit, establishing a concrete cost barrier for this regrouping.

## Method and input law

The curve is `EC1N131Ckb1heb5f1998f20b` over GF(2)[t]/(t^131+t^13+t²+t+1), with `y²+xy=x³+1`, subgroup order `680564733841876926932320129493409985129`, and cofactor four. The W18 fixed-seed source uses seed mask 212. Seven free pairs occupy Frobenius rotations `16,32,48,64,80,96,112`; the first pair's 17-bit source selector is at rotation zero. The terminal edge is selected from the eight exact edges in the frozen 32-state pool at rotation 128. The terminal's four point-sign choices are represented implicitly by the two-quadratic eliminant and require exact group replay if a Boolean model appears. The ordinary input is workload `cc09e7eb202a`, public point `(1052727368764798954359115163823647684025, 2071227447786120917960296877345506689833)`, and raw preimage index zero used by the terminal-fiber comparator. All source selectors retain the exact 33,191-code W18 BDD; cross-pair folded-column reuse must be checked after candidate extraction.

Let `p` be the first pair's source product, `q` the selected rotated terminal product, `z` the reciprocal coordinate of their four-point sum, and `s` the sum of the seven other pair outputs. Six S3 links compute `s`; a seventh constrains `s+z` to the supplied raw target. The pair laws are `k c²+p c+h²=0` and `ell d²+q d+h'²=0`, with the terminal coefficients rotated by Frobenius^128. The circuit imposes their two-quadratic resultant `H_{q,z}(p)=0` using the degree-four expression audited in the preceding [pool-root experiment](../n131_pool_root_unpinned_control_20261011/RESULT.md). It is a necessary, source-aware constraint. Exact point-sign, folded-column, and raw-sum checks remain part of candidate verification.

The [source protocol](protocol.json) froze the implementation and checked [Sage runtime](sage_runtime_info.json) before construction. The constructed control uses the same nine mask pairs as the earlier fixture with a new all-sign-zero raw target, computed and stored before building the formula. The [query protocol](query_protocol.json) froze the public workload, solver binary and flags, one worker, 600-second parent cap, 520-second solver setting, and 4 GiB combined RSS cap before the ordinary query. The first pre-protocol import failure is retained in [preflight_failure_v1.json](preflight_failure_v1.json) as `PRODUCER_FAILURE`; it carries no search decision.

| Frozen measure | Seven-pair eliminant | Earlier 32-state terminal fiber |
| --- | ---: | ---: |
| Variables | 499,045 | 450,948 |
| AND gates | 228,256 | 195,294 |
| Clauses | 686,791 | 588,373 |
| Native-XOR rows | 268,804 | 253,645 |
| Ordinary XCNF bytes | 26,337,656 | 19,271,319 |
| Ordinary solver status | `BOUNDED_UNKNOWN`, parent wall cap | `BOUNDED_UNKNOWN`, 195-second solver parent cap |
| Sampled combined peak RSS | 576,880,640 B | 379,650,048 B |

The eliminant encoding adds **48,097 variables, 32,962 AND gates, 98,418 clauses, 15,159 XOR rows, and 7,066,337 XCNF bytes** relative to the terminal-fiber formula. The two queries use the same public point and one worker but different formulas and time caps. Their CPU timing ratios are exploratory on a contended host; the table establishes exact formula size and recorded bounded statuses.

The [ordinary query receipt](query_result.json) charges 0.0066 seconds of target conversion, 47.076 seconds of formula construction, 0.026 seconds of serialization, 552.934 seconds of solver activity, and 0.0013 seconds of terminal parsing, totaling **600.044 seconds** including the parent monitor's 44 ms stop overshoot. Solver stdout contains 38 bracketed diagnostic rows, no terminal SAT/UNSAT line, and no model; both error streams are empty. The [receipt verifier](verify.py) checks source hashes, both exact XCNF byte hashes, the constructed assignment, public workload identity, phase sum, cap and status accounting, and the solver trace. It passes with `python3 -B verify.py`. This run measured a component query; it did not produce a verified relation row or rank update.

## Next experiment

The degree-four inverse is selective when `z` is supplied, but this Boolean eliminant encoding costs more gates than the terminal-fiber encoding. The next cheapest test is a **direct regrouped circuit**: keep explicit first and terminal reciprocal outputs, retain the eight-edge terminal selector, and link those outputs to a seven-pair partial sum and the public target. Freeze the same constructed witness and public point, compare exact gate counts first, then give it the same one-worker, 600-second, 4 GiB ordinary cap only if construction fits. A smaller direct circuit would isolate the cost of elimination from the cost of regrouping; any model must be independently replayed as a complete ordinary relation.
