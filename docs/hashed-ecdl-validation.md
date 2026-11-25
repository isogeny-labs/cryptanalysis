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

## Packaging correction after PR #1296

PR #1296 merged on 2026-10-29. A final cross-commit whitespace check showed
that the first pre-add working-tree check had not covered new untracked files:
the generated PDF was heuristically treated as text, and the test transcript
ended with a blank line. Declare this one PDF path binary in `.gitattributes`
and remove only that final transcript blank line. The algorithm, PDF bytes and
test result lines are unchanged; the original transcript remains in commit
`ff11fd7a653f064d1fc6f85b62f5b8a7494caa14`.

`cargo clippy --manifest-path bindings/rust/Cargo.toml -p cryptanalysis
--all-targets -- -D warnings` also passed (exit 0), including the test targets.
The packaging-only follow-up needs no repeated arithmetic tests. Text diff
checks pass with the PDF correctly classified. Paired implementation:
[crypto #2878](https://github.com/isogeny-labs/crypto/pull/2878).

## Historical receipt; tensor follow-up

PR1297 merged as `fecb0698bf9697bf72360c0752ae02175ad0fad5` at
2026-10-29T21:01:28Z. The hashes and outcomes above describe the first bounded
reference and packaging correction. The native compact encoder, contraction
backend and tensor relation reduction have a separate
[current validation receipt](hashed-ecdl-tensor-validation.md); no historical
outcome or source hash above is overwritten.
