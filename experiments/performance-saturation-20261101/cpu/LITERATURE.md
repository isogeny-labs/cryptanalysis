# CPU performance-saturation literature and prior evidence

**Status:** pre-measurement review, 2026-11-01. No CPU build, benchmark,
profiler, or correctness workload was run by this lane. The adjacent
`protocol.json` is preserved as the frozen version-1 three-arm design; its
candidate commits and executable hashes are unresolved, so it cannot govern a
pre-candidate run. `protocol-baseline-aa-v2.json` is the separate prospective
baseline/A-A authority only when its own freeze block is frozen and committed.
It binds no candidate and authorizes no speedup claim.

## Scope

This lane covers three prospective Rust implementation changes and one C
non-regression control:

1. AVX2 table XOR plus branchless row clearing in `gf2_elim`;
2. direct construction of packed Matrix-F5 rows;
3. three-product/two-limb and six-product/three-limb carry-less Karatsuba in
   `F2mElement::mul`; and
4. all 34 fixed-input `ca_perfbench --full` kernels, whose C sources are not
   intended to change.

The review distinguishes prior evidence used to select candidates from a
baseline for this repository. Sibling-repository results do not transfer a
timing ratio to this checkout, host, compiler, or measurement boundary.

## Repository contracts and measurement literature

| Source checked | What it establishes | Consequence for this study |
| --- | --- | --- |
| [`AGENTS.md`](../../../AGENTS.md), especially “Experiment protocol, export and review” and “CPU performance evidence tiers” | A protocol must be frozen before the first data point; wall-time claims require qualified isolation, alternating pairs, exact results, and retained failures. | Preserve frozen version 1, file the baseline/A-A temporal repair separately, and keep the current local executor explicitly nonqualified. No local wall observation may be promoted to Tier 0 or Tier 1. |
| [`docs/perf/PERFORMANCE_INDEX.md`](../../../docs/perf/PERFORMANCE_INDEX.md) | `scripts/perf/perfindex.py` is the canonical Rust/C comparison harness; fixed-input kernels return fingerprints and are compared at identical production-call boundaries. In `--no-aa` mode it deterministically mirrors two arms A/B then B/A by round. | The repair uses the same baseline path as both `--base` and `--cand`, six fixed mirrored rounds, one discarded time-based warmup phase per invocation, three to five emitted samples under the canonical budget, one- and four-thread panels, and exact fingerprint equality before reading clocks. |
| [`suite/examples/perfbench/harness.rs`](../../../suite/examples/perfbench/harness.rs) | Setup and per-sample input restoration are untimed; `Workload::run` is the complete timed call; changed fingerprints invalidate a comparison. | The decisive metric is the full `run` interval, not an isolated loop or phase. Preparation remains reported but cannot support a speedup. |
| [`tools/ca_perfbench.c`](../../../tools/ca_perfbench.c) | The C harness has 34 fixed-input kernels. It fingerprints answers, coordinates, residues, ranks, or recovered logs and refuses within-run fingerprint drift. | Require the same 34 IDs/descriptions and one exact fingerprint per ID across baseline, candidate, A/A, rounds, samples, and thread panels. |
| [`docs/ISOLATED_BENCHMARKS.md`](../../../docs/ISOLATED_BENCHMARKS.md) | Tier-0 host evidence requires an exclusive physical-host CPU/NUMA partition, fixed frequency, IRQ control, full topology/affinity receipts, and no noise events. Tier-1 is instance-scoped and has a different claim. | The repair pins CPUs 0/0-3, reserves 0-3 under the shared global lock, and retains the service receipt, but the local KVM placement still lacks Tier-0/Tier-1 proof. Its clocks remain nonqualified even if the internal isolation/noise gate is quiet. |
| Hoefler and Belli, “Scientific Benchmarking of Parallel Computing Systems,” SC15, DOI [10.1145/2807591.2807644](https://doi.org/10.1145/2807591.2807644) (publisher record retrieved) | Performance reports need reproducible environments, statistical treatment, full disclosure, and meaningful baselines. | Retain raw alternating rounds, A/A spread, exact host/build identities, confidence intervals, neutral/regressing cells, and failures. |
| Mytkowicz et al., “Producing Wrong Data Without Doing Anything Obviously Wrong!”, ASPLOS 2009, DOI [10.1145/1508244.1508275](https://doi.org/10.1145/1508244.1508275) (publisher record retrieved) | Link order, environment size, and layout can create performance effects without semantic changes. | Build arms separately but identically, alternate fresh processes, retain environment and binary hashes, and treat Callgrind/hardware-counter deltas as diagnostics rather than portable timings. |

The canonical cross-repository machine contract was also checked in
`crypto-autoresearcher:docs/experiment-protocol.md`, its
`experiment.protocol/v1` schema, and `tools/experiment_protocol.py`. The
repair is filed before affected data and is checked with that validator;
execution remains prohibited unless its own freeze block says `frozen`.

## GF(2) elimination

### Primary algorithm source

Albrecht, Bard, and Pernet, “Efficient Dense Gaussian Elimination over the
Finite Field with Two Elements,” arXiv
[1111.6549](https://arxiv.org/abs/1111.6549) (full text retrieved), describes
the Method of Four Russians/M4RI construction: form the `2^k` combinations
of pivot rows, use Gray-code updates to construct the table cheaply, and tune
the number of tables and block size to the cache hierarchy. This supports
table-based XOR and locality work; it does not predict that a particular
AVX2 implementation wins on every matrix or CPU.

Rust’s official
[`is_x86_feature_detected!`](https://doc.rust-lang.org/std/macro.is_x86_feature_detected.html)
documentation (retrieved) specifies runtime detection for features including
`avx2` and `pclmulqdq`. Therefore a new AVX2 path must retain the scalar path,
use runtime dispatch, and be measured independently of the AVX-512 path.

### Prior implementation evidence

- Current cryptanalysis source has scalar and AVX-512 table-XOR dispatch but
  no AVX2 table-XOR default, and its strip clear is conditional:
  [`suite/src/cryptanalysis/gf2_elim.rs`](../../../suite/src/cryptanalysis/gf2_elim.rs).
- The sibling implementation contains branchless AVX2 clearing, AVX2 table
  XOR, scalar/AVX2/AVX-512 runtime dispatch, and an explicit rollback:
  `crypto:src/cryptanalysis/gf2_elim.rs`.
- `crypto:research/gf2_branchless_strip_20260929/RESULT.md` reports exact
  ranks, rows, terms, counters, and fingerprints over its frozen cases. Its
  qualified segmented replay reported a 1.210x one-thread and 1.309x
  two-thread complete-call ratio on its own hosts and source. These are
  candidate-selection evidence only.
- `crypto:research/gf2_avx2_table_20260928/RESULT.md` reported a smaller
  complete-call gain and failed that study’s original 1.20 incremental gate.
  The two historical ratios must not be multiplied or presented as this
  repository’s expectation.

Implication: measure the AVX2 table XOR and branchless clear as one candidate
only after exact row/rank/word-operation equality. Profile the dense random
matrix and the real `k5m3d5` Macaulay RREF/echelon calls. Preserve scalar and
AVX-512 fallbacks and an explicit rollback until qualification.

## Matrix F5 packed-row construction

### Primary algorithm sources

Faugère, “A New Efficient Algorithm for Computing Gröbner Bases without
Reduction to Zero (F5),” ISSAC 2002, DOI
[10.1145/780506.780516](https://doi.org/10.1145/780506.780516) (publisher
record and repository citation checked), establishes the signature criterion.
The Matrix-F5 and Boolean-system references used by this implementation are
listed in
[`suite/src/cryptanalysis/matrix_f5_f2.rs`](../../../suite/src/cryptanalysis/matrix_f5_f2.rs).
Direct packing changes representation and allocation, not the F5 criterion,
selected row set, row order, or algebraic result.

### Prior implementation evidence

- Current cryptanalysis source materializes monomial lists, discovers
  columns, then packs them. The sibling source has a direct packed-row XOR
  builder: `crypto:src/cryptanalysis/matrix_f5_f2.rs`.
- `crypto:research/f5_direct_pack_20260929/RESULT.md` reports exact row-space,
  rank, row-count, criterion, and reduction-work equality. On its own frozen
  case it reported a 3.753x build-stage ratio and a 1.210x complete-call
  incremental ratio. The stage ratio is not a production-call speedup.
- `crypto:research/f5_gf2_defaults_20261017/README.md` found direct packing
  non-regressing across its second-host F5 cells, but direct unpacking lost
  at four threads and table reuse regressed a Matrix-F4 cell. Those two
  adjacent ideas are excluded from this candidate.

Implication: port only direct packed construction and prerequisites needed by
that construction. Require equality of degree, F4/pruned/built row counts,
column count, rank, zero reductions, criterion rows/word operations,
reduction word operations, returned polynomials, roots, and solver statistics.
The complete Matrix-F5 call must pass; a build-only result is diagnostic.

## Binary-field carry-less Karatsuba

### Standards and instruction documentation

- NIST SP 800-186, DOI
  [10.6028/NIST.SP.800-186](https://doi.org/10.6028/NIST.SP.800-186) (full
  standard retrieved), fixes the polynomial-basis representations and sparse
  irreducible polynomials used by the legacy binary curves. It supplies field
  identities, not a performance claim.
- Intel’s official
  [Intrinsics Guide](https://www.intel.com/content/www/us/en/docs/intrinsics-guide/index.html)
  and Optimization Reference Manual (official Intel copy linked from
  `crypto:research/ecc_arithmetic_20261013/ARCHITECTURE.md`) document
  PCLMULQDQ/VPCLMULQDQ and their feature requirements. Latency and throughput
  vary by microarchitecture; product count alone is not elapsed time.
- Putranto et al., DOI
  [10.1007/978-981-96-1624-4_1](https://doi.org/10.1007/978-981-96-1624-4_1),
  was checked through its publisher record and abstract; the full paper was
  inaccessible in this environment. The local implementation already cites
  its improved-Karatsuba construction. The evidence gap is recorded rather
  than treating an abstract as an implementation proof.

### Prior implementation evidence

- Current x86 PCLMUL and AArch64 PMULL helpers use schoolbook nested loops:
  four products for two limbs and nine for three:
  [`suite/src/binary_ecc/f2m.rs`](../../../suite/src/binary_ecc/f2m.rs).
- The sibling source uses three products for two limbs and six for three,
  retaining schoolbook for other widths: `crypto:src/binary_ecc/f2m.rs`.
- `crypto:research/ecc_arithmetic_20261013/RESULTS.md` and its modal report
  recorded bitwise equality and descriptive improvements for 113-, 131-, and
  163-bit fields, with 233 bits as an unchanged control. The runs lacked a
  qualifying CPU/isolation receipt and remain exploratory.

Implication: measure 131- and 163-bit full multiply-plus-square recurrences,
163-bit inversion, and sect163k1 scalar multiplication. Keep 233-bit
multiplication as the negative-width control. Inspect generated instructions
and PCLMUL counts, but accept or reject only on full-call results with exact
raw field words and point coordinates.

## C-library control and known blockers

[`experiments/c-kernel-cpu-v1/PROTOCOL.md`](../../c-kernel-cpu-v1/PROTOCOL.md)
defines an earlier independent replay of all 34 C kernels. Its
[`REPORT.md`](../../c-kernel-cpu-v1/REPORT.md) preserves historical exploratory
summaries, while [`BLOCKED.md`](../../c-kernel-cpu-v1/BLOCKED.md) records that
the campaign collected no timings because its executor failed Tier-0 gates
and its original multi-CPU support was incomplete. Those old numbers are not
a baseline for this study.

The current C sources already include the prior linalg, EC/group, rho, and
modular-arithmetic work. Static inspection did not justify another C source
candidate. The full C index is therefore a control for unintended build or
performance effects of the Rust-only candidate. Its source set, registry,
descriptions, fingerprints, and fixed work must remain unchanged.

## Decisions fixed before candidate implementation

- The source baseline is commit
  `c273e62140071fe4370fbe6946dcb898c95b4eb2`; version 1's candidate commit
  and candidate executable hashes remain unresolved until implementation and
  clean builds.
- The many-thread panel is four threads. It is distinct from the one-thread
  panel and must use a qualified four-CPU placement that covers SMT siblings
  and NUMA policy; container affinity alone is insufficient.
- Version 1 retains its six rotating A/B/A′ rounds for a future candidate.
  The baseline-only repair instead fixes six two-arm mirrored rounds: A/B in
  rounds 1, 3, and 5 and B/A in rounds 2, 4, and 6. No result-dependent
  extension or early stop is permitted.
- Fingerprints and embedded/fixed work counters must match exactly before
  any clock is read. A mismatch invalidates the affected opportunity.
- Callgrind `Ir`, `perf stat`, disassembly, and `perf record` are diagnostic.
  They may explain a result but cannot replace a qualified full-call wall
  comparison.
- No stage-only improvement licenses retention. Each Rust opportunity must
  pass its complete production-call panel at both thread settings, while the
  unchanged C panel must pass its preregistered non-regression gate.
- A future A/B protocol still needs a qualifying host/CPU receipt, one clean
  candidate commit, exact baseline/candidate toolchains and executable hashes,
  and prospectively fixed promotion/rollback decisions. The baseline/A-A
  amendment does not fill those candidate fields.

## Baseline/A-A temporal repair filed before data

Frozen version 1 is identified by protocol SHA-256
`0e883304ca31da59ab2ece5e400a6c79b46d4b669a84f1ea05e2978c72dd541d`,
registration commit `050af6a5edbaccee4028574492597049a06cfd83`, and
freeze-file commit `a8f4244ddb7b916ec67b7b2e6a9dcf97c53817b5`. It is
not edited by the repair.

`protocol-baseline-aa-v2.json` narrows the next admissible phase to the
retained baseline and a byte-identical A/A label. It fixes all 44 cells at one
and four threads, six mirrored pairs per cell/thread, and therefore exactly
1,056 measured invocations. Each invocation uses one discarded warmup phase
that runs at least once and continues until 0.2 seconds, then emits three to
five samples under `samples=5`, `min_samples=3`, and the two-second budget.
The external fixed N counts invocations, not internal samples. The Rust and C
cell schedules are pinned by seed and prospective schedule hashes.

The source identity is the baseline commit/tree plus a SHA-256 of its complete
Git archive and per-file hashes. The build identity is one exact, globally
locked two-command recipe with pinned Python, Rust 1.99.1, CMake 4.4.3, GCC
14.2.0, GNU make/binutils, offline Cargo, and tool/package manifest hashes.
No campaign Rust or C executable exists at filing time because this task
forbids a build. After that recipe runs, a child artifact-binding amendment
must be registered and frozen before the first registry, fingerprint, test,
benchmark, or profiler invocation. It must bind the canonical build manifest,
both `build.json` receipts, both executable paths, sizes, modes, and SHA-256
values; A and A/A must use those same paths and bytes. Absence or mismatch
blocks data rather than inviting an unregistered rebuild.

All CPU-intensive work must hold
`/workspace/.benchmarks/performance-saturation/local/global-cpu.lock`.
Wall sessions additionally use the retained `isolated_bench reserve` binary,
run on CPU 0 or CPUs 0-3, reserve CPUs 0-3, leave CPU 4 for services, and keep
the full receipt. These controls do not cure the missing physical-host or
provider allocation proof: the frozen local status is **nonqualified** and no
Tier-0/Tier-1 timing or speedup claim is authorized.

Task-local Valgrind 3.28.0 and its Callgrind executable are available and
bound by exact SHA-256 values. After the unprofiled A/A wall panel, the repair
fixes 88 one-thread Callgrind A/A invocations over all 44 cells. Task-local
`perf` 6.12.113 and every shipped library are likewise bound: 88 later
`perf stat` diagnostics collect only `task-clock`, `cpu-clock`,
`context-switches`, and `page-faults`; eight still-later `perf record`
diagnostics sample `cpu-clock` for three fixed Rust representatives and the
five C cells with largest baseline Callgrind `Ir` (lexicographic ties).

The host exposes only `breakpoint`, `msr`, and `software` event sources with
`perf_event_paranoid=2`. Core hardware-PMU cycles, instructions, branch, and
cache events are therefore explicitly unavailable and forbidden rather than
imputed. All profiler failures are retained once, never rerun, and affect only
their diagnostic. Callgrind and `perf` can never replace the unprofiled
complete-call gate or support a speedup claim.

No candidate may be built or timed under this amendment. Once a clean
candidate commit and binaries exist, a fresh protocol must be registered and
frozen before candidate-affected data. It must bind both source and binary
identities, a fresh A/B/A-prime schedule, qualified placement, exact
fingerprint/work gates, profiler tools, full-call thresholds, stopping rules,
and promotion/rollback decisions.
