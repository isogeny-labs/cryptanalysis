# Native volcano jobs campaign status

**Status: blocked before timing.** The frozen v1 campaign has no timed rows.
No performance result or claim is available, and the historical comparison
in [`volcano-jobs-historical-observation.md`](../../docs/perf/volcano-jobs-historical-observation.md)
remains unverified.

## Required qualification

The repository's [CPU performance evidence tiers](../../AGENTS.md#cpu-performance-evidence-tiers)
require a timing ratio to retain its evidence tier and say that a failed
preflight cannot be promoted by silently changing tiers. The tier service
defines Tier 0 as a physical Linux host with an audited exclusive CPU and
NUMA partition, fixed frequency, and IRQ routing; its strict preflight
requires administrative control, complete SMT coverage, `nohz_full`, no CPU
quota or overlapping IRQ affinity, fixed frequency, an isolated cgroup, and
`numactl` ([`docs/ISOLATED_BENCHMARKS.md`, Tier 0](../../docs/ISOLATED_BENCHMARKS.md#tier-0-host-isolated-result)).
This campaign's frozen protocol further selects `tier0_host` as its only
qualified timing path and explicitly prohibits substituting a lower tier
([`protocol.md`](protocol.md#isolation-gate-and-run-procedure)). A Tier 1
cloud run is also unavailable: no paid or cloud work is authorized.

## Probe result

The saved read-only host and strict Tier 0 probe outputs are
[`current-executor-host-probe.json`](preflight/current-executor-host-probe.json)
and [`current-executor-tier0-probe.json`](preflight/current-executor-tier0-probe.json).
The Tier 0 probe returned `ok: false` for the frozen example CPU set `4-7`.
It reports `virtualization: container-other`, effective online CPUs `0-4`,
and no host root. The requested CPUs are not covered by the online set. The
isolated cgroup and effective/exclusive cpuset files are unavailable;
`nohz_full`, frequency controls, complete SMT/NUMA topology, throttling and
memory counters, and `numactl` are unavailable. A CPU quota is active, the
runner is allowed on benchmark CPUs, and effective IRQ affinity overlaps the
requested set. The JSON retains all preflight diagnostics, including the
missing cgroup, IRQ, and topology checks.

No timed command was started. The frozen protocol, workloads, binaries,
correctness harness, and commands remain ready for a host that passes the
same Tier 0 checks. This failed probe is retained as qualification evidence,
not as a measurement. No campaign graph, performance index entry, or
benchmark mirror is generated from it. This PR changes CLI job scheduling;
it does not change curve data, isogeny structure, ECDLP results, or
library-kernel measurements. With no qualified campaign metric changed, the
existing canonical curve/volcano research graphs and dashboards remain
current. The campaign-specific plots, benchmark mirror, supplemental index
row, and formal impact audit remain pending until qualified results exist.
