# #880 native CPU evidence status

**Status: blocked before campaign timing.** The new v1 protocol is independent
of the historical measurements in PR #880. No timed output was collected for
this protocol.

The original PR description records an exploratory C library performance
index, a two-thread rho kernel, instruction counts, field-operation timings,
and ECC2K-130 one-worker throughput/start-up summaries. The report did not
include the raw per-kernel compare JSON/CSV, A/A pair records, original
binary/build receipts, exact f131 benchmark source/command, or complete
ECC2K paired rows. The body remains preserved verbatim in the PR; its values
are not silently removed. The exact historical gaps and source citations are
listed in [`REPORT.md`](REPORT.md).

## Host qualification

The recurring host-isolation obstruction is tracked in
[`problems/cpu-performance-tier0-host-qualification.md`](../../problems/cpu-performance-tier0-host-qualification.md)
and indexed in [`problems/README.md`](../../problems/README.md). This branch's
read-only strict Tier 0 probes for both the one-CPU set `4` and proposed
multi-CPU set `4-7` returned `ok: false`. They observe `container-other`,
online CPUs `0-4`, no host root,
no isolated cgroup or effective/exclusive cpuset, no `nohz_full`, unavailable
frequency and SMT/NUMA details, missing throttling/pressure/interrupt
counters, no `numactl`, an active CPU quota, runner affinity on the requested
cores, and IRQ affinity overlap. Full probe output is preserved in
[`preflight/current-executor-tier0-single-probe.json`](preflight/current-executor-tier0-single-probe.json)
and [`preflight/current-executor-tier0-probe.json`](preflight/current-executor-tier0-probe.json);
the host summary is in `preflight/current-executor-host-probe.json`.

The Tier 0 service in this branch currently pins one logical CPU. That does
not qualify the historical two-thread `dlp/c_rho_ec44_mt` measurement. A
reviewed multi-CPU worker-affinity extension and its strict preflight are also
required before that panel can run. No lower tier or paid/cloud allocation is
substituted. No timed command started.

Until a qualified host and the multi-CPU service extension are available,
the C and ECC2K campaign plots, benchmark mirrors, and new index rows remain
pending. The canonical research graphs and dashboards checked by this audit
remain current because this PR changes engineering paths but contributes no
new qualified scientific/curve metric. The historical timing-summary chart
is marked as unverified history, not as a fresh campaign graph.
