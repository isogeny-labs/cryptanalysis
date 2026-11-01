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
