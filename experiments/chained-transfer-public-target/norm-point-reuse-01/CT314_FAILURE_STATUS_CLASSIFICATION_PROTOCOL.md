# CT314 — fail-closed failure classification of captured native child process

Date: 2026-11-22. Existing draft cryptanalysis PR #1912, same bounded CT310 producer. Standing: [pcc:unverified]. Prospective protocol, committed **before** implementation.

## Prior work and defect

Reviewed CT313 failure-receipt schema, CT310 `capture_one`, CT304 success-only admission, CT312 source mutations, the original CT176/177 bounded collector and the existing CT310 source-only mocks. CT313 binds failed raw-output byte digests but does not establish that `status` corresponds to its **own** reported `exit_code`, `collector_error`, host or executable drift. For instance a receipt with `status="timeout"`, `exit_code=0`, `collector_error=null`, unchanged host and binary passes the current CT313 checker if its raw output hashes match. This is a source-level misclassification weakness, not evidence of a fraudulent native run.

## Frozen repair contract

1. Keep the producer's existing *ordered* failure classification: changed executable bytes > changed host/affinity > collector timeout > collector pipe overflow > spawn failed > other collector error > missing/noninteger exit > nonzero child exit. Use exactly the serialized receipt fields used by the producer. A successful `exit_code=0` with `collector_error=null`, no binary mutation and no host change **must not** be representable as a failed capture.
2. Independent CT313 auditor recomputes this precedence using the before/after binary SHA256, before/after host dictionaries, `collector_error`, and `exit_code`; reject any receipt where the derived classification is absent or differs from `status`. Preserve all earlier exact stdout/stderr byte hashes, fixture digest, retained executable digest and explicit `admitted=false`, `pcc=unverified` checks.
3. Add synthetic contradictory-status mutation controls for a successful exit disguised as timeout, a nonzero exit disguised as overflow, mismatched timeout/overflow, missing spawn evidence, bad `invalid_exit`, and unclassified collector errors. Preserve four existing real **benign test-child** bounded failure variants and four forged stdout hashes. The self-test runs in normal and optimized Python through the existing CT244 source CI, with zero native Jacobian executions.
4. No changes to frozen six-object S3 model manifest, artifact revision/STS decisions, protected branches, EKS/Spot, CT248 Rust evaluator, original 695/701 corpus, budget, PCC or original ECDLP cost ledger. This only makes negative outcomes reliable as `unadmitted` source receipts; it is **not** independently verified process execution, measured primitive timing or a complete cold single-target ECDLP improvement.

## Reproduction and acceptance

```sh
python3 experiments/chained-transfer-public-target/norm-point-reuse-01/ct310_bounded_native_pair_producer.py --self-test
python3 -O experiments/chained-transfer-public-target/norm-point-reuse-01/ct310_bounded_native_pair_producer.py --self-test
```

The CT313 audit must reject every status/exit/error contradiction even if all producer-supplied cryptographic hashes are self-consistent; existing four failure roles remain classified correctly. Exact-head CI and commit must be inspected before declaring the source check passed. Next scientific gate remains owner-approved genuine six-object S3 custody, physical 695/701 native original/reuse replay, C169/C13a/C13b/D/N2_actual same-host cold pricing, fully charged rho/BSGS/frontier IC, memory, uncertainty and independently signed PCC. [pcc:unverified]
