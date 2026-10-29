# hashed-ecdl-tensor

Native, arbitrary-precision implementation of the compact Boolean encodings
and conditional hashed-factor-base ECDL algorithm. The recursive contraction
backend follows the pinned October 25 manuscript's Appendix D.4. The source
constants require exact finite-size fallback on practical inputs; diagnostics
report that fact. No practical or asymptotic performance result is claimed.

Public modules provide exact arithmetic and prime certification, certified
curves, graph construction, compact arithmetic/point/hash encodings, exact
contraction, deterministic witness extraction, exact prefix-count sampling, relation collection and
independent algebraic certificate replay. Resource exhaustion is an error.

`Counter::sample` implements Lemma 1's random prefix choices using caller
randomness. It samples interface words uniformly when the encoding is
parsimonious; otherwise each word is weighted by its number of satisfying
auxiliary assignments. Pins condition this distribution. Forced branches use
no entropy, and entropy or work failures remain errors rather than empty
languages. `Counter::witness` remains the deterministic relation oracle.

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
not execution counters. All bundled examples are public tiny fixtures.

Sources and implementation boundaries:
[implementation report](https://github.com/isogeny-labs/crypto/blob/main/docs/hashed-ecdl.md),
[Bochum v0.2](https://github.com/bochum-crypto/subexponential-ecdl/tree/1ee44e562b1b9a50ea339f3b8f81112b5a24b96f),
[OpenAI Appendix D](https://github.com/openai/math/tree/7ef5c0cc5ca4b0e072b7a050fca09ab24bc6fa3a/preprints/The-Exponential-Time-Hypothesis-is-False-October-25-2026).

This crate is mirrored in crypto and cryptanalysis. Its source files must
remain byte-identical; the owning repositories have separate integration locks.
