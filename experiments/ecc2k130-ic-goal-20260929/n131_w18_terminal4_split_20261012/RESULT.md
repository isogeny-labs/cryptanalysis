# Exact terminal-sign partition tests four N131 search branches

The four signed states of the fixed W18 terminal edge partition the earlier N131 public-point query exactly. Rebuilding its target-dependent XCNF produced the same SHA-256 as the [monolithic query](../n131_w18_terminal4_20261012/RESULT.md); each state formula adds exactly one unit clause forcing its own choice wire. Under one 600-second total budget, four sequential 132-second CryptoMiniSat searches each ended `BOUNDED_UNKNOWN`. The [receipt audit](audit_result.json) verifies all four formula byte diffs, solver transcripts, source hashes, public-point identity, and the complete phase sum.

## Frozen method and workload

The field is `GF(2)[t]/(t^131+t^13+t²+t+1)`, the curve is `y²+xy=x³+1`, and the subgroup order is `680564733841876926932320129493409985129` with cofactor four. The curve ID is `EC1N131Ckb1heb5f1998f20b`. The workload is the same public point `cc09e7eb202a` and raw preimage index zero as the monolithic four-state comparator. Eight W18 pair slots remain unpinned; the terminal edge and all four signed point states were frozen before this query. Each state has an exact uniform raw-point mean source ceiling of `35.4022876484`; the four-state union has ceiling `141.609150594`. These are exact source counts divided by the full curve order, not fixed-point yield measurements.

The [protocol](protocol.json) freezes the source and solver hashes, state order `0,1,2,3`, one worker, 4-GiB combined RSS cap, 132 seconds per state, and 600 seconds from the first target-dependent residual calculation. The [checked Sage runtime](sage_runtime_info.json) and earlier independent [Sage fiber replay](../n131_w18_terminal4_20261012/sage_audit_result.json) bind the four point states and residuals. The present [query result](query_result.json) contains exactly the same residuals and reproduces the prior base formula byte for byte. A separate [parser control](xor_then_clause_control.xcnf) returns `s SATISFIABLE` with an XOR row followed by a CNF unit clause, the ordering used by the split formulas.

| Forced terminal state | Added choice wire | Search wall | Restart rows | Sampled peak combined RSS | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| 0 | 22014 | 132.016 s | 154 | 509,722,624 B | `BOUNDED_UNKNOWN` |
| 1 | 22015 | 132.042 s | 92 | 223,248,384 B | `BOUNDED_UNKNOWN` |
| 2 | 22016 | 132.062 s | 57 | 218,382,336 B | `BOUNDED_UNKNOWN` |
| 3 | 22017 | 132.073 s | 49 | 218,595,328 B | `BOUNDED_UNKNOWN` |

Each state formula has 441,736 variables and 821,759 total CNF-plus-XOR constraints. All four solver stderr files are empty; each solver entered search and was stopped at its frozen state cap without a terminal SAT/UNSAT line or model. The exclusive target-dependent phases are 3.376 seconds for residual generation, 44.278 seconds for circuit construction, 0.202 seconds for base and four forced XCNF writes, and 528.201 seconds for all solver launches/searches/parsing, totaling **576.058 seconds**. The corresponding monolithic four-state query was charged 600.130 seconds at its cap. These capped outcomes do not rank the methods by successful relation cost; both used the same shared host, so CPU wall comparisons are exploratory.

The experiment narrows the design decision: forcing one terminal sign gives an exact, cheap restriction, but this four-way schedule produced no model within its frozen per-state allocation. The next useful step is to replace the SAT search over all eight free pair selectors with a target-conditioned partial-sum rejection rule that can be checked on N41 natural relations before carrying its cost and completeness proof to this N131 workload.
