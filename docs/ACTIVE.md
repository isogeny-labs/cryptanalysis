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
- [ ] CT201–CT203: complete cold ECDLP source adjudication (matched five-arm rho/BSGS/IC, Williams order, distinct-Q per-block prospective gate; automation, started 2026-11-18, branch research/ct201-complete-single-target-gate-20261118, PR #1766; source CI 44/44 normal and -O at 36807d15; native/PCC blocked) [pcc:unverified]

- [x] Massively parallel `ic` relation collection: speculative multi-core decomposition with in-order commit (bit-identical `S`, relations and logarithm to the serial run), forkable oracles, `--threads`; strong-scaling curve and exact-dlog parity checks (Claude Code, completed 2026-11-20, branch claude/ic-parallel-relations, PR #1878; O(q^1/4) instance search 35-254x per phase-3 cell, --threads 3.22x subtract / 2.75x descent+f4 at 4 threads, counts identical; records 20261120T1852Z-ic-*, 20261120T1913Z-ic-threads-gate) [pcc:unverified]

- [ ] Coset filter behind the BASELINES n = 41 K_0 row: Koblitz base builder at n >= 41 and the filter wired into that row's pair-table pipeline (Claude Code, started 2026-11-22, branch claude/coset-filter-n41-koblitz) [pcc:unverified]

- [ ] ic bench: coset-filtered MITM pair tables (`mitm` / `mitm-frobenius` `coset_filter=1`), frozen ratchet protocol and bench record; stage improvement from the trunk's graph-theory note (Claude Code, started 2026-11-22, branch claude/mitm-coset-class-filter, PR #1892) [pcc:unverified]

- [ ] Controlled comparison of curve-coordinate relation solvers on growing toy instances with matched controls (Codex, started 2026-11-18, branch codex/curve-representation-controlled-20261118, PR #1767) [pcc:unverified]

- [ ] Establish current-main CPU/perf and Runpod GPU baselines, then iteratively optimize the maintained Rust, Go, C, and CUDA paths end to end with correctness and evidence gates (Codex, started 2026-11-18, branch codex/end-to-end-performance-saturation-20261118, PR #1771) [pcc:unverified]

- [x] Round-4 D (done: KILL after control amendment, by-letter INCONCLUSIVE; L=1 vs L_max 21-34 up to (2,2)): Macaulay solving degree of the bilinear (t; q) leaf system, L vs L_max with planted/null controls, n=13/17 (Claude, started 2026-11-19, branch claude/sat-solver-index-calculus-zczysc, PR #1772)
- [x] L2c confirmatory test (done: CONFIRMED 0.631x [0.494,0.809] on fresh SAT targets; solver effect, not an IC gain): RREF prefix-chain rows speed up CaDiCaL on decomposable (SAT) m=4 PDP targets, fresh curves and targets, frozen protocol (Claude, started 2026-11-18, branch claude/sat-solver-index-calculus-zczysc, PR #1772)
- [ ] Mirror the general binary hyperelliptic-cover transfer interface from crypto after its source commit is frozen, with split provenance and exact parity checks (Codex, started 2026-11-18, branch codex/general-binary-cover-transfer-mirror-20261118, PR #1765) [pcc:unverified]

- [x] Validate fixed index-calculus candidate residuals and subgroup status (Codex, started 2026-11-18, branch test-fixed-candidate-residual, PR #1755)

- [x] Report candidate scalar residuals in fixed index-calculus status (Codex, started 2026-11-18, branch cli-fixed-candidate-residual, PR #1752)

- [x] Report base-point and scalar availability in fixed index-calculus status (Codex, started 2026-11-18, branch cli-dlp-input-status, PR #1750)

- [x] CT188: randomized physical A/B crossover and carryover diagnostics, source-only; protocol PR #1723 merged, implementation draft PR #1725 (automation, started 2026-11-17, branch research/ct188-physical-crossover-20261117) [pcc:unverified]

- [x] Extend certified Xedni lift-success trials to the ten-coefficient `r=7..9` regime with exact rational dependence verification; local frozen panel completed 1,600/1,600 rows with 67 certified relations and 23 recoveries (Codex, started 2026-11-17, branch codex/xedni-breakthrough-20261117, implementation PR #1730 merged, outcome draft PR #1762) [pcc:unverified]

- [ ] Freeze and run a fresh-seed target-bearing relation-enumeration panel, preserving target-independent lift success and comparing complete recovery work against the frozen baseline (Codex, started 2026-11-18, branch codex/xedni-breakthrough-20261117, outcome draft PR #1762) [pcc:unverified]

- [x] CT187: bounded admitted-source native 1,536-call same-route sham producer, strict evidence reader and synthetic handshake; no paid execution (automation, started 2026-11-17, branch research/ct187-native-sham-source-admission-20261117, PR #1719)

- [x] CT186: source-only first-four-slot blinded sham scorer/tests (no native approval or execution; original price gates remain) (automation, started 2026-11-17, branch research/ct186-sham-label-source-control-20261117, PR #1718)

- [ ] In progress: publish completed buffer-state timing evidence and pursue the next primary-cost optimization; 200blocks,9failed A/A, no new primary gain; prior tracking PRs #1712/#1717/#1720/#1724 merged before final evidence (Codex, started 2026-11-17, branch codex/ic-buffer-state-timing-20261117, PR #1727)
- [x] Specialize the static IC witness dictionary and measure full-pipeline and collector effects against frozen controls; negative result retained and indexed route restored, broader performance goal continues (Codex, started 2026-11-17, branch codex/ic-static-witness-map-20261117, PR #1709)
- [x] Measure index-driven compact IC pair preparation with exact order/witness preservation; exploratory gains and collector regressions retained, broader optimization continues (Codex, started 2026-11-17, branch codex/ic-pair-index-gather-20261117, PR #1707)
- [x] Combine packed squaring with constant-polynomial IC preparation and measure against compact baseline; unsigned exploratory panel preserved, broader collector optimization continues (Codex, started 2026-11-16, branch codex/ic-packed-const-square-20261116, PR #1705)

- [x] Measure frozen SIMD abscissa-output candidate against compact IC baseline: candidate rejected and previous source restored; broader performance goal remains open (Codex, started 2026-11-16, branch codex/ic-simd-output-20261116, PR #1703)

- [x] Import prime-field subexponential index-calculus notes and exact Sage checks (Codex, started 2026-11-18, branch codex/prime-field-subexponential-20261118, PR #1760)

<!-- One line per task, added as the task's first step with its draft PR:
- [ ] <task> (<runtime>, started YYYY-MM-DD, branch <branch>, PR #<n>) -->
- [ ] Gröbner reference table: `f4_fp` vs msolve on PKM tower + direct Semaev systems (workspace goal GB-1/GB-2) (Claude Code, started 2026-11-21, branch claude/gb-reference-20261121, PR #1882)

## Blocked / questions for the owner

- Controlled representation comparison PR #1767: real S3 checkpoint upload/gate failed with AllAccessDisabled; explicit CPU/Git exception question is pending. Source/protocol preparation is not a measured panel. [pcc:unverified]
