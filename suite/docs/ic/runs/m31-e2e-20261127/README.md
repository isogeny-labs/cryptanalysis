# Complete M31 recovery command

From repository root, with Rust1.88 installed:

```sh
scripts/m31-complete 2144058214 807222724 --out recovery.json --seed 1
```

This builds current source, recovers from public coordinates, saves the complete
signed dependency, and checks the saved report through the original strict
certificate verifier and a second native arithmetic implementation. Existing
output files are refused. Success returns exit0 and a checked-result JSON;
a bounded incomplete result is retained and returns1; invalid input returns2.
These are local producer checks, not a signed independent PCC verdict.
[pcc:unverified]

To use the components separately:

```sh
scripts/m31-fast 2144058214 807222724 --seed 1 > recovery.json
scripts/m31-verify recovery.json --qx 2144058214 --qy 807222724
```

The optional expected target binds the saved certificate to the point you
intend to check. The normal native executable is `m31-fast`; `--help` lists
all budgets and base choices. The fixed public lab curve is
Fp p=2147483647, y²=x³+2x+14, N=2147505293, G=(1,814455902).
Defaults are the prospectively selected B256/m2 interval-base configuration.
The full build cost and final JSON emission sit outside the historical native
cold timing boundary; binary/source hashes distinguish the completed command
from the original frozen measurement worker. [pcc:unverified]

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
