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

- [x] Report candidate scalar residuals in fixed index-calculus status (Codex, started 2026-11-18, branch cli-fixed-candidate-residual, PR #1752)

- [x] Report base-point and scalar availability in fixed index-calculus status (Codex, started 2026-11-18, branch cli-dlp-input-status, PR #1750)

- [x] CT188: randomized physical A/B crossover and carryover diagnostics, source-only; protocol PR #1723 merged, implementation draft PR #1725 (automation, started 2026-11-17, branch research/ct188-physical-crossover-20261117) [pcc:unverified]

- [x] Extend certified Xedni lift-success trials to the ten-coefficient `r=7..9` regime with exact rational dependence verification; local frozen panel completed 1,600/1,600 rows with 67 certified relations and 23 recoveries (Codex, started 2026-11-17, branch codex/xedni-breakthrough-20261117, implementation PR #1730 merged, outcome PR #1762 merged) [pcc:unverified]

- [x] Derive and implement target-dependent chord-origin recovery, including a zero-explicit-target exact relation, Rust/Python controls, Lean algebra, diagram and PDF (Codex, started 2026-11-18, branch codex/xedni-breakthrough-20261117, draft PR #1768) [pcc:unverified]

- [ ] Freeze and run a fresh-seed target-bearing relation-enumeration panel, preserving target-independent lift success and comparing complete recovery work against the frozen baseline (Codex, started 2026-11-18, branch codex/xedni-breakthrough-20261117, draft PR #1768) [pcc:unverified]

- [x] CT187: bounded admitted-source native 1,536-call same-route sham producer, strict evidence reader and synthetic handshake; no paid execution (automation, started 2026-11-17, branch research/ct187-native-sham-source-admission-20261117, PR #1719)

- [x] CT186: source-only first-four-slot blinded sham scorer/tests (no native approval or execution; original price gates remain) (automation, started 2026-11-17, branch research/ct186-sham-label-source-control-20261117, PR #1718)

- [ ] In progress: publish completed buffer-state timing evidence and pursue the next primary-cost optimization; 200blocks,9failed A/A, no new primary gain; prior tracking PRs #1712/#1717/#1720/#1724 merged before final evidence (Codex, started 2026-11-17, branch codex/ic-buffer-state-timing-20261117, PR #1727)
- [x] Specialize the static IC witness dictionary and measure full-pipeline and collector effects against frozen controls; negative result retained and indexed route restored, broader performance goal continues (Codex, started 2026-11-17, branch codex/ic-static-witness-map-20261117, PR #1709)
- [x] Measure index-driven compact IC pair preparation with exact order/witness preservation; exploratory gains and collector regressions retained, broader optimization continues (Codex, started 2026-11-17, branch codex/ic-pair-index-gather-20261117, PR #1707)
- [x] Combine packed squaring with constant-polynomial IC preparation and measure against compact baseline; unsigned exploratory panel preserved, broader collector optimization continues (Codex, started 2026-11-16, branch codex/ic-packed-const-square-20261116, PR #1705)

- [x] Measure frozen SIMD abscissa-output candidate against compact IC baseline: candidate rejected and previous source restored; broader performance goal remains open (Codex, started 2026-11-16, branch codex/ic-simd-output-20261116, PR #1703)

<!-- One line per task, added as the task's first step with its draft PR:
- [ ] <task> (<runtime>, started YYYY-MM-DD, branch <branch>, PR #<n>) -->

## Blocked / questions for the owner

- The fresh Xedni selector panel is frozen but cannot generate its first row: checkpoint upload has no token/profile, and the documented ambient AWS fallback returns `AllAccessDisabled`. Resume requires valid scoped checkpoint transport; the earlier local waiver explicitly excludes modified panels. [pcc:unverified]
