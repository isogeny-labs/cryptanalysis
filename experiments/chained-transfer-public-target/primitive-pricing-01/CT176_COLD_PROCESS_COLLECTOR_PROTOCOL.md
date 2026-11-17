# CT176 — prospective independent-process paired transfer collector

Date: 2026-11-17 UTC. Scientific standing: **[pcc:unverified]**. This contract is committed before collector implementation or native measurement. It extends CT175 in cryptanalysis PR #1700; source-only work is not an end-to-end ECDLP claim.

## Immutable subject and strata

- The previously frozen real CT125 selected public fixture is `experiments/chained-transfer-public-target/evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json`, Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`, exactly 48 rows, two directions (0→2, 2→0), four cofactor sectors, six scalar *diagnostic labels* (0,1,2,17,12345,2771710) per sector/direction; eight exceptional identity rows and 40 nonidentity rows.
- The executable is the CT175 `ct172-replay --cold-route INDEX ARM` source on a separately pinned native build, not a newly substituted evaluator. Every invocation has exactly one public packet and one arm; never pass a scalar for point construction.
- Arm A = `direct_composite`; arm B = `strongest_retained_lift_chain`. Compare only the same frozen packet on the same physical host and executable.
- For each of 48 packets, **eight fixed paired blocks** of six separate processes in order **A,B,B,A,A,A**: first four are paired ABBA, final two provide A/A drift controls. Total planned invocations = `48×8×6=2304`. The entire 48-operand roster is required; no stopping when an apparent improvement appears. Packet order is a deterministic shuffle from the fixed seed `20261117` for each block, identical for both arms; block sequence is fixed independently of outcomes.
- Raw external elapsed monotonic wall time starts immediately before process spawn and ends after process termination and stdout/stderr collection. Preserve literal stdout, stderr, exit, timeout/failure, host metadata, on-target verification, exact target 19 words and 21 primitive counters, peak RSS as reported by the process, in-process route/setup nanoseconds and immutable executable/fixture digests. Never replace an unsuccessful subprocess with an unlogged rerun.

## Admission and invalidation

The collector must default to **plan-only** and refuse native execution without an explicit `--execute` and the positive admission token `--admission-approved`; this does not itself grant AWS/EKS/Spot permission. The existing paid STOP and owner/runner admission take precedence. An exact executable SHA-256 must be supplied at invocation and checked before any process starts. The Git blob of the fixture must also be checked. The binary must have been typechecked, linked and passed CT172 full native 48-case parity before first paid timing.

Every subprocess JSON must use CT175 schema `ct175-single-public-packet-cold-route/v1`, match selected index, from/to, sector, scalar diagnostic label, A/B route, exact public source and canonical destination key (19 unsigned 32-bit words) and exact counter dictionary (21 nonnegative integer fields) against immutable fixture. All JSON numbers requiring exact integer semantics must reject booleans and floats. A/A controls are mandatory. Reject malformed, duplicate, contradictory and unverified outputs, but preserve raw failure records. The collector must not quietly trim samples, interpolate failures, or report a speedup on failed/incomplete panels.

Write-only fresh JSONL output: an identifying manifest first, an ordered entry per attempted process, and a terminal record with explicit counts/verification status; never overwrite or append a partial previous run. A partially completed file remains a failed/incomplete record, not publishable timing evidence. Explicitly avoid shell interpretation and `cargo run` for timed commands.

## Cost and decision gates

These process timings are **cold transfer-only**, not a cold prime-field discrete-log solve, and the selected 48 sample is not the independent 695/701 raw replay. The longer-term required cost is: `S_candidate = cold_setup + source→target transfer + target_solver + inverse/recovery + linear_algebra + verification + memory/overheads`, on the identical public instances versus strongest optimized rho, BSGS and index calculus. Separately price **actual** `C169,C13a,C13b,N2_actual,D_padd` on the same host and operands. Independent full 695/701 custody and signed PCC remain mandatory; only an independently reproduced full-solve ratio `S_baseline/S_candidate>1` with uncertainty, all costs and successful answers can establish advantage. Do not promote a warm route or component improvement.

## Sources and restrictions

CT125, CT126, CT172–CT175, cryptanalysis PRs #1523/#1533/#1692/#1700, crypto #3877/#3904/#4215, GPU IC #4178, latest cryptanalysis AGENTS and original frozen source. Richelot crypto #4514 is separately active; avoid its branch. Locked crypto-autoresearcher vault is not to be opened. Research-KB/service and authenticated 695/701 object-store fixtures are inaccessible in this run. No novelty or signed verification inferred. [pcc:unverified]
