# Native CPU performance replay lacks a qualified Tier 0 host

- **Status:** `open`
- **Kind:** empirical bottleneck; host access and measurement-service capability limit
- **Affected work:** [PR #880 and its independent v1 campaign](../experiments/c-kernel-cpu-v1/REPORT.md), [frozen #880 protocol](../experiments/c-kernel-cpu-v1/PROTOCOL.md), [#963 volcano-jobs v1 campaign](https://github.com/aburan28/cryptanalysis/pull/963)
- **Next action owner:** repository performance-measurement lane
- **Last updated:** 2026-10-19

## Problem

The exploratory native CPU timings in PR #880 cannot be promoted to qualified
wall-time evidence because the original host/raw records are missing, this
executor fails the strict Tier 0 isolation checks, and the current service
cannot prove affinity for its two-worker comparison.

The blocked #880 campaign is pinned to baseline
`9b45e8c8db2f078a2419ad604ab427856391bd79` and candidate
`30dcdce8147d9b217760e07122e1a839486a0175`. It covers the C library's 34
fixed-input performance kernels and the ECC2K-130 CPU field/table-walk paths.
A one-thread measurement needs one isolated CPU; the historical two-thread
rho row needs two reserved physical cores with all worker threads proven to
remain within their exclusive partition. The current service version pins one
logical CPU only. Tier 0 requires an auditable physical Linux host with
exclusive CPU/NUMA control, fixed frequency, IRQ routing, quota counters, and
correctness/raw-pair receipts under `docs/ISOLATED_BENCHMARKS.md`.

## Evidence and uncertainty

- **Observed:** The original PR body identifies its wall timings as
  exploratory measurements on a 2-vCPU cloud-agent VM without isolation
  receipt. The source tree and PR payload contain summary values but no
  original per-kernel compare JSON/CSV, A/A/A/B raw pair rows, host receipt,
  or exact ECC2K field-benchmark source/command. See the evidence audit in
  [`experiments/c-kernel-cpu-v1/REPORT.md`](../experiments/c-kernel-cpu-v1/REPORT.md)
  and the preserved source summaries in
  [`historical-claims.csv`](../experiments/c-kernel-cpu-v1/historical-claims.csv).
- **Observed:** Saved strict preflights for one requested CPU (`4`) and for
  the proposed multi-CPU set (`4-7`) both returned `ok: false`:
  `container-other`, host root unavailable, online CPUs `0-4`,
  requested CPUs not online, isolated cgroup/cpuset files missing, empty
  `nohz_full`, active CPU quota, runner allowed on benchmark CPUs, no
  `numactl`, missing frequency/topology/pressure/interrupt counters, and IRQ
  overlap. Full probe output is in
  [`preflight/current-executor-tier0-single-probe.json`](../experiments/c-kernel-cpu-v1/preflight/current-executor-tier0-single-probe.json)
  and [`preflight/current-executor-tier0-probe.json`](../experiments/c-kernel-cpu-v1/preflight/current-executor-tier0-probe.json).
- **Observed:** `docs/ISOLATED_BENCHMARKS.md` says the current Tier 0 runner
  pins one logical CPU and that multiworker experiments need an extension
  proving worker affinity. The #880 two-thread result is therefore outside
  the current service's qualified contract.
- **Derived or proved:** no Tier 0 measurement can be collected on the
  currently observed executor under these preflight results. No timing command
  was run. This is an environment and service limitation, not a mathematical
  or performance result.
- **Suspected explanation:** none asserted. Missing host controls and raw
  records explain why qualification is unavailable, not what a future replay
  will measure.
- **Missing capability:** controlled physical Tier 0 executor and tested
  multi-CPU worker-affinity/preflight support. The original observations also
  lack the inputs needed for an exact historical replay.
- **What this evidence does not establish:** a slowdown, a speedup, failure of
  the implementation, or reproduction/validation of the historical numbers.
  A future v1 campaign is independent and will not repair missing original
  provenance.

## What would unblock it

- [ ] Assign a physical Linux Tier 0 host whose full preflight passes for the
  reserved CPU and NUMA sets, fixed frequency, IRQ routing, no quota, complete
  SMT coverage, housekeeping-only runner, and noise counters.
- [ ] Extend the isolated service to support declared multi-CPU execution and
  prove every worker thread stays within the exclusive reserved set; add
  strict preflight and rejection tests for unobservable or overlapping cores.
- [ ] Run the frozen v1 panel and preserve all A/A/A/B raw pairs, fingerprints,
  build/source hashes, failures, and host receipts; pass the complete ECC2K
  correctness replays and report acceptance criteria in the protocol.

Passing these conditions can qualify only the new source pair/workloads and
measurement boundaries in v1. It cannot establish the provenance or validity
of the old PR body figures; the full scientific/index-calculus graph set also
remains separate.

## Next discriminating step

- **Action or proof obligation:** bring up and independently test the strict
  multi-CPU Tier 0 service on a dedicated host, then run protocol v1.
- **Inputs and controls:** exact commits, C 34-kernel IDs and fingerprints,
  f131 operation harness, fixed ECC2K table-walk command, A/A controls, and
  the exact commands and sample counts in
  [`PROTOCOL.md`](../experiments/c-kernel-cpu-v1/PROTOCOL.md).
- **Execution limits and stop condition:** the protocol is Tier 0 only. A
  failed preflight, missing counter, worker escaping the set, correctness
  failure, or noise-gate failure stops promotion; retain every row. No lower
  tier or paid/cloud substitute is allowed.
- **Outcomes and next actions:** a fully qualified panel publishes independent
  v1 reports, graphs, PDF, and benchmark/index mirrors. A failed preflight or
  noisy/incorrect run remains blocked and updates this record without erasing
  historical summaries. A passing panel still leaves the original records
  unverified.
- **Recheck trigger:** an assigned Tier 0 host and tested multi-CPU service
  contract become available.

## Resolution and history

2026-10-19: Added while reviewing PR #880 after inventorying the existing
checkout and PR payload. The current executor's strict preflight failed and
no timed commands ran. The independent campaign protocol is frozen but
unexecuted. Unresolved.
