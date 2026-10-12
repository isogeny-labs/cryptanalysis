# Gaussian activation on the frozen N131 seven-pair public formula

Raising CryptoMiniSat's matrix limits activated **six `3315 × 9132` XOR
matrices and one `277 × 2504` matrix** on the exact seven-pair public-point
XCNF. The frozen one-worker replay searched through **300.857 solver CPU
seconds**, ending at its soft CPU cap with **`BOUNDED_UNKNOWN`**. Thus the
setting exercised the intended Gaussian propagation, while its capped search
returned no relation row for rank measurement.

The formula is byte-identical to the [audited ordinary query](../n131_w18_four_seed_sevenpair_ordinary_20261011/RESULT.md):
SHA-256 `eca62860f7842396421cc522211c7efddc62db4a51c3bb38109ea972d50fcbf9`,
curve `EC1N131Ckb1heb5f1998f20b`, workload `cc09e7eb202a`, and the same
public subgroup point. The replay changed only the solver flags
`--maxmatrixrows=4000 --maxmatrixcols=10000 --maxnummatrices=7`.
Its protocol froze the binary hash, formula hash, one-worker cap of 300 solver
CPU seconds, 4,500 solver wall seconds, and 4-GiB combined RSS cap before
the run. The original 44,172-row matrix remained outside the raised limits.

| Solver-stage measure | Default matrices | Raised matrix limits |
| --- | ---: | ---: |
| Selected matrices at initialization | five `52 × 356` | six `3315 × 9132`; one `277 × 2504` |
| Solver CPU seconds | 300.893746 | 300.856764 |
| Solver wall seconds on contended host | 1,380.671349 | 669.153611 |
| Sampled peak parent plus solver RSS, bytes | 461,537,280 | 572,850,176 |
| Restart rows | 2,681 | 2,528 |
| Terminal status / stop | `BOUNDED_UNKNOWN` / `CPU_SOFT_LIMIT` | `BOUNDED_UNKNOWN` / `CPU_SOFT_LIMIT` |

The matrix-enabled [solver log](solver.stdout.txt) records Gaussian
propagation and elimination in the enabled matrices; its stderr is empty and
it has no SAT or UNSAT line. The [terminal receipt](run_result.json) and
[independent audit](audit_result.json) check the original audited archive,
restored formula bytes, frozen source and binary hashes, solver flags,
resource cap, raw streams, and status. The restored local raw formula was
removed after its byte hash passed; the original query retains the
compressed formula. The replay is a solver-stage diagnostic. Its wall time
excludes the original target-dependent formula construction, and this host
has no isolation receipt, so the wall-time ratio is not an online IC
speedup. This proposal keeps `candidate_id: null`.

The next source-to-output step should generate pair-output proposals from a
fresh public target **before** opening the W18 selector families. The
[affine-plane inverse](../n131_affine_plane_block_inverse_20261010/RESULT.md)
already extracts four-atom sources efficiently for a supplied output;
the [target-split S3 root method](../n131_mixed_s3_halftrace_split_20261010/RESULT.md)
reduces repeated fixed-output inversion work. A concrete next gate is an
unpinned N41 public point with a frozen target-conditioned proposal law,
all failed proposals charged, and independent group replay of any returned
row. Its measured proposal count and cost must support an N131 one-worker,
4-GiB source-bound cap before another challenge-field query.
