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

- [ ] CT188: randomized physical A/B crossover and carryover diagnostics, source-only; protocol PR #1723 merged, implementation draft PR #1725 (automation, started 2026-11-17, branch research/ct188-physical-crossover-20261117) [pcc:unverified]

- [ ] Extend certified Xedni lift-success trials to the ten-coefficient `r=7..9` regime with exact rational dependence verification (Codex, started 2026-11-17, branch codex/xedni-breakthrough-20261117, PR #1722) [pcc:unverified]

- [x] CT187: bounded admitted-source native 1,536-call same-route sham producer, strict evidence reader and synthetic handshake; no paid execution (automation, started 2026-11-17, branch research/ct187-native-sham-source-admission-20261117, PR #1719)

- [x] CT186: source-only first-four-slot blinded sham scorer/tests (no native approval or execution; original price gates remain) (automation, started 2026-11-17, branch research/ct186-sham-label-source-control-20261117, PR #1718)

- [ ] In progress: measure the indexed IC collector regression with staged/indexed and counter-presence setup contrasts in one binary, preserving frozen controls; implementation PR #1712 merged, panel continuation (Codex, started 2026-11-17, branch codex/ic-collector-panel-20261117)
- [x] Specialize the static IC witness dictionary and measure full-pipeline and collector effects against frozen controls; negative result retained and indexed route restored, broader performance goal continues (Codex, started 2026-11-17, branch codex/ic-static-witness-map-20261117, PR #1709)
- [x] Measure index-driven compact IC pair preparation with exact order/witness preservation; exploratory gains and collector regressions retained, broader optimization continues (Codex, started 2026-11-17, branch codex/ic-pair-index-gather-20261117, PR #1707)
- [x] Combine packed squaring with constant-polynomial IC preparation and measure against compact baseline; unsigned exploratory panel preserved, broader collector optimization continues (Codex, started 2026-11-16, branch codex/ic-packed-const-square-20261116, PR #1705)

- [x] Measure frozen SIMD abscissa-output candidate against compact IC baseline: candidate rejected and previous source restored; broader performance goal remains open (Codex, started 2026-11-16, branch codex/ic-simd-output-20261116, PR #1703)

<!-- One line per task, added as the task's first step with its draft PR:
- [ ] <task> (<runtime>, started YYYY-MM-DD, branch <branch>, PR #<n>) -->

## Blocked / questions for the owner
