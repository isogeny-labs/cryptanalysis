# Integrated native M31 recovery

The original source-compatible direct pipeline remains available. The new
indexed path uses a target-independent signed pair table with all collision
witnesses, batched probes, retained signs and an x-cache, then shares the
original walk, sparse elimination and complete certificate verifier.
Cold preparation is charged. These are source-level implementation
descriptions; experimental evidence remains [pcc:unverified].

Build the dependency-free native worker from repository root:

```sh
cargo +1.88.0 build --release \
  --manifest-path crates/prime-field-auxiliary-ic/Cargo.toml --example m31_e2e
scripts/m31-fast 2144058214 807222724 --seed 1
```

The worker accepts public coordinates only and emits a full recovery
certificate, exact base points, complete cost boundaries and counters.
Use `--profile` only for a separate diagnostic. See PROTOCOL.md for frozen
tuning/held-out selection and the exact scope of any reported result.

The normal CLI also exposes `ca-ic auxiliary --pair-index --summands 2`.
Its pair-index setup is included in target-independent preparation, and
only a checked solved/replayed auxiliary report receives a successful
exit status. The direct path and all verifier thresholds remain intact.
[pcc:unverified]

The separately frozen follow-up selects 256 interval-base columns and direct
two-point lookup. Its five fresh primary targets all recovered: median
71.356 ms cold (54.148–110.804 ms). See [REPORT.md](REPORT.md),
[REPORT.pdf](REPORT.pdf) and [RESULTS.json](RESULTS.json). These are local
producer observations, with no admitted isolation or signed verification.
[pcc:unverified]
