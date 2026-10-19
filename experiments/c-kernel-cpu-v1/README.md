# PR #880 native CPU evidence package v1

This directory freezes an independent C-library/ECC2K-130 CPU replay protocol
and records why its timing gate is currently blocked. It contains no timing
results.

- [`REPORT.md`](REPORT.md) and [`REPORT.pdf`](REPORT.pdf): historical evidence
gap, graph-impact audit, and source-linked figures.
- [`PROTOCOL.md`](PROTOCOL.md): pinned versions, workloads, controls, commands,
  acceptance rules, and the strict Tier 0 qualification requirement.
- [`BLOCKED.md`](BLOCKED.md): current executor probe failure and stop state.
- [`f131_microbench.cpp`](f131_microbench.cpp): proposed direct-operation
  workload, including a non-timing fingerprint mode.
- [`measure_cli.py`](measure_cli.py): wrapper for preserving/validating ECC2K
  child output and timer boundaries.
- [`historical-claims.csv`](historical-claims.csv): values copied from the PR
  description, explicitly unverified.
- [`source-manifest.json`](source-manifest.json): SHA-256 values for frozen
  protocol, code, figures, and probe records.
- [`campaign-flow.dot`](campaign-flow.dot) and
  [`plot_historical_claims.py`](plot_historical_claims.py): editable figure
  sources; SVG/PNG renderings are beside them.
- [`preflight/`](preflight/): saved host and strict Tier 0 probe output.

No timing command has been started. See the canonical open blocker in
[`problems/cpu-performance-tier0-host-qualification.md`](../../problems/cpu-performance-tier0-host-qualification.md).
