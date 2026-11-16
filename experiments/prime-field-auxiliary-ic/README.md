# Retrospective prime-field auxiliary-map index calculus import

The maintained native implementation now lives in
[the Rust crate](../../crates/prime-field-auxiliary-ic/README.md), with safe
bindings and `ca-ic auxiliary` integration. It adds signed graph elimination
and a batched direct IC control without changing the frozen snapshot. No new
qualified timing claim is made. [pcc:unverified]

The [random-versus-special comparison follow-up](random-vs-special/README.md)
adds equal-column random-base controls, opt-in core phase accounting and
projective scalar/row arithmetic shared by all arms. Producer correctness
checks are retained by source; they establish no measured auxiliary speedup.
[pcc:unverified]

The subsequent [field-fiber implementation report](rust-validation/field-fibers-20261115/REPORT.md)
and [PDF](rust-validation/field-fibers-20261115/REPORT.pdf), claim
`PCC-20261115-82ccdd`, add multiplicative and norm-one trace encodings,
trace-orbit preparation, a pre-split terminal, and same-column direct controls.
Twenty core checks on each toolchain and four CLI checks pass; these are
unsigned producer checks, with no new timing conclusion. [pcc:unverified]

The [Rust implementation-check report](rust-validation/producer-checks.json)
pins the source files, exact commands, raw outputs, and unsuccessful setup
attempts. Claim `PCC-20261115-c2f013` records the unsigned producer checks;
it is not an execution proof or signed independent replay. [pcc:unverified]

This imports the implementation, public fixtures, and historical outputs from
the standalone `index_calculus_demo` workspace. The snapshot includes the
quadratic-resultant solver, known-root GCD tree, centered SIMD circuit, batched
target generation, complete relation-matrix recovery, and a Pollard rho control
sharing the native arithmetic. This PR launches no new research experiment.

## Evidence status

All historical performance statements and self-reported verification flags in
`snapshot/` are producer assertions, not repository-approved results.
The measurements are retrospective, exploratory CPU observations: three search
seeds on one already-known 31-bit target, no pinned CPU or accepted isolation
tier, no five-fresh-target panel, and no signed independent replay. The original
clock includes process startup and reusable preparation; it does not establish
the repository's primary single-target online metric. No baseline, leaderboard,
canonical candidate, or qualified speedup is promoted. [pcc:unverified]

The earlier chat called a separately implemented Python checker "independent."
That checker was written by the same producing session. Under this repository's
contract that wording was too strong; its outputs are retained as producer
checks. The unsigned recomputation claim is `PCC-20261115-288dc5` and the public
group-equation certificate claim is `PCC-20261115-bb0887`. Signed standing must
be obtained from `tools/pcc/pcc.py standing`, not from JSON booleans or this
README. [pcc:unverified]

The imported producer reports the following medians in seconds. These are
archival observations, not a qualified cross-method performance claim.
[pcc:unverified]

| Variant | Reported cold wall median | Search seeds |
|---|---:|---|
| Preserved v1 IC | 35.416334295 | 0, 1, 2 |
| Centered/fused IC | 15.083680401 | 0, 1, 2 |
| Centered/fused IC with batched targets | 9.685107569 | 0, 1, 2 |
| Shared-arithmetic Pollard rho | 0.018318452 | 0, 1, 2 |

The exact public target is `p=2147483647`, `y²=x³+2x+14`,
`n=2147505293`, `P=(1,814455902)`,
`Q=(988441464,1643383878)`. Its public scalar fixture is kept separate from
solver input. The 61-bit files concern arithmetic/relation diagnostics and
older explicitly scoped fixtures; they do not establish a full 61-bit attack.
[pcc:unverified]

## Contents and reproducibility

- [Latest implementation and archived report](snapshot/algebraic/optimized/README.md).
- [Raw latest per-run inputs, outputs, and relation certificates](snapshot/algebraic/optimized/results/field31_s5_base0/).
- [Earlier full-pipeline comparison](snapshot/algebraic/end_to_end/README.md).
- [GCD implementation](snapshot/algebraic/known_root_gcd.py) and
  [resultant implementation](snapshot/algebraic/resultant_solver.py).
- [Original-file SHA-256 inventory](SNAPSHOT_SHA256.json); the original snapshot
  bytes are unchanged. Compiled binaries, vendored dependencies, and caches
  are excluded.
- [Unsigned headline recomputation](producer-recompute.json) and
  [public group-equation certificate](solve-certificate.json).
- [Retrospective benchmark-record index](BENCHMARK_RECORDS.json) and
  [import report PDF](IMPORT_REPORT.pdf).

The snapshot retains unsuccessful and superseded experiments. A historical
filename, boolean, report, or known-scalar correctness fixture is not evidence
of independent verification or natural relation yield. [pcc:unverified]

For implementation checks, install `snapshot/algebraic/requirements.txt`, a
C++17 compiler, and Singular, then run from `snapshot/algebraic`:

```sh
python -m unittest test_solver test_resultants test_optimized optimized.test_v2 -v
```

Set `SYMPY_GROUND_TYPES=python` when python-flint is globally installed. The
archived SymPy extraction code otherwise attempts to sort FLINT `nmod` values,
which raises `TypeError: nmods cannot be ordered` in that dependency combination.
The CI environment pins this setting and retains extraction logs on failure;
the archive itself remains byte-for-byte unchanged. [pcc:unverified]

The dedicated CI job runs those checks in a temporary copy so that outputs
cannot overwrite the frozen snapshot. The historical standalone benchmark
commands remain in the archive for inspection; any new research run must first
meet the repository's checkpoint, benchmark-record, GPU, target-panel, and
measurement requirements. The import records label their source commit as a
snapshot identity, not as a commit that existed at execution time.

## Remaining validation work

| Requirement | Import status |
|---|---|
| Native Rust API, CLI, auxiliary/direct IC controls, sparse certificate solver | Implemented and producer checked; timings unqualified |
| Source, public parameters, seeds, raw successes/failures, source hashes | Retained in the snapshot and import inventory |
| Arithmetic and relation checks | Implemented; archived producer reports retained |
| Independent scalar certificate check | Submitted to the repository PCC checker; signed standing pending |
| Independent replay and signed measurement verdict | Not established |
| Qualified IC-versus-rho online comparison | Not established; requires a new compliant panel and timing protocol |

The next research step is to freeze a compliant target panel and exclusive
online accounting, register the exact candidates and bases, and replay IC and
the repository's strong rho reference through the admitted measurement
harness. This PR imports the existing work; it does not schedule that run.
The outstanding obligations are tracked in
[the validation problem record](../../problems/prime-field-auxiliary-ic-validation.md).
