# Widened XOR matrices propagate locally but double early N131 search CPU

On the exact archived N131 W18 inverse-trace public-target formula, raising CryptoMiniSat's matrix limits admits six **3,315 × 9,132** local XOR blocks that the default policy discards. These matrices make branch-local propagations, but the same **20,000-conflict** search boundary retains **185,587 free variables** in both arms. The widened policy consumes **2.577 sampled solver CPU seconds** versus **1.233 seconds** for the default policy. This bounded diagnostic directs the next solver work toward constraints that couple the public target to multiple pair outputs.

Both arms read the byte-identical **189,687-variable, 391,305-clause, 56,545-native-XOR** [ordinary XCNF](ordinary.xcnf), SHA-256 `80bb34951b6b57b929a1952fc502782e54ffe0b74aaf984f447ecd066b7f682c`. Its source is the [audited inverse-trace query](../n131_w18_inverse_trace_terminal_20261011/RESULT.md) on curve `EC1N131Ckb1heb5f1998f20b`, public workload `cc09e7eb202a`, raw preimage zero, with the same fixed terminal state and eight free W18 pairs. The [protocol](protocol.json) fixes formula and solver hashes, arm order, one worker, a 20,000-conflict solver cap, a 120-second solver time cap, a 180-second parent wall cap, and 4 GiB combined RSS.

| Solver-stage measure | Default matrix limits | 4,000 rows / 10,000 columns / 8 matrices |
| --- | ---: | ---: |
| Accepted matrices at first initialization | 5 small blocks | 6 medium plus 2 small blocks |
| Matrix rows rejected for size | 7 | 1 |
| Matrix columns rejected for size | 8 | 0 |
| Restarts at 20,000 conflicts | 81 | 81 |
| Free variables in last restart row | 185,587 | 185,587 |
| Solver-reported propagations | 31 million | 32 million |
| Sampled solver CPU | 1.233 s | 2.577 s |
| Solver-stage wall / sampled peak RSS | 10.384 s / 138.7 MB | 26.392 s / 242.1 MB |
| Solver status | `BOUNDED_UNKNOWN` | `BOUNDED_UNKNOWN` |

The [default](default.result.json) and [widened](matrix8.result.json) receipts retain the flags, exit codes, raw transcript hashes, conflict-limit status, CPU samples, wall intervals, memory samples, and last restart rows. Both exit normally at the conflict cap, enter active search, and have empty stderr. The [audit](audit.json) verifies identical formula and public workload, source and binary hashes, active matrix initialization and restarts, protocol binding, and resource caps. CPU and wall ratios are exploratory on this heavily contended macOS host; the fixed conflict boundary and unchanged free-variable count are the operative diagnostics. This is a point-decomposition solver-stage comparison with `candidate_id: null`.

The largest XOR component still exceeds both settings at **32,152 rows × 91,403 columns** and is not used by either arm. Before any larger Gaussian attempt, its sparse rank, memory growth, and target-coupled elimination value need an explicit preflight. The medium blocks produced branch-local propagation, including 1.484 million truth-find checks in one block, but no durable reduction in the solver's reported free-variable count at this conflict boundary. A complete N131 ordinary decomposition search should next be driven by a target-coupled partial-sum or output-coordinate constraint and checked on the known N41 unpinned public relation before transfer.
