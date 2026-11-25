# Four-sign terminal conditioning shrinks the N131 W18 circuit

Restricting the ninth W18 pair to one fixed source edge and its four signed point states gives an exact target-conditioned residual selector. The public-point formula has **441,736 variables, 190,001 AND gates, 572,004 clauses, and 249,754 native-XOR rows**. Relative to the prior 32-state terminal pool on the same point, this removes 9,212 variables, 5,293 AND gates, 16,369 clauses, and 3,891 native-XOR rows. The constructed-control assignment satisfies every row of its formula, and checked Sage independently verifies all four signed terminal points and public/control residuals.

## Frozen source and query

The field is `GF(2)[t]/(t^131+t^13+t²+t+1)`, the curve is `y²+xy=x³+1`, and the subgroup has order `680564733841876926932320129493409985129` and cofactor four. The curve ID is `EC1N131Ckb1heb5f1998f20b`. Eight free pair slots use W18 seed mask 212 and rotations `0,16,...,112`; the terminal slot has rotation 128. The fixed terminal edge is the constructed-control edge, selected before the public query, with all four sign choices. All eight ordinary-query pair masks remain unpinned.

The [source count](source_count.json) finds 33,191 eligible unordered pair edges and 36,472,060,901,118,348,738,895,098,162,681 eight-edge matchings after excluding the terminal edge's two folded columns. The four signed terminal states give 385,496,775,533,026,822,364,135,517,826,396,433,940,480 distinct-column ordered signed tuples. Dividing by the full curve order `4r` gives an exact uniform raw-point mean upper ceiling of **141.609150594**. This count is a source-support bound for a uniform raw point; fixed-point existence is tested by the ordinary query.

The [protocol](protocol.json) binds source and solver hashes, the same frozen public point/workload `cc09e7eb202a`, raw preimage index zero, one worker, a 4-GiB combined RSS cap, and a 600-second total target-dependent query cap before construction or search. The [checked Sage runtime receipt](sage_runtime_info.json) was saved before the measured query. The [control receipt](control_result.json) records 572,004 satisfied clauses and 249,751 satisfied native-XOR rows; its formula has 190,001 AND gates. The ordinary point changes a few constant-folded wires and XOR rows, so its formula counts differ slightly.

## Ordinary public-point query

The [ordinary query receipt](query_result.json) records `BOUNDED_UNKNOWN` at the 600-second total query cap. CryptoMiniSat entered search and logged 670 restart rows. Its stderr is empty; the parent stopped the child at the frozen cap, with no SAT/UNSAT status line or model. The sampled combined RSS peak is 448,626,688 bytes, below the 4-GiB cap. The [checked Sage replay](sage_audit_result.json) verifies every signed terminal point and both sets of residuals. The [receipt audit](audit_result.json) checks source hashes, protocol binding, public point/workload identity, XCNF hashes and sizes, solver transcript, resource bounds, phase sum, and the formula reduction against the 32-state comparator.

| Exclusive target-dependent phase | Time |
| --- | ---: |
| Generate and check four residuals | 0.608 s |
| Construct ordinary formula | 43.177 s |
| Serialize formula | 0.160 s |
| Solver launch, search, and stop | 556.183 s |
| Parse terminal output | 0.001 s |
| **Total charged attempt** | **600.130 s** |

The structural circuit reduction is exact; CPU wall times from this shared host are exploratory. The source ceiling gives an exact counting bound, while this capped solver outcome is censored evidence for the fixed point. A useful next circuit experiment is to split the four terminal signs into four separately frozen one-state queries, holding the same total 600-second budget, to test whether the monolithic one-hot disjunction is masking search progress. That comparison must retain all four outcomes and charge every formula build and failed attempt to the same public point. The project goal then still requires a verified ordinary relation, novel rank, complete target recovery, and matched same-point rho under an isolation receipt before an online speedup can be assessed.
