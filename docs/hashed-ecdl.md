# Hashed-factor-base ECDL: native tensor implementation

2026-10-29. The compact encoder, exact contraction algorithm and relation
pipeline are implemented in Rust in both repositories. Small-case correctness
checks do not establish the manuscript's asymptotic bound or a practical speedup.

## Scalar tensor companion


An independently executable [scalar BTN reference](../experiments/hashed-ecdl-tensor-reference/README.md)
accompanies the native implementation as a separately scoped development reference. It implements the ell=1
Cauchy/mode/Hermite recursion and coordinate constraints using compact integer
Fourier multiplication and a tested binary-polynomial Fourier adaptation.
It now also includes official Certicom ECCp-131 parameters and prime-field
coordinate constraints, hashed membership, relation collection and replay.
The companion is Python and is not wired into the Rust API below.

Its 39 development correctness tests include exact rational checks,
independent direct contractions, two recursion levels and an OpenSSL arithmetic
comparison. The recorded ECC2K-130 graph has 2,694,680 edges and maximum degree
1,032. The paper's default u_0 is zero at this size; the attempt selects exact
summation and exceeds its configured work budget, without finding a challenge
relation or scalar. Historical timings are retrospective local diagnostics,
not admitted speed measurements. The small indexed tensor fixture is explicitly
separate from the coordinate construction and has no compact-encoding guarantee.

The added ECCp-131 target graph has 1,564,506 edges and degree 1,032, and also
selects u_0=0 and exceeds its exact-leaf budget. Sixteen published P/Q multiples
match OpenSSL. See the separate [prime validation report](../experiments/hashed-ecdl-tensor-reference/prime-development/README.md).

The native tensor implementation is now available on main; this companion is
not its backend. The companion's general ell>1 case, independent cross-checks,
formal verification and complete algorithm/complexity audit remain open. See the companion's requirement/status table.

## Native implementation

The source is Akshima et al., *A Subexponential Time Algorithm for Elliptic
Curve Discrete Logarithm*, v0.2,
[pinned Bochum revision](https://github.com/bochum-crypto/subexponential-ecdl/tree/1ee44e562b1b9a50ea339f3b8f81112b5a24b96f).
Upstream contains a PDF, with no executable implementation. This independent
implementation follows §2, §3 and Figure 2. Its recursive backend follows
Appendix D.1/D.4 of OpenAI's October 25 manuscript,
[pinned revision](https://github.com/openai/math/tree/7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026).
The Bochum theorem is conditional on that external result; general correctness
and the complexity proof have not received an independent audit here.

| Requested component | Delivery | Validation boundary |
| --- | --- | --- |
| Code in crypto and cryptanalysis | Identical `hashed-ecdl-tensor` sources, public Rust exports and native runner | Integration commands and actual outcomes in the tensor validation receipt |
| Compact low-degree Boolean encoding | Ripple operations, two-stage Fourier integer products, canonical modular products, exceptional point-addition branches, affine hashes and cofactor clearing | Independent integer products through 513-bit words; degree/edge bounds; exhaustive small-curve pairs |
| Exact tensor contraction | Unramified 2-adic ring; conditional-expectation packing; integral Cauchy deformation; weighted modes; implicit packet tensors; tapered Hermite recovery and depth-first recursion | Exact ring/interpolation tests; forced small recursion versus independent direct contraction; retained entries preserve creation precision |
| Full relation reduction | Inverse-hash bases, deterministic tensor witnesses, N+1 relations, slot-specific columns, modular dependency, V=0 retries and scalar replay | Full tiny known-answer pipeline; cofactor projection; certificate corruption controls |
| General field/subgroup inputs | Arbitrary-precision integers, exact AKS primality, Tonelli–Shanks and certified full cardinality c*r | Explicit resource limits; fixed-cofactor asymptotics only; no deployed-size run |
| Conditional asymptotic claim | Source algorithm transcribed, including its admission guards | Not independently proved or measured; no performance conclusion |

## Use the tensor API

In crypto the API is `crypto_lib::cryptanalysis::hashed_ecdl::tensor`; in
cryptanalysis it is `cryptanalysis::hashed_ecdl::tensor`. Both also depend on
the standalone `hashed_ecdl_tensor` crate. The earlier bounded `hashed_ecdl`
API remains available for comparison; its generic residual-enumeration oracle
and field bound are not the implementation of the tensor path.

```rust
use crypto_lib::cryptanalysis::hashed_ecdl::tensor::{
    arithmetic::OsRandom, contraction::Counter, curve::{Curve, Point},
    reduction::{self, Config}, Limits, Meter,
};

let mut meter = Meter::new(Limits { steps: 2_000_000_000, ..Limits::default() });
let generator = Point::Affine { x: 0u8.into(), y: 1u8.into() };
let curve = Curve::new(5u8.into(), 2u8.into(), 1u8.into(), 7u8.into(),
                       generator, &mut meter)?;
let target = Point::Affine { x: 3u8.into(), y: 2u8.into() }; // Public fixture.
let mut counter = Counter::default();
let certificate = reduction::solve(&curve, &target, &Config::for_curve(&curve),
    &mut OsRandom, &mut counter, &mut meter)?;
reduction::verify(&curve, &target, &certificate, &mut meter)?;
assert_eq!(certificate.scalar, 4u8.into());
# Ok::<(), crypto_lib::cryptanalysis::hashed_ecdl::tensor::Error>(())
```

`Curve::with_cofactor` accepts a certified full cardinality c*r, prime r>c,
and a nonzero r-torsion generator. A unique Hasse-interval multiple certifies
cardinality when possible; ambiguous cases are counted exactly under the same
meter. For fixed c the ambiguity is confined to a finite parameter range.
The encoder projects free Si to Ai=[c]Si; assignment counts can include several
Si preimages, while witnesses still project exactly onto subgroup decompositions.

`GraphBuilder` accepts arbitrary Boolean predicates, including parallel edges
and isolated scalar vertices. `Counter::count` returns an exact integer.
`Counter::witness` fixes interface bits through exact prefix counts, using at
most one initial count and one count per unfixed interface bit. `None` means
an exact zero contraction. `Error::Limit` means unknown, never unsatisfiable.

## Run and replay from files

From crypto:

```sh
cargo run --locked --release --manifest-path crates/hashed-ecdl-tensor/Cargo.toml -- \
  solve crates/hashed-ecdl-tensor/examples/fixture.json /tmp/hashed-ecdl-receipt.json
cargo run --locked --release --manifest-path crates/hashed-ecdl-tensor/Cargo.toml -- \
  verify /tmp/hashed-ecdl-receipt.json
```

In cryptanalysis replace the manifest and fixture prefixes with
`bindings/rust/hashed-ecdl-tensor/`. The output path must be new: the runner
never silently replaces an existing receipt. Inputs use unsigned decimal
strings; a null target is the identity. Omit `fixture_seed` for OS randomness.
The seeded generator is only a reproducibility aid for public correctness
fixtures; it does not satisfy ideal independent-uniform runtime hypotheses.

Receipts contain the input problem, successful trial's seeds, relations, row
dependency, scalar and informational execution counters. Big integers inside
the certificate use num-bigint's JSON array of little-endian 32-bit limbs;
problem coordinates and `scalar_decimal` are decimal strings. Replay ignores
the counters, rebuilds bases, verifies every group equation and slot-column
cancellation, requires a nonzero dependency and V, and checks [scalar]P=Q.
No receipt attests discarded trials or execution time.

Standalone replay obtains root-extraction randomness from the OS.
`verify_with_rng` accepts an explicit source for reproducible public fixtures;
the solver forwards its caller's source through self-verification. Selecting
a nonresidue changes work, not the canonical decoded point. Fixed test seeds
are not used internally for production replay.

## Algorithm and finite-size behavior

The encoder uses the paper's integer J/k/L parameters, canonical words over
Z/(2^J+1), two-stage Fourier transforms, unique carry witnesses and checked
quotient identities. Hash tests use coordinate bits and modular arithmetic,
without consulting enumerated base lists. Point predicates include identity,
inverse, ordinary addition and doubling. Boolean zero tests replace the
source's inverse witnesses without changing the stated edge/degree orders.

Contraction subdivides edges to obtain a bipartite network and uses precision
E+1 to recover an integer count. The recursive branch checks the source's
u/a/L/D/degree/shrink conditions. Packet entries are evaluated at their
immutable creation precision before canonical lifting. Mode tuples are
streamed; child tensors materialize their local description instead of
composing callbacks to old tensor evaluators. Hermite reconstruction uses
exact rational arithmetic and rejects a nonunit final denominator.

The literal source constants make the recursive admission threshold
astronomical: u=floor(ceil(log2(s))/131072), with s the source's network-size
parameter here, is zero for all practically
addressable networks. The implementation therefore uses the manuscript's
finite-size fallback there. For built-in encodings, private unique-witness
metadata permits exact enumeration over free input bits rather than every
auxiliary edge. Arbitrary caller predicates cannot attach these hints.
`last_backend` reports `Direct`, `Functional` or `Recursive`; a functional
leaf is not reported as a measured fast contraction. Forced small-recursion
tests bypass size/shrink admission only and compare the same kernel, modes,
packet entries and reconstruction with independent direct contraction.

Factor-base enumeration inverts each t<tau and uses Tonelli–Shanks, with no
root table. Prime certification follows
[AKS §4](https://www.cse.iitk.ac.in/users/manindra/algebra/primality_v6.pdf),
with trial division only below a fixed 16-bit prefix. `Config::for_curve`
chooses the integer version of ceil((log2(b))^(1/4)), at least two.
Default tau is a conservative integer-root version of Lemma 13, clamped to s
when finite-size coverage hypotheses fail. An override need not satisfy the
coverage theorem. Each trial makes at most 20(N+1) attempts, and V=0 restarts.
Decomposition and dependency selection receive no u/v information.

Steps, vector lengths, integer precision, columns and trials all have explicit
caller bounds. These may stop a run far below cryptographic sizes. The code
does not certify the source theorem, reproduce its general asymptotic bound,
or establish a security consequence for any deployed curve. No performance
experiment, IC/rho comparison, new mathematical result or Lean proof is claimed.

## Validation and provenance

Use the [tensor validation receipt](hashed-ecdl-tensor-validation.md) for
current commands, source hashes, failures and outcomes. The
[first reference receipt](hashed-ecdl-validation.md) records the earlier
bounded implementation and capped broad regression; its historical hashes
and outcomes remain unchanged. The completion table is in
[the workstream record](hashed-ecdl-completion.md).

Prior review included crypto's index-calculus boundary ledger,
`semaev_decomp.rs`, `aps_single_relation.rs`, cryptanalysis's multiplicative
finite-field IC binding and the ECDLP atlas's first-fall-degree lead. None
supplied this exact BTN implementation. No novelty claim follows from that
search. The external manuscript and AKS primary source were read before
implementing their algorithms.

During implementation, a separate binary-curve bucket/cutset prototype landed
in crypto at `research/btn_ecdl_20261029/`. Its README and contractor were reviewed at
main `57bb19c48`; it uses a quadratic multiplier and a stand-in contractor,
with an untested GPU path. Its files and historical outputs are preserved.
The native prime-field Fourier and Appendix D.4 implementation here does not
execute or extend that Python path.

[Diagram](hashed-ecdl.svg) · [PDF](hashed-ecdl.pdf) ·
[remaining independent-audit obligations](https://github.com/isogeny-labs/crypto/blob/main/problems/hashed-ecdl-tensor-backend.md).
No scoreboard, leaderboard, frozen run, curve route or measurement gate is
changed: this addition supplies development correctness evidence only.
