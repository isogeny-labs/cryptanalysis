# Exact inverse-trace source in the target-conditioned five-pair circuit

**Replacing the W18 source BDD by exact inverse-trace witnesses reduced the public N131 five-pair formula to 132,961 variables and 10,780,411 XCNF bytes.** Against the otherwise matched BDD circuit, this is 86.73% fewer variables and 74.79% fewer bytes. The retry charged target projection, formula construction, and solver search to one frozen public point for 600.155675667 seconds. Its process status is `PARENT_TIME_CAP`, and its mathematical outcome is `BOUNDED_UNKNOWN` under that cap. The [independent audit](audit_result.json) rebuilt the control and public formulas byte for byte and verified all parent phase times and the saved solver transcript.

## Exact instance and method

The curve is `EC1N131Ckb1heb5f1998f20b` over `GF(2)[t]/(t^131+t^13+t²+t+1)`, with equation `y²+xy=x³+1` and subgroup order `680564733841876926932320129493409985129`. The workload is `cc09e7eb202a`; its public point is `(1052727368764798954359115163823647684025, 2071227447786120917960296877345506689833)`. The checked Sage target phase maps it by `(1+Frobenius^16)^{-1}` to `Q′=(1011194589287210738281611435711478792573, 464867644853173232674848580669299498572)` and checks the four raw preimage fibers. The [query protocol](query_protocol.json) freezes shift 16, target, fibers, implementation and solver hashes, one worker, a 600-second total cap, and 4-GiB combined RSS cap. The [runtime receipt](sage_runtime_info.json) records the checked Sage launcher.

Each of five free pair blocks takes two W18 diagonal source masks. For each mask `w`, the new source gate introduces an inverse `v` with `wv=1` and `Tr(v)=0`; the [source census](../n131_w18_inverse_trace_terminal_20261011/gate_equivalence.json) connects that exact condition to the former BDD. The circuit computes five signed pair outputs, enforces ten distinct folded columns, and joins the outputs by four upper S3 equations to one of the four target fibers. The [constructed control](../n131_common_frob_inverse_trace_20261012/RESULT.md) verifies a complete assignment. [Checked Sage](gate_result.json) independently confirms the ten concrete inverse witnesses and their distinct folded columns. The [proof map](PROOF_MAP.md) links the five-pair source substitution to a checked Lean theorem and identifies the remaining concrete field bridge.

| Exact formula | Matched BDD control | Inverse-trace control | Matched BDD public | Inverse-trace public |
| --- | ---: | ---: | ---: | ---: |
| Variables | 993,071 | 123,741 | 1,002,291 | 132,961 |
| AND gates | 350,789 | 80,739 | 356,208 | 86,158 |
| CNF clauses | 1,075,479 | 266,639 | 1,091,743 | 282,903 |
| Native-XOR rows | 641,054 | 40,464 | 644,851 | 44,261 |
| XCNF bytes | 42,354,147 | 10,376,697 | 42,767,135 | 10,780,411 |

The public formula has 75.81% fewer AND gates, 74.09% fewer CNF clauses, and 93.14% fewer native-XOR rows than its BDD counterpart. These are exact encoding sizes. `candidate_id` is `null` because this is a point-decomposition stage, with no fully specified relation matrix and target-recovery pipeline.

## Frozen public attempt

The [first launch](../n131_common_frob_inverse_trace_20261012/RESULT.md) exited at the target projection stage because its frozen protocol omitted `frobenius_shift`. That failure remains a separate 9.188600958-second receipt. This corrected retry has its own [frozen protocol](query_protocol.json) and [raw process receipt](query_result.json).

| Exclusive target-dependent interval | Seconds |
| --- | ---: |
| Checked Sage target projection and four raw fibers | 11.332713792 |
| Public formula build process | 4.570375209 |
| CryptoMiniSat process, including capped search | 584.240377166 |
| Parent bookkeeping | 0.012209500 |
| **Total charged attempt** | **600.155675667** |

The solver used `--threads=1 --maxtime=540 --maxmatrixrows=4000 --maxmatrixcols=10000 --maxnummatrices=6`, returned 720 restart rows, and emitted no SAT/UNSAT terminal line before the parent stopped it. The [raw solver stream](solver.stdout) records six admitted matrices at initialization, including four `3315 × 9132` matrices, and a larger `28777 × 66529` matrix excluded by the declared limits. Sampled combined RSS peaked at 293,175,296 bytes. The 0.156-second excess over the parent cap is polling and termination latency. The local CPU timing is an algorithmic diagnostic without an isolation receipt; it is not an online speedup comparison. The [audit protocol](audit_protocol.json), [byte-replay audit](audit_result.json), and [read-only receipt checker](verify.py) preserve the status and accounting.

## Next experiment

The exact source reduction removes most Boolean encoding cost, while the capped solver still cannot select a witness from the free five-pair family. The next falsifiable step is **output-first, target-conditioned proposal**: combine the existing W18 pair-output inverse with a joint constraint on at least two partial sums, and reject incompatible output families before expanding their source masks. Freeze an unpinned N41 public-target family-rejection test, measure its complete proposal/rejection cost and genuine relation yield, then project that measured work to the N131 source bound before another capped public query. :codex-annotation{index="1"} A successful N131 proposal must still produce an independently replayed signed group relation and novel row before a complete single-target online comparison with same-point rho.
