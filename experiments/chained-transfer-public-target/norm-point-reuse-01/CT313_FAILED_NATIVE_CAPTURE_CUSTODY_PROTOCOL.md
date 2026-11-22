# CT313 — preserve failed native child capture custody without admitting its data

Date: 2026-11-22. Scope: existing draft cryptanalysis PR #1912, extending CT310's bounded original/reuse producer. Standing: [pcc:unverified].

## Observed defect (read-only source audit)

`ct310_bounded_native_pair_producer.capture_one` currently saves bounded raw stdout and stderr and immediately refuses on a nonzero exit, timed out child or overflow, **before** creating any corresponding receipt. `terminal.json` records only an error string. This makes a partial failed original/reuse process impossible to bind back to its raw bytes, executable, host and observed time using a structured negative-result record. The source-only `self_test` even asserts that the success receipt must not exist for failures, but never checks a separate failure receipt. This is an evidence-retention gap, **not** a claim of an observed malicious native process or a mathematical transfer failure.

## Prospective correction (before code)

1. Continue using CT176's unchanged process-group-limited collector and CT304's unchanged **success-only** verifier. Keep plan-only default, explicit owner admission, source/binary/model custody locks and all budgets.
2. For *every returned bounded child capture* with exit != 0, timeout, overflow or spawn failure, after saving the exact existing raw stdout/stderr bytes, write an exclusively created `<role>.failure.json` with a separate `ct313-failed-native-capture/v1` schema. Include role, source commit, binary SHA before/after, unchanged argv, pinned fixture Git blob + SHA256, host/affinity before/after, exit code, collector error, elapsed external wall, both raw-output digest/length pairs, `admitted:false`, `pcc:unverified`. Require stdout/stderr hash equality with retained partial files in the source test. Do not insert any made-up timing samples.
3. If the binary digest or host/affinity changes after the child, produce the same failure receipt with an explicit mismatch reason (when the corresponding postcheck can execute). Do not write a success receipt for such cases. A bounded process that completes with exit 0 and no collector error retains its **unchanged CT304 success schema** and audit path.
4. The CT304 dual-log comparator, pricing, independent PCC and any future complete-solve comparison must reject `failure.json` records as scientific runs. A failure receipt records an *unadmitted* attempt, never an execution proof.
5. Source-only tests: mock child success, nonzero exit, timeout, pipe overflow and launch failure. Every failure must leave raw bytes plus an exact typed failure receipt and **no success receipt**, with distinct nonzero/timeout/overflow/spawn statuses; mutate recorded stdout digest to demonstrate rejection by a separate local test check. Run both normal and Python -O in the existing source CI. Zero real Jacobian model runs, no S3, no paid compute.

## Out of scope

No changes to original six-source manifest, artifact-tool/config revisions, CT244/248 native Rust, source selected fixture, EKS/Spot, immutable ledger or signed PCC. Actual six-object authenticated S3 access and original/reuse 695/701 replay with physical C169/C13a/C13b/D/N2_actual plus same-host complete cold source-target ECDLP versus strongest retained lift/rho/BSGS/frontier IC remain outstanding. This amendment addresses *failed-run custody* only. [pcc:unverified].
