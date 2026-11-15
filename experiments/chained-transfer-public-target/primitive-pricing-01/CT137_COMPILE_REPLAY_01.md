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
