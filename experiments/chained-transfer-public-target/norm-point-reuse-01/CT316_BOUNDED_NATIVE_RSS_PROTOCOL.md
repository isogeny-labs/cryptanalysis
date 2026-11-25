# CT316 — independently inspectable peak RSS on bounded native captures

Registered 2026-11-22; continuation of the existing draft PR #1912. [pcc:unverified].

## Scientific gap / scope

CT310 records `peak_rss_kib: null`; CT315 correctly refuses an unmeasured-memory cold run. A source-only receipt cannot claim actual resident memory. CT316 integrates **GNU time** (the Linux `/usr/bin/time` executable, NOT a shell builtin) around the exact locked binary invoked by CT176's unchanged, bounded, concurrent stdout/stderr capture. GNU time obtains child `wait4` resource usage including `ru_maxrss`, expressed as KiB on Linux. Its wrapper and measurement overhead stay **inside** CT310's external wall clock, a conservative full-cost comparison. Existing 4 MiB per-pipe, timeout, process-group kill, aggregate deadline and exit checks remain mandatory.

## Conditions before admission

1. Real --execute requires existing owner/provider approval, independently authenticated six-object original S3 custody, pinned original/reuse hashes and exact native 695/701 fixture. In addition, require Linux, an **explicit absolute** path and SHA-256 lock for the GNU time executable, and a fresh previously nonexistent per-role memory output. No silent fallback to `resource.getrusage(RUSAGE_CHILDREN)`: its monotone high-water value across sequential children cannot identify each run's RSS.
2. Invoke `[time, "-f", "CT316_V1 RSS_KIB=%M EXIT=%x", "-o", fresh_output, native_binary, ...args]` through CT176 without `shell=True`; preserve the original native argv in the receipt and record actual instrumentation argv, meter digest, and raw meter-output digest in a separate source-linked receipt. Preserve original stdout/stderr unmodified and their SHA-256 bindings.
3. Only successful bounded captures with exact zero child/meter exit, one strictly parsed positive `RSS_KIB`, unchanged meter and native binary hashes, authentic raw sidecar and exact meter/child arguments may populate `peak_rss_kib`. Any missing/zero/noncanonical/inconsistent or tampered meter result must **fail closed** with a terminal refusal, not substitute a synthetic value. Failed native captures remain distinct from successful CT304 receipts. A GNU-time diagnostic or nonzero return must never become an admitted memory result.
4. Maintain CT304's exact receipt schema and CT309 clock nesting; add independent CT316 sidecar verification to the producer. This proves only source-bound provenance internal consistency, NOT independent child execution, process-tree memory of unrelated descendants, PCC, or a speedup. A complete solver requires **separate** CT315 cold receipts for each arm, including rho/BSGS/IC and all phases.
5. Source-only tests: benign Python native-stand-in with real OS memory measurement, parse/missing/zero/boolean/changed sidecar/time-SHA/meter-exit controls under normal and `python -O`. Distinguish these from the original Jacobian fixture, which remains unexecuted. Negative path must preserve CT313/314 failure receipts.

## Constraints and next action

This does not change CT176's pinned bytes or CT304 admission, the frozen 695/701 data, six-object custody, Rust/native evaluator, PR/merge gates, credentials, EKS/Spot or spending. Original S3/tool/config/STS approval still blocks the actual same-host 695/701 reproduction. After that, measure physical C169/C13a/C13b/D/N2_actual and a full cold CT315 panel, compare against strongest retained-lift/rho/BSGS/frontier IC, with memory cap and independent signed PCC. Preserve negative outcomes. [pcc:unverified].
