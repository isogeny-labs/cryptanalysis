# hashed-ecdl-tensor

Native, arbitrary-precision implementation of the compact Boolean encodings
and conditional hashed-factor-base ECDL algorithm. The recursive contraction
backend follows the pinned October 25 manuscript's Appendix D.4. The source
constants require exact finite-size fallback on practical inputs; diagnostics
report that fact. No practical or asymptotic performance result is claimed.

Public modules provide exact arithmetic and prime certification, certified
curves, graph construction, compact arithmetic/point/hash encodings, exact
contraction, deterministic witness extraction, relation collection and
independent algebraic certificate replay. Resource exhaustion is an error.

```sh
cargo test --locked --release
cargo clippy --locked --all-targets -- -D warnings
cargo +1.78.0 check --locked --all-targets
cargo run --locked --release -- solve examples/fixture.json /tmp/hashed-receipt.json
cargo run --locked --release -- verify /tmp/hashed-receipt.json
```

The file runner uses decimal-string problem coordinates and an exclusive new
output path. Omit the fixture seed for OS randomness. Certificates serialize
large integers as little-endian 32-bit-limb arrays. Replay checks mathematics,
not execution counters. All bundled examples are public inputs; the challenge example below is not a tiny fixture.

Problem, receipt, certificate and point records reject duplicate and unknown
fields at every typed level. An optional field set to null still counts as
present for duplicate detection. File inputs are limited to 16 MiB of actual
content; the reader uses one extra byte to reject oversized inputs, including
growing files and streams.

Sources and implementation boundaries:
[implementation report](https://github.com/isogeny-labs/crypto/blob/main/docs/hashed-ecdl.md),
[Bochum v0.2](https://github.com/bochum-crypto/subexponential-ecdl/tree/1ee44e562b1b9a50ea339f3b8f81112b5a24b96f),
[OpenAI Appendix D](https://github.com/openai/math/tree/7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026).

This crate is mirrored in crypto and cryptanalysis. Its source files must
remain byte-identical; the owning repositories have separate integration locks.

## Exact validation and witness search

Primality now uses deterministic bounded tests throughout u64, with the first
twelve prime bases and the published Sorenson/Webster bound. Larger values
retain AKS unless independently checked Pocklington certificates are supplied.
`Curve::with_cofactor_and_certificates` verifies every supplied proof node and
the existing curve/order/cofactor conditions; a missing proof uses the original
exact fallback. The runner includes proof data in its receipt for replay.

```sh
cargo run --locked --release -- validate examples/eccp131-certified.json
```

The certified input supplies four small proof nodes for the official p/r. The
original `eccp131.json` remains an uncertified-input control. Parameter validation
does not recover the challenge scalar or establish feasible relation search.

Built-in functional leaves now select the same least interface word in a
single input search. A free-input interface permits stopping at the first
valid assignment in interface order; derived interface bits require a complete
pass to find the least word. Every returned assignment still passes full graph
evaluation. Exact count queries and the source recursion guards are unchanged.
Set `Counter::functional_witnesses = false` or call `witness_by_counts` to use
the original prefix-count control. Arbitrary caller predicates retain it.

Correctness controls compare complete seeded certificates and retain forged
proof, UNSAT, alias/pin, derived-interface and resource-limit cases. See the
paired optimization report for actual checks and open benchmark requirements;
these changes alone do not establish a runtime or end-to-end speedup.


## Certicom ECCp-131 input

`examples/eccp131.json` contains the exact public prime-field challenge from
[Certicom's curve list](https://www.certicom.com/en/curves-list). The official
name is ECCp-131, rather than ECCp-130. It supplies the 131-bit field and
subgroup order, cofactor one, generator P and published target Q. It has no
known scalar and omits fixture_seed, so admitted random choices use the OS RNG.

```sh
cargo run --locked --release -- solve examples/eccp131.json /tmp/eccp131-receipt.json
```

The bundled input bounds work at 2,000,000 charged steps, 200,000 vector entries
and 4,096 integer bits. An exhausted prime-certification, enumeration or tensor
budget is an error with unknown result, not a solution or proof that no solution
exists. These bounds do not make the challenge feasible. No ECCp-131 scalar
has been recovered by the development checks. A successful receipt would need
independent replay with the existing verify command.
