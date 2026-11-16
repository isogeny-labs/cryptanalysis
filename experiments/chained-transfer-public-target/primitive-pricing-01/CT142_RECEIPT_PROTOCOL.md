# CT142 — Independent process-receipt and paired-drift gate

2026-11-15. Parent cryptanalysis #1533 (CT125/CT141 merged stack); root crypto #3877; cost frontier crypto #4215. Scientific standing [pcc:unverified].

## Frozen validation contract (commit before code)

CT141 `check_pair.py` validates four JSON primitive timing records, but does not check the external process receipts, their recorded SHA-256s, binary/source custody, actual process exit status, nor enforce A/A stability. CT142 must be **source-only until a separately owner-approved CT141 execution**. No native execution or budget authorization.

Verify exact `original-1,reuse-1,reuse-2,original-2` order; sixteen expected SHA-256 receipt entries (stdout, stderr, GNU resources, exit status for each of the four processes), with no duplicates, all matching actual bytes; process exit code 0 and GNU-time `Exit status: 0`; positive external elapsed; positive GNU peak RSS at most 2,097,152 KiB (2 GiB). Check source and binary SHA receipts against live workspace bytes, marking downloaded archives insufficient for that provenance check. Require four valid CT126 schema and identity-equivalent input JSON objects, exactly six timing labels, 12 recorded positive integer blocks each, repetitions 64/5.

Predeclared noise gate: per-label and `setup_construct_ns` within-variant A/A **median ratio must lie in [0.8, 1.2]**, on raw per-call blocks. Any failure blocks scientific promotion and leaves raw evidence untouched. Compute and retain each of 48 *same-block* normalized differences `C169/64 - C13_first/64 - C13_second/64`; do not replace this by differences of pooled medians. Mixed signs are inconclusive. Positive microtiming deltas are **not** complete ECDLP speedup.

Run valid independent synthetic four-arm fixture and at least ten mutation controls: corrupted SHA; missing SHA; duplicate receipt; wrong process status; missing or invalid external elapsed; excessive memory; reversed sequence; binary hash mismatch; changed public identity; >20% A/A drift; zero duration; mismatched resource SHA. Run identical normal and `python -O` self-tests, fail closed without `assert`.

Additive runner integration is allowed only after unchanged CT126 checks finish. Rejection preserves raw data via the workflow's `if: always()` upload. Source-only CI must never trigger native executable without separate owner-approved admission. The original 695/701 Jacobian replay, complete cold strongest rho/BSGS/IC + setup, LA, transfer and RSS, and signed PCC remain open. [pcc:unverified]

Sources checked: cryptanalysis #1553 protocol/workflow/run, #1549 compile evidence, original #1534 CT126 `check_pair.py` and Rust source; crypto #4215 and root #3877; current repository AGENTS.md. Research-KB MCP unavailable; no novelty/absence assertion. No paid compute, secret access or protected merge. [pcc:unverified]
