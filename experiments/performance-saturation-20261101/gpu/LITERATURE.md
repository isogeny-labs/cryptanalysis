# GPU A/A study: literature and prior-art check

## V8 prospective update-grid A/B, 2026-11-01

The separately retained v7 run is now the planning baseline for one engineering
variable: the `f4e_update` launch target changes from four to six resident
blocks per SM.  No v7 timing row is reused in the v8 distribution, and this is
not an algorithmic or novelty claim.  The v8 runner constructs both arm trees
from one candidate archive and overlays only the registered baseline
`suite/src/cryptanalysis/f4_gpu.rs` file in the baseline arm.  It hashes the
scoped production diff and refuses any second file difference.

The following sources were checked before the v8 tooling was written:

| source | provenance | consequence for v8 |
|---|---|---|
| [`V7_REPORT.md`](V7_REPORT.md), [`v7-outcome.json`](v7-outcome.json), and retained v7 Nsys SQLite reports | immutable internal measurement, read 2026-11-01 | Keep the exact five matrices and answers.  The primary trace has 2,941 `f4e_update` launches; update is about 51.7% of kernel time.  These observations choose the candidate and mechanism check only; v8 takes fresh warmups, rows, and traces. |
| [`suite/src/cryptanalysis/f4_gpu.rs`](../../../suite/src/cryptanalysis/f4_gpu.rs) and [`suite/cuda/f4_gf2_echelon.cuh`](../../../suite/cuda/f4_gf2_echelon.cuh) | production source, read 2026-11-01 | Change only the host-side update partition count.  Keep 256 threads, 32-word tiles, the 32-part cap, kernel code, and every other launch unchanged. |
| [CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html) and [CUDA Programming Guide, occupancy](https://docs.nvidia.com/cuda/cuda-c-programming-guide/index.html#occupancy-calculator) | official NVIDIA documentation, checked 2026-11-01 | Occupancy is resource-constrained and must be verified rather than inferred from a larger grid.  At the observed 31 registers/thread, 256 threads/block, and 16 KiB shared/block, six blocks use 48 warps, 47,616 registers, and 98,304 bytes shared per SM, the intended RTX 5090 target. |
| [Nsight Systems User Guide, SQLite export](https://docs.nvidia.com/nsight-systems/AnalysisGuide/index.html#exported-data) | official NVIDIA documentation, checked 2026-11-01 | Read `CUPTI_ACTIVITY_KIND_KERNEL` directly after the post-timing trace.  Gate all 2,941 ordered update launches, block/grid dimensions, registers, static/dynamic shared memory, and local memory; profiled durations never enter the speedup distribution. |
| `crypto-autoresearcher:docs/experiment-protocol.md`, `schemas/experiment-export.v1.json`, and `tools/experiment_protocol.py` | sibling canonical contract, read 2026-11-01 | Freeze the analyzer and all thresholds before data, use a ten-test Bonferroni family, enumerate all `6^6` paired-bootstrap resamples with exact rational arithmetic, and emit a real `experiment.export/v1` beside `rows.jsonl`. |

The prospective decisive family has ten one-sided lower bounds: primary device
improvement; complete-stage non-regression on all five cells; and device-stage
non-regression on the four non-primary cells.  The primary median paired
baseline/candidate ratio must be at least 1.02 and its simultaneous lower bound
must exceed one.  Every non-regression median and lower bound must be at least
`1/1.02 = 50/51`.  With family alpha 0.05, each exact lower-tail quantile is
`1/200`.  The run is one attempt on one Secure RTX 5090 pod, with one excluded
warmup and six alternating fresh-process pairs per cell, followed by one Nsys
capture per arm.  NCU remains outside the protocol.

### V8 source-delivery correction

Frozen v8 was classified `prospectively_invalid/superseded_before_data` after
registration: the HTTP bootstrap intentionally fetches the tooling ref with
`--depth=1`, while the v8 arm constructor expected the candidate and retained
baseline ancestor objects to be present.  No provider API was called, no pod
was created, and no v8 row exists.  V9 keeps every scientific threshold and
workload unchanged, but prospectively deepens that same immutable public
tooling ref by 16 commits, verifies `FETCH_HEAD` still equals the bootstrapped
tooling commit, and only then resolves and hashes the two registered ancestors.
The correction is source delivery, not a candidate or statistical change.

### V9 terminal-adjudication correction

Frozen v9 was also classified
`prospectively_invalid/superseded_before_data`, before any provider API call,
pod, or scientific row.  Its scientific analyzer necessarily ran inside the
pod before the HTTP controller produced the final archive and exact-ID cleanup
receipt.  It nevertheless labeled its two timing outcomes as terminal, did not
read `order.tsv`, and could not validate the receipt, internal archive
manifest, extracted inventory, completion marker, runner exit, or deletion and
absence proof.  A remote gate failure exited with status 2 rather than
materializing `invalid_measurement` or `incomplete_session`.

V10 preserves the five cells, one warmup, six alternating fresh-process pairs,
70 exported rows, exact rational ten-test analysis, thresholds, Nsys sequence
and resource gates, and depth-16 source delivery unchanged.  The remote
analyzer now emits only `provisional_mechanical` timing classification.  After
the controller has returned and cleaned up the one pod, a separately
hash-bound finalizer uses the pinned canonical protocol tool and validates the
complete order/row/export/receipt/archive/manifest/completion/cleanup chain.
Its frozen precedence is `incomplete_session`, then `invalid_measurement`, then
`geometry_not_supported`, then `geometry_supported`; it is the sole terminal
adjudicator.  The controller receipt records the exact remote command,
request, source, pod, price, result, and cleanup.  It does not serialize its
own full local argv, so the one-create-attempt claim additionally depends on
the hash-bound controller implementation and its registered argv template.

Historical status of the initial A/A draft: pre-measurement design, 2026-11-01. No pod has been created, no GPU
measurement has been taken, and this study is not frozen. The two arms are
byte-identical copies of the current binary; there is no optimization candidate
and no speedup claim.

## V7 Nsys-only correction, 2026-11-01

V6 is now retained as `invalid_measurement`, not as an infrastructure retry.
Its exact recovered receipt and archive are committed at `0005179e`; the
required NCU phase stopped on NVIDIA's `ERR_NVGPUCTRPERM` after all 10 warmups,
60 unprofiled executions, and two Nsys captures.  The evidence binding and the
rule that the earlier rows are planning-only are in [`v6-outcome.json`](v6-outcome.json).

The v7 design checked these additional primary sources before implementation:

| source | provenance | consequence for v7 |
|---|---|---|
| [NVIDIA GPU performance-counter security guidance](https://developer.nvidia.com/ERR_NVGPUCTRPERM) | official NVIDIA guidance, checked 2026-11-01 | Counter access requires a host-driver policy change or an administration capability. Installing another NCU package, changing sections, or running as container UID 0 cannot grant it. NCU is therefore outside v7 rather than an optional retry gate. |
| [Nsight Systems User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/index.html) | official NVIDIA documentation, checked 2026-11-01 | Keep the post-timing CUDA/NVTX/OS-runtime trace and the `cuda_gpu_kern_sum` and `cuda_api_sum` reports. Profiled durations remain diagnostics and never enter the A/A distribution. |
| [Runpod Pod REST API](https://docs.runpod.io/api-reference/pods/POST/pods) and [Pod lookup](https://docs.runpod.io/api-reference/pods/GET/pods-pod-id) | official provider API, checked 2026-11-01 | The registered request can bind image, placement, lifetime, environment, disk, and ports, but exposes no privileged-container or performance-counter entitlement. Host re-rolling for counter access would be unregistered selection. |
| [`cloud/runpod_http_batch.py`](../../../cloud/runpod_http_batch.py) and [`cloud/runpod_http_recover.py`](../../../cloud/runpod_http_recover.py) | repository transport implementation and tests | V7 permits one allocation only. A normal receipt is required unless the controller disappears; only then may the exact committed recovery tool reconstruct the authenticated, hash-bound result and exact-ID cleanup receipt without a new allocation. |
| [`protocol-http-rtx5090-v6.json`](protocol-http-rtx5090-v6.json), [`v6-outcome.json`](v6-outcome.json), and the recovered v6 archive | immutable internal protocol and observed failure | Preserve the same five cells, exact answers, RTX 5090 placement, byte-identical A/A arms, order, 10 warmups, 60 measured executions, and two Nsys captures. Remove the four NCU captures and every NCU completion gate prospectively; no v6 row enters v7. |

This is a correction to the measurement design, not a performance candidate.
V7 asks only for an admissible A/A noise and Nsys baseline on the exact Secure
RTX 5090 scope.  A hardware-counter campaign requires a separately registered,
explicitly counter-enabled host.

## Sources checked

| source | provenance | consequence for this study |
|---|---|---|
| [`AGENTS.md`](../../../AGENTS.md), especially “Experiment protocol, export and review”, “Remote compute”, and “Run index calculus on a GPU” | repository rule | Write and validate an `experiment.protocol/v1` before data, retain failures, use an ephemeral GPU runner, record the device, and delete every created pod. |
| `crypto-autoresearcher:docs/experiment-protocol.md`, schema `experiment-protocol.v1.json`, and checker `tools/experiment_protocol.py` | sibling canonical contract, read 2026-11-01 | Fix arms, A/A control, workload, order, sample size, metrics, invalidation, analysis, and no-resume semantics before measurement. This file’s protocol remains a draft until an actual preflight and commit are available. |
| [`experiments/f4-gpu-panel-20261007/README.md`](../../f4-gpu-panel-20261007/README.md) and its `receipts/final-rtx4090` | internal measured prior work | The incumbent RTX 4090 result and exact answer gates come from the landed kernel: on the primary D=6 cell, the current profile was gather 67.0 ms, materialise 105.3 ms, panel 809.9 ms, and update 1300.0 ms. The update is the largest kernel. |
| [`suite/cuda/f4_gf2_echelon.cuh`](../../../suite/cuda/f4_gf2_echelon.cuh), [`suite/cuda/f4_gf2_kernel.cu`](../../../suite/cuda/f4_gf2_kernel.cu), and [`suite/src/cryptanalysis/f4_gpu.rs`](../../../suite/src/cryptanalysis/f4_gpu.rs) | current source, read 2026-11-01 | The study must exercise `f4e_panel_block` and `f4e_update` through `f4_matrix_bench`, retain the current 1024-thread panel and 32-word tiled update, and hash these sources in every session. |
| [NVIDIA Nsight Systems User Guide](https://docs.nvidia.com/nsight-systems/UserGuide/index.html) | official, retrieved 2026-11-01 | Use an unprofiled timing run for the A/A evidence, then a CUDA timeline to diagnose launch gaps and kernel shares. CPU sampling is disabled to reduce observer overhead. |
| [NVIDIA Nsight Compute CLI Guide](https://docs.nvidia.com/nsight-compute/NsightComputeCli/index.html) and [CUDA C++ Best Practices Guide](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html) | official, retrieved 2026-11-01 | Counter collection replays kernels and is diagnostic, not timing evidence. Filter to one matching launch of each hotspot and retain LaunchStats, Occupancy, SpeedOfLight, MemoryWorkloadAnalysis, and SchedulerStats. Run this only after the Nsight Systems phase. |
| [Runpod Pods overview](https://docs.runpod.io/pods/overview), [Manage Pods](https://docs.runpod.io/pods/manage-pods), [`cloud/README.md`](../../../cloud/README.md), and [`cloud/runpod_pod.py`](../../../cloud/runpod_pod.py) | official and repository tooling, retrieved/read 2026-11-01 | Request Secure Cloud and exactly one RTX 4090 with a unique name. `runpod_pod.py run` ships the working tree, fetches named outputs, deletes only the pod it created in its `finally` path, and installs a maximum-lifetime stop guard. An SSH-startup failure occurs before that `finally`; retain the printed unique name/ID and explicitly delete that exact pod. Never reuse or operate on an unrelated running pod. |

The retained GPU studies contain no current-vs-byte-identical A/A session and
no Nsight Systems/Compute counter receipt for the landed `e7c2575e` kernel.
This study fills that measurement gap; it does not establish that the kernel is
optimal.

## Frozen workload proposed by the draft

The primary and holdout are members of the fixed five-cell panel. Every warmup,
unprofiled row, and profiler diagnostic must match all four answer fields exactly.

| role | tag | cell and degree | rank | refuted | pinned | word operations |
|---|---|---|---:|---:|---:|---:|
| panel | `k0n13m2d5` | `0:13:2:1234`, D=5 | 27,250 | true | 0 | 10,745,652,033 |
| panel | `k0n9m3d5` | `0:9:3:77`, D=5 | 31,069 | false | 1 | 1,196,809,344 |
| panel | `k1n11m2d5` | `1:11:2:301`, D=5 | 12,091 | false | 0 | 986,408,355 |
| holdout | `k1n11m2d6` | `1:11:2:301`, D=6 | 46,747 | false | 0 | 57,968,918,179 |
| primary | `k0n13m2d6` | `0:13:2:1234`, D=6 | 130,583 | true | 0 | 1,110,114,894,889 |

The runner builds `f4_matrix_bench` once and copies those exact bytes to the
`control` and `current` arm paths. It refuses unequal SHA-256 hashes, an
unexpected GPU, a second GPU, or a foreign compute process. It then performs:

1. one complete warmup per arm and cell, followed by the exact-answer gate;
2. six fresh-process rounds per arm and cell, alternating which arm runs first;
3. the exact-answer gate over all 60 measured executions;
4. Nsight Systems on the primary cell for both byte-identical arms;
5. only after that passes, Nsight Compute on one `f4e_update` and one
   `f4e_panel_block` launch for each arm;
6. a deterministic exact paired bootstrap over the six A/A pairs per cell.

Profiler timings cannot enter the A/A timing distribution. The resulting
interval is a session noise calibration, not an equivalence test. Runpod Secure
Cloud is instance-scoped capacity, not proof of physical-host exclusivity; the
session records requested placement, observed GPU identity, clocks, power,
temperature, utilization, foreign processes, source hashes, and tool versions.

## Safe prospective invocation

Do not run this until `protocol.json` has had a real preflight runtime filled,
has been frozen by the canonical tool, and has been committed before data. The
following shape creates a new pod name and fetch path and omits `--keep`, so it
cannot attach to the unrelated existing pod:

```bash
run_id="gpu-aa-$(date -u +%Y%m%dT%H%M%SZ)-$RANDOM"
out="experiments/performance-saturation-20261101/gpu/runs/$run_id"
python3 cloud/runpod_pod.py run "$run_id" \
  --cloud SECURE --gpu "NVIDIA GeForce RTX 4090" --max-hours 2 \
  --out "$out" -- \
  "GPU_STUDY_SECURE=1 bash experiments/performance-saturation-20261101/gpu/run_gpu_aa.sh '$out' '$run_id'"
```

The chosen image must expose `nsys` and `ncu`, or their absolute paths must be
supplied as `NSYS` and `NCU`. The runner checks the required reports and sections
before building or measuring. If pod creation succeeds but SSH never becomes
ready, `runpod_pod.py` deliberately leaves that newly created pod for diagnosis;
delete only the printed unique name with `python3 cloud/runpod_pod.py down NAME`.

The previous study reports roughly fifteen minutes for two builds and its
matrix panel. This design has one build but adds profiler replay; its draft
runtime and cost are estimates only. The provider prints the actual hourly rate
at allocation, the two-hour lifetime guard bounds accidental compute billing,
and fetched receipts—not an estimate—must carry the final duration and cost.
