# CPU performance-saturation literature and prior evidence

**Status:** pre-measurement review, 2026-11-01. No benchmark, profiler, or
correctness workload was run for this study. The adjacent `protocol.json` is
an unfrozen draft and authorizes no data collection.

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
| [`AGENTS.md`](../../../AGENTS.md), especially “Experiment protocol, export and review” and “CPU performance evidence tiers” | A protocol must be frozen before the first data point; wall-time claims require qualified isolation, alternating pairs, exact results, and retained failures. | The draft remains explicitly unfrozen. The current local executor is nonqualified and may be used only for validation of the draft, never for timing. |
| [`docs/perf/PERFORMANCE_INDEX.md`](../../../docs/perf/PERFORMANCE_INDEX.md) | `scripts/perf/perfindex.py` is the canonical Rust/C A/B/A′ harness; fixed-input kernels return fingerprints and are compared at identical production-call boundaries. | Use six fixed rotating A/B/A′ rounds, five samples per invocation, one- and four-thread panels, and exact fingerprint equality before reading time. |
| [`suite/examples/perfbench/harness.rs`](../../../suite/examples/perfbench/harness.rs) | Setup and per-sample input restoration are untimed; `Workload::run` is the complete timed call; changed fingerprints invalidate a comparison. | The decisive metric is the full `run` interval, not an isolated loop or phase. Preparation remains reported but cannot support a speedup. |
| [`tools/ca_perfbench.c`](../../../tools/ca_perfbench.c) | The C harness has 34 fixed-input kernels. It fingerprints answers, coordinates, residues, ranks, or recovered logs and refuses within-run fingerprint drift. | Require the same 34 IDs/descriptions and one exact fingerprint per ID across baseline, candidate, A/A, rounds, samples, and thread panels. |
| [`docs/ISOLATED_BENCHMARKS.md`](../../../docs/ISOLATED_BENCHMARKS.md) | Tier-0 host evidence requires an exclusive physical-host CPU/NUMA partition, fixed frequency, IRQ control, full topology/affinity receipts, and no noise events. Tier-1 is instance-scoped and has a different claim. | The local container cannot be silently treated as Tier 0. Before freeze, choose and pin a qualifying host and receipt path or keep all clocks explicitly nonqualified. |
| Hoefler and Belli, “Scientific Benchmarking of Parallel Computing Systems,” SC15, DOI [10.1145/2807591.2807644](https://doi.org/10.1145/2807591.2807644) (publisher record retrieved) | Performance reports need reproducible environments, statistical treatment, full disclosure, and meaningful baselines. | Retain raw alternating rounds, A/A spread, exact host/build identities, confidence intervals, neutral/regressing cells, and failures. |
| Mytkowicz et al., “Producing Wrong Data Without Doing Anything Obviously Wrong!”, ASPLOS 2009, DOI [10.1145/1508244.1508275](https://doi.org/10.1145/1508244.1508275) (publisher record retrieved) | Link order, environment size, and layout can create performance effects without semantic changes. | Build arms separately but identically, alternate fresh processes, retain environment and binary hashes, and treat Callgrind/hardware-counter deltas as diagnostics rather than portable timings. |

The canonical cross-repository machine contract was also checked in
`crypto-autoresearcher:docs/experiment-protocol.md`, its
`experiment.protocol/v1` schema, and `tools/experiment_protocol.py`. The
draft is validated with that checker but is not frozen.

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

## Decisions fixed before implementation

- The source baseline is commit
  `c273e62140071fe4370fbe6946dcb898c95b4eb2`; the candidate commit and all
  executable hashes are unresolved until implementation and clean builds.
- The many-thread panel is four threads. It is distinct from the one-thread
  panel and must use a qualified four-CPU placement that covers SMT siblings
  and NUMA policy; container affinity alone is insufficient.
- Exactly six measured rotating A/B/A′ rounds and five internal samples per
  invocation are planned. No result-dependent extension or early stop is
  permitted.
- Fingerprints and embedded/fixed work counters must match exactly before
  any clock is read. A mismatch invalidates the affected opportunity.
- Callgrind `Ir`, `perf stat`, disassembly, and `perf record` are diagnostic.
  They may explain a result but cannot replace a qualified full-call wall
  comparison.
- No stage-only improvement licenses retention. Each Rust opportunity must
  pass its complete production-call panel at both thread settings, while the
  unchanged C panel must pass its preregistered non-regression gate.
- Before freeze, the draft still needs a qualifying host/CPU set, candidate
  commit, toolchain and binary hashes, preflight runtime, and a hashed analysis
  script. Until then the local-host status is **nonqualified; no timing
  authorized**.
