# Go coordinator performance literature and evidence review

Reviewed 2026-11-01 before adding the benchmark instrument or selecting a
candidate optimization.  This note scopes only the Go coordinator bindings in
`bindings/go`; it does not report benchmark results or claim a speedup.

## Repository evidence

- [`docs/COORDINATOR.md`](../../../docs/COORDINATOR.md) defines the append-only
  check-in log, version-vector semantics, reverse-channel push loop, and the
  requirement that `DeltaSince` credit only records actually sent.  Therefore
  an optimization must preserve order, exact line content, and the reached
  vector, not merely return the same number of records.
- [`docs/FFI.md`](../../../docs/FFI.md) makes the C ABI the shared implementation
  boundary and documents that Go calls cross cgo.  Per-record cgo calls and
  fixed-size transfer buffers are consequently part of the measured path.
- [`bindings/go/coord.go`](../../../bindings/go/coord.go) implements
  `VersionVector` and `DeltaSince` by calling `LogLen` and then `LogAt` for every
  record.  Each `LogAt` allocates an 8,192-byte line buffer and a 64-byte peer
  buffer before crossing cgo.  Even a caught-up `DeltaSince` therefore scans and
  copies the complete log.
- [`bindings/go/cmd/ca-coordinator/hub.go`](../../../bindings/go/cmd/ca-coordinator/hub.go)
  invokes `DeltaSince` for every live channel on each push tick.  The caught-up
  case is a production workload rather than a synthetic corner case.
- [`src/coord.c`](../../../src/coord.c) and
  [`include/cryptanalysis/ca_coord.h`](../../../include/cryptanalysis/ca_coord.h)
  already expose `ca_coord_state_vv` and `ca_coord_delta_for`, which traverse C
  state while holding its lock.  They are candidate building blocks, but this
  preregistration does not assume that using them will win after cgo callback,
  copying, and allocation costs are charged.
- Existing correctness coverage in `bindings/go/coord_test.go` and
  `bindings/go/cmd/ca-coordinator/{hub,peer}_test.go` checks log/delta semantics,
  convergence, reconnect behavior, and the rule that a reached vector covers
  only sent records.  These tests are mandatory gates around any candidate.

At the current 8,192-byte line and 64-byte peer buffer sizes, one Go full-log
scan over 8,192 entries requests at least 67,633,152 bytes of temporary byte
buffers before accounting for strings, maps, slices, or cgo overhead.  This is
a source-level lower bound, not a measured allocation result.

## Primary external guidance

- Go 1.21 `testing` package documentation:
  <https://pkg.go.dev/testing@go1.21.13>.  Go 1.21 benchmarks use the `b.N`
  loop; `B.ReportAllocs`/`-benchmem` supply bytes and allocations per operation.
  The benchmark therefore avoids the newer `B.Loop` API.
- Go command testing flags:
  <https://pkg.go.dev/cmd/go@go1.21.13#hdr-Testing_flags>.  Fixed
  `-benchtime=100x`, explicit `-count=1`, and an outer preregistered repetition
  schedule prevent the harness from silently changing the number of operations
  between arms.
- Go diagnostics guide: <https://go.dev/doc/diagnostics> and runtime pprof
  documentation: <https://pkg.go.dev/runtime/pprof@go1.21.13>.  CPU and heap
  profiles are diagnostic follow-ups; profiled trials are not mixed into the
  decisive unprofiled timing distribution.
- cgo command documentation: <https://pkg.go.dev/cmd/cgo@go1.21.13> and the Go
  runtime cgo-call implementation:
  <https://github.com/golang/go/blob/go1.21.13/src/runtime/cgocall.go>.  A cgo
  transition has runtime bookkeeping, so reducing calls is a plausible
  mechanism that still requires end-to-end measurement.
- Go race detector guidance: <https://go.dev/doc/articles/race_detector>.
  Race runs are correctness gates only because their instrumentation changes
  performance.
- Linux `getrusage(2)` documentation:
  <https://man7.org/linux/man-pages/man2/getrusage.2.html>.  The benchmark emits
  process user-plus-system CPU nanoseconds per operation from this counter; its
  underlying microsecond resolution is recorded and wall time remains the Go
  benchmark clock.
- Linux `perf stat(1)` documentation:
  <https://man7.org/linux/man-pages/man1/perf-stat.1.html>.  `perf stat` and
  profiles may explain cycles, cache misses, faults, and context switches after
  the unprofiled baseline is frozen.  They are diagnostic evidence, not a
  substitute for paired wall/CPU/allocation measurements.
- The official Go download manifest, retrieved from
  <https://go.dev/dl/?mode=json&include=all> on 2026-11-01, identifies
  `go1.27.3.linux-amd64.tar.gz` as 70,588,678 bytes with SHA-256
  `65efbc80fdc1fa2cd2631cad5b481777a68e8725f34e89f50fc6ac714e379b40`.
  The remote runner pins all three fields and refuses to extract or build when
  any differs.
- RunPod's Pod API describes CPU placement memory as a provider `memory`
  quantity, not an IEC GiB byte conversion:
  <https://docs.runpod.io/api-reference/pods/GET/pods-id>.  The exact v5
  `cpu3c` allocation returned provider memory `64` while its cgroup v2
  `memory.max` was exactly `64000000000`.  The runner must therefore bind the
  provider's raw value and the observed decimal-byte enforcement limit as two
  separate fields.  The controller records the former as
  `cpu_guard.provider_memory_value`; the runner accepts the latter through
  `--expected-memory-bytes`.  Treating `64` as `64 << 30` is the retained v5
  infrastructure failure, not benchmark evidence.

## Consequences for the instrument

The added benchmark fixes the Go compatibility floor at 1.21, constructs logs
outside the timed region, measures both a caught-up channel and a one-record
delta at 1,024 and 8,192 log entries, reports allocations, wall nanoseconds,
and process CPU nanoseconds per operation, and hashes the returned lines and
canonical sorted vectors after timing.  The fixture normalizes sender time so
its encoded log is reproducible while retaining valid C-core check-ins.

No relevant published benchmark for these repository-specific Go wrappers was
found in the repository notes or official Go material above.  That absence is
an evidence gap, not a novelty claim.  No timed Go measurement had been run when
this draft and benchmark instrument were written; the local image also lacked
the Go compiler/toolchain, so compilation remains a preflight obligation.

## V8 fixed-peer-key follow-up

Reviewed 2026-11-01 before writing the v8 runner, formal analyzer, or protocol.
The repository sources above remain the semantic and measurement basis.  The
additional source review covered production commits
`7c712913b7e912494e87c35e854cfd0129bad89c` and
`37b96362a53a7364dd4cc2a18f450a3627ec08d3`, their exact `coord.go` diff,
the retained v7 analysis/report, and the canonical experiment-protocol guide
at `crypto-autoresearcher:docs/experiment-protocol.md`.

The candidate replaces transient string lookup keys with owned fixed-size peer
keys during `VersionVector`, `DeltaSince`, and `DeltaFrom` scans.  Its production
commit also adds tests; the synthetic A/B build trees deliberately differ only
at `bindings/go/coord.go` and add the same pinned benchmark blob plus the same
candidate `coord_test.go` blob.  The shared tests exercise maximum-length,
short, shared-prefix, and embedded-NUL peer keys against both arms.  This is an
engineering optimization, not a cryptographic or novelty claim.  V7's retained
rows motivate the candidate but cannot decide v8: v7 did not prospectively bind
its exact bootstrap procedure, an L2 attestation, or a numeric PSI gate.

The Linux kernel PSI documentation, retrieved from
<https://docs.kernel.org/accounting/psi.html> on 2026-11-01, defines `some` as
the share of time with at least one task stalled, `full` as the share with all
non-idle tasks stalled, and `avg10` as a ten-second percentage trend.  V8
therefore parses both CPU and memory records rather than treating the strings as
opaque metadata.  Its prospective timing gate requires every before/after
snapshot for all 276 rows to have CPU `some avg10 <= 10`, CPU `full avg10 = 0`,
and memory `some/full avg10 = 0`, alongside zero steal, cgroup throttling,
memory-event, and affinity changes.  PSI is a host-contention screen, not a
substitute for the paired design or those other isolation checks.

The exact empirical paired-bootstrap median distribution is fixed before data:
enumerate the joint tenth/eleventh order-statistic mass for 20 draws with
replacement from the 20 observed pair ratios, use exact rational arithmetic,
and take `inf{x: CDF(x) >= 1/480}`.  The `1/480` lower quantile is the
two-sided Bonferroni allocation of family alpha `1/20` over twelve timing
comparisons.  No RNG, Monte Carlo draw count, interpolation, or post-result
choice is involved.
