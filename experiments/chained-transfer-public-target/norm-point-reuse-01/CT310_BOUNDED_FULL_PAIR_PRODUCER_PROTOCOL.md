# CT310 — prospective bounded full-population native capture producer (2026-11-22)

**Status:** protocol frozen before implementation; additive follow-up on draft [#1912](https://github.com/isogeny-labs/cryptanalysis/pull/1912). **[pcc:unverified]**

## Evidence gap and reuse

CT302/304/309 admit exact raw bytes, 695 original/reuse source records, 144 scoped samples and a self-consistent process receipt, but do not provide a **producer** for paired whole-run captures. Existing CT176/177 (cryptanalysis `experiments/chained-transfer-public-target/primitive-pricing-01/ct176_cold_process_collector.py`) implements bounded in-flight subprocess capture for **single-packet CT175**. Reuse its tested `bounded_subprocess` primitive; do **not** relabel or edit its 21-counter CT175 packet validator, and do not silently substitute the 48 selected records for the full original model.

This extension does **not** revise CT304's v1 read-only auditor. It introduces a separate prospective producer, with no claim of independent execution attestation. Original authenticated six-object custody, coherent approved artifact tool/config, valid STS/S3, and an approved bounded EKS/Spot budget must exist **before** real native execution. This protocol is *not* authorization.

## Exact execution contract

1. Plan-only by default. Require separately supplied `--execute`, `--admission-approved`, strictly positive individual and global time limits, exact immutable source fixture, two existing distinct executable paths with SHA-256 locks, exact per-role command arrays beginning with those retained executable paths, and separate 40-digit source Git commit SHAs. An approval flag is a *claim*, not a grant of authorization; budget/provider approval remains external. No shell=True, unbounded subprocess, network retrieval, or implicit compiler action.
2. Produce into an exclusively created output directory, with immutable `original.stdout`, `reuse.stdout`, separate stderr files, binary receipt copies or exact references, and per-role JSON receipts satisfying CT304 v1 exactly. Generate distinct unpredictable 128-bit run IDs; record actual host/kernel/affinity snapshot and refuse its mutation; retain command paths, binary SHA-256, fixture Git-blob and SHA-256, monotonic external wall, precise exit, complete capture and optional RSS (null if not measured; do **not** infer zero).
3. Reuse CT176/177 in-flight capped dual-pipe process capture and child process-group cleanup, with an explicit finite cap appropriate to 695-record output; impose both per-child and aggregate deadlines. Refuse overflow, timeout, nonzero exit, missing model custody, changed executable or host/CPU affinity. Never produce a successful v1 receipt from incomplete bytes. Preserve the bounded partial outputs and a **failure terminal** on error; never label them admitted. Do not silently retry a failed subprocess.
4. After both successful captures, invoke the unchanged CT304 paired audit on actual raw outputs, exact executable bytes and frozen fixture. A returned `full_695_and_144_population_consistent=true` is a **producer-level admission**, not independent native provenance, independently verified ECDLP or signed PCC. Preserve the returned scientific false/null fields.
5. The harness must never inject synthetic rows, clocks or altered producer records into execution mode. Read-only source CI may use synthetic command outputs to test the shell-free capture pipeline but must label those tests as *mock* and must not call them native arithmetic.

## Pre-registered safety tests

- Without both explicit execution/admission flags or without positive/global time limits: plan or fail, **no child spawn**.
- Reject fixture mismatch, binary SHA mismatch, mismatched argv[0], same executable paths, missing/corrupted artifact model-custody receipt and changed source commits.
- Source-only mock children: successful bounded exact stdout/stderr/exit receipt; nonzero exit; timeout; >cap stdout; >cap stderr; externally forged short wall; and error between the two captures. Tests must keep partial refusal and must never produce accepted complete-pair evidence from mocks.
- Python normal and `-O` must agree. CI must never request AWS credentials, dispatch paid compute, or mark PCC verified.

## Physical follow-through (separate authorization)

First independently validate original six S3 objects and tool/config source semantics; pin Rust 1.99.1 source and record executable hashes. On a permitted, bounded single host, capture full original versus reuse 695/701 native processes, validate all receipts and frozen rows, then measure physical C169/C13a/C13b/D/N2_actual, A/A and ABBA same-target cold complete solves with setup/transfer/LA/recovery/verify/RSS, matched strongest rho/BSGS/frontier IC, uncertainty and independent signed PCC.

Failure of any gate is retained as a **negative/incomplete observation**; it is not a speedup and not a proof of impossibility. [pcc:unverified]
