# Structured prime-field IC consumer integration

2026-11-04. Producer report for PCC-20261104-f011a3; standing unverified.
[pcc:unverified]

Both Rust consumer paths expose the structured request/count/witness/replay
interface. The bindings package contains the scoped structured predicate and
runner; the older suite package depends on that backend for the new component,
preserving its existing tensor arithmetic and API. [pcc:unverified]

| Consumer | Entry point |
|---|---|
| Bindings API | `cryptanalysis::hashed_ecdl::tensor::structured_runner::{execute_json,replay_json}` |
| Standalone bindings command | `bindings/rust/hashed-ecdl-tensor/src/bin/tensor-structured.rs` |
| Suite command/API | `crates/hashed-ecdl-tensor` runner re-export and `structured_backend` |

`structured_backend` types belong to the bindings backend. Code using its direct
predicate API constructs its curve through `structured_backend::curve::Curve`;
the versioned JSON interface avoids mixing the two curve representations.
The structured source, runner, CLI wrapper, tests and public fixture are copied
from the paired crypto implementation, with exact scoped digests retained.
Underlying older modules are not claimed byte-identical. [pcc:unverified]

## Use the public fixture

From the repository root:

```sh
cargo run --release --locked --manifest-path bindings/rust/hashed-ecdl-tensor/Cargo.toml \
  --bin tensor-structured -- bindings/rust/hashed-ecdl-tensor/examples/structured-prime.json > receipt.json
cargo run --release --locked --manifest-path bindings/rust/hashed-ecdl-tensor/Cargo.toml \
  --bin tensor-structured -- replay receipt.json
```

Use `crates/hashed-ecdl-tensor/Cargo.toml` to invoke the suite command. Paths may
be `-` for stdin. The schema is `structured-prime-ic-request/v1`; all example
fields are required, integers are decimal strings, and a null target denotes
identity. Duplicate/unknown fields are rejected. `membership` selects `circuit`
or `fibre_message`; both retain rational subgroup restrictions and complete sum
charts. Ordered signed tuples permit repeats and inverse pairs.

One caller budget spans validation, local-message/template setup and every
count-plus-witness query. A later resource error emits no partial success JSON.
Counts, witnesses, requests and relation policy form the semantic digest.
Replay checks selected source pins and recomputes semantic answers, including
when a forged answer's digest has been recomputed. Diagnostics are separate.
Selected pins are partial source provenance, not a full build identity.
Receipts and same-implementation replay retain producer_assertion standing.

## Development checks

Native controls cover the three command paths with the shared public fixture,
strict/duplicate fields, source mutations, rehashed answers, empty fibres and
mid-batch resource exhaustion. Bindings structured-predicate controls are also
ported; existing library checks, strict Clippy, formatting and Rust1.78 checks
are retained. Results are producer assertions in `checks.json` and raw `checks/`
outputs. The tensor CI workflow covers both bindings and the suite adapter.
[pcc:unverified]

Initial builds referenced optional Meter fields missing from this older backend;
the common runner now reports only shared diagnostics. Initial offline resolution
proposed unrelated cc/find-msvc downgrades; Cargo precise updates restored the
base versions. Failed compile logs remain alongside subsequent checks.
[pcc:unverified]

The implemented reusable message is local membership. The next component is a
compact exact full constrained-summation message with construction/live-storage
accounting, routed through autoresearcher KN-OPEN-08ba7e. No scientific-state
transition accompanies this consumer integration. See [integration.svg](integration.svg)
and the inspected `report.pdf`.

Primary context is the landed [crypto C1–C3 study](https://github.com/isogeny-labs/crypto/tree/11173ecd0230a9ceedc4d833736402934fdcb95e/research/prime_ic_zero_filter_20261030/implementation),
PKM2016, Hexagon2610.00600v1/2610.00594v1/2610.00613v1 and Kosters–Yeo.
Existing C APIs are unchanged. This integration uses native development controls;
it introduces no benchmark or cloud experiment. [pcc:unverified]
