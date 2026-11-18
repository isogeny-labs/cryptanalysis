# Phase ceiling and next optimization admission

Derived from the completed frozen panel, without rerunning or modifying a workload. These are paired median arithmetic bounds, not measured candidate timings or confidence intervals. All failed A/A controls remain. [pcc:unverified]

| Field | Table / primary | Collector / primary | Primary / negation rho | Free table: residual / rho | Free collector: residual / rho | Both free: residual / rho |
| --- | --- | --- | --- | --- | --- | --- |
| N15 | 0.0815 | 0.5072 | 2.4151 | 2.2189 | 1.1765 | 0.9857 |
| N18 | 0.2679 | 0.3963 | 3.1713 | 2.3138 | 1.9656 | 1.0695 |
| N21 | 0.3613 | 0.4473 | 4.3095 | 2.7803 | 2.3965 | 0.8360 |
| N24 | 0.5465 | 0.3392 | 8.2060 | 3.6939 | 5.3499 | 0.9179 |
| N27 | 0.5155 | 0.4282 | 16.0350 | 8.1570 | 9.2864 | 0.8839 |

Each residual subtracts only the named recorded phase from that same row primary and divides by its same-target matched negation-rho interval. No cost is amortized across targets; no ratio from another panel is multiplied into this one. Setting a phase to zero is deliberately unattainable and leaves all other recorded costs fixed. It gives an optimistic bound for changing only that phase, not a causal model of cache/allocator changes. [pcc:unverified]

At N27, removing either table preparation or the entire collector still leaves a large gap. Reservation/gather is rejected as the next performance remedy. The prior static witness dictionary also failed its primary comparison; the reduced Apple ARM wrapper audit already emits native polynomial-multiply instructions. Repeating those leads or adding a C/assembly wrapper does not itself supply a new cost case. [pcc:unverified]

Next admission must target both dominant phases or reduce relation work algorithmically. Before another timing request: identify an exact operation or data movement eliminated from setup and collection, preserve complete first-witness maps and query order, audit actual compiler output on the relevant native backend, and give a whole-primary cost case. A GPU proposal must include allocation, transfers, table construction and completion of collection; a reused table is a separately named many-target model. No further allocation is launched or requested by this analysis. [pcc:unverified]
