# One target-conditioned trace row links all nine W18 pair outputs

The four-fiber W18 selector now has an **exact 40-literal parity row** linking seven free pair-output traces, two selected terminal-point traces, and the selected public raw-fiber trace. It preserves the full N131 constructed assignment and the archived unpinned N41 ordinary relation. Independent checked Sage verified the residual identity on all **8,320 public and 8,320 constructed N131 lookup entries**, and separately checked all 96 terminal state traces and 2,080 joint sums. The frozen public query completed its one-worker, 600-second attempt with `BOUNDED_UNKNOWN` after **598.051372333 s**.

## Exact identity and source

For a nonexceptional reciprocal S3 link, the absolute trace of the output reciprocal is the XOR of the two input traces. Along the six links combining seven free pair points, the selected residual therefore has trace equal to the XOR of their seven trace bits. The frozen lookup uses residual `T_k-(P_i+P_j)`; its trace equals the trace of raw target `T_k` XOR the traces of the selected terminal points. Combining these equalities yields one necessary target-dependent parity row on all nine selected pair outputs and the raw-fiber selector. The field/S3 implication was proved in the earlier [trace propagation](../n131_w18_trace_gate_v2_20261014/TracePropagation.lean) work; this experiment's [Lean theorem](TraceParity.lean) checks the nine-output Boolean implication, with scope in the [proof map](PROOF_MAP.md).

The exact field is `GF(2)[t]/(t^131+t^13+t²+t+1)` and the curve is `y²+xy=x³+1`, `EC1N131Ckb1heb5f1998f20b`, subgroup order `680564733841876926932320129493409985129`, cofactor four. The workload `cc09e7eb202a` supplies the same public subgroup point as the [four-fiber baseline](../n131_w18_two_terminal_fourfiber_20261017/RESULT.md). The source retains seven free seed-212 W18 pair rotations, two terminal rotations, 48 signed states per terminal slot, 2,080 admissible terminal sums, and four raw preimages. Its `candidate_id` remains `null` pending a complete IC pipeline. The [protocol](protocol.json) froze source hashes, this parity law, target, one solver worker, 590-second solver limit, 600-second target-dependent wall limit, and 4-GiB sampled combined-RSS cap before the public query.

The tempting stronger predicate “free-seven residual trace is zero” is false for this source: the valid constructed assignment has free-seven and selected-residual trace **one**. The checked-Sage [preflight](trace_audit_result.json) records that control and counts both trace values across all four public fibers. The [terminal-table audit](trace_table_audit_result.json) checks the per-state decomposition of all 2,080 joint traces, preventing a source-table mismatch from justifying the circuit row. The N41 relation control has free-five, terminal-two, and selected raw-target trace bits `(0,0,0)`; the N131 constructed control exercises the nonzero case.

## Formula and query

| Frozen measure | Four-fiber baseline | Added parity row |
| --- | ---: | ---: |
| Variables | 402,572 | 402,573 |
| AND gates | 179,828 | 179,828 |
| CNF clauses | 543,701 | 543,702 |
| Native XOR rows | 220,947 | 220,948 |
| Public XCNF bytes | 20,488,321 | 20,488,574 |
| Public XCNF SHA-256 | `dacb1f21dcc4fb4a1be6d43ef8661233e7830fd6b7c2734021fc57504982c7d6` | `9f32e17bbdff7b095953a3b6601a32fb79b84c4d9a20d7c163802c3487d56ec3` |
| Public target-dependent wall | 598.064997167 s | 598.051372333 s |
| Sampled peak combined RSS | 704,937,984 B | 740,720,640 B |
| Solver restart rows / status | 1,775 / `BOUNDED_UNKNOWN` | 1,652 / `BOUNDED_UNKNOWN` |

The parity-gated constructed assignment passed all **543,702 clauses and 220,948 native XOR rows**. Public raw-target trace bits were `(0,0,1,1)`; the constructed control used `(1,1,0,0)`. The new row is one XOR gate output constrained by one unit clause. Both XCNFs are saved as deterministic [constructed](control.xcnf.gz) and [public](ordinary.xcnf.gz) gzip archives, with decompressed lengths and hashes checked by the [terminal audit](audit_result.json).

The public attempt's exclusive target-dependent phases were residual generation **2.164358000 s**, formula construction **3.816409291 s**, serialization **0.021312750 s**, solver launch/search/stop **592.028287667 s**, and terminal parsing **0.021004625 s**; they sum to **598.051372333 s**. The runner stopped the solver at `TARGET_DEPENDENT_TIMEOUT`, exit `-9`, with empty stderr, no terminal SAT/UNSAT line, and 740,720,640 B sampled peak combined RSS. Default CryptoMiniSat initialization selected zero Gaussian matrices from 14 oversized candidate components. Both the baseline and gated query are censored, so their small wall and restart differences do not establish a search-cost ranking. The ordinary-host wall measurements have no CPU isolation receipt.

The first frozen constructed-control attempt used `require_zero(parity_lits)`, which constrained each literal separately and failed assignment checking. Its exact source, protocol, formula archive, and failure are retained in [attempt1](attempt1/FAILURE.md). The corrected source wraps the literals in one XOR before applying the zero constraint; a new protocol was frozen before the public query. This distinction is checked by the terminal audit.

## Reproduction and next gate

The checked Sage launcher supplied the saved [runtime receipt](sage_runtime_info.json). The preflight, terminal-table audit, and terminal receipt passed with:

```sh
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w18_fourfiber_trace_parity_20261017/trace_audit.py
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w18_fourfiber_trace_parity_20261017/audit_trace_table_sage.py
./sage -python experiments/ecc2k130-ic-goal-20260929/n131_w18_fourfiber_trace_parity_20261017/audit.py
```

`lean TraceParity.lean` passes under the pinned Lean 4.34.1 toolchain; both `#print axioms` reports list only `propext` in [build output](lean_check.log). The exact target-conditioned parity is mathematically valid and cheap, but one global trace bit did not settle this public query within the cap. The next algorithmic gate should produce **more than a constant number of independent target-conditioned bits** or a source-aware family rejection that acts before the seven pair-output variables expand. A concrete follow-up is to test a compact mod-four torsion character on the raw source points: first prove and independently replay its signed-point law on an unpinned N41 ordinary relation, then measure whether its source-bit encoding costs less than the branches it removes at N131. Preserve every exceptional chart and charge the full target-dependent construction and failed attempts.
