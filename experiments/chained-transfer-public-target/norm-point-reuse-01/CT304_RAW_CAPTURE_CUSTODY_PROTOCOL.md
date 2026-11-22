# CT304 — exact raw process capture custody before native timing admission

**Prospective source-only extension to CT302, registered 2026-11-22 UTC before implementation. [pcc:unverified]** Owning draft [#1912](https://github.com/isogeny-labs/cryptanalysis/pull/1912); parent source/clock protocols CT244/248/300/301/302 remain unchanged. This task neither authorizes paid EKS/Spot execution nor edits the original 695/701 model, the six signed object-store inputs, the Rust evaluator, historical benchmark ledger or independent PCC.

## Observable gap

The CT302 two-log checker can accept 695 matching producer events and 144 self-consistent clock samples from synthetic text. It has no binding to successful **external** process termination or retained stdout bytes, stderr, binary and host identity. Its self-test deliberately fabricates 694 population events. The source CI pass therefore cannot establish native execution, physical operation price, mathematical independence or a complete single-target ECDLP advantage.

## Frozen v1 custody contract

Introduce a **read-only**, additive `ct304_execution_receipt_gate.py` CLI. It requires:
- Both raw original/reuse stdout logs, separate raw stderr files, retained original/reuse executable files, two corresponding JSON receipts and the exact 48-vector fixture (Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`). No synthetic fixture substitution.
- Unique nonempty process IDs, exact roles, source commit IDs, executable SHA-256, exact argv[0] executable path, unchanged same-host/cpu-affinity identity and independent raw SHA-256 *and byte-length* checks for both stdout and stderr.
- Strict finite JSON with no duplicate keys or type aliases. Exit code must be exactly integer zero; `timed_out=false`, `capture_complete=true`, positive external wall time, valid optional RSS, canonical SHA encodings. Every missing/truncated/changed artifact fails closed.
- The **existing** CT302 full dual-695/672/48, original-immutable fixture and 144 primitive/lifetime consistency checks must pass after custody. Source-only controls may use synthetic bytes, but cannot be promoted as measurement evidence.
- Explicitly separate **receipt internal consistency** from independent execution proof: a producer can fabricate a plausible receipt. Independently signed PCC, execution attestation, independent arithmetic and end-to-end complete cold solver timing remain separate gates. The new checker returns `native_execution_independently_verified=false`, `complete_single_target_ecdlp_cost=null` and `pcc=unverified` unconditionally.

## Preregistered source-only negatives

One synthetic positive, 15 typed/status/hash/path/affinity/fixture mutations, and three strict-JSON corruptions, exercised under Python normal and `-O -S` at the exact PR head. A separate end-to-end synthetic fixture test may use the authentic *48-row source* with mocked other records/clock samples, clearly labeled synthetic; no native process may be launched by CI.

## Execution boundary and the next scientific experiment

No new subprocess launcher or paid compute is created by this task. The already-existing CT176 bounded capture workflow is for **single-packet cold CT175** and cannot simply be relabeled as the CT125 full-695 native evaluator. Before a real CT304 admission, the owner-approved native producer/capture runner must freeze its exact matching v1 receipts and executable SHA/source commit identity, retain stdout/stderr and successful exit, satisfy STS plus six-object SHA/length custody, then run the unchanged CT302 math/output comparison. An authenticated, bounded physical run must price `C169,C13a,C13b,D,N2_actual` and compare all setup, transfer, relation collection, linear algebra, recovery, verification, memory and uncertainty against retained lift, optimized rho/BSGS and frontier IC. **No success claim without an independently replicated complete baseline/candidate >1 and PCC.**

Current blocker: previous STS `invalid_token` / S3 403, owner EKS/Spot budget and independent signatures. All failures are preserved. [pcc:unverified]
