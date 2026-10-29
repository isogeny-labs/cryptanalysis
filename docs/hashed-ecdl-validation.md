# Hashed ECDL development validation — 2026-10-29

Base: `0150e952add9a5c20a881dc0d01cbaf28f78c42b`.
Host: Linux x86-64 cloud development container. No performance isolation or
performance claim. Compiler: rustc 1.99.1 (58cf8f9c3 2026-10-13).

The byte-identical shared algorithm source has SHA-256
`9c8bf104089521179a7f830e79e9bc226083dd9d26897677f4a52d8a32bb4d3b`.
This receipt records correctness checks; no experiment was launched.

| Command / check | Observed outcome |
| --- | --- |
| `rustc --edition 2021 --test -O -D warnings -D missing-docs src/cryptanalysis/hashed_ecdl.rs -o /tmp/hashed-ecdl-tests` in crypto; execute test binary | 9 shared tests passed, no failures |
| Same standalone compilation/tests with `rustc +1.78.0` | 9 passed on the Rust binding's declared minimum version |
| `cargo test --release --manifest-path bindings/rust/Cargo.toml -p cryptanalysis --lib` | 19 passed, no failures; includes all shared tests and full 199-scalar cross-check against C arithmetic |
| `cargo clippy --manifest-path bindings/rust/Cargo.toml -p cryptanalysis --lib -- -D warnings` | exit 0 |
| `cargo fmt --manifest-path bindings/rust/Cargo.toml --all --check` | exit 0 |
| `cargo doc --manifest-path bindings/rust/Cargo.toml -p cryptanalysis --no-deps` | exit 0; generated public API documentation |
| `cmp` between the algorithm modules in the two checkouts | identical |
| `git diff --check` | exit 0 |
| Typst 0.15.0 report build; `pdfinfo`; inspect both rendered pages | 2 pages; diagram and text inspected |

## Setup failures retained

- No preinstalled Rust compiler; installed the official stable minimal
  toolchain. Initial rustfmt invocation failed because the component was not
  installed; installed rustfmt/clippy and repeated successfully.
- Initial cryptanalysis build could not find `../cuda/ca_device.cuh` because
  the existing CUDA headers were outside the sparse checkout. Materialized
  `cuda/`, then both release tests and strict lint passed. No build script,
  header, C arithmetic, or test was disabled or changed to bypass this error.
- Initial binding format check requested placing the new module declaration
  after `mod group`; formatted that declaration and the scoped check passed.
- Conductor check exited 127 (`conductor: command not found`). Used the
  warn-and-allow fallback documented in crypto's `docs/CONDUCTOR.md`. No
  shared reservation or coordinator approval is claimed.

The fast tensor encoder/backend, general-size fields, fixed cofactors and
the paper's conditional asymptotic conclusion remain unresolved. See the
[implementation documentation](hashed-ecdl.md) and canonical problem link there.
CI and merge status are reported by the PR, not asserted by this local receipt.
