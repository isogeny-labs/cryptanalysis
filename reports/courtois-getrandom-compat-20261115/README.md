# Restore the Rust crate's declared getrandom 0.4 API

`bindings/rust/hashed-ecdl-tensor` declares getrandom 0.4 but its `OsRandom`
implementation calls `getrandom::getrandom`, which no longer exists in that
API. The companion native Courtois field-replay build exposed this mismatch.
The edit calls `getrandom::fill` and synchronizes the package lockfile with its
existing manifest. It does not change binary-field arithmetic.

The retained producer output reports five binary Rust unit tests passing after
the API correction. Independent signed standing is pending.
Claim: `PCC-20261115-8d2645`. [pcc:unverified]

Files:

- `build-before.txt`: compiler E0425 on the removed getrandom function.
- `build-after.txt`: the replay consumer's corrected native build.
- `native-binary-tests.txt`: the binary module's producer unit-test output.

Reproduction:

```sh
cargo test --locked --manifest-path bindings/rust/hashed-ecdl-tensor/Cargo.toml --lib binary::tests
```

The cross-repository caller is in crypto's
`research/courtois_native_20261115/replay-cryptanalysis/`. These records are
development checks, not performance measurements or an execution-proof verdict.
