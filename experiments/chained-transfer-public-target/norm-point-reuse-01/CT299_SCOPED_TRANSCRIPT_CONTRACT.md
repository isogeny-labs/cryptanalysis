# CT299 — exact program-shape binding for 48 selected native timing vectors

**Prospective protocol, 2026-11-21; [pcc:unverified].** Parent draft: [CT244/248 #1871](https://github.com/isogeny-labs/cryptanalysis/pull/1871). This child is source/auditor-only. No S3 access, native replay, clock result, cold ECDLP solver, paid compute, or PCC is implied.

## Observed gap in CT248 source auditor

The CT248 auditor checks 144 primitive samples, arm counter patterns, and 48 source rows. But it checks only the *type* of the frozen per-row scalar, input and output arrays and only three out of the 21 native `Calls` fields. A changed scalar schedule, truncated/fabricated class-key payload, dropped common full-norm counter, or extra route counter can pass those field checks. This is an audit-contract problem, not an observed producer corruption or performance defect.

## Frozen source program

Keep these immutable Git inputs unchanged:
- Original evaluator tests `src/tests.rs` blob `bcd27773a7b179c3beeb3d5782a5de97a7df19f2`;
- Original evaluator `src/lib.rs` blob `8016634385d76207b23a3eb3a4dae9b0366ac68d`;
- Existing CT125 and CT248 generator source and original native 695/701 fixture.

The selected test loops use directions `(0,2)`, `(2,0)`, six scalars `(0,1,2,17,12345,ELL-1)` with `ELL=2773073`, four cofactor sectors per scalar, and 48 rows. `PicClass.key().0` contains 19 `u32` words. Each selected arm writes the exact 21-field `Calls` Rust struct. The source test asserts three common external counters and two final actual checks are one each; quadratic source/target Phi are one in direct and retained, two in literal. CT248 original seven-clock/counter identity remains unchanged.

## Proposed additive check and tests

- Strictly require the exact source `scope`, scalar-by-position schedule, 19 bounded integer words in both selected class key arrays, exact 21-key native `Calls` schema with nonnegative integer fields, original common call charges, and quadratic Phi counts for the three route types.
- Preserve the 144 selected call samples, seven primitive slots, original per-direction counters, lifetime timing reconciliation, and zero/duplicate/failure gates.
- Add negative controls for each newly constrained field. Make the synthetic positive fixture faithfully shaped but unmistakably synthetic.
- This is only a *structural* source transcript check. The 19-word contents are not cryptographically committed: a separate immutable corpus comparison and independent native arithmetic must reject same-shape malicious changes. A source label or self-test does **not** certify source identity.
- Test with `python3 -S ct248_scoped_sample_audit.py --self-test` and `python3 -O -S ct248_scoped_sample_audit.py --self-test` in a fresh checkout, compare outputs. Run no native trial or paid workload.

## Admission / stop

If either source-mode fails, reject the patch. If it passes, leave the PR draft until inherited CI/review/PCC gates have run. Do not change protected artifact paths or original source, merge around red gates, or claim complete-solve improvement. Actual 695/701 parity, physical `C169/C13a/C13b/D/N2_actual`, same-host full cold ECDLP, retained-lift/rho/BSGS/IC comparisons and memory are separate pending gates.

**Sources checked:** repo `AGENTS.md`, parent CT248 protocol and source adjudication, original pinned `src/tests.rs` and `src/lib.rs`, CT125 generator, CT198 cost attribution #1748, root crypto #3877, crypto #4215, CT243 negative #4715. Research-KB tools were unavailable through this connector runtime; no novelty claim is made.
