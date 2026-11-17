# Active goal and items

Owner-pinned work queue. `tools/goal_brief.py` prints this file at the start
of every Claude and Codex session (SessionStart hooks) and for `/goal`
(AGENTS.md, "Goal: what to work on next"). When this file has no unchecked
item, sessions fall back to the newest "Open threads" in `docs/session-logs/`.

Keep it short: one goal, a few ordered items. Sessions add their task here as
the first step of the task (AGENTS.md, "First step of every task"), keep the
line current, and tick it when done; history belongs in the session log or the
PR, not in this file.

## Current goal

Achieve a large, evidence-backed Xedni-calculus breakthrough across the
prime-field lift pipeline, while continuing to track the binary/Koblitz source
and construction gates. [pcc:unverified]

## Active items (top = next)

- [ ] CT194: make each CT192 Rust primitive timing iteration consume a compiler-opaque public point; guard against loop-invariant hoisting and retain per-route parity (Chained ECDLP Transfers, started 2026-11-17, branch research/ct194-opaque-input-timing-20261117, PR #1738) [pcc:unverified]

- [ ] CT193: bind each true pre-norm operand to its entire target Jacobian class, not only its doubled norm; add 2-torsion alias regression (Chained ECDLP Transfers, started 2026-11-17, branch research/ct193-class-bound-pre-norm-20261117, PR #1737) [pcc:unverified]

- [ ] CT192: scalar-blind all-48 true pre-norm target operands and paired N2_actual/D_padd Rust pricing, source-only validation; no native execution (Chained ECDLP Transfers, 2026-11-17, branch research/ct192-public48-norm-operand-price-20261117, PR #1735) [pcc:unverified]

- [x] CT191: implemented a guarded Rust N2_actual primitive arm next to historical D_padd proxy; source-only CI 10/10 normal + 10/10 -O passed, NO native timings or full ECDLP evidence (Chained ECDLP Transfers, 2026-11-17, PR #1734) [pcc:unverified]

- [ ] Extend certified Xedni lift-success trials to the ten-coefficient `r=7..9` regime with exact rational dependence verification (Codex, started 2026-11-17, branch codex/xedni-breakthrough-20261117, PR #1722) [pcc:unverified]

- [x] CT187: bounded admitted-source native 1,536-call same-route sham producer, strict evidence reader and synthetic handshake; no paid execution (automation, started 2026-11-17, branch research/ct187-native-sham-source-admission-20261117, PR #1719)

- [x] CT186: source-only first-four-slot blinded sham scorer/tests (no native approval or execution; original price gates remain) (automation, started 2026-11-17, branch research/ct186-sham-label-source-control-20261117, PR #1718)

- [ ] In progress: preserve successful native buffer-state admission and prepare the separate collector timing packet; prior tracking PRs #1712/#1717/#1720 merged before final evidence (Codex, started 2026-11-17, branch codex/ic-setup-native-admission-20261117)
- [x] Specialize the static IC witness dictionary and measure full-pipeline and collector effects against frozen controls; negative result retained and indexed route restored, broader performance goal continues (Codex, started 2026-11-17, branch codex/ic-static-witness-map-20261117, PR #1709)
- [x] Measure index-driven compact IC pair preparation with exact order/witness preservation; exploratory gains and collector regressions retained, broader optimization continues (Codex, started 2026-11-17, branch codex/ic-pair-index-gather-20261117, PR #1707)
- [x] Combine packed squaring with constant-polynomial IC preparation and measure against compact baseline; unsigned exploratory panel preserved, broader collector optimization continues (Codex, started 2026-11-16, branch codex/ic-packed-const-square-20261116, PR #1705)

- [x] Measure frozen SIMD abscissa-output candidate against compact IC baseline: candidate rejected and previous source restored; broader performance goal remains open (Codex, started 2026-11-16, branch codex/ic-simd-output-20261116, PR #1703)

<!-- One line per task, added as the task's first step with its draft PR:
- [ ] <task> (<runtime>, started YYYY-MM-DD, branch <branch>, PR #<n>) -->

## Blocked / questions for the owner
