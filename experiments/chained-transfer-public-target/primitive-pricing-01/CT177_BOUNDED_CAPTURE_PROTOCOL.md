# CT177 — prospective bounded process-output capture protocol

Date: 2026-11-17 UTC. Standing: **[pcc:unverified]**. Frozen before CT177 collector implementation. Base: merged CT176 PR #1700, source `ct176_cold_process_collector.py` and tests, exact original selected 48 public Jacobian packets (Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`).

## Defect and measured/observed scope

Existing CT176 `run_sample` invokes `subprocess.run(..., capture_output=True)` and only *after termination* checks `len(stdout)>131072` and `len(stderr)>131072`. The condition does not limit the bytes allocated while the child is running. A misbehaving, compromised or unexpectedly verbose native executable can exhaust collector memory before the evidence refusal is written. This is a code-level resource-bound defect; no real CT125 native run or observed excessive output is alleged.

## Amendment to the frozen measurement contract

Retain the identical 48 × 8 × A/B/B/A/A/A roster, known-scalar-blind public inputs, original fixture and executable digest admission, 19-word target checks, 21 route-counter checks and all cold wall/memory/evidence fields. For each child, stream stdout and stderr via **nonblocking pipes with a selector** while the process is alive. Store at most `MAX_CAPTURE + 1` bytes of either stream; the extra byte is an overflow sentinel. Do not use an unbounded `communicate`, `subprocess.run(capture_output=True)`, or unbounded temporary file. A timeout or limit hit must stop the process (and its new process group on POSIX), reap it, preserve any captured prefix as base64 and SHA-256, explicitly refuse the row, and stop the full panel without retrying or trimming a completed panel into a success. No oversized sample may be classified `verified`. Record external monotonic elapsed including process creation, execution and stream draining. Two streams must be drained concurrently without deadlock. On valid bounded output, the existing child-evidence validator remains unchanged.

A refusal's captured bytes are *bounded prefixes*, not full lossless output; do not describe them as full raw process output when the cap is exceeded. Only successful rows retain lossless full stdout/stderr.

## Predetermined negative controls

1. Baseline one-line valid synthetic CT175 JSON passes with unchanged canonical-output/counter verification.
2. Synthetic child writes >1 MiB to stdout before exit: result refuses with `capture limit`, retained prefix length <=131073 and nonzero evidence digest.
3. Symmetric >1 MiB stderr flood: same properties.
4. Child sleeps beyond a one-second timeout: refusal `timeout`, bounded elapsed, no panel success.
5. Nonzero exit with bounded output retains its exit, raw stream and refusal.
6. All previously authored 24 CT176 test cases and frozen fixture plan remain intact, both normal and `python -O` modes.

The source CI must import and execute these synthetic controls with no native executable, no paid hardware and no external-network dependency. Preserve any failure and require exact-head CI before treating source behavior as checked. This test work is neither independently signed PCC nor a native arithmetic benchmark.

## Evidence and limits

Sources inspected: cryptanalysis `AGENTS.md`; CT172/174/175/176 PRs and report, current main source/test; crypto #3877/#3904/#4215 and concurrent #4514. Shared research-KB service and authenticated 695/701 corpus are not mounted in this runtime; no novelty or whole-corpus assertions follow. User/owner EKS, Spot, GPU and budget STOP, original native parity, independent custody, measured `C169,C13a,C13b,N2_actual,D`, best same-target cold rho/BSGS/IC and signed PCC gates remain unchanged. Not a complete ECDLP attack or a speedup.
