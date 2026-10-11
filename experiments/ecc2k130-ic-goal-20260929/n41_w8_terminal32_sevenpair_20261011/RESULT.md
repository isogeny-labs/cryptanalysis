# Terminal-32 N41 relation collection reaches rank two and target recovery

A seven-pair N41 W8 group join with only **32 signed terminal states** found two ordinary relations on one frozen public point under a 120-second, one-worker cap. Independent checked Sage replay verified both raw sums, fourteen distinct folded columns per row, and **two novel relation rows**. Combining either row with the previously prepared, independently checked 70-column factor logs recovered scalar **`445577591162`** relative to `G=(1236950581268,1658150202663)`; Sage replay confirmed that scalar gives the supplied point `(920359962848,755404565011)`.

The field is `GF(2)[t]/(t^41+t³+1)` and the curve is `y²+xy=x³+1`, with curve ID `EC1N41Ckb1h7d5e80d3c4d0`, subgroup order `549756390943`, and cofactor four. The W8 seed-184 source has 35 eligible pair edges and 70 selected folded columns; each edge has four signed states. Six slots reuse the [independently prepared state input](../n41_w8_sixpair_mitm_20261011/prepare_result.json) at Frobenius rotations `0,7,14,21,28,35`. The seventh slot repeats rotation zero but is restricted to IDs `0..31`, all four signs of the first eight edges. Its source rule was frozen before the public-point query. Only raw preimage index zero was queried, matching the terminal-fiber raw-preimage policy used in the N131 control.

The [protocol](protocol.json) fixes the input, native executable and compiler hashes, the 32-state law, one worker, 4-GiB RSS cap, 120-second parent wall cap, and an eight-hit collection stop. Since all 35 source edges have disjoint folded columns, the exact selected-source count is `32·(34)_6·4⁶` labeled ordered seven-pair tuples. Dividing by the full curve order `4r` gives a **uniform raw-point mean upper ceiling of 57.7169575444**. This source count does not substitute for the measured fixed-point relation yield.

| Stage or check | Recorded result |
| --- | ---: |
| Native-versus-Sage group-addition checks | 128/128 passed |
| Reusable three-pair table | 2,513,280 entries; 43.9065 s cumulative local time |
| First verified hit after table build | 38,365 probes; 0.5713 s local diagnostic |
| Second verified hit after table build | 2,631,587 probes; 73.1165 s local diagnostic |
| Parent run / sampled combined peak RSS | 120.407 s / 208,633,856 B |
| Independent relation replay | 2/2 passed, 14 distinct columns per row |
| Novel rank from an empty relation matrix | **2** |
| Prepared factor-log system | 70 columns, rank 70 with generator anchor |
| Scalar recovered from each new row | **`445577591162`**, replay passed |
| Eight-hit collection stop | `CENSORED_TIME`, two hits retained |

The [native receipt](query_result.json) preserves both hit lines and the wall-stop status. The [Sage relation audit](sage_audit_result.json) rebuilds source points from the field polynomial, checks every signed pair and raw sum, derives the signed-Frobenius coefficients, and computes incremental rank modulo the subgroup order. Its first attempt completed the group and rank assertions but failed while serializing a Sage integer; the [failure receipt](sage_audit_failure_v1.json) and partial output remain archived. The repaired audit converts that rank to a plain integer. The separate [target-recovery replay](recovery_result.json) binds the earlier [factor-log system](../n41_w8_sixpair_logprep_20261011/RESULT.md), combines both new rows, and verifies the scalar on the curve. The [terminal receipt audit](audit_result.json) binds source, input, runtime, output, cap, rank, and scalar checks.

The native target probe, Sage row audit, and Sage scalar replay were separate intervals on a contended host. The first-hit query time is a stage diagnostic; it is not a verified single-target online IC/rho speedup for this variant. The two new rows validate that the terminal-state restriction can retain ordinary relations and useful rank in a smaller-field full pipeline. The N131 [32-state terminal-fiber circuit](../n131_w18_terminal_fiber_20261011/RESULT.md) has a larger source ceiling but its ordinary SAT query remains `BOUNDED_UNKNOWN`; explicit N41 triple-table storage does not scale to that field. The next N131 step must improve target-conditioned implicit search or run the frozen circuit with auditable CPU entitlement before relation yield can be measured there.
