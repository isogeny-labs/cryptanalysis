# GPU A/A study: literature and prior-art check

Status: pre-measurement design, 2026-11-01. No pod has been created, no GPU
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
