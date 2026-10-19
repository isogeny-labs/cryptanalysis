# Reused-buffer sparse row reduction

Reusing one scratch vector for each sparse-row XOR preserved all five exact N41 block exclusions and the retained public-relation block. It did **not** improve this reducer's measured throughput: five of six N41 cells ran slower than the preceding dependency-traced version, and the frozen N131 120-second prefix screen reached 11,000 rows at 118.968 s, versus 114.517 s for the preceding version at the same checkpoint. The N131 screen ended at `WALL_CAP`; the public-target block remained gated with status `UNKNOWN_search_cap`. This is a component experiment with `candidate_id: null`.

The [preceding trace experiment](../n41_n131_trace_block_macaulay_20261019/RESULT.md) defines the exact N41 and N131 fields, curve IDs, W11/W33 encodings, target-conditioned 13-term eliminant, and degree-six row family. This run used the same hashed `.eqs` files. The only algorithmic change was to retain a scratch vector across reductions instead of allocating a fresh output vector for every sorted symmetric difference. The compiled source, binary hash, compiler, flags, and checked Sage runtime are retained in [build metadata](build_result.json) and [runtime info](sage_runtime_info.json).

| Frozen cell | Result | Trace wall | Reused-buffer wall | Reused-buffer sampled combined peak RSS |
| --- | --- | ---: | ---: | ---: |
| N41 target 0, left 0–3 | `REJECT_CERTIFICATE` | 0.719 s | 0.679 s | 32,374,784 B |
| N41 target 0, left 252–255 | `UNRESOLVED_AT_DEGREE6` | 2.569 s | 2.707 s | 34,799,616 B |
| N41 target 0, left 512–515 | `REJECT_CERTIFICATE` | 0.672 s | 0.716 s | 34,701,312 B |
| N41 target 1, left 0–3 | `REJECT_CERTIFICATE` | 0.449 s | 0.537 s | 32,686,080 B |
| N41 target 1, left 252–255 | `REJECT_CERTIFICATE` | 0.737 s | 0.760 s | 35,012,608 B |
| N41 target 1, left 512–515 | `REJECT_CERTIFICATE` | 0.754 s | 0.879 s | 34,914,304 B |
| N131 constructed positive | `WALL_CAP` | 11,000 rows at 114.517 s | 11,000 rows at 118.968 s | 556,924,928 B |
| N131 public raw point | `GATED_BY_POSITIVE_CAP` | — | — | — |

The [N41 protocol](query_protocol_n41.json) froze one worker, 120 s per cell, 4 GiB, all six inputs, and prerequisite hashes before its run. The [N131 prefix protocol](query_protocol_n131.json) froze one worker, **120 s**, 4 GiB, the positive-first gate, and the N41 verification result. It explicitly labels this run `N131_PREFIX_SCREEN_NOT_FULL_590S_GATE`. The N131 last emitted checkpoint reports 11,000 independent pivots, 1,179,320 row reductions, and 521,682,944 B raw worker peak; the combined peak and exact parent wall appear in the [receipt](n131_t0_a0.receipt.json). A progress checkpoint is a lower bound on rows processed before the cap, not a terminal row count. Timings are ordinary-host diagnostics without an isolation tier.

`python3 verify_n41.py` replayed every exclusion certificate against the frozen equations, checked all six expected statuses, and passed. `python3 verify_n131.py` checked the input and runtime hashes, prior independent Sage audit, N41 gate, 120-second cap receipt, and public gating; it passed. Their stdout and stderr are retained. The [proof map](PROOF_MAP.md) links the unchanged certificate theorem and finite checks.

This negative throughput result redirects the next iteration toward the ordering and structure of the target-conditioned row family. In the current order, all 596 multiples of one N131 coordinate are processed before the next coordinate, so the 17,000-row 590-second run touched only a prefix of the 131 coordinates. An interleaved or target-informed row order can be tested on the same six N41 cells, then screened on the N131 positive before attempting the public point. Its stopping decision must retain `UNKNOWN_search_cap` if no certificate is emitted within the resource envelope.
