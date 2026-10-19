# #880 C and ECC2K-130 native CPU campaign v1

**Status: frozen as a proposed independent replay; no timings have been
collected.** This campaign is separate from the exploratory measurements
summarized in PR #880. It cannot reconstruct or validate those original runs,
whose exact per-kernel raw rows, host receipt, and ECC2K commands were not
committed.

## Question and limits

Compare the C library's fixed-input kernel performance and the ECC2K-130
CPU table walk/start-up on the exact source pair below. Verify all 34 C
kernel fingerprints, the field-operation outputs, and the ECC2K walk/check
results. The campaign may support only the measured kernel, host, build,
workload, and timer-boundary claims. It does not measure CUDA, Metal, other
CPU architectures, full ECDLP performance, or an algorithmic operation-count
improvement.

The C panel covers all 34 `ca_perfbench run --full` kernel IDs, one-thread
wall time, the two-thread `dlp/c_rho_ec44_mt` case, A/A noise, and deterministic
Callgrind instruction counts. The ECC2K panel has three distinct measurements:

1. direct `f131::mul` and `f131::sqr` versus the old packed polynomial path,
   using the checked-in `f131_microbench.cpp` workload;
2. the table-walk CPU throughput command with one worker and fixed geometry;
3. cold process-start plus table-build/arithmetic-check latency using the
   `check` command.

## Immutable source pair and builds

- Baseline: `9b45e8c8db2f078a2419ad604ab427856391bd79`.
- Candidate: `30dcdce8147d9b217760e07122e1a839486a0175`.
- C harness: this PR's `tools/ca_perfbench.c`, overlaid on both revisions by
  `scripts/perf/perfindex.py build --c`, as prescribed in
  [`docs/perf/PERFORMANCE_INDEX.md`](../../docs/perf/PERFORMANCE_INDEX.md).
- Compiler/build configuration: one recorded GCC/CMake toolchain, separate
  clean output roots, CMake Release, `-O3 -DNDEBUG`, `CA_NATIVE=OFF` for both.
  Do not reuse a candidate object or generated file in the baseline build.
- ECC2K builds: same host C++ compiler, `-O3 -std=c++17 -pthread -march=native`
  (or the compiler's equivalent native flag), `WALK=table`, separate `BUILD`
  directories, and the same `HostTable`/KAT sources. Record complete compiler,
  linker, feature, source, executable, and workload hashes.

The source pair is fixed even if the PR's target branch advances. Any change to
source, compiler, flags, kernel list, sample count, or workloads requires a
new protocol version and fresh outputs.

## Qualified host and isolation

This protocol requires Tier 0 only. Run on a controlled physical Linux host
whose Tier 0 receipt passes the strict preflight in
[`docs/ISOLATED_BENCHMARKS.md`](../../docs/ISOLATED_BENCHMARKS.md#tier-0-host-isolated-result):
root-controlled isolated cgroup v2 partition, full selected-core SMT sibling
coverage, exclusive CPU and NUMA sets, fixed frequency, no quota, `nohz_full`,
no overlapping IRQ affinity, housekeeping-only runner, and `numactl`. Retain
preflight, before/after noise counters, exact affinity, build/source hashes,
all commands/stdout/stderr, failures, answers, and paired order. Any failed
preflight/noise/correctness gate stops the run; retain the failed receipt and
start no timer. Do not substitute another tier.

The C one-thread panel uses one isolated logical CPU. The historical C
multi-thread claim uses two workers. The current isolated benchmark service
pins one logical CPU and explicitly says multiworker trials need a validated
multi-CPU affinity extension. Therefore the two-thread panel stays blocked
until that extension exists, is tested to prove all worker threads remain
inside a declared exclusive CPU set, and its preflight covers both CPUs and
all SMT siblings. Do not use a one-CPU taskset for a two-thread speed claim.

No paid or cloud allocation is part of this protocol. This executor is a
container with a 4-CPU quota, lacks the isolated partition and `nohz_full`,
has no `numactl`, and cannot inspect host-level controls; its saved strict
preflight fails. See [`BLOCKED.md`](BLOCKED.md) and the complete probe records
under [`preflight/`](preflight/).

## Frozen C library panel

Build both binaries with the same harness and toolchain, then retain build
logs and executable hashes. Before wall timing, run `ca_perfbench list --full`
and verify that the same 34 IDs are present. For every `id`, require the
fingerprint fields already defined by the harness to match across baseline,
candidate, samples, and the A/A control. A fingerprint mismatch invalidates
the whole comparison; do not omit that row.

On the Tier 0 single-CPU service, use the existing seeded pairing and noise
logic in `scripts/perf/perfindex.py`, with eight paired rounds, five samples
per kernel, and the full kernel set:

```sh
python3 scripts/perf/perfindex.py build --c --ref 9b45e8c8db2f078a2419ad604ab427856391bd79 --out /bench/c880/base
python3 scripts/perf/perfindex.py build --c --current --out /bench/c880/candidate
python3 scripts/perf/perfindex.py compare --base /bench/c880/base/ca_perfbench --cand /bench/c880/candidate/ca_perfbench --full --rounds 8 --threads 1 --samples 5 --taskset "$CPU" --out /bench/c880/c-full-1t
python3 scripts/perf/perfindex.py instr --base /bench/c880/base/ca_perfbench --cand /bench/c880/candidate/ca_perfbench --full --out /bench/c880/c-full-ir
```

`$CPU` must be one audited logical CPU in the isolated partition; the
benchmark service itself remains pinned to housekeeping CPUs. The external
service receipt must retain and attest every child command and raw output.
Callgrind `Ir` is deterministic diagnostic evidence and cannot substitute for
wall time. Report the full per-kernel table, A/A noise, indices, confidence
intervals, fingerprints, and all rejected/neutral rows. Use the existing
index's verdict threshold; do not promote a row that is inside A/A spread.

The two-thread panel is the same full source pair and same `dlp/c_rho_ec44_mt`
workload with `--threads 2`, eight paired rounds, and the multi-CPU service
extension above. Pin each child and all its workers to the same two reserved
physical cores; save the exact multi-CPU manifest and worker-affinity proof.
Keep single-thread and two-thread outcomes separate. This step has no runnable
command until the service extension and its tests are accepted.

## Frozen ECC2K-130 panel

Build the baseline and candidate table-walk executables separately with
`make -C ecc2k130 WALK=table BUILD=/bench/c880/ecc2k-base cpu` and the
corresponding candidate build directory. Copy the same frozen
`experiments/c-kernel-cpu-v1/f131_microbench.cpp` into the baseline build
inputs; compile the same source once with `-DF131_BENCH_BASE` (packed
polynomial implementation) and once without it (`f131` candidate). Use the
same compiler flags and `cpuknobs.h`:

```sh
cd ecc2k130
g++ -O3 -DNDEBUG -std=c++17 -pthread -march=native -include src/cpuknobs.h -Isrc -Iinclude ../experiments/c-kernel-cpu-v1/f131_microbench.cpp -o /bench/c880/f131_microbench_candidate
g++ -O3 -DNDEBUG -std=c++17 -pthread -march=native -DF131_BENCH_BASE -include src/cpuknobs.h -Isrc -Iinclude ../experiments/c-kernel-cpu-v1/f131_microbench.cpp -o /bench/c880/f131_microbench_base
```

Before freezing the final service manifest, run the harness's non-timing
fingerprint mode on both binaries and require equal verified results:

```sh
/bench/c880/f131_microbench_base mul 1000000 20261019 --fingerprint
/bench/c880/f131_microbench_candidate mul 1000000 20261019 --fingerprint
/bench/c880/f131_microbench_base sqr 1000000 20261019 --fingerprint
/bench/c880/f131_microbench_candidate sqr 1000000 20261019 --fingerprint
```

Freeze those expected result digests in the final manifest; this setup pass
does not emit timing data. The direct-operation timing commands are:

```sh
/bench/c880/f131_microbench_base mul 1000000 20261019
/bench/c880/f131_microbench_candidate mul 1000000 20261019
/bench/c880/f131_microbench_base sqr 1000000 20261019
/bench/c880/f131_microbench_candidate sqr 1000000 20261019
```

The program has eight deterministic independent lanes, 10,000 untimed warm-up
iterations, and a one-million-iteration timed recurrence. It reports its
internal timer, checks the final outputs against the independent packed
polynomial recurrence outside that timer, and emits a stable output digest.
For each operation, first run eight alternating A/A and A/B pairs on the
qualified one-CPU panel. Retain every pair, raw output, and digest; require
identical baseline/candidate output digests and `verified=1` on every row.
Wrap each timing binary in the checked-in `measure_cli.py` with
`--boundary native --result-field result --`; the wrapper preserves child
stdout/stderr and surfaces the executable's own verified answer and timer to
the service.

For full table-walk throughput, run the same fixed command in each separate
build, one worker. Use the `internal` timer so table-build/process startup is
not counted as walk throughput, and retain outer elapsed time as context:

```sh
python3 experiments/c-kernel-cpu-v1/measure_cli.py --boundary internal --result-field iterations -- /bench/c880/ecc2k-base/table/ec2k-cpu bench --steps 1024 --launches 64 --workers 1
python3 experiments/c-kernel-cpu-v1/measure_cli.py --boundary internal --result-field iterations -- /bench/c880/ecc2k-candidate/table/ec2k-cpu bench --steps 1024 --launches 64 --workers 1
```

Run eight alternating baseline/baseline control pairs and eight alternating
baseline/candidate pairs. Retain all raw progress and final status lines;
require identical iteration counts and successful exit. The one-worker result
is a single-core throughput claim only.

For cold startup plus table construction and arithmetic checks, run:

```sh
python3 experiments/c-kernel-cpu-v1/measure_cli.py --boundary process --result-field checks -- /bench/c880/ecc2k-base/table/ec2k-cpu check --rounds 64
python3 experiments/c-kernel-cpu-v1/measure_cli.py --boundary process --result-field checks -- /bench/c880/ecc2k-candidate/table/ec2k-cpu check --rounds 64
```

The timed boundary is process start through final JSON output. Capture outer
wall time and process CPU time; check that each revision reports
`status=ok`, `rounds=64`, and equal check counts. Run eight A/A and eight A/B
pairs, alternating order. Report this as cold CLI check latency; do not label
it pure table-construction time because it includes process startup and the
complete check command.

The original `cputest` host/golden-model suite, table-mode `make test`,
`make cpu-verify`, and 300-report model replay must pass on both builds before
any timing. Correctness failures remain retained rows and invalidate that
measurement. The direct-operation harness and exact commands are frozen here;
no original ECC2K raw record has been found.

## Reporting and graph/index impact

All campaign outputs remain under one content-addressed run directory and
include the frozen protocol, host manifest/preflight, compiler/build receipts,
raw pair order, per-run stdout/stderr, raw JSON/CSV, expected/result hashes,
calculated summaries, failures, and source hashes. Generate from these records
only after the whole applicable panel passes. Produce a new dated report,
source-linked timing graph, source-linked ECC2K work-path diagram, PDF,
benchmark mirror, C performance-index row, ECC2K benchmark index row, and a
canonical graph/dashboard impact audit. Do not edit the weighted PI for
partial results. The PR's algorithms and fingerprints are engineering-only;
no ECDLP method speedup follows.

The historical summaries in `historical-claims.csv` may be plotted only as
explicitly unverified historical observations. A new campaign result must
have its own series, raw source, host, and confidence interval and must never
be described as recovery, replication, or validation of those values.
