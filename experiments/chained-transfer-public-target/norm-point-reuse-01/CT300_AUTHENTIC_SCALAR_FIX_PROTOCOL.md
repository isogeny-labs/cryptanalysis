# CT300 — pinned authentic 48-vector scalar admission repair

**Prospective protocol, 2026-11-21; [pcc:unverified].** Child of [CT299 PR #1899](https://github.com/isogeny-labs/cryptanalysis/pull/1899), stacked on CT244 #1871. No native timing, paid compute, merge, PCC, or scientific speedup claim.

## Observed regression, prior to modification

CT299 added hardcoded `SCALARS=(0,1,2,17,12345,2773072)`. Its pinned original source `fixed-jacobian-chain-evaluator-01/src/tests.rs` (Git blob `bcd27773a7b179c3beeb3d5782a5de97a7df19f2`) loops over `[0,1,2,17,12345,ELL-1]`, with `ELL` imported via the fixed-chain model, whose source subgroup order is **2,771,711**, not the separate original-prime model order 2,773,073. The existing immutable selected-vector evidence `evidence/fixed-chain-norm-point-native-01/literal-selected-vectors.json` (Git blob `9ac741668dd1ffa9632ff0d58e6f4dd9f2dd18c3`) records final scalar **2,771,710** in exactly eight rows. The current CT299 audit therefore rejects authentic rows before timing can be evaluated. Passing generated synthetic tests did not detect the mismatch.

## Intended repair and source-bound test

1. Correct only the auditor's final scalar to `2771710`. Retain its 144 ordered route samples, 48 source vectors, original 19-word key types, 21-counter schema, lifetime reconciliation, fail-closed mutations, and unverified standing.
2. Add a **source-only** exact Git-blob checked authenticator for the published real 48-row fixture. It shall reject changed bytes, reordered scalar/cofactor/direction programs, truncated or changed real class-key payloads and changed original counter dictionaries.
3. Transform *only in the test harness* the archived `transported_norm_doubling` name into the CT125/CT244 instrumentation's `norm_point_doubling` field to exercise the CT299 auditor on all real 48 pre-existing rows, with **fabricated zero elapsed_ns values explicitly marked as test data**, not physical clocks. Do not present this as native producer replay or independent curve arithmetic.
4. Add a regression for the original erroneous scalar and at least one tampered real fixture. Run Python normal and `-O` in a GitHub Actions source-only job using a sparse checkout that explicitly contains the immutable source fixture. Never fetch substitute models or objects or weaken exact SHA checks.
5. Keep the original Rust source, actual 695/701 fixture, all signed data, CT244 instrumentation, protected ledger and existing negative timing evidence unchanged. Leave PR draft while inherited gates are red.

## Acceptance and next science

Accept only if authenticated fixture replays through the structural CT299 auditor and wrong scalar fails, on both Python modes. This is **not** a native 695/701 result, typecheck, physical C169/C13a/C13b/D/N2_actual measurement, complete cold ECDLP, independently signed PCC, or claim of advantage. Original AWS STS invalid-token / S3 403 remains a separate blocker. The owner-priority next experiment remains approved full original custody and same-host cold complete target comparison against retained lift, optimized rho, BSGS and IC with setup/LA/memory/uncertainty fully counted.
