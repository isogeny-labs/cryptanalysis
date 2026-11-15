# CT137 first native compilation: missing upstream generated source

2026-11-15, standing [pcc:unverified]. First scoped GitHub Actions run [43719284031](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43719284031), exact PR head `a0325f3a7de1aa22cef2df9f90354c05cb4fc031`, job `132827561285`, **failed** during the actual original Cargo dependency graph. The independent runner successfully checked out both pinned repositories; checked the source blobs and sibling link; constructed the original seven helper sections and distinct guarded CT125 norm-reuse evaluator. Both Rust source derivations therefore passed their source gates.

The **first and only fatal compiler diagnostic** was:
```text
error: couldn't find file .../paired-fourth-preflight/generated/lib.rs
error: could not compile chained-n4-paired-fourth-preflight (lib) due to 1 previous error
```
The compiler did not yet reach CT126 `main.rs` or the reuse graph. No arithmetic result, norm-point parity, performance or ECDLP conclusion is supported by this failure.

The omitted prerequisite is the pre-existing `paired-fourth-preflight/materialize.py`, which assembles literal predecessor source and frozen LZMA fixtures without changing any mathematical Rust source. Add a new preparatory step invoking that exact script **before** the CT126 Cargo checks, keep original source and protocol frozen, and rerun. If compilation then stops on a different generated prerequisite or an actual type error, retain and classify that diagnostic, rather than weakening validation.

Source: [CT137 artifact #14163997299](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43719284031/artifacts/14163997299), SHA-256 d4800f201f423919934457dccbfffd336f1a973f4706f7175330cdcde30f7f6c. The earlier CT137 protocol remains prospectively frozen; this addendum documents the failure and scope-limited preparation repair. No paid EKS/Spot, benchmark admission, 695-record replacement, protected merge or signed PCC.


## Second replay: original-artifact symlinks were not hydrated

The next exact-head GitHub run [43719898130](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43719898130) at `d3a8f52741e7c60eaa66e1d260bce7601459ca76` failed in job `132829390617` **before Cargo**. The preceding added predecessor-materialization step now ran, but `paired-fourth-preflight/materialize.py` attempted to decompress `nondual13-preflight/models/expected-native-01.json.xz`, which is a Git symlink to an absent artifact-store file. Actual runner traceback: `FileNotFoundError: .../nondual13-preflight/models/expected-native-01.json.xz`. Whole failure log and custody output are retained in [artifact 14163599705](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43719898130/artifacts/14163599705). [pcc:unverified]

The two genuine symlink blobs are Git `46a2e766` and `f6d47eef` and point to `docs/research-artifacts/chained-transfer/nondual-models-18/{second,third}-model-expected-native-01.json.xz`. Those binary targets are excluded from Git by the original `.artifacts.json` policy and require the existing vault hydration step. The manifest at this branch pins the compressed original byte counts/SHA256 as **217960 / 22225094...** (second) and **326200 / 1a7c90c8...** (third). A normal `actions/checkout` cannot restore them. No Rust compile or benchmark failed here; neither had started. [pcc:unverified]

Commit `4269ae3454d8848545b1c3fe040e0cc7929f0e39` repairs only the additive CI: it checks out the immutable original artifact tool at `3de8c174`, compares the checked-out policy/tool bytes, uses the **existing repo-approved manifest hydration procedure** under the existing workflow secrets, then checks both SHA256, byte lengths and symlink resolution before running the unchanged predecessor materializer. That is the same restoration mechanism already used by the standing `chained-transfer-fixed-chain.yml` and `chained-transfer-paired-fourth.yml` workflows, with only the necessary original `nondual-models-18` class selected. No private keys are read into logs; hydration is capped at 180 seconds and does not authorize EKS/Spot or any benchmark. [pcc:unverified]

**Next gate:** inspect an exact-head CT137 run after this repair. Success requires the genuine model bytes to match the two manifest hashes, both source derivatives to materialize without mutation, and `cargo check --release` to complete on **both** original and norm-reuse Rust graphs at pinned Rust 1.99.1. If another dependency or type failure occurs, preserve the first compiler diagnostic and repair only that failure. Passing `cargo check` is not a (C_{169}, C_{13a}, C_{13b}, D) timing, parity or full cold ECDLP speedup, and PCC remains unverified.


## Third replay: first Rust compilation reaches the fixed-chain nominal modules

[Run 43721405143](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43721405143), job `132833984378` at exact input commit `4269ae3454d8848545b1c3fe040e0cc7929f0e39`, **reproduced the complete original-artifact hydration** and passed both original manifest checks, both symlink resolutions, literal paired-fourth source assembly, seven literal CT126 helper assembly and guarded CT125 derivative generation. The reviewed complete job log confirms Rust 1.99.1 entered the actual original Cargo graph; it failed when the pre-existing fixed-Jacobian predecessor's nominal-type derivative had not been materialized:

```text
Checking chained-n4-fixed-jacobian-chain v0.1.0
error: couldn't find file .../fixed-jacobian-chain-01/src/../generated/adapter.rs
  --> .../fixed-jacobian-chain-01/src/lib.rs:5:1
  5 | pub mod adapter;
error: could not compile chained-n4-fixed-jacobian-chain (lib) due to 1 previous error
```

This is a **new upstream generated-source dependency**, not yet a CT126 source type error. The raw CI artifact [#14163879404](https://github.com/isogeny-labs/cryptanalysis/actions/runs/43721405143/artifacts/14163879404) includes compile stdout and all custody receipts. The source original fixed-chain CI's `ci_fixed_chain/check.sh` names the deterministic materialization order `paired-fourth-preflight`, `fixed-jacobian-chain-01`, `fixed-jacobian-chain-evaluator-01`; CT137 had only the first and third. [pcc:unverified]

Commit `cbdf45e61944e4350dc57d012cc4b32273627e86` adds the unchanged `fixed-jacobian-chain-01/materialize.py` between its two predecessors, corresponding exactly to the original fixed-chain CI sequence. Its three generated modules derive literally from original `odd-product-maps` and `beta-complete-evaluator` with the previously declared nominal type substitutions only; neither stored source nor mathematical formulas were changed. The new CI will be inspected separately, and no native benchmark, full cold solve, original-prime solver timing or signed PCC claim follows from a compilation gate. [pcc:unverified]
