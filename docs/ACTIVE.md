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

- [x] Expand higher-genus support: genus-generic index calculus and Pollard rho for hyperelliptic and non-hyperelliptic (superelliptic one-point) Jacobians over F_p, genus 5..131 (`suite/src/highgenus/`; rho verified at g = 5..131 hyperelliptic and g = 5, 7, 11, 23, 97 non-hyperelliptic; IC with order-from-relations verified to g = 47; `suite/docs/highgenus/RESULTS.md`) (Claude Code, completed 2026-11-21, branch claude/higher-genus-5-131, PR #1884) [pcc:unverified]

- [ ] Run the registered PKM tower phase-1 comparison at feasible m=5,6 with the frozen baseline, planted controls and resource limits; report full cell outcomes; prepared and checkpoint upload blocked (Codex, started 2026-11-21, branch codex/pkm-high-arity-phase1-20261121, PR #1883)

- [ ] Complete native import-cache verification (Codex, started 2026-11-17, branch fix/native-import-cache-followup-20261117; tracking PR #1763 merged before implementation; full CI pending).

- [x] Massively parallel `ic` relation collection: speculative multi-core decomposition with in-order commit (bit-identical `S`, relations and logarithm to the serial run), forkable oracles, `--threads`; strong-scaling curve and exact-dlog parity checks (Claude Code, completed 2026-11-20, branch claude/ic-parallel-relations, PR #1878; O(q^1/4) instance search 35-254x per phase-3 cell, --threads 3.22x subtract / 2.75x descent+f4 at 4 threads, counts identical; records 20261120T1852Z-ic-*, 20261120T1913Z-ic-threads-gate) [pcc:unverified]

- [x] Representation technique (Delaplace–May 2019 / DFKM 2020) in `ic bench`: (a) `descent-algebraic` m = 4 balanced split with intermediates restricted to a subspace V' (sweep ℓ'), (b) generic filtered m-list join oracle `rep-join` (m = 2..9, filter density), (c) an F_{p^2} regime with the subfield abscissa base; each through the trunk lead-sweep protocol against the fixed baseline (Claude Code, completed 2026-11-20, branch claude/representation-join-ic-20261120, PR #1877; (b) both leads FAIL phase 1, (a) no cheaper relation at l'=4..13, (c) fp2-weil 7x-284x over table mitm but S/rho 13->61; results, report and bench records in crypto PR #4840, research/representation_join_ic_20261120) [pcc:unverified]

- [ ] Complete or obstruct the P-256 full-bitangent Frobenius/Hilbert-90 descent, with all 28 lines, cocycle verification, and exact base-field round-trip checks (Codex, started 2026-11-20, branch codex/nist-333-transfer-evidence-20261120, PR #1876) [pcc:unverified]

- [x] Integrate the NIST P-224/P-256 genus-3 (3,3,3)-isogeny reconstruction and the bounded genus-3 HECDLP cover-reduction evidence, preserving quartic/Kummer maps, empirical controls, and open transfer obligations (Codex, completed 2026-11-20, branch codex/nist-333-transfer-evidence-20261120, PR #1876) [pcc:unverified]

- [x] Move agent skills to the workspace trunk: delete local `.agents/skills`/`.claude/skills` copies, point docs and checks at isogeny-labs/workspace (Claude, started 2026-11-19, branch claude/skills-to-trunk-20261119, PR #1852)

- [x] Lead 2D: evaluate prescribed-singularity (nodal) degree-`d >= 4` plane Bezout lifts (`d in {4, 5, 6}`) and Cayley-Bacharach 9-point cubic pencils + shared `CoordinateFb` preimage sieve (Cursor, started 2026-11-19, branch cursor/pdp-lead-2d-xedni-cb-nodal-20261119, PR #1849) [pcc:unverified] Lean 14/14 [pcc:unverified]

- [x] PDP Lead 3B: Aut-equivariant signed multi-orbit coefficient-box (`wsum`) relation collector on Generic/J1728/J0 prime curves in `prime_orbit_index_calculus` (Cursor, started 2026-11-19, branch cursor/pdp-lead-3b-orbit-wsum-20261119, PR #1848) [pcc:unverified] 27/27 tests [pcc:unverified]
- [x] Rho-parity remasure: CLI `--wsum` + `orbit_wsum_vs_rho` panel vs matched rho — Generic fp28 S/wall ~2.3–2.6×; falsified for cold single-target (Cursor, 2026-11-20, PR #1848; workspace #42)

- [x] Lead 2B: implement compact binary-selector arity-three disjoint-window chained-S3 native Fp CDCL(T) solver with checked explanations and run s=5..12 scaling screen (Cursor, started 2026-11-19, branch cursor/pdp-lead-2b-m3-cdclt-fp-20261119, PR #1847) [pcc:unverified]

- [ ] Xedni scaling Phase 2: test Cayley--Bacharach pencil-enforced lifting (`dim ker_Q B = 2`) and shared coordinate-factor-base decomposition above `11` bits (Cursor, follow-up to PR #1810) [pcc:unverified]

- [x] Advance Xedni toward cryptographic scale (Phase 1): native Rust multi-prime subgroup-kernel LLL relation extractor, order-statistic 3D-LLL preselection, `ca-icx xedni-solve` (verified non-collinear solves through `p = 1021`), and Lean 4 modular-kernel + function-field section specialization bridge (Cursor, started 2026-11-18, branch cursor/xedni-crypto-scale-ef34, PR #1810) [pcc:unverified]

- [x] Prove Xedni chord-origin good-reduction bridge in Lean 4, decompose Nov 17 `r=6..9` panel collinearities, and implement JKSST `PGL_3(F_p)` + 3D-LLL plane-cubic lift (Cursor, started 2026-11-18, branch cursor/xedni-plane-group-chase-ef34, PR #1779) [pcc:unverified]

- [x] Chase Xedni Phase 2 geometric escapes: Cayley-Bacharach 9-point cubic pencils, nodal degree-d>=4 Bezout curves, and L4-check F1 small-height lift selector; all three escapes benchmarked in native Rust (`crates/xedni-phase2`) with Lean 4 obstruction proofs (`experiments/xedni-phase2-20261119/formal/Phase2Obstructions.lean`) and closed against sub-sqrt(p) thresholds (Cursor Cloud, started 2026-11-19, branch cursor/xedni-cb-nodal-escapes-3858, PR #1846) [pcc:unverified]

- [x] Execute preregistered 5-encoding/3-arm auxiliary-IC benchmark panel, implement division-free m=3,4 split-S3 resultant evaluation in `crates/prime-field-auxiliary-ic`, and audit disjoint 3-window CDCL(T) nogood width + CT186 prime-field cost floor; KN-FIND-007 yield conservation confirmed across 5 fresh 31-bit targets, Multiplicative(126) m=3,4 circuit beats same-base direct by 1.32x/1.23x, CDCL(T) slope e=2.00 refutes sub-birthday gate (Cursor, started 2026-11-19, branch cursor/aux-ic-m34-and-cdclt-audit-3858, PR #1845) [pcc:unverified]

- [x] Fix second-pass audit C-F6, C-F7, C-F8, C-F10, C-F11, C-F12 (coordinator check-in forgery, sequence overflow, unverified step sums, walkers_done, ca_bench averaging, walker start-up steps) (Cursor, started 2026-11-18, branch cursor/coord-bench-audit-fixes-a95f, PR #1774)

- [x] Repair the second-pass C library findings (rho/gpu_rho dp_bits defeats the runaway guard; kangaroo interval wider than the group; grumpy unbounded on an unsolvable target; dense linear-solve fallback unchecked; GLV batch start-up for n >= 2^39; ca_crt2 zero modulus) and re-sync the shared pcc files to the crypto owner copy (claude, completed 2026-11-18, branch claude/codebase-assessment-report-fp044d, PR #1773; coord.c dp cap left for the owner)

- [ ] Trace the documented and reproducible origins of the NIST/ANSI elliptic-curve base points, including bounded negative generator searches (Codex, started 2026-11-18, branch codex/nist-base-point-origins-20261118, PR #1769) [pcc:unverified]

- [x] Audit rational 2-isogeny ECDLP transfer: subgroup, kernel, image, dual/inverse, exact costs and toy DLP (automation, started 2026-11-18, branch research/examine-2isogeny-obligations-20261118, PR #1775; 64/64 local BSGS logs, independent PCC pending) [pcc:unverified]

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

- [x] Extend certified Xedni lift-success trials to the ten-coefficient `r=7..9` regime with exact rational dependence verification; local frozen panel completed 1,600/1,600 rows with 67 certified relations and 23 recoveries (Codex, started 2026-11-17, branch codex/xedni-breakthrough-20261117, implementation PR #1730 merged, outcome PR #1762 merged) [pcc:unverified]

- [x] Derive and implement target-dependent chord-origin recovery, including a zero-explicit-target exact relation, Rust/Python controls, Lean algebra and an editable SVG diagram (Codex, started 2026-11-18, branch codex/xedni-breakthrough-20261117, draft PR #1768) [pcc:unverified]

- [ ] Freeze and run a fresh-seed target-bearing relation-enumeration panel, preserving target-independent lift success and comparing complete recovery work against the frozen baseline (Codex, started 2026-11-18, branch codex/xedni-breakthrough-20261117, draft PR #1768) [pcc:unverified]

- [ ] Derive, formalize and prospectively freeze a target-origin-pencil relation search that expands bounded target-bearing coefficient coverage without claiming new relation information; measure it only after checkpoint transport is restored (Codex, started 2026-11-18, branch codex/xedni-breakthrough-20261117, draft PR #1768) [pcc:unverified]

- [ ] Prospectively implement and freeze a first-representative fixed-coordinate dedup arm for the target-origin pencil, requiring semantic parity and full work accounting before any optimization claim (Codex, started 2026-11-18, branch codex/xedni-breakthrough-20261117, draft PR #1768) [pcc:unverified]

- [ ] Actively attempt to disprove the Xedni rank-decay heuristic over 16--32-bit primes with independent lift, r, and exact Silverman/JKSST local-condition factors; preserve the frozen signed-slope/useful-recovery criterion, close production gates, and run the first admissible rows without downscaling (Codex, started 2026-11-18, resumed 2026-11-19, branch codex/xedni-breakthrough-20261117, PR #1768) [pcc:unverified]

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

- PR #1883: registered PKM phase-1 measurement cannot start until checkpoint S3 upload access is restored; token HTTP 403; refresh agent exits 1 on S3 listing; configured AWS profiles return InvalidAccessKeyId or AllAccessDisabled. See `research/pkm_tower_registered_m5m6_20261121/PREPARATION.md`. [pcc:unverified]

- The fresh Xedni selector panel is frozen but cannot generate its first row: checkpoint upload has no token/profile, and the documented ambient AWS fallback returns `AllAccessDisabled`. Resume requires valid scoped checkpoint transport; the earlier local waiver explicitly excludes modified panels. [pcc:unverified]
- The rank-decay panel additionally needs licensed pinned Magma, a trusted execution-verifier/keyring, an integrated authorizing freeze, a natural `r=7..9` constructor/global map certificate, a trusted full saturated-basis route, fresh replication primes, and committed powered compute. The current runner diagnostic is intentionally `BLOCKED_NON_PRODUCTION` with zero rows. [pcc:unverified]

- Controlled representation comparison PR #1767: real S3 checkpoint upload/gate failed with AllAccessDisabled; explicit CPU/Git exception question is pending. Source/protocol preparation is not a measured panel. [pcc:unverified]
