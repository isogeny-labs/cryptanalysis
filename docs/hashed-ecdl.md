# Hashed-factor-base ECDL reference

2026-10-29. **Partial replication: executable reduction, no fast tensor solver.**

The requested source is Akshima et al., *A Subexponential Time Algorithm for
Elliptic Curve Discrete Logarithm*, v0.2 (October 29, 2026),
[upstream revision 1ee44e5](https://github.com/bochum-crypto/subexponential-ecdl/tree/1ee44e562b1b9a50ea339f3b8f81112b5a24b96f).
That revision contains only a PDF. This is an independent Rust implementation
of its §3.2–3.5 reduction and Figure 2, not copied upstream code.

| Requested requirement | Status | Evidence / remaining gap |
| --- | --- | --- |
| Add code to `isogeny-labs/crypto` and `isogeny-labs/cryptanalysis` | implemented | Public `hashed_ecdl` modules in both Rust APIs; byte-identical algorithm source |
| Replicate affine-hashed factor bases | implemented, unit-tested | `HashBase::enumerate`; inverse-hash enumeration cross-checked against every point in the fixture group |
| Replicate randomized relations and scalar extraction | implemented, unit-tested | `solve`, `solve_with_oracle`, `verify`; slot-specific columns, N+1 rows, modular dependency, nonzero V, scalar replay |
| Compact low-degree Boolean tensor encoding | not implemented | Requires the arithmetic networks of §2 and composition of §3.3 |
| Claimed fast Boolean tensor contraction | not implemented | Theorem 2 assumes external [Ope26] Theorem D.1; no executable solver is supplied by the linked repository |
| Reproduce the subexponential complexity | unresolved | Neither enumeration nor passing toy tests establishes the conditional asymptotic bound |

## Using the code

In crypto:

```rust
use crypto_lib::cryptanalysis::hashed_ecdl::{Curve, Config, solve, verify};

let curve = Curve::new(211, 0, 7, 199)?;
let generator = Some((3, 33));
let target = curve.mul(generator, 42)?; // Public known-answer fixture only.
let certificate = solve(&curve, generator, target, &Config::default())?;
assert_eq!(certificate.scalar, 42);
verify(&curve, generator, target, &certificate)?;
# Ok::<(), crypto_lib::cryptanalysis::hashed_ecdl::Error>(())
```

In cryptanalysis, import `cryptanalysis::hashed_ecdl` instead. This addition is
in its Rust API; the existing C ABI, Python and Go APIs are unchanged.

The generator and target are public points. The oracle never receives the
known scalar, generator, or query coefficients. Every decomposition is checked
for membership in each slot and for its group sum before entering the matrix.
The certificate contains the successful trial's hash seeds, relations and row
dependency. Replay rebuilds the bases and matrix, verifies each relation and
nonzero dependency, checks V != 0 and recomputes `[scalar]P = Q`. Trial/attempt
counters describe execution but are not attestations of discarded trial history.

## Implemented choices and differences from the theorem

- `enc(A) = 2x + (y mod 2)`; independent affine hashes over the first prime
  s in `[2p,4p]`. Multiplier is nonzero. Enumeration inverts each hash for
  `0 <= t < tau`, decodes the point and sorts by coordinates.
- The default tau is the integer ceiling of
  `s * max(ceil(r^(1/m)), 10m) / (r-1)`. There are no floating-point roots.
  If tau exceeds s, an error is returned rather than silently clamping it.
  Explicit tau overrides are allowed for tiny correctness fixtures and have
  no claimed coverage guarantee.
- The default `Enumerate` oracle exhausts the first m-1 bases and tests the
  final group residual in the last base. It is **generic decomposition
  (bounded by sqrt(r); cannot beat rho)** under the repository's track naming,
  not the algebraic/tensor track. Its per-query work can grow as the product
  of m-1 base sizes. It does not implement or emulate the claimed fast solver.
- Each `(slot, point)` is a separate column, including points shared by slots.
  Each trial collects N+1 relations or stops after 20(N+1) targets. Elimination
  depends on incidence rows only, not on u or v; V=0 restarts with fresh bases.
- Seeded SplitMix64 with rejection sampling supplies reproducible public
  fixtures; it is not a cryptographic RNG or a proof of genuinely independent
  uniform sampling. No probabilistic runtime guarantee is asserted for it.
- Cofactor one and full odd-prime cardinality are checked by exact counting.
  Supported p is at most 65521, m is 2 through 8, dense columns at most 512,
  and fresh trials at most 1000. Default limits are 16 trials and 1,000,000
  first-m-1 tuples per query. Work exhaustion is `Error::Limit`, never
  `None`/a false nonexistence certificate.
- Small-curve arithmetic is intentionally self-contained so the identical
  module can be checked without the large root crate. A square-root lookup
  table is constructed in O(p) time/space, unlike the paper's polynomial-in-b
  square-root routine. General-size fields and fixed-cofactor support remain
  absent. The independent C-arithmetic cross-check is in cryptanalysis's
  Rust library tests.

## Validation

These are development correctness tests, not experimental performance evidence.
No IC/rho comparison, speed ratio, benchmark, deployed-curve run, or asymptotic
verification was performed. No new mathematical theorem or Lean proof is claimed.

The shared module can be checked in isolation without the full dependency tree:

```sh
# crypto checkout
rustc --edition 2021 --test -O -D warnings -D missing-docs \
  src/cryptanalysis/hashed_ecdl.rs -o /tmp/hashed-ecdl-tests
/tmp/hashed-ecdl-tests

# cryptanalysis checkout, including independent C arithmetic
cargo test --release --manifest-path bindings/rust/Cargo.toml -p cryptanalysis --lib
cargo clippy --manifest-path bindings/rust/Cargo.toml -p cryptanalysis --lib -- -D warnings
```

Nine shared tests include complete-group hash enumeration, every target in a
199-point group for the decomposition oracle, all logarithms in a 19-point
group for full recovery, seeded two- and three-slot solves, deterministic
reproduction, invalid curve orders and coordinates, overlapping columns,
uninformative V=0 extraction, empty bases, exhausted work/trials, malicious
oracle output and corrupted certificate rejection. See the PR validation
section for actual integration commands and outcomes on the published head.

## Literature and prior-code review

The primary source's abstract, Theorems 2 and 4, §3.2–3.5, and limitations
explicitly make the asymptotic conclusion conditional and disclaim a concrete
improved attack on deployed curves. The linked repository supplies neither the
external [Ope26] manuscript nor a solver; that theorem was not independently
verified here. This is an implementation gap, not a proof of impossibility.

Checked local prior work: crypto's
`research/notes/index-calculus/RESEARCH_IC_BOUNDARY_LEDGER.md`,
`src/cryptanalysis/semaev_decomp.rs`, `aps_single_relation.rs`, and
cryptanalysis's `bindings/rust/cryptanalysis/src/index_calculus.rs`. The latter
implements multiplicative finite-field IC, not this elliptic-curve reduction.
The ECDLP atlas was searched for tensor, subexponential and randomly hashed
factor-base leads; no exact tensor-reduction entry matched. Its
`ic-engine/LEAD-ICE-first-fall-degree-assumptions.yaml` was read as adjacent
prior work; this addition makes no first-fall-degree or novelty claim.

[Pipeline diagram](hashed-ecdl.svg) · [PDF report](hashed-ecdl.pdf) ·
[open implementation obstruction](https://github.com/isogeny-labs/crypto/blob/main/problems/hashed-ecdl-tensor-backend.md).
The IC scoreboard, progress timeline, leaderboard and curve diagrams stay
unchanged: this code supplies no admitted measurement or new mathematical
curve/route finding to plot. No frozen evidence or ledger row is modified.
