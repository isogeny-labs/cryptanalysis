# Direct first/terminal regrouping removes the eliminant gate cost

A direct W18 first/terminal block circuit retains a complete constructed nine-pair witness while using **26,097 fewer AND gates** than the degree-four eliminant circuit. It keeps the two pair reciprocal outputs explicit and joins them with one S3 link, then joins the seven remaining pairs to the supplied raw target. The frozen ordinary N131 public-point query entered CryptoMiniSat search and ended at the 600-second parent cap with `BOUNDED_UNKNOWN`. The result separates the eliminant's Boolean gate cost from the cost of regrouping; the direct topology remains larger than the earlier terminal-fiber formula.

## Source, curve, and exact circuit

The field is GF(2)[t]/(t^131+t^13+t²+t+1), the curve is `y²+xy=x³+1`, and the curve ID is `EC1N131Ckb1heb5f1998f20b`. The odd-order subgroup has order `680564733841876926932320129493409985129` and cofactor four. The W18 fixed-seed source uses seed mask 212 and 33,191 eligible pair codes. Seven free pairs use Frobenius rotations `16,32,48,64,80,96,112`; the first pair is at rotation zero. The terminal edge selector uses the eight edges from the frozen 32-state pool at rotation 128. The first pair, seven free pairs, and terminal pair each obey their exact half-trace quadratic. The circuit has six S3 links for the seven-pair partial sum, one for the first/terminal block, and one from those two blocks to the target. Source selectors use the exact W18 BDD. Any Boolean candidate still requires distinct folded-column and signed point-sum checks.

The ordinary workload is `cc09e7eb202a`, public point `(1052727368764798954359115163823647684025, 2071227447786120917960296877345506689833)`, raw preimage index zero. The [version-two protocol](protocol_v2.json) froze source, source table, pool, checked [Sage runtime](sage_runtime_info.json), target, and solver before its control. The first formula had a branch-wire mix-up in the target S3 link; [failure_v1.json](failure_v1.json) records the first failing unit clause, exact source and formula hashes, `PRODUCER_FAILURE`, and no scientific decision. The corrected [circuit_v2.py](circuit_v2.py) and [run_v2.py](run_v2.py) have separate frozen identities. The corrected constructed control passes all **608,765 clauses and 257,417 XOR rows** on a raw point obtained by summing nine all-sign-zero source pairs. The [public-query protocol](query_protocol.json) then fixed the same previously published public point, one worker, a 600-second parent cap, 520-second solver setting, and 4 GiB combined RSS cap.

| Ordinary formula | Terminal fiber | Degree-four eliminant | Direct regroup |
| --- | ---: | ---: | ---: |
| Variables | 450,948 | 499,045 | **461,828** |
| AND gates | 195,294 | 228,256 | **202,159** |
| Clauses | 588,373 | 686,791 | **608,765** |
| Native-XOR rows | 253,645 | 268,804 | **257,421** |
| XCNF bytes | 19,271,319 | 26,337,656 | **20,298,743** |
| Public query status | `BOUNDED_UNKNOWN` at 195-second solver parent cap | `BOUNDED_UNKNOWN` at 600-second parent cap | `BOUNDED_UNKNOWN` at 600-second parent cap |
| Sampled combined peak RSS | 379,650,048 B | 576,880,640 B | **375,144,448 B** |

Direct regrouping saves 37,217 variables, 26,097 AND gates, 78,026 clauses, 11,383 XOR rows, and 6,038,913 bytes against the eliminant formula. Relative to terminal fiber it adds 10,880 variables, 6,865 AND gates, 20,392 clauses, 3,776 XOR rows, and 1,027,424 bytes. These are exact structural counts from frozen byte-hashed formulas. Host wall times and restart counts are exploratory because the runs were not isolated and the terminal-fiber query had a shorter cap.

The [query receipt](query_result.json) charges 0.0045 seconds of target conversion, 30.950 seconds of formula construction, 0.104 seconds of serialization, 568.967 seconds of solver work, and 0.0015 seconds of terminal parsing: **600.028 seconds**, including 28 ms of parent-monitor stop overshoot. Solver stdout has 156 bracketed diagnostic rows and no terminal SAT/UNSAT line; both error streams are empty. The [receipt verifier](verify.py) binds the corrected source and control, both exact formula byte hashes, the frozen public point and solver, phase sum, memory, and status. It passes with `python3 -B verify.py`. Candidate ID remains null because relation collection, final matrix solution, and target recovery have not been measured as one method.

## Next gate

The [exact terminal source count](../n131_w18_terminal_fiber_20261011/source_count.json) gives a uniform raw-point mean upper ceiling of **35.4023 labeled eight-pair relations for one fixed signed terminal state** on the first edge, under the declared source law. A single fixed state removes the terminal choice from the Boolean search while retaining substantial source multiplicity. Freeze that state before the public query, verify the restriction on an unpinned N41 workload, and then compare the fixed-state N131 formula and 600-second ordinary status with the three circuits above. The count is a source-support ceiling; ordinary yield must be measured on the frozen point.
