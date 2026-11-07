# Hashed ECDL strict-input correction

2026-10-29. This is a code-quality follow-up in crypto and cryptanalysis,
based on crypto `d188c5a6775dff07129084ab2f3f7ae39547c9fc` and cryptanalysis
`1caa747d9bb888e0b98c739a59b17fbb1bd92e99`. The mirrored native crate remains
byte-identical. No cryptographic algorithm, theorem, performance or deployed-
curve claim changes.

## Reproduced defects and correction

The old record parser first decoded a `serde_json::Value` map. That map
silently replaced repeated keys, including nested certificate seeds, relation
scalars and point coordinates. Two of three new wire-format regression tests
fail against the original parser: it accepts repeated certificate fields and
two `Affine` variants. The third test confirms the existing missing/unknown
field checks. The original failure output is retained separately in
`hashed-ecdl-tensor-input-before.txt`.

Records now deserialize directly through `MapAccess` visitors and reject
duplicates before consuming the repeated value. Nested records keep the same
rule; escaped names such as `alpha` and `\u0061lpha` denote the same field.
Missing optional fields still default to `None`, explicit null still counts
as a present field, and the nullable `target` remains required. Unknown fields
remain errors. Points retain exactly their existing string/object wire forms.
Serialization and mathematical certificate checks are unchanged. Diagnostic
values remain informational JSON and are not certificate attestations.

The runner previously checked path metadata and then performed an unbounded
read. A growing file or stream could have a length different from that check.
It now opens the input once and reads through `Read::take(16 MiB + 1)`, rejecting
the lookahead byte rather than parsing a truncated prefix. Empty and exact-limit
inputs are accepted; oversized sources stop after the lookahead. A synthetic
reader asserts no additional read occurs, without risking an unbounded test.
I/O errors still propagate. Receipt output remains exclusive creation.

## Sources reviewed before editing

- Existing `docs/hashed-ecdl.md`, the original tensor receipt, and the native
  serialization, curve, reduction and runner code supplied the current contract.
- [Serde's manual struct implementation](https://serde.rs/deserialize-struct.html)
  uses `Visitor`, `MapAccess`, `duplicate_field` and `missing_field`. This
  correction uses that approach without new procedural derives or dependencies.
- [Rust `Read::take`](https://doc.rust-lang.org/std/io/trait.Read.html#method.take)
  specifies a byte-bounded adapter that returns EOF after its limit. One extra
  byte distinguishes a complete input at the limit from an oversized prefix.
- The pinned Bochum v0.2 paper's section 3.4 was rechecked: replay still verifies
  the same group equations, column cancellation and extracted scalar. This
  change concerns the representation and resource boundary, not the reduction.

## Validation

Development container: Linux x86-64, Rust 1.99.1; declared floor Rust 1.78.0.
All new data are synthetic parser/reader fixtures. No experiment, challenge
solve, cloud resource, benchmark or artifact-store upload was launched.

| Check | Observed result |
| --- | --- |
| Original parser, new `strict_json` integration target | exit 101; 1 passed, 2 failed as described above |
| `cargo test --locked --release --manifest-path bindings/rust/Cargo.toml -p hashed-ecdl-tensor -p cryptanalysis` | exit 0; 27 core, 5 runner, 3 wire-format, 20 binding-unit, 19 FFI-parity and 14 doc tests passed; [transcript](hashed-ecdl-tensor-input-tests.txt) |
| Native and binding all-target strict Clippy (`-- -D warnings`) | exit 0 for both |
| Rust 1.78.0 all-target check | exit 0; enclosing root manifest's existing unused `check-cfg` warning only |
| Strict binding/core API docs (`RUSTDOCFLAGS='-D warnings'`, `--no-deps`) | exit 0 |
| Standalone/workspace formatting and staged whitespace | exit 0 |
| Rebuilt native runner, verify the existing stored receipt | exit 0; independently verified scalar 4 |
| Same runner, duplicate top-level receipt schema | exit 1; `duplicate field schema` |
| Same runner, 16 MiB + 1 byte file | exit 1; `input file exceeds 16 MiB runner policy` |
| Mirror tree comparison | identical, excluding build directories |
| Existing artifact policy against the complete staged tree | exit 0; no data files committed, no waiver |
| Crypto root release library | not claimed by this binding receipt; the paired crypto PR records its separate current validation |

An intermediate selected-package run passed the 27 core, 20 binding and 19
FFI tests, but one new runner assertion failed because its expected JSON
omitted optional fields which the existing serializer emits as explicit null.
Corrected the test's expected value without changing serialization. The entire
selected-package command then passed, including all eight new tests. The
[initial panel](hashed-ecdl-tensor-input-initial-panel.txt) retains that failure.
The final compact transcript omits only the terminal separator blank line.

The new [source manifest](hashed-ecdl-tensor-input-sources.sha256) covers the
17 Cargo/source/test files and has SHA-256
`f3ab5c7f5e2aa83b47c40b5cb43d150d9c9fd5b9ed24fef66939965167df24b4`.
Run it from the crate directory, with the owning
repository's relative path to `docs/`. Earlier source manifests and validation
receipts remain historical snapshots and were not overwritten. The original
large root trace's not-uploaded status remains unchanged.

Full independent mathematical and complexity audit remains open in the
[canonical problem](https://github.com/isogeny-labs/crypto/blob/main/problems/hashed-ecdl-tensor-backend.md).
