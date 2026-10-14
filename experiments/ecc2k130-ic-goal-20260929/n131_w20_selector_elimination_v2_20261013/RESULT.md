# Direct parity eliminates free W20 source selectors

The N131 W20 inverse-output circuit now derives each pair's 19 source-selector bits from its output and inverse wires. Product-image membership is enforced by direct parity rows on those same wires. The frozen constructed seven-pair relation satisfies all **423,009 clauses and 73,844 native XOR rows**. The result removes 117 circuit variables relative to the prior inverse-output form while retaining an exact source gate and the same target-coupled S3 chain.

For the selected seed 898618, the 19 source-product basis vectors have pivot coordinates 21–39. Version one materialized the 131-bit product and then its projection. This version precomputes, for each of the 262 output/inverse input bits, its contribution to (i) the 19 decoded selector bits and (ii) the 112 nonzero product-image syndrome bits. `selector.py` emits the corresponding XOR rows directly. The reconstructed source endpoint feeds the two nonzero inverse and trace-zero gates from the prior circuit. The exact decoder and its exhaustive 524,288-code check are reused with an identical hash from the first frozen experiment; the generic projector and unique-selector theorems were checked in Lean there.

| Exact formula | Variables | Clauses | Native XOR rows | Bytes |
| --- | ---: | ---: | ---: | ---: |
| Prior inverse-output | 217,842 | 423,142 | 73,828 | 11,914,495 |
| Materialized projector v1 | 218,397 | 423,009 | 74,516 | 12,735,095 |
| Direct parity v2 | **217,725** | **423,009** | 73,844 | 11,922,594 |

The one-worker control build completed in **54.237171458 s** under its frozen 120 s and 4 GiB caps, with intact RSS monitoring. The parent interval includes construction, serialization, and full assignment evaluation; internal construction took 38.8903935 s. These local CPU intervals are exploratory without host isolation. The source and basis hashes, run limits, formula hash, and assignment counts are in `protocol.json`, `control_run_protocol.json`, and their result receipts. `python3 -B verify.py` checks the artifacts without rebuilding the circuit. This is still a point-decomposition component, with `candidate_id: null`.

The next promotion gate is a one-worker unpinned N41 query using the same direct-parity transformation on a frozen source and public point. It must preserve a saved positive relation, measure natural search status and memory, and then justify a same-point N131 600 s attempt. Formula size alone is a structural improvement, not evidence of solver speed or relation yield.
