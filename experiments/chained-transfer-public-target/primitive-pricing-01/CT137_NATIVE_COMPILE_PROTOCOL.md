# CT137 — original-prime native primitive-pricing compilation gate

Date: 2026-11-15. [pcc:unverified]. Child of cryptanalysis PR #1534; root crypto PR #3877. This gate is separate from concurrently active CT136 #1547 and original-prime #1523. It changes neither native mathematical code nor the pinned 695/701 fixtures, CT125 derivative, original evaluator, PCC ledger, or another research branch.

## Scientific question
Can the original/reuse CT126 **actual** C169, C13a, C13b, D evaluator be built from the complete, pinned Rust and sibling crypto tree on a clean independent GitHub runner? Previous CT126 source-only CI only parsed Rust with rustfmt and did not compile its dependencies.

## Fixed inputs and custody
* cryptanalysis base exact commit `69b6d2b4112a8b90b97c855eda84a51fab686e27`; checkout each PR exact head, never synthetic merge.
* crypto sibling commit `4de29a113dfc1b9d32c1809820b8caa2975042a8` from root #3877, read-only, at the exact path required by all existing Cargo manifests. Never change its source.
* Require original evaluator's lib.rs exact Git blob `8016634385d76207b23a3eb3a4dae9b0366ac68d` before any preparation. Run the original `materialize.py` to obtain its seven literal helper sections, then the existing guarded CT125 `build_norm_reuse.py` to create a distinct sibling derivative.
* Use pinned Rust 1.99.1, `cargo check --release` for CT126 original and derivative manifests. Capture full stdout/stderr, toolchain and host IDs and exact hashes of the original/derived source. Retain failures and preserve all generated materials in workflow artifacts.
* Bounded CI only: ubuntu-24.04, at most 15 minutes, no EKS, Spot, cloud GPU, secret, paid remote cluster, source rewrite or benchmark admission. If cross-repo checkout fails because of permissions, record access failure rather than weakening the identity guard.

## Success / failures
Success for **this gate only** is both native Cargo graphs compiling and exact source/derivative identity checks passing on the specified commits. A compiler failure identifies a concrete defect to repair in a separate addendum; it is not evidence of an arithmetic flaw or impossibility. Cargo test, unchanged 695-record native replay, C169/C13a/C13b/D timing, ABBA/A/A controls and complete single-target rho/BSGS/IC comparison remain distinct gates and are NOT performed by source compilation.

Exact results, check-status, failures, toolchain and receipts must be inspected; source CI or self-attested output is not signed PCC. Next gate after native compilation: execute admitted, independent same-host ABBA primitive timing on original/reuse, full 695/701 parity and matched cold single-target ECDLP, counting transfer/setup/LA and peak memory. No speedup claim until strongest end-to-end competitor and signed validation.

References: crypto #3877/#4215; cryptanalysis #1523/#1533/#1534/#1547; CT125 README; existing original materialize script; CT126 PROTOCOL and read-only Rust Cargo package manifests; owner Pcc/AGENTS. Shared research-KB and local Conductor unavailable in this execution context, so no novelty or absence inference.
