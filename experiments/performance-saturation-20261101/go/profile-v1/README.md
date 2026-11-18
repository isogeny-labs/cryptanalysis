# Go coordinator accepted-baseline profile v1

Status: prospective diagnostic design; no profile or benchmark row has been
collected. This study cannot support a speedup claim or select a production
change by itself.

## Question and scope

Where do cgo transitions, CPU samples, Go allocation objects/bytes, and Linux
software-event samples occur in the six retained coordinator scan workloads on
the exact accepted implementation? The source under diagnosis is the retained
production commit `7c712913b7e912494e87c35e854cfd0129bad89c`, tree
`735e671e9492fb890a4e87825644c46bace88e4a`, with
`bindings/go/coord.go` blob `0d3f53806361e7442bc1d108c16b8b847f029918`.
The fixed-peer-key candidate is not an arm: v9 showed allocation ratios of
approximately one, raw clock regressions, and invalid clocks after every row
failed the frozen L2 gate.

The six cases remain:

1. `BenchmarkProfileStateVersionVector/log_1024`
2. `BenchmarkProfileStateVersionVector/log_8192`
3. `BenchmarkProfileStateDeltaSinceCaughtUp/log_1024`
4. `BenchmarkProfileStateDeltaSinceCaughtUp/log_8192`
5. `BenchmarkProfileStateDeltaSinceOneBehind/log_1024`
6. `BenchmarkProfileStateDeltaSinceOneBehind/log_8192`

The experiment-only Go file in this directory is copied beside the retained
`coord_benchmark_test.go` in a synthetic source tree. It reuses that file's
deterministic fixture and correctness digests and changes no production file.

## Literature and evidence checked

- [`../LITERATURE.md`](../LITERATURE.md), retained v7 evidence, frozen
  [`../protocol.v9.json`](../protocol.v9.json), and v9
  [`../remote-peer-key-ab-aa-v9/analysis/analysis.json`](../remote-peer-key-ab-aa-v9/analysis/analysis.json):
  profile the accepted implementation before proposing another candidate;
  never reuse v9 clocks or treat a profile as a timing comparison.
- [`../../../../docs/COORDINATOR.md`](../../../../docs/COORDINATOR.md),
  [`../../../../docs/FFI.md`](../../../../docs/FFI.md), retained
  `bindings/go/coord.go`, `src/coord.c`, and `include/cryptanalysis/ca_coord.h`:
  one scan currently crosses cgo and takes the C log mutex once per log entry;
  correctness must preserve order, raw lines, and the reached-vector rule.
- [Go `runtime.NumCgoCall`](https://pkg.go.dev/runtime#NumCgoCall) and
  [runtime/pprof](https://pkg.go.dev/runtime/pprof): `NumCgoCall` is a
  process-wide cumulative count; CPU profiles are sampled; allocation profiles
  are cumulative. Therefore the overlay brackets the exact operation loop for
  the cgo delta and CPU profile, while the allocation profile explicitly
  includes fresh-process startup, deterministic fixture construction, and the
  operation loop. The sampling rate changes to one immediately before fixture
  construction; earlier startup allocations may retain the runtime default.
- [Go diagnostics](https://go.dev/doc/diagnostics) and
  [`go tool pprof`](https://pkg.go.dev/cmd/pprof): profiles diagnose where
  resources are spent and add observer overhead. CPU and allocation profile
  processes are separate; neither contributes a clock to an optimization gate.
- [`perf-stat(1)`](https://man7.org/linux/man-pages/man1/perf-stat.1.html) and
  [`perf-record(1)`](https://man7.org/linux/man-pages/man1/perf-record.1.html):
  retain raw software-event outputs and failures. The fixed portable event set
  is `task-clock,cpu-clock,context-switches,cpu-migrations,page-faults`; the
  record event is `cpu-clock` at 99 Hz. Hardware PMU events are outside v1
  rather than conditionally selected after preflight.
- Canonical sibling contract
  `crypto-autoresearcher:docs/experiment-protocol.md`: freeze identities,
  commands, fixed N, failure rows, and analysis before data; export one
  `experiment.export/v1`. Since no clock is a metric, no CPU evidence tier is
  inferred.

No published profile exists for these repository-specific wrappers. That is
an evidence gap, not a novelty claim.

## Fixed attempt matrix

Each case is run once in each of five fresh-process modes, for exactly 30
attempts. An attempt is retained even when the profiler or event is
unavailable.

| mode | fixed operations | retained artifacts | interpretation |
| --- | ---: | --- | --- |
| `cgo-count` | 100 | benchmark output and correctness digest | `runtime.NumCgoCall` delta per operation; process-wide diagnostic |
| `go-cpu` | 20,000 | loop-bracketed CPU pprof | sampled CPU attribution only |
| `go-alloc` | 100 | one cumulative `allocs` pprof after the loop | startup-plus-fixture-plus-loop allocation attribution |
| `perf-stat` | 20,000 | raw delimited stat output/stdout/stderr | full fresh-process software-event counts; fixture is included and disclosed |
| `perf-record` | 20,000 | `perf.data`, `perf script`, stdout/stderr | full fresh-process sampled stacks; fixture is included and disclosed |

Every benchmark process uses `GOMAXPROCS=1`, `CGO_ENABLED=1`, `-test.cpu=1`,
`-test.count=1`, `-test.benchmem`, an exact case regex, and the official pinned
Go 1.27.3 archive (70,588,678 bytes, SHA-256
`65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40`).
The build is `go test -c -trimpath -buildvcs=false`; its binary hash is bound by
a pre-data artifact amendment. A fresh process gets exactly one case and mode.

For `go-cpu`, set `MISAGI_CPU_PROFILE` to a create-once output path and
`MISAGI_PROFILE_EXPECTED_N=20000`. For `go-alloc`, set
`MISAGI_ALLOC_PROFILE` and `MISAGI_PROFILE_EXPECTED_N=100`; the overlay refuses
CPU and allocation profiling together. The expected-N guard skips Go's initial
`b.N=1` subbenchmark discovery call so only the registered final-N call can
create the one-shot profile. Allocation stack totals include process startup
and fixture construction and must be labeled that way. The cgo delta is read only from the
unprofiled `cgo-count` mode. `ns/op`, profiler durations, and elapsed command
time are retained diagnostics but are explicitly not metrics.

## Completion and stopping

Attempt the lexicographically ordered case list above, with modes in table
order, once each, then stop. There are no replacement rows, result-dependent
extensions, candidate arms, or infrastructure retries under the same run ID.
A non-zero exit, unreadable profile, missing correctness digest, unavailable
perf event, timeout, or interrupted process is a retained failed attempt.

The only terminal classifications are `complete_diagnostic`,
`incomplete_diagnostic`, and `wrong_answer`. `complete_diagnostic` means all
30 attempts and their required artifacts are present and every repeated
correctness digest matches the retained case digest. It does not mean a
candidate is supported. All classifications admit zero speedup claims.

## Required follow-up before execution

The adjacent protocol remains a draft until the analysis/runner identities,
synthetic source archive, binary, exact perf executable/runtime closure,
backend placement, and canonical export path are hash-bound. Register and
freeze that completed record in one commit, commit the freeze-file change in a
later commit, and take no profile or benchmark row before both commits exist.
