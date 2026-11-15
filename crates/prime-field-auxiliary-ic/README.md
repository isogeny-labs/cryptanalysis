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
running a generic polynomial GCD for this complete known-root case. It is an
exact solver specialized to two-term decompositions (`m=2`), not a general
multivariate Gröbner solver.

The implementation includes these optimization choices:

- Precomputed coordinate squares and map constants, a folded terminal map,
  and three interleaved SIMD vectors. AVX2/AVX-512 are selected only after CPU
  feature checks, for fields up to 31 bits. The 61-bit path is scalar `u128`.
- Fixed addition-chain inverses and a configurable number of target walks
  sharing one inversion. Scratch buffers are reused between queries.
- Signed graph elimination with a certificate DAG, instead of a dense
  matrix. Union by size and path compression track the two-column rows;
  certificate coefficients are expanded only for a useful dependency.
- `FactorBase::without_maps` provides IC with batched direct subtraction,
  arbitrary coordinates, and no auxiliary curve or quadratic pair table.
  It shares target generation, distinct-row handling, recovery, and public
  certificate checks with the auxiliary path.

Rust 1.78 supports the portable/AVX2 paths. AVX-512 is compiled on Rust 1.89
or later, with a fallback on older toolchains. Explicit requests for an
unavailable backend fail. No architecture flags are required.

## API

```rust
use prime_field_auxiliary_ic::{AuxiliaryMap, Backend, Config, Curve,
    FactorBase, PreparedSolver, SolveOutcome, verify_certificate};

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
- `--rho` additionally invokes the repository C batched negation-map rho
  reference on the same target. It uses Montgomery arithmetic, so this is
  explicitly a different arithmetic backend. `--rho-max-ops` bounds it.
- `--decompose-only` checks one target decomposition, without recovery.
- `--replay-relations rows.jsonl` replays public `a,b,i,j,si,sj` rows. The
  report identifies certificate replay and leaves attack-time/query fields
  null. It cannot be combined with `--rho`.
- `--max-queries`, `--walk-lanes`, `--max-relations`, `--max-proof-nodes`,
  `--max-millis`, `--backend`, and `--seed` specify execution limits.

Run research measurements only after the repository checkpoint and GPU-host
requirements are met. CLI durations are producer diagnostics. Exclusive phase
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
