# Active research tasks

## Active items
- [ ] Implement genus-4/5 trigonal plane-model bridge for the high-genus index-calculus table (Codex, started 2026-11-28, branch codex/trigonal-plane-model-20261128, draft PR #2024; companion crypto draft PR #5346; cryptanalysis #2010 merged; bounded genus-4/5 affine chart and split-line rows passed in both Jacobians; genus-5 F_7 seeded DLP recovered and verified a toy target, while exceptional branches, arbitrary projective lines, and geometric target descent remain open).
- [x] Fuse P+Q and P-Q construction with one shared affine denominator in the native M31 signed-pair index and compare cold same-target solves (Codex, started 2026-11-27, branch codex/m31-fused-pair-build-20261127, draft PR #2022; all 90 arms completed and 28,073 certificate relations replayed; the combined B768 path lost to current B384, so the opt-in code was removed and no Lean performance claim was made). [pcc:unverified]
- [ ] Improve cold same-target M31 index-calculus solves with exact signed-pair indexing, factor-base and graph leads (Codex, started 2026-11-27; merged PRs #2009, #2011, #2012, #2013, #2014, #2015 and #2017; the standalone Rust collector's dual-bitmap local gain did not transfer to native PairIndex, where dual lost to high-only on five public targets x three seeds; high-only's separate fresh-seed confirmation missed its 1.05 paired wall/CPU gate, so neither is selected as the library default; native evidence in PR #2018, pending independent standing; torus, single-generator anchor, B512 cold size and paired x-filter also did not clear their gates). [pcc:unverified]
- [x] Clear the lead-testing papercuts in `ic bench` and the PKM pilot (workspace PROTOCOL.md §10) — done: configurations-only sweep files, empty matrix axes refused, a clean exit-3 `unsupported` refusal for m > tower engine capacity, a size check before a Koblitz divisor base materialises 2^dim abscissae, the listing's missing parameters, and `git_commit` read from the build checkout without the caller's `GIT_*` (Claude Code, started 2026-11-26, branch claude/kind-pascal-7ree1e, PR #1996; tracking workspace PR #180)
- [x] PKM symmetrised presentation as a pilot flag (`pkm_tower_pilot --presentation sym`: Dickson/torus and, new, Kummer towers; Vélu towers fall back to raw, labelled) and its lead-sweep phase 1 against the raw f4_fp reference, m = 2..9 (Claude Code, started 2026-11-27, branch claude/pkm-sym-presentation-20261127, draft PR; workspace item PKM M31, umbrella workspace#190). Prior: M31 sym on plain F4 completed m = 3, t = 4 at 4/4 where raw did 2/4 (workspace docs/notes/pkm-m31-20261125/results_sym.md). [pcc:unverified] — **done** 2026-11-28: workspace lead-sweep PASS at phases 1, 2 and 3 (p = 786433, 469762049, 3221225473): widest F4 matrix 1.49–3.24× narrower than raw at m = 2..4, larger N, 0 planted violations; m ≥ 5 unsupported (dense S̃ fit). Report isogeny-labs/workspace docs/notes/pkm-sym-presentation-20261127/REPORT.md, record RES-pkm-sym-presentation-20261127 [pcc:unverified]
- [ ] Mirror exact point hashing into the native two-slot collision graph collector (Codex, started 2026-11-27, branch codex/point-hash-collision-graph-20261127, draft PR #1997; paired Crypto draft PR #5263, native checks pending).
- [ ] Audit p plus one smoothness leads on public fixtures (Codex, started 2026-11-25, branch codex/p1-smoothness-leads-20261125, PR #1979) [pcc:unverified]
- [x] Publish degree-5 horizontal joint S4 component screen (Codex, started 2026-11-23, branch research/cm-joint-s4-screen-20261123, PR #1967): same-base positive and negative query checks, source/endpoint/wire/joint solve costs, and bounded conclusion in research/cm_joint_s4_20261123/. [pcc:unverified]
- [ ] Batch ECDLP: lower the IC-vs-batch-rho crossover (Claude Code, started 2026-11-23, branch claude/batch-ecdlp-crossover-20261123, draft PR; workspace item PR #91): freeze prediction first; rebuild the `ca-ic prime` batch IC arm on `mitm-prime-batched` (#1891) / k=3 harvester (#1901) where they apply to F_p curves; re-measure up-front and per-target cost and the crossover K vs executed folded batch rho at 20/24/28 bits with CIs; define and measure best-seeded rho and report distance remaining
- [x] GT-02 coset filter at the S-optimal factor base (Claude Code, started 2026-11-23, branch claude/gt02-optimal-base-20261123, PR #1952; follows #1892/#1911): re-measure the coset-filtered MITM pair table against the baseline at the S-optimal base (char2 n=17..33 m=2,3; prime at the recalibrated sizes), lead-sweep protocol, paired CIs, distance to matched rho; result: char2 m=2 gain survives at the baseline-optimal dimension (1.11-1.42x, n=17..33), m=3 and prime 1.000; suite/docs/ic/runs/gt02-optimal-base-20261123/. [pcc:unverified]
- [ ] Gain-forest harvester k=3/k=4 beyond toy sizes (Claude Code, started 2026-11-23, branch claude/harvester-k3-scale-20261123, draft PR; follows #1901): frozen ladder protocol extending gaudry_cubic past p=2083 with >=6 seeds, harvester vs eliminator vs matched rho, exponent fit with CI, S-accounting check; trunk notes docs/notes/harvester-k3-scale-20261123/. [pcc:unverified]
- [x] `mitm-prime-batched` independent verification of PCC-20261122-ae5817 (fresh derived seeds, S-accounting audit, pcc claim to a verifier) and extension to 28/32 bits (claude, started 2026-11-23, branch claude/mitm-batched-verify-20261123, PR #1938; claims PCC-20261123-932211, PCC-20261123-99112d unverified; result: priced S reproduces, ~2.3x of it is accounting, genuine wall gain 1.37x at 24 bits, no growth past 28 bits; trunk item workspace PR #91)
- [ ] G33-005 Lead 2B canonical IR export for the three archived s=5 fixtures (Codex, 2026-11-22, branch research/g33-sp-canonical-ir-export-20261122, draft PR #1933): opt-in sidecars preserve the archived SHA-256 hashes; focused export and group-model tests pass (counts 1/0/0). The checkpoint upload gate returned HTTP 403, so no screen or SP run was launched; a gated screen replay and frozen comparable cohort remain open. [pcc:unverified]
- [ ] CT325 retrospective CT324 four-target native cold control **record-only** audit (ChatGPT, 2026-11-23 UTC, draft implementation [#1930](https://github.com/isogeny-labs/cryptanalysis/pull/1930), original protocol/ACTIVE parent [#1928](https://github.com/isogeny-labs/cryptanalysis/pull/1928) auto-merged before source): original artifact pinned, 24-row check and 14 semantic mutations/changed SHA rejected; [exact-code source-only CI #45108859889](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45108859889) passed at 839863e0. Four public target ratios old/new 0.596/1.015/1.821/1.821, geometric 1.190, descriptive four-target bootstrap [0.778,1.821], conditional p=0.1875, **not a qualified advantage**. Signed PCC/native Jacobian/695-701/physical C169/C13/D/full-rho/IC all unmet; active producer #1920 untouched. [pcc:unverified]
- [ ] CT323 bounded native same-public-Q BSGS / negation-quotient rho cold comparison (ChatGPT, started 2026-11-22, existing draft PR #1920, branch research/ct318-joint-cold-admission-20261122): preregister before Rust source; affine rho is provisional, not strongest optimized rho; separate source+CI, no S3/native Jacobian/PCC claim. [pcc:unverified]
- [x] CT322 exact-prime31 live public-only Rust BSGS reference control (ChatGPT; draft PR #1920): preregistered protocol, four fresh CSPRNG Q per cohort, genuine Linux wait4 individual child wall/RSS and post-exit CT321 reveal/group replay; [exact-source scoped CI #45097487126](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45097487126) passed at c7da997b, normal/-O eight distinct ordinary p=2^31-1 public DLPs recovered with real native Rust BSGS, public Q/commitments preserved, no scalar/salt disclosed by summary. **Unoptimized BSGS control only**; zero Jacobian original native calls, zero transfer candidate, no strongest rho/BSGS/IC complete-cost comparison, no independent PCC. CT304 S3/tool/STS remains blocked. [pcc:unverified]
- [x] CT321 prospective commit-then-reveal distinct public ECDLP challenge source (ChatGPT, started 2026-11-22, existing draft PR #1920, branch research/ct318-joint-cold-admission-20261122): generate four distinct Q via CSPRNG, keep scalar/salt in separately permission-restricted unpublished manifest; audit reveal and source CI #45090878506 on exact code c088ec98: normal/-O both pass, four genuine toy Q, 28 synthetic complete cold rows, 15 corruption/exclusive-create refusals; no authenticated blindness, native benchmark or PCC. [pcc:unverified]
- [ ] CT320 distinct-public-target challenge coverage for CT319 cold ECDLP admission (ChatGPT, started 2026-11-22, existing draft PR #1920, branch research/ct318-joint-cold-admission-20261122): require four algebraically distinct Q across matched blocks and reject repeated-target benchmark specialization; source-only negative controls, no native execution or signed PCC. [pcc:unverified]
- [ ] CT319 bind CT315 reported per-run wall/RSS/argv/binary/host fields to original CT304 bounded-process capture receipts, raw stderr and retained executable bytes (ChatGPT, started 2026-11-22, existing draft PR #1920, branch research/ct318-joint-cold-admission-20261122): source-only protocol and synthetic controls; original S3 custody and native complete-solve timing still blocked. [pcc:unverified]

- [ ] CT318 combine CT315 full cold seven-arm timing/RSS gate and CT317 independent Q=[k]P raw-output replay in a single fail-closed source-auditable admission (ChatGPT, started 2026-11-22, branch research/ct318-joint-cold-admission-20261122, PR #1920); native S3/STS/cold physical benchmark and signed PCC blocked. [pcc:unverified]

- [x] Document the matched single-large-prime control for `ca-ic prime` (Codex, started 2026-11-20, branch codex/document-prime-large-prime-control, PR #1925)

- [x] PKM auxiliary-curve (isogeny) factor base (workspace PROTOCOL.md lead sweep + direct pilot runs): `pkm_tower_pilot --iso-degrees` (odd/mixed Vélu levels, x-only, tested on the guide's F_61 example); odd degrees are constant factors at equal |V| (m = 2: degree 3 1.4-2.5x, degree 5 3.3-5.7x wall; mixed no effect), lead-sweep pkm-iso-deg3 phase 1 FAIL (t-paired gate); frontier |V| ~2^8-2^9.5 (m = 2), 2^5 (m = 3), 2^3 (m = 4), none at m >= 5; univariate elimination = enumeration's order, F4 and msolve far worse (`research/pkm_aux_curve_odd_isogeny_20261123/README.md`; Claude Code, completed 2026-11-23, branch claude/pkm-aux-curve-odd-isogeny-20261123, PR #1927; workspace PR #86; built at 9824fb08 + this PR's pilot because main does not build) [pcc:unverified]

- [ ] hashed-tensor lead sweep (workspace PROTOCOL.md, m = 2..9, prime regime): plug-in spec, phase 1 vs prime-abscissa+mitm; calibrate contraction steps and fix the `root_u` floor if the oracle cannot run (Claude Code, started 2026-11-22, branch claude/hashed-tensor-lead-sweep-20261122, PR #1915; built at 80c9f4dd9 + this PR's pricing commit because main does not build) [pcc:unverified]

- [ ] CT317 independent prime-field cold-target group replay (ChatGPT, started 2026-11-22, existing draft PR #1912, branch research/ct302-full-native-log-admission-20261121): source-only bound exact raw solver stdout/receipt to verified Q=[k]P on short-Weierstrass <=31-bit prime curves; independent subgroup and curve validation, toy sabotages; native 695/701 and authenticated custody still blocked. [pcc:unverified]

- [ ] CT316 Linux per-child GNU-time RSS capture (ChatGPT, started 2026-11-22, existing draft PR #1912, branch research/ct302-full-native-log-admission-20261121): explicit time-executable SHA pin, full CT176 bounded original/reuse capture, separate read-only meter/output receipt, measured positive OS RSS on benign Python stand-ins, 18 meter corruption controls, no original Jacobian models or independent PCC; same-host native 695/701 and CT315 full-cold panel still blocked on authenticated S3/tool/STS owner gate. [pcc:unverified]

- [ ] CT315 complete-cold ABBA ECDLP cost-panel admission (ChatGPT, started 2026-11-22, existing draft PR #1912): prospective 7-run/block, >=4-block exact-target panel with per-run cold setup/transfer/precompute/relation/LA/descent/recovery/verification/teardown, measured RSS and fixed memory cap; compare candidate to min(retained-lift, rho, BSGS, IC) rather than primitive-only cost; source-only synthetic positive/negative and 19 sabotage/parser controls. Original S3 custody, real cold logs, independent source group-law verification, CI/PCC still open; never a speedup claim. [pcc:unverified]

- [x] CT314 enforce failure-receipt status/exit/error consistency (ChatGPT, started 2026-11-22, branch research/ct302-full-native-log-admission-20261121, PR #1912): preregister and reject forged timeout/overflow/spawn/nonzero/invalid-exit labels while preserving raw failed-capture custody; source-only CI #45051825751 passed at da20cbb5 (nine status mutations, four bounded negative controls); no native execution or pricing. [pcc:unverified]

- [ ] CT302 bind primitive pricing to dual full 695-record native logs (ChatGPT, started 2026-11-21, branch research/ct302-full-native-log-admission-20261121, PR #1912): reuse existing whole-population comparator and CT301 frozen-vector gate; source-only controls first; no native timing/PCC claim.

- [ ] CT311 direction/sector-resolved CT248 C169/C13/D physical-cost frontier (ChatGPT, continued 2026-11-22, branch research/ct302-full-native-log-admission-20261121, PR #1912): 48 paired exact-source rows, 24+24 directions and six per sector; CT304-admitted full 695 logs required for production, synthetic positive/negative and sector-reversal source-only controls. No native provenance, measured speedup or PCC from tests; owner-approved six-S3-object custody and physical hardware remain blocked.

- [ ] CT304/CT309/CT310 full-native evidence gate on existing draft PR #1912 (ChatGPT, continued 2026-11-22, branch research/ct302-full-native-log-admission-20261121): dual-695 audited receipts, seven-slot clock nesting and new plan-only bounded full-native pair producer with exact retained binaries; source-only CI #45029620704 passed (mock/benign children only). Approved original S3 six-object custody, actual physical C169/C13a/C13b/D/N2_actual, complete cold single-target ECDLP cost, independent PCC, per-process RSS and protected merge gates remain open; no paid compute.

- [ ] CT301 bind native CT248 transcript to immutable authentic 48-vector fixture (ChatGPT, started 2026-11-21, branch research/ct301-native-transcript-fixture-binding-20261121, PR #1905): reject same-shape class-key/counter substitutions in actual --log admission; synthetic source guards only, retain draft until native/PCC gates. 

- [ ] CT300 authentic 48-vector norm-pricing admission fix (ChatGPT, started 2026-11-21, branch research/ct300-authentic-scalar-fixture-20261121, PR #1904): correct the real fixed-chain scalar and literal C13 counts; freeze genuine fixture source gates; retain draft until inherited CI/review/PCC gates are satisfied.

- [ ] CT312 source-admission clock/byte fix (ChatGPT, continued 2026-11-22, branch research/ct302-full-native-log-admission-20261121, PR #1912): reject every called but zero-ns direct/retained C169/C13/D primitive and preserve exact receipt-bound stdout bytes for SHA256 even with CRLF; only source mocks, no native measurement or speedup.

- [x] CT313 retain bounded failed-native capture bytes and separate SHA-bound refusal receipts (ChatGPT, started 2026-11-22, branch research/ct302-full-native-log-admission-20261121, PR #1912): four nonzero/timeout/overflow/spawn mocks, independent source-only failure receipt checker and four SHA tamper refusals; [source CI #45045972591](https://github.com/isogeny-labs/cryptanalysis/actions/runs/45045972591) passed at d1a31e2b. No native model execution, complete solver, authenticated S3 or PCC.

## Blocked / questions

- Full native CT244/CT300 pricing and 695/701 record replay still require approved authenticated original six-object artifact custody; previous STS invalid-token and S3 403 are unresolved. This source-only correction does not authorize paid compute, artifact substitution, modified provenance or protected merge.

## Priority

- Complete cold single-target source-curve ECDLP improvement against retained-lift, optimized rho, BSGS and frontier IC, with C169/C13a/C13b/D/N2_actual, setup, linear algebra, memory and independently signed PCC all charged.
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
- [x] Add an exact compressed leaf-product presentation for the ECC2K mixed-edge S3 lead: retain full-width `edge-ab` as the matched control, but represent `w = x_a x_b` in the product space `V·V` and freeze a separate solving-degree comparison (Codex, completed 2026-11-27, branch codex/ecc2k130-mixed-edge-presentation-20261127, PR #2000; measurement remains checkpoint-gated) [pcc:unverified]
- [x] Integrate the ECC2K-130 mixed-edge lifted S3 presentation (`w = x_a x_c`) into the index-calculus degree/closure framework, with matched standard-edge controls and a prospectively frozen lead-sweep plan (Codex, completed 2026-11-27, branch codex/ecc2k130-mixed-edge-presentation-20261127, PR #2000; measurement remains checkpoint-gated) [pcc:unverified]
- [ ] PKM torus (p+1-side Dickson) tower kind for M31 in pkm_tower_pilot (claude, started 2026-11-25, branch claude/pkm-torus-tower-m31; tracking workspace#130)
- [ ] CT201–CT203: complete cold ECDLP source adjudication (matched five-arm rho/BSGS/IC, Williams order, distinct-Q per-block prospective gate; automation, started 2026-11-18, branch research/ct201-complete-single-target-gate-20261118, PR #1766; source CI 44/44 normal and -O at 36807d15; native/PCC blocked) [pcc:unverified]

- [x] gaudry_cubic: gain-forest cycle harvester with k = 3 large primes and a threshold stop beside `LargePrimeEliminator`, paired against the six-seed §11.11 protocol; k = 4 follow-on if it passes — k=3 harvester PASS (S 0.31-0.57x, exponent 0.428 -> 0.332, paired 6 seeds x 4 sizes); k=4 r 0.532 -> 0.279 (LA phase only) (Claude Code, completed 2026-11-22; started 2026-11-22, branch claude/gaudry-gain-forest-harvester) [pcc:unverified]
- [x] WP0 symmetric cipher IR (sym_ir): types, eval, GF(2) matrices, primitive descriptions and bit-exact regression tests against symmetric/* and hash/* (Claude Code, started 2026-11-21, completed 2026-11-22 with WP1–WP5 via #1909, branch claude/sym-ir-wp0, plan docs/plans/2026-11-21-generic-symmetric-cryptanalysis.md in workspace PR #62, PR #1890) [pcc:unverified]

- [ ] Audit high-genus order-certification claims and gate unproved exact-order language (ChatGPT, started 2026-11-21, branch audit/highgenus-order-certification-20261121, PR #1897) [pcc:unverified]

- [x] Expand higher-genus support: genus-generic index calculus and Pollard rho for hyperelliptic and non-hyperelliptic (superelliptic one-point) Jacobians over F_p, genus 5..131 (`suite/src/highgenus/`; rho verified at g = 5..131 hyperelliptic and g = 5, 7, 11, 23, 97 non-hyperelliptic; IC with order-from-relations verified to g = 47; `suite/docs/highgenus/RESULTS.md`) (Claude Code, completed 2026-11-21, branch claude/higher-genus-5-131, PR #1884) [pcc:unverified]

- [ ] Run the registered PKM tower phase-1 comparison at feasible m=5,6 with the frozen baseline, planted controls and resource limits; report full cell outcomes; prepared and checkpoint upload blocked (Codex, started 2026-11-21, branch codex/pkm-high-arity-phase1-20261121, PR #1883)

- [ ] Complete native import-cache verification (Codex, started 2026-11-17, branch fix/native-import-cache-followup-20261117; tracking PR #1763 merged before implementation; draft PR #1879 includes original arithmetic PDF recovery in progress; full CI pending).

- [x] `ic bench` CLI: validate every configuration before the instance, calibration and rho run (plug-in names per regime, parameter keys, targets, solver, oracle m range) with did-you-mean suggestions and exit 2; show skip reasons on the terminal; human-readable `--list` (Claude Code, completed 2026-11-20, branch claude/ic-bench-cli-ux, PR #1881) [pcc:unverified]

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

- [x] Coset filter behind the BASELINES n = 41 K_0 row: Koblitz base builder at n >= 41 and the filter wired into that row's pair-table pipeline — row made by crypto ic price; its subgroup-orbit base is one coset class, so the filter cannot help it; n=41 oom_alloc was real (136/544 GiB), now a clean refusal; koblitz-orbit points= base added (Claude Code, completed 2026-11-22; started 2026-11-22, branch claude/coset-filter-n41-koblitz) [pcc:unverified]

- [x] ic bench: coset-filtered MITM pair tables (`mitm` / `mitm-frobenius` `coset_filter=1`), frozen ratchet protocol and bench record; stage improvement from the trunk's graph-theory note — merged as PR #1892 (Claude Code, completed 2026-11-22; started 2026-11-22, branch claude/mitm-coset-class-filter, PR #1892) [pcc:unverified]

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
- [ ] Speed up prime-field index-calculus relation finding and solving in `ic bench`: batched x-only pair-table preparation and m=3 probes with complete native accounting, faster prime arithmetic, gated by the lead-testing protocol (Claude Code, started 2026-11-21, branch claude/ic-prime-batched-relations-20261121, PR #1891) [pcc:unverified]
- [ ] Gröbner reference table: `f4_fp` vs msolve on PKM tower + direct Semaev systems (workspace goal GB-1/GB-2) (Claude Code, started 2026-11-21, branch claude/gb-reference-20261121, PR #1882)
- [x] Licence files and SECURITY.md (disclosure, acceptable use, dual-use) per business action plan F3/F4/F5 (Claude Code, completed 2026-11-22; started 2026-11-22, branch claude/licence-security-policy-20261122, PR #1916)

## Blocked / questions for the owner

- PR #1883: registered PKM phase-1 measurement cannot start until checkpoint S3 upload access is restored; token HTTP 403; refresh agent exits 1 on S3 listing; configured AWS profiles return InvalidAccessKeyId or AllAccessDisabled. See `research/pkm_tower_registered_m5m6_20261121/PREPARATION.md`. [pcc:unverified]

- The fresh Xedni selector panel is frozen but cannot generate its first row: checkpoint upload has no token/profile, and the documented ambient AWS fallback returns `AllAccessDisabled`. Resume requires valid scoped checkpoint transport; the earlier local waiver explicitly excludes modified panels. [pcc:unverified]
- The rank-decay panel additionally needs licensed pinned Magma, a trusted execution-verifier/keyring, an integrated authorizing freeze, a natural `r=7..9` constructor/global map certificate, a trusted full saturated-basis route, fresh replication primes, and committed powered compute. The current runner diagnostic is intentionally `BLOCKED_NON_PRODUCTION` with zero rows. [pcc:unverified]

- Controlled representation comparison PR #1767: real S3 checkpoint upload/gate failed with AllAccessDisabled; explicit CPU/Git exception question is pending. Source/protocol preparation is not a measured panel. [pcc:unverified]
