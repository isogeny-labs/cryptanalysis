# CT190 session record — 2026-11-17 UTC

**Standing:** [pcc:unverified]. Separate project-specific handoff instead of overwriting the concurrently edited shared daily log.

## What was done (commands, files, features)

- Inspected merged [crypto #3877](https://github.com/isogeny-labs/crypto/pull/3877), [#4215](https://github.com/isogeny-labs/crypto/pull/4215), [#4178](https://github.com/isogeny-labs/crypto/pull/4178), merged [cryptanalysis #1523](https://github.com/isogeny-labs/cryptanalysis/pull/1523), CT173 norm-price audit, merged CT188 design #1725, open CT189 #1729, draft #1726, current AGENTS.md, docs/ACTIVE.md and current 2026-11-17 daily session log. Checked CT189 actual native process code, old seven-column adjudication, CT125 norm reuse source, CT172 Rust source, and whole-corpus outstanding gates. The 2026-11-17 repo-wide research KB service is not exposed in this runtime; GitHub's autoresearcher lab-contract text fetch raised a UTF-8 decoding error. No novelty claim or new mechanism search inferred.
- Created branch `research/ct190-block-fixed-effect-crossover-20261117` based on cryptanalysis/main `cfc03a37`. Tracked task in docs/ACTIVE.md as first isolated commit `569f83c6`; opened draft [cryptanalysis PR #1732](https://github.com/isogeny-labs/cryptanalysis/pull/1732).
- Froze prospective `CT190_BLOCK_FIXED_EFFECT_PROTOCOL.md` at `c5d65f45` before implementation; added `ct190_block_fixed_effect_diagnostic.py` at `202f2f6d` and tests at `07a048d6`. Added source-only workflow at `f3ed3ee7`.
- Exact-code [CT190 workflow #44165880160](https://github.com/isogeny-labs/cryptanalysis/actions/runs/44165880160), job `134331664810`, completed **success**; decoded logs show 5/5 normal and 5/5 Python -O tests passing on source `f3ed3ee7`. The tests establish exact rational 14/14 block+period/treatment/carryover rank on every one of 48 public packets; in controlled 2,304-row synthetic timing, CT188 gives **spurious 1.50x** with equal intrinsic route cost/common block latency, while CT190 gives 1.00x and A/A drift is zero. Programmed 1.25x with block shocks plus first-order carryover is recovered by CT190 as 1.25x. Mutation controls reject truncated/extra/wrong-arm/invalid-time evidence. [pcc:unverified]
- Committed source report `CT190_BLOCK_FIXED_EFFECT_SOURCE_REPORT.md` and tracked the isolated source-only component as checked in ACTIVE.md. No real process timings, native Rust compile, signed PCC, authenticated original 695/701 corpus, paid compute, protected merge, or completed ECDLP solve.

## Decisions made (and why)

- Addressed a concrete unmodeled nuisance in CT188/189 rather than duplicating CT189 producer, original 21-counter frozen input, concurrent IC collector or new transfer-algorithm branches.
- The 14-column design uses eight block intercepts, three period indicators, physical B, previous B, and B×previous B. Within-block demeaning exactly removes each arbitrary additive log-block baseline before solving six coefficients, conditional on the model. The old estimator remains alongside the new so its interpretation cannot silently change. Original physical roster SHA is pinned. No new seed, arm assignment or fixture bytes modified.
- The synthetic 1.50x counterexample is adversarially generated, not observed host confounding. A source-only rank/check/test is not independent scientific validation. The scoped green workflow does not supersede the broader repository's existing failed workflow gates; keep PR draft until CI/review/PCC disposition is legitimate.

## Open threads

- Prospectively integrate the second estimator into a versioned next physical-cold reader after review; do not rewrite CT189 v3 evidence or its frozen protocol.
- Independent original 695/701 whole-corpus authentication and 48-case native Rust arithmetic parity still gate actual route measurements. Source-only original 21-counter CT175 contract does not certify the additional `N2_actual` timing path. Obtain owner/provider admission for same-host C169/C13a/C13b/N2_actual/D (including actual norm `pmul(P,2)+descend_point`, not only `padd`) and paired sham/carryover controls; preserve all failures.
- A complete **single-target** public prime-field ECDLP comparison still needs matched optimized rho, BSGS and IC, all cold setup/transfer/LA/recovery/inversion/memory, identical public logs, uncertainty, negative results, and independent PCC. No speedup asserted.

## Errors (what went wrong, how it was handled)

- GitHub connector cannot decode autoresearcher AGENTS/lab contract as UTF-8; recorded evidence coverage gap, used committed primary PRs, CT188 source and CT173 audit rather than inventing knowledge-base coverage.
- On the exact source SHA, broader inherited workflows had failures while the isolated CT190 tests passed. No CI bypass, cherry-pick onto protected branches, or nonadmitted workload.
