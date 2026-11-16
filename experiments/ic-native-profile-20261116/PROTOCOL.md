# Attribute the native IC cost before choosing the next optimization

Question: for the pinned current IC binary on fixed registered N27, where are
whole-process guest instruction events spent, and which preparation/query paths
should the next specialized implementation change? This is an instruction
attribution diagnostic, not a native wall-time or GPU performance comparison.
No requirement or timing gate from earlier studies is changed.

Use binary2e8b4e26b30756ce2910572a45642eab29def58544fbf58b71d88dde49591bdf
from clean preparation20261116-111450-d78a/source82ccc06d610a45b70356f3b78943c7e4638350d5.
Extract and verify source-job metadata, receipt and binary SHA against a frozen
profile-input.json before execution. Reuse the exact N27 instance/prefix base
from ic-packed-square-20261116, dimension10,531sign columns. Public development
fixture0 uses the existing locked point/scalar/walk law. Freeze its one-target
workload manifest and the exact positive original-arithmetic calibration receipt
from completed timing20261116-112736-c9d0, index4, before launch. No curve/base/
target/seed search, replacement or algorithm change.

Profile product1024 and packed1024 on the same point in fixed ABBA order:
mitm-vector,mitm-vector-packed,mitm-vector-packed,mitm-vector. max_trials500000,
m2,walk, original inverse and dense Gauss. Then fresh separate rho-plain and
rho-negation processes on the same public point/seed with their existing2million
trial cap. Every scalar answer is checked using the existing independent Python
field/point implementation. Record exact input/method, phase/query/relation/rank/
matrix counters, routing, memory, stdout/stderr, rusage and outcomes. Repeats
must match normalized answers and deterministic work. Failed/capped/unsupported
cases remain; no rerun, host filter, resampling or cap extension.

One L4 allocation, requested4CPU/8GiB/900s, CPU execution only, --apt time,
--apt valgrind, --apt binutils. Controller780s, each instrumented IC child120s,
rho child60s, capability preflight90s, annotation/disassembly child20s. Pin one
allowed CPU. Instrumentation's child RLIMIT_AS is32GiB virtual address space,
distinct from the requested8GiB physical allocation; fixed guest inputs remain
small, and actual RSS/cgroup limits are recorded. This distinct profiling
resource envelope does not relax a prior timing experiment's8GiB limit.

Before targets, run N27 verify-table under Valgrind --tool=none, with25complete
witness comparisons, positive vector and packed-square counts and actual backend
avx2-pclmul128 required. The same binary's exact scalar fallbacks remain, but
fallback does not satisfy this profile's vector-admission criterion. Unsupported
Valgrind ISA/host is a preserved failure, not a reason to select another host.
Ordinary and packed pair counts must match the requested method after each
profile. Native feature detection from a previous allocation never substitutes
for this interpreter's actual execution.

For every target use Valgrind --tool=callgrind --dump-instr=yes
--collect-jumps=yes --callgrind-out-file=<distinct capture>. Default Ir collection
covers the entire guest process, including runtime loader/startup, input/unit
loading, context/base/cache/table, queries/matrix/final check and output/cleanup.
It does not isolate the primary one-target online interval. Save raw .callgrind
captures before annotation, exclusive and inclusive callgrind_annotate exports,
and objdump instruction disassembly with binary/source/tool hashes. Missing
source-line info and inlined attribution remain explicit. Inclusive costs overlap
and are never added as exclusive phases; recursion/cycles may limit attribution.
Ir means instruction-read events in instrumented execution, not hardware-retired
instructions, cycles, scalar field operations, native throughput or latency.
Report whole-guest totals and repeat differences without silently subtracting
startup or transferring a count ratio into a wall-time claim. Rho counts use the
same whole-guest boundary; any ratio is supplementary to attribution.

[pcc:unverified] Competing hypotheses: arithmetic/field reduction dominates, map insertion/probing
and allocation dominates, or query/matrix work dominates. Report all leading
exclusive functions and caller paths with actual counts. Choose the next source
change from the observed profile. A compact u64 first-witness table is only a
candidate if map costs warrant it; smaller representation alone does not imply
faster probes. If unsupported/capped, retain failure and choose a distinct
available static/phase diagnostic rather than retrying unchanged.

All counters are unsigned producer/tool observations; qualifiednull and benchmark
recordinvalid for promotion. Preserve requested/exposed hardware distinction,
unknown physical memory technology/speed/channels, placement/throttle/OOM limits,
actual ISA backend, OS/runtime versions and profiling overhead. No cryptographic-
size, GPU-throughput, asymptotic or broad-goal conclusion from this diagnostic.
Archive all captures/exports/logs and a lossless per-file SHA/URI bundle before
record closure. Deliver an editable source-linked report/diagram and inspect all
rendered PDF pages. Raw native timing panels remain immutable.

## Sources checked

KB revision9141e386254340a9bdba3036f2bb706a, lexical ready, hybrid not current,
last_refresh2026-11-14T21:44:48Z; older than these new source changes, so owning
files and receipts were read. Queries: Callgrind index calculus instruction
profile HashMap; packed pair sum table open addressing first witness compact u64.
- source:c5b44937741b2f73ed2237dced16f1c1,
  cryptanalysis:docs/perf/PERFORMANCE_INDEX.md, internal-analysis/evidence none,
  not superseded. Read primary file at39340d0c7426800a3dc7ec81d762d1651d8ef03f:
  fixed fingerprints and matching work are required; this scoped profile does
  not claim the full performance-index protocol.
- source:c525825f5c51c500234cb8b8749a45dc,
  cryptanalysis:papers/frobenius-orbits/sec-benchmarks.tex, primary-source,
  external-source/evidence none/not superseded. Read packed-index section at
  the same commit: reduced bytes can accompany slower probes. No timing is
  transferred to the new table hypothesis.
- Read ic_boundary.rs MixHasher/PairTable build/probe, current simd256 arithmetic,
  packed-square frozen protocol and actual source/receipts. No novelty assertion.
- Official Callgrind manual https://valgrind.org/docs/manual/cl-manual.html:
  Ir and call attribution, exclusive/inclusive exports, instruction dumps and
  cycle limitations. Official platform list https://valgrind.org/info/platforms.html
  identifies AMD64 support through AVX2. Actual tool version/ISA execution still
  requires the frozen preflight; documentation alone does not admit the host.
