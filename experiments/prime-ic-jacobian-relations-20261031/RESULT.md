# Jacobian relation-walk implementation result

## Outcome

The opt-in implementation is complete and passes the scoped correctness
gates.  No performance result was produced: the required resume-checkpoint
upload failed before any timing command, as recorded in the linked
[access problem](../../problems/prime-ic-jacobian-checkpoint-access.md).
Accordingly this result establishes neither a speedup nor a slowdown.

The affine collector remains the default.  The candidate is selected with:

```sh
ca-ic prime --solver orbit --relation-coordinates jacobian ...
```

Its JSON configuration reports `relation_coordinates: "jacobian"` and
`relation_lanes: 32`.  The full-decomposition control remains affine.

## Correctness evidence

Source base: `1ee4f47e962aac7f0f09781e34fccfaec1c6456e`, branch
`codex/prime-jacobian-relations`.  Checks ran in the repository's Rust 1.87
Docker toolchain, release mode where specified:

```sh
cargo clippy --locked --lib --bin ca-ic --test ic_prime -- -D warnings
cargo doc --locked --no-deps --lib  # RUSTDOCFLAGS="-D warnings"
cargo test --locked --release --lib jacobian_lanes_match_affine_on_every_curve_shape
cargo test --locked --release --lib known_answer_runs_for_every_type
cargo test --locked --release --test ic_prime jacobian_relation_lanes_recover_every_prime_curve_type
cargo test --locked --release
python3 -m py_compile experiments/ic-bench/prime_bridge.py
```

All commands passed.  The full release gate reported 3,042 unit tests passed,
90 ignored, zero failed; every binary, integration test, and doc-test group
also passed (including all 12 `ic_prime` integration tests).  The arithmetic
differential test covers identity,
inverse, doubling, mixed addition, non-unit accumulated `Z`, and simultaneous
normalization.  The pipeline tests cover generic `a = -3` (the P-224 shape),
`j = 0`, and `j = 1728`; every known-answer target recovers, with zero rejected
relations, uncertified columns, or inconsistent components.

The current main revision also contained two build-gate defects in its recent
hashed-tensor integration: two distinct path crates shared the exact package
identity `hashed-ecdl-tensor v0.1.0`, and four current clippy lints failed.  The
candidate gives the suite-local crate version `0.1.1`, regenerates the lockfile,
and applies only the four mechanical lint rewrites.  This allowed the exact
native tree, without a manifest overlay, to pass the checks above.

## Accounting and claim boundary

The candidate is charged for all 32 initial scalar multiplications, every lane
restart, and one existing abstract probe operation per processed walk advance.
Projective coordinates receive no operation-count discount.  The benchmark
bridge includes coordinate representation and lane count in the candidate
manifest and ID, preventing affine and Jacobian receipts from colliding.

This is an implementation and correctness result.  A stage speedup requires
the frozen paired measurement in [PROTOCOL.md](PROTOCOL.md) after the checkpoint
gate succeeds; an end-to-end IC speedup would require a separate whole-pipeline
result.
