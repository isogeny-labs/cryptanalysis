# CT245 — bounded semantic typecheck of the CT244 measured-primitive derivative

2026-11-19. Research engineering only. **[pcc:unverified]**. Protocol frozen before adding the workflow. Stacked on [cryptanalysis PR #1871](https://github.com/isogeny-labs/cryptanalysis/pull/1871), itself a CT125 derivative of the original Jacobian experiment. Does not authorize paid EKS/Spot, large native runs, timing, or benchmark promotion.

## Purpose

The CT244 source-only gate [#44613796822](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44613796822) proved only generator guards and `rustfmt` parse. A real Rust typecheck is the next discriminating check of the seven-slot runtime instrumentation; it must not be reported as evidence that the 695-record fixture runs, that the norm reuse is correct in native arithmetic, or that a complete ECDLP solver is faster. CT200 [cryptanalysis #1761](https://github.com/isogeny-labs/cryptanalysis/pull/1761) separately typechecks the CT192 public-48 driver; this gate only tests the separate **CT244** derivative and does not duplicate that driver.

## Preregistered frozen inputs

- GitHub Actions: `ubuntu-24.04`, 15-minute job; `rustc/cargo 1.99.1`, `cargo check --release` only, no `cargo run/test`.
- Checkout the exact PR head, credential-free, not GitHub's synthetic PR merge ref. Original Rust source `fixed-jacobian-chain-evaluator-01/src/lib.rs` Git blob MUST equal `8016634385d76207b23a3eb3a4dae9b0366ac68d`; CT244 generator itself must pass its six negative mutation tests in normal and optimized Python.
- Stage the unchanged sibling `isogeny-labs/crypto@4de29a113dfc1b9d32c1809820b8caa2975042a8` for its original isogeny algorithms and genus-3 arithmetic; do not change its source.
- Reuse CT137/CT200's read-only approved manifest hydration code, pinned at `cryptanalysis@3de8c174cf65e6b34bf8579d97b817b8f5dc2ded`, without altering approved bucket, credentials, or policies. Pull **only** original `nondual-models-18` materialization inputs, max 180 s, and verify both fixed SHA-256 hashes and byte lengths (second 217960 bytes: `22225094b7e3727332a761593b47ac44a2efd2f04bbdb1b1865abf3c35ba7267`; third 326200 bytes: `1a7c90c81310a9d1a329b830c9c7b9f52a6c4504152c26162fb46f7fc5184787`). If artifact admission or authentication fails, preserve failure; **never** substitute synthetic data.
- Assemble original three predecessor source packages using existing `paired-fourth-preflight/materialize.py`, `fixed-jacobian-chain-01/materialize.py`, and `fixed-jacobian-chain-evaluator-01/materialize.py`.
- Generate `fixed-jacobian-chain-priced-01` once from original via `ct244_primitive_probe.py` (which in turn applies unchanged CT125 derivative). Enforce seven clock slots, actual final Jacobian norm assertion and receipt. Run release semantic typecheck with `cargo check --release --manifest-path .../fixed-jacobian-chain-priced-01/Cargo.toml` under a 360s cap.
- Retain original and generated blob digests, exact source heads, toolchain versions, primitive-source guard, compiler stdout/stderr, stage failure location via a GHA artifact even if the first prerequisite fails.

## Interpretation and decision

Success = exact-input custody + deterministic CT244 generator + Rust 1.99.1 release semantic typecheck exit zero, **only**. It does not demonstrate linking, executable native parity, physical `C169/C13a/C13b/D/N2_actual`, timing, peak RSS, cold ECDLP, strongest matched rho/BSGS/frontier IC or signed PCC. Failure = classify as source materialization, original input custody, Rust dependency/type error, or unavailable approved artifact access. Keep raw failure and fix only a concrete defect without relaxing any custody check. Stop before compute when admission is missing.

Scientific next gate remains bounded original-vs-CT125-vs-CT244 full 695/701-record native replay and independently priced same-host counterbalanced primitive timings; only after that a cold *single-target* end-to-end comparison. All source claims here are **[pcc:unverified]**.

Sources checked: [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [crypto #4215](https://github.com/isogeny-labs/crypto/pull/4215), [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), [cryptanalysis #1533](https://github.com/isogeny-labs/cryptanalysis/pull/1533), [cryptanalysis #1871](https://github.com/isogeny-labs/cryptanalysis/pull/1871), [CT200 #1761](https://github.com/isogeny-labs/cryptanalysis/pull/1761), and [crypto #4715](https://github.com/isogeny-labs/crypto/pull/4715). The research-KB service is not accessible through this GitHub connector; no novelty/absence conclusion.
