# Native prime-field auxiliary index calculus

Dependency-free Rust implementation, re-exported as
`cryptanalysis::auxiliary_ic` and
`cryptanalysis_suite::cryptanalysis::prime_auxiliary_index_calculus`.
The main fields are `p=2^31-1` and `p=2^61-1`; smaller Mersenne primes support
bounded correctness fixtures. The core has no C++, Python, Singular, or FLINT
runtime dependency.

`FactorBase::new` checks a complete splitting fiber of maps
`f(z)=(z-r)+A+B/(z-r)`. It lifts the fiber to the **target** curve and folds
point negation. Auxiliary group smoothness supplies the membership encoding;
it does not transfer the target's discrete logarithm to the auxiliary curve.
Map construction and point counting remain in the archived preparation tools.

The relation solver eliminates the quadratic Semaev variable through a
homogeneous, centered resultant circuit. It evaluates the resulting exact
polynomial at the known base coordinates and verifies surviving signed sums
in the target group. This avoids constructing a high-degree resultant or
running a generic polynomial GCD for this complete known-root case. It supports
exact `m=2` decompositions directly and `m=3` / `m=4` split-`S_3` chains via
batched outer base shifts (`FactorBase::decompose_multi` and `solve_multi`),
not a general multivariate Gröbner solver. These are producer implementation
assertions. `[pcc:unverified]`

The implementation includes these optimization choices:

- Precomputed coordinate squares and map constants, a pre-split terminal quadratic,
  and three interleaved SIMD vectors. AVX2/AVX-512 are selected only after CPU
  feature checks, for fields up to 31 bits. The 61-bit path is scalar `u128`.
- The final map is split once during preparation. Evaluation then uses
  `q(u)*q(v)`, with five general field multiplications instead of eight for
  the previous general terminal formula. Opposite roots share their square;
  unit opposite roots require only the final product. These are source-level
  counts, excluding preparation and the initial Semaev coefficients.
- `FactorBase::multiplicative` builds complete `x^S=coset^S` fibers for
  `S | p-1`, with factors 2, 3 and 7 (at most one 2). Cube/seventh-power
  coefficient recurrences avoid auxiliary elliptic curves. In both main
  fields, 126 divides `p-1`; this is an additional encoding to compare.
- `FactorBase::torus` builds complete fibers of iterated `x^2-2` using a
  primitive trace of the norm-one group of order `p+1`. Each intermediate
  quadratic update uses four field multiplications. A trace-orbit recurrence
  generates the complete raw fiber with one square root instead of the
  inverse tree's `2^depth-2` extractions (none is needed at depth one).
  Every generated root still receives a forward membership check. Depth is bounded by
  `min(20, field_bits-2)` to avoid ramified terminal fibers.
- Scalar and packed backends share the same homogeneous coefficient kernel;
  no step divides by the quadratic leading coefficient, including when it is
  zero. Both field families generate/check every raw root before lifting.
  Empty target-curve lifts fail explicitly; a split fiber alone does not
  guarantee a usable factor base.
- Each intermediate map reuses `t = delta*nd` across its coefficient updates:
  `h = norm + delta*(cd+t)` and `c = cd+t+t`. This replaces one field
  multiplication with one addition per intermediate coefficient update in
  the scalar and SIMD paths.
- SIMD comparison masks collect zero indices while the final vectors are in
  registers; padding bits are discarded before index extraction. The scalar
  path collects indices during evaluation. All exact circuit values remain
  available in the workspace, without a second scan to find the zeros.
- Fixed addition-chain inverses and a configurable number of target walks
  sharing one inversion. Scratch buffers are reused between queries.
- Scalar multiplication keeps intermediate points in Jacobian coordinates,
  with at most one inversion when converting the result back to affine form.
  This applies equally to generator/subgroup validation, random cofactor
  clearing, sampler initialization, row checks and certificate replay in all
  IC arms. Affine/batched addition is retained. No runtime gain is inferred
  from the change in inversion placement. `[pcc:unverified]`
- New-row and certificate-row checks compute `aG+bQ` in one interleaved
  projective scalar loop and compare it with the signed base-point sum by
  cross multiplication. Neither side is normalized to affine coordinates;
  the row-equation check itself uses no field inversion. Bounds, distinct-row
  and final scalar checks remain. This is common arithmetic for all arms,
  with an affine equation oracle retained in correctness tests; its runtime
  benefit is unmeasured. `[pcc:unverified]`
- Signed graph elimination with a certificate DAG, instead of a dense
  matrix. Union by size and path compression track the two-column rows;
  certificate coefficients are expanded only for a useful dependency.
- `FactorBase::without_maps` provides IC with batched direct subtraction,
  arbitrary coordinates, and no auxiliary curve or quadratic pair table.
  `base.direct_control()` reuses exactly the same columns and raw-root count
  for any encoding. It shares target generation, distinct-row handling, recovery, and public
  certificate checks with the auxiliary path.

Rust 1.78 supports the portable/AVX2 paths. AVX-512 is compiled on Rust 1.89
or later, with a fallback on older toolchains. Explicit requests for an
unavailable backend fail. No architecture flags are required.

## API

```rust
use prime_field_auxiliary_ic::{AuxiliaryMap, Backend, Config, Curve,
    FactorBase, PreparedSolver, SolveOutcome, verify_certificate};

// API example; local replay is not an independent verdict. [pcc:unverified]
let curve = Curve::<7>::new(2, 51)?;
let roots = [3, 111, 78, 67, 85, 119, 57, 91];
let maps = vec![
    AuxiliaryMap { r: 0, offset: 0, residue: 1 },
    AuxiliaryMap { r: 2, offset: 6, residue: 8 },
    AuxiliaryMap { r: 70, offset: 71, residue: 70 },
];
let base = FactorBase::new(curve, maps, 38, &roots, Backend::Auto)?;
let generator = curve.point(3, 46)?;
let target = curve.point(6, 122)?; // Public point; no secret passed to solve.
let prepared = PreparedSolver::new(&base, 109, generator)?;
let config = Config { max_queries: 10_000, ..Config::default() };
match prepared.solve(target, &config)? {
    SolveOutcome::Solved { certificate, stats } => {
        verify_certificate(&base, &certificate)?;
        println!("scalar={} queries={}", certificate.scalar, stats.queries);
    }
    SolveOutcome::Exhausted { reason, stats } => {
        println!("incomplete: {reason:?}, queries={}", stats.queries);
    }
}
# Ok::<(), prime_field_auxiliary_ic::Error>(())
```

Only odd prime-order subgroups below `2^63` are supported. Preparation checks
the generator and base subgroup membership. Certificates require distinct
signed rows, at least three nonzero weights, complete base-column
cancellation, a nonzero target coefficient, every public group equation, and
`kP=Q`. Query, lane, relation, proof-storage, and soft time caps are explicit;
exhaustion is not reported as recovery.

## CLI

From the repository root, build `cargo build --release --manifest-path
suite/Cargo.toml --bin ca-ic`. `ca-ic auxiliary --input public.json` accepts
the archived public manifest:

```json
{
  "public": {"p":127,"a":2,"b":51,"n":109,"P":[3,46],"Q":[6,122]},
  "auxiliary": {"p":127,"terminal_c":38,"maps":[
    {"r":0,"A":0,"B":1},{"r":2,"A":6,"B":8},{"r":70,"A":71,"B":70}
  ]},
  "structured_roots": [3,111,78,67,85,119,57,91]
}
```

- `--without-auxiliary` selects the direct IC control on the same roots.
  Independent arbitrary roots may also be supplied with this flag, without
  an `auxiliary` block. `roots` aliases `structured_roots`.
- `--random-base-columns K [--factor-base-seed 701]` selects ordinary IC on
  a separately sampled random base with exactly K usable negation classes.
  Match K to the special base's `folded_columns`, rather than its raw roots.
  Construction uses rejection-sampled field coordinates and cofactor clearing,
  without target access or known base logarithms. The cofactor must be
  certified by the generator order and Hasse interval and coprime to the
  subgroup order; other cases fail explicitly. Both archived requested-field
  subgroups meet this condition. `--random-base-max-draws` bounds every draw,
  including rejections; the default is 4,194,304. This mode requires only
  `public` input and runs direct subtraction with the shared relation solver.
  Its base seed is separate from the `--seed` relation-search seed.
- `--multiplicative-degree 126 [--coset 1]` or `--torus-depth 7
  [--torus-trace TRACE]` generates a field-based fiber. Only the `public`
  object is required in the JSON input. The modes are mutually exclusive;
  the selected degree/coset or depth/trace appears in the report.
  Add `--without-auxiliary` to run direct IC on exactly the generated columns.
  `uses_circuit` distinguishes these encodings from direct search;
  `uses_auxiliary_maps` is true only for supplied auxiliary-curve maps.
- `--rho` additionally invokes the repository C batched negation-map rho
  reference on the same target. It uses Montgomery arithmetic, so this is
  explicitly a different arithmetic backend. `--rho-max-ops` bounds it.
  Version 2 reports charge the Rust scalar replay to its online wall time,
  with integer search/replay partitions. Its group-operation counter still
  describes the native solver only, excluding the Rust replay.
- `--decompose-only` checks one target decomposition, without recovery.
- `--relation-yield-only` processes a public query prefix without early
  recovery or graph elimination. Compare the three arms below with identical
  `--seed`, `--walk-lanes`, `--max-queries` and resource limits. Only a
  `complete` report with `stop_reason: QueryBudget` completed the requested
  prefix. Relation/storage/time caps retain explicitly incomplete reports.
  `work.relations` counts distinct nonzero signed rows; `duplicate_rows`
  counts repeated rows. Failed and infinity queries remain in `work.queries`.
  This is a relation-collection stage, not an end-to-end solve measurement.
- `--profile-phases` opts into an exclusive partition of the core search
  interval, from target validation through outcome construction and local
  certificate replay. `online_exclusive_phases` reports integer nanoseconds
  for initialization, target walks, decomposition (including signed-sum
  checks), new-row coefficient validation, graph recovery, local replay and
  bookkeeping. Their sum is exactly the core interval; clock overhead is
  included, not estimated or subtracted. In version 2 reports,
  `online_wall_ns` and both online seconds fields cover the enclosing call,
  beginning with construction/validation of the supplied target point and
  ending after the search result and any local replay. `online_accounting`
  splits that interval into target-input validation, core and caller overhead.
  An unprofiled core/overhead stays null. Match profiling across
  controls. The library exposes `solve_profiled` and
  `relation_yield_profiled`, leaving the original APIs uninstrumented.
  Soft deadlines may be affected by instrumentation. Yield-only collection
  has zero graph and certificate-replay phases. Replay/decomposition-only
  modes cannot request these attack-search phases.
- `--replay-relations rows.jsonl` replays public `a,b,i,j,si,sj` rows (or
  `a,b,terms` rows when `--summands` is `3` or `4`). The report identifies
  certificate replay and leaves attack-time/query fields null. It cannot be
  combined with `--rho`.
- `--summands 2|3|4` selects two-term (`m=2`, default), three-term (`m=3`), or
  four-term (`m=4`) signed factor-base decompositions and sparse mod-`n`
  certificate recovery (`verify_multi_certificate`). `[pcc:unverified]`
- `--max-queries`, `--walk-lanes`, `--max-relations`, `--max-proof-nodes`,
  `--max-millis`, `--backend`, and `--seed` specify execution limits.

The primary IC comparison has three arms: special auxiliary maps; direct IC
on the same special base; and direct IC on an independent equal-size random
base. The middle arm isolates the maps' effect; it cannot substitute for the
random-base comparison. Freeze several base seeds before generating fresh
targets. All arms use the same target subgroup and public query sampler.
Run both fixed-prefix relation collection and full certificate-producing
search. Charge base construction, auxiliary-curve discovery/counting/kernel
preparation, collection, linear algebra and replay to the cold total; a warm
comparison reports excluded setup separately. Existing CLI preparation times
do not include offline auxiliary-curve discovery. The comparison specification
is in `experiments/prime-field-auxiliary-ic/random-vs-special/COMPARISON.md`.
Reports include `factor_base.columns_blake3` for the actual ordered columns.
The companion `random-vs-special/compare_reports.py` checks three saved scalar
yield reports and derives exact row/hit fractions only for matching completed
prefixes. It refuses mismatched bases/settings, censored rows and replay/solve
modes; it supplies no timing or end-to-end qualification. Full base archives
and signed replay remain required for research measurements.

Version 2 reports also expose a disjoint `cli_accounting` partition through
the resource snapshot: preparation, pre-call bookkeeping, online call,
reporting and optional rho reference. The IC observed total excludes the
rho interval. Accounting serialization, process start/exit, upstream
auxiliary preparation and independent replay are outside this observed
interval, and cold total stays null. These are local producer diagnostics.
Version 1 reports retain their historical meaning: profiled
`online_wall_seconds` covered only the core. The checker accepts either
version under its own rules and refuses mixed-version comparisons.
`[pcc:unverified]`

Run research measurements only after the repository checkpoint and GPU-host
requirements are met. CLI durations and phase partitions are producer
diagnostics. Upstream discovery/construction costs and independent replay are
outside the core partition and remain explicitly unmeasured. Complete cold
accounting, an admitted fresh-target panel, and independent signed replay are
still needed for a qualified speedup. No new Rust-versus-C++ or
IC-versus-rho speedup is established by this integration. `[pcc:unverified]`

## Correctness checks

```sh
cargo test --release --manifest-path crates/prime-field-auxiliary-ic/Cargo.toml
cargo +1.78.0 test --manifest-path crates/prime-field-auxiliary-ic/Cargo.toml
cargo clippy --manifest-path crates/prime-field-auxiliary-ic/Cargo.toml --all-targets -- -D warnings
cargo test --manifest-path bindings/rust/Cargo.toml -p cryptanalysis --test auxiliary_ic
cargo test --manifest-path suite/Cargo.toml --lib cli::tools::ic::auxiliary::tests
```

Tests compare exact circuit values with the explicit product of the Semaev
quadratic over every raw root in both requested fields, check available SIMD
backends, compare graph rank and recovery with separate dense elimination,
perform complete small-field IC solves, reject forged certificates and bad
inputs, compare both IC paths on matched walks, and replay historical public
31-bit rows. Binding tests compare point operations with the C Montgomery
implementation. These are producer correctness checks, not independent signed
verification or performance measurements. `[pcc:unverified]`

Additional cases cover zero/mixed center shifts and a 128-root fixture with 58
usable coordinates, spanning multiple SIMD tiles and a partially padded final
tile. The arithmetic rewrite and fused zero collection have no fresh timing
result yet. `[pcc:unverified]`

The field-fiber checks compare explicit Semaev products, zero indices and
signed rows against direct subtraction in both requested fields, with odd and
even multiplicative degrees, multiple cosets, and torus depths spanning SIMD
tiles. Full small-field recoveries use matched walks and identical recovery
certificates. These are additional implementation leads; their effect on
relation yield, cold setup and end-to-end time remains unmeasured.
`[pcc:unverified]`


## Complete M31 command

From the repository root with Rust1.88 installed:

```sh
scripts/m31-complete 2144058214 807222724 --out recovery.json --seed 1
```

The command rebuilds current source, recovers from public coordinates, creates
an output file without overwriting another, and checks the saved complete
signed certificate with the original verifier and a second native arithmetic
implementation. `scripts/m31-verify recovery.json --qx X --qy Y` also checks
an existing report. Exit0 denotes a locally checked recovery; bounded
incomplete reports return1 and invalid worker inputs return2. The standalone
`m31-fast` binary defaults to B256/m2 on the fixed public lab curve
p=2147483647, a=2,b=14,N=2147505293,G=(1,814455902). These producer checks do
not constitute a signed independent verdict. `[pcc:unverified]`
