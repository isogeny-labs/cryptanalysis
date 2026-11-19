# CT245 original Jacobian model hydration receives S3 HeadObject 403

- **Status:** `open`
- **Kind:** access/tool limit; downstream native measurement qualification remains open
- **Affected work:** [CT244/CT245 PR #1871](https://github.com/isogeny-labs/cryptanalysis/pull/1871), [CT245 preregistered protocol](../experiments/chained-transfer-public-target/norm-point-reuse-01/CT245_NATIVE_TYPECHECK_PROTOCOL.md), [CT125 PR #1533](https://github.com/isogeny-labs/cryptanalysis/pull/1533), and the owner-priority original 695/701-record norm reuse experiment
- **Next action owner:** approved object-storage credential / access-policy administrator; native typecheck maintainer after access recovery
- **Last updated:** 2026-11-19

## Problem

A credentialed, exact-head GitHub Actions run stopped before CT244's native Rust typecheck because the preapproved original `nondual-models-18` artifact store returned `403 Forbidden` to `HeadObject`. We therefore cannot yet authenticate the original model inputs, reconstruct the unmodified predecessor Rust packages, typecheck the seven-channel CT244 clocks, or time physical `C169/C13a/C13b/D/N2_actual` in this chain. **This is an input-access failure, not an arithmetic counterexample, a Rust compile defect, a measured cost, or evidence that the objects do not exist.** [pcc:unverified]

## Evidence and uncertainty

- **Observed:** [GitHub Actions #44622872809](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44622872809), job `135908889249`, exact PR head `1db41a22c220a32df86bd327ce89503fb672eb78` on 2026-11-19. Checkout, pinned crypto source checkout, original blob validation, six guarded CT244 source-generator mutations in normal/optimized Python, and unchanged read-only artifact policy validation **passed**. The next `Hydrate original manifest-verified model inputs` step exited 2 after its first three S3 `HeadObject` attempts returned `403 Forbidden`. GitHub-hosted upload of the diagnostic receipts succeeded. Reconstruction and `cargo check --release` were skipped, not failed.
- **First refused content-addressed keys:** `store/sha256/22/22225094b7e3727332a761593b47ac44a2efd2f04bbdb1b1865abf3c35ba7267` (217960 bytes), `store/sha256/38/38ab7bc29e49230073c81d3531fbe5f904aeaad06827d8ae19eb9a616a483387` (150556 bytes), and `store/sha256/b9/b9a2c87714bad75ced53d9903d43f6347caf21efff7bcc3faa986cc032541dfa` (150136 bytes), from the immutable [six-file manifest](../docs/research-artifacts/chained-transfer/nondual-models-18/.artifacts.json). The other three objects were **not** demonstrated accessible in this failed invocation.
- **Original immutable source Git blob:** `8016634385d76207b23a3eb3a4dae9b0366ac68d`. Pinned sibling crypto source: `4de29a113dfc1b9d32c1809820b8caa2975042a8`; pinned hydration tool `3de8c174cf65e6b34bf8579d97b817b8f5dc2ded`.
- **Derived or proved:** no mathematical result. A bare S3 403 does not distinguish authorization denial from an absent key hidden by an access policy, temporary credential scope, object-store configuration, or account policy.
- **Missing capability:** approved `s3:HeadObject` (underlying read/HeadObject) and `s3:GetObject` for the six exact content-addressed keys in the configured `s3://setec-astronomy-artifacts/store` object store, or another *explicitly approved* source that supplies byte-identical inputs with the six immutable SHA-256 digests and lengths. No broadened bucket access, credential disclosure, policy bypass, synthetic model replacement or unpublished object recreation is authorized.
- **What this evidence does not establish:** native compilation success/failure, original vs CT125/CT244 695-record parity, full ECDLP solve, calibrated timing, complete-cost crossover, independent execution verification or signed PCC. [pcc:unverified]

## What would unblock it

- [ ] The approved access owner confirms the intended credential/role and object-policy route for the **six exact manifest keys**, without printing secret values or weakening existing budget/security policy. Check visibility and obtain authenticated bytes on the same approved runner.
- [ ] Fresh bounded CT245 replay retrieves **all six** immutable objects, verifies their manifest SHA-256 and byte lengths, materializes the original source tree, and only then executes Rust 1.99.1 `cargo check --release` on the separate CT244 sibling with full compiler/receipt retention.
- [ ] For the later scientific gate, run admitted and bounded original/CT125/CT244 complete 695/701-record raw-output parity and same-host ABBA and A/A costing, retaining all exceptional and negative records, setup, memory and strong source-matched rho/BSGS/IC. Obtain independent arithmetic/execution replay and PCC standing before any speedup claim.

The first two conditions only unblock typechecking; they are insufficient for a timing or ECDLP speedup claim.

## Next discriminating step

- **Action:** ask the approved object-store owner to inspect `HeadObject` authorization for the exact first three keys and the rest of the six-file manifest using the existing CT245 GitHub Actions identity; if approved access is repaired, rerun the *unchanged* source-bound typecheck.
- **Inputs and controls:** same PR head, crypto source commit, artifact tool digest, six-file manifest, 180s hydration timeout, 15-minute overall CI limit and `cargo check` 360s timeout. The source-only CT244 gate is a positive control, **not** a substitute for artifact custody.
- **Stop condition:** any forbidden or missing hash/length immediately halts before native compilation; do not fetch arbitrary alternate models, turn off checks, or launch paid EKS/Spot.
- **Outcomes:** complete byte-verified access moves to native typechecking; a new error is recorded at its exact stage; repeated 403 stays an infrastructure/access blocker and the research queue continues on an independently unblocked lead.
- **Recheck trigger:** an approved credential/access-policy repair or validated custody-equivalent source, not another unchanged blind CI retry.

## Resolution and history

2026-11-19 — first authenticated exact-head typecheck attempt stopped at three forbidden object reads. Source identity and source-only checks passed. All native compilation and performance conclusions remain **unresolved**. [pcc:unverified]
