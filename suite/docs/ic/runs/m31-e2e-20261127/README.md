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
crates/prime-field-auxiliary-ic/target/release/examples/m31_e2e \
  --qx 2144058214 --qy 807222724 --method indexed \
  --columns 256 --summands 4 --base interval --seed 1
```

The worker accepts public coordinates only and emits a full recovery
certificate, exact base points, complete cost boundaries and counters.
Use `--profile` only for a separate diagnostic. See PROTOCOL.md for frozen
tuning/held-out selection and the exact scope of any reported result.
