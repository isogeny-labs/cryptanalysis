# Native factoring and weighted-profile integration

This change imports the new tensor modules from the paired `isogeny-labs/crypto`
work and exposes them through the existing Rust re-export:

```rust
use cryptanalysis::hashed_ecdl::tensor::{factoring, weighted};
```

The same additions are included in `crates/hashed-ecdl-tensor`, the native
dependency used by `suite/Cargo.toml`, so both current entry points expose
the APIs and the standalone factoring runner. The older suite copy and the
bindings copy retain their other existing differences.

`factoring` supplies a parsimonious multiplication/divisor network, exact
MSB-prefix counts, smallest-factor self-reduction and complete factorization.
`tensor-factor N [MAX_STEPS]` is the native standalone runner. The minimum-factor
boundary conventions match Mathlib; complete factorization rejects zero and
returns an empty list for one. Resource errors never become zero counts or a
successful partial list.

`weighted` supplies exact local-cost coefficient profiles with hard constraints
and minimum/maximum extraction. It is an exhaustive reference backend. Neither
module establishes the Hexagon papers' asymptotic bounds: factoring uses the
existing OpenAI-based counter rather than the Anthropic engine re-proved by the
factoring authors, and weighted recursive contraction is not implemented.

The complete 22-paper review and additional prime-field factory recipes live in
`crypto:research/hexagon_cscc_20261030/` and `crypto:tools/factor-base/`. The
searchable catalog records every work's assumptions, integration scope and
evidence status. This repository's existing factor-base archive and curve
authorities are preserved; no new curve, IC1 result or performance row is minted.

```sh
cargo test --locked --release --manifest-path bindings/rust/Cargo.toml -p hashed-ecdl-tensor
cargo clippy --locked --manifest-path bindings/rust/Cargo.toml -p hashed-ecdl-tensor --all-targets -- -D warnings
cargo test --locked --release --manifest-path crates/hashed-ecdl-tensor/Cargo.toml
cargo clippy --locked --manifest-path crates/hashed-ecdl-tensor/Cargo.toml --all-targets -- -D warnings
```

## Parity and validation scope

The new `factoring.rs`, `weighted.rs`, `tensor-factor.rs` and `factoring_cli.rs`
are byte-identical in both copies and in the paired crypto change. Both copies
export the modules. At initial checkout the bindings and crypto differed in
eight other source files; those independent changes were preserved. Current
main's additional finite-size modules were then incorporated without changing
their contents. Whole-crate parity is not claimed. Software-check logs and
new-file hashes are retained in `checks/`.

After integrating main `55f659309e510fc861a1e54ff199b9f2bf63e17a`, the complete
bindings tensor package passes 88 tests (57 library, eight binary-runner and
23 integration tests). The suite copy passes 34 tests (33 library and one CLI).
Both pass strict all-target Clippy, formatting and the declared Rust 1.78
minimum-toolchain check. Final outputs are `checks/cryptanalysis-*-integrated.*`
and `checks/cryptanalysis-suite-tensor-*`. Earlier passing outputs are retained
separately. Verbatim logs with trailing blank lines are stored losslessly as
gzip. This is software validation, not a timed research result. The report
lives under `docs/ic/` under the existing PDF artifact-policy exemption.

The report's [PDF](report.pdf), [Typst source](report.typ),
[catalog](catalog.json) and [diagram](integration.svg) are derived copies of the
canonical crypto report. Statements and limitations were reviewed; full proofs
and Lean developments were not independently rebuilt. Existing performance and
frontier graphs receive no new data. There is no benchmark, new theorem,
challenge solve or research-state promotion in this PR. The general tensor
correctness/complexity audit remains open in the existing cross-repository
problem record.
