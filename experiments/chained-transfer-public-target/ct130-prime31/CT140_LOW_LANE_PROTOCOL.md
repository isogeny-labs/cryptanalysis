# CT140 — prospectively fixed small-lane native cold ECDLP control

Date: 2026-11-15. [pcc:unverified]. Stacked on cryptanalysis #1550, ultimately rooted in crypto #3877. This is *not* the original-prime 695/701 Jacobian chain, and does not replace CT126/C137 native C169/C13a/C13b/D pricing.

## Scientific question and hypothesis (committed before CT140 execution)

Prior CT138/139 measured only batch widths 16, 32, 64 on a selected 31-bit CM-neighbor toy curve. The best fixed source/target pair there was 16/16 and the second-container ratio was 1.31936789. Smaller source-batch widths could improve direct-source performance enough to narrow or erase the apparent isogeny advantage. Test **widths 2, 4, 8, 16**, never pick a source or target arm separately for each logarithm. A counterexample to the speed claim is a fixed direct-source cohort time <= the best transferred cohort time, including transfer/verification.

## Frozen implementation and public samples

- Read-only native generator source: CT136 `ct136_native.cpp`, SHA256 `20b0305d0b291602dd141a278c00459c47e78608f17e33bea6395a3106438921`; its pinned CT135 `#include` is preserved. No curve, seed, scalar or collision path changed.
- Guarded derivative replaces exactly one `LANES=32`, `round<6250`, schema, two arm names and default count. Exactly **200000 maximum transitions/trial** for every width, 6 trials, one inversion per batch. This changes the number of lanes and per-lane transitions; no asymptotic or full-rho uniformity claim.
- Four fixed public seeds: 20261340, 20261341, 20261342, 20261343; 32 distinct source public targets/seed, generated unchanged. Width/seed execution order is a **four-row cyclic rotation**: seed 20261340: 2/4/8/16; 20261341: 4/8/16/2; 20261342: 8/16/2/4; 20261343: 16/2/4/8.
- Five complete source/target solvers per target, executed twice in the existing alternating ten-run loop. Thus **16 processes, 160 target-processes, 5120 complete scalar recoveries**; 128 distinct public targets; original plus target verifications. Three baseline arms unchanged and the source/target new batch arms exact-width labeled.
- Use the same local host for all widths, single-threaded `g++ -std=c++17 -O3 -DNDEBUG`, pinned inherited source and public curves, /usr/bin/time RSS, process time, source/binary SHA256, errno and stderr, pre-existing independent `ct136_verify.py` after fail-closed width-label normalization. Capture full failure records and independent arithmetic verification. Cap each process to 120 seconds and virtual memory to 2 GiB. No paid EKS/Spot/GPU and no protected branch merge.

## Acceptance, uncertainty and alternative outcomes

- Fail on missing/extra process, wrong seed/target/schema, incorrect original-log verification, unequal public points across widths, invalid ratios, incomplete repeats, changed source hash, missing RSS, or time/memory ceiling.
- Whole-cohort total ns for each named fixed solver is compared across all seeds. Best **fixed** source over best **fixed** transferred total is exploratory. Publish all width arms, no per-target oracle selection. Include A/A ratios and a descriptive paired resampling interval; do not call it an independent host confidence interval.
- Reject any invalid unit label. The inherited CT139 `by_width.extra_headroom_ms_per_target` stores *nanoseconds*, an observed x1,000,000 reporting-unit mistake; preserve its original bytes, add an independent dimension-check correction, then compute ms explicitly as `(source_ns-target_ns)/(128*1e6)`. Its top-level `transfer_extra_headroom_ms_per_target` is already correct and must remain distinct.
- If width 2/4/8 beats width16 on source, change the reference; if it beats transferred cost, log as a negative-to-transfer outcome and prioritize source-optimized algorithms. If transfer stays faster, retain only scope-limited evidence. Either way the owner acceptance remains: original-prime native CT126 paired pricing, 695/701 full chain, same-host strongest rho/BSGS/IC, setup/transfer/LA/RSS, independently signed PCC.
- Do not claim novelty: Montgomery batch inversion and endomorphism-based rho are established literature. Sources checked: Bernstein-Lange `On the correct use of the negation map in the Pollard rho method` (https://cr.yp.to/elliptic/negation-20110102.pdf); GLV https://arxiv.org/abs/1106.5149; existing cryptanalysis #1547/#1550, #1549 and crypto #4215/#3877. Shared KB and local Conductor unavailable through connector-only session.
