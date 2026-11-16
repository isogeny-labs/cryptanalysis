# CT154 protocol — public-point-only q223 source solver and mixed negation-rho diagnostic

Date: 2026-11-16 UTC. Root crypto #3877; stacked cryptanalysis #1589. Standing: **[pcc:unverified]**.

## Scope, prior work and priority

- Freeze source: the **original** CT152/CT153 cubic-extension model over F_223[z]/(z^3-3), a2=(127,56,199), a4=(152,35,36), a6=(212,109,150), G=((162,197,140),(45,11,207)), ell=2,773,073, #E=4ell. Do not use the separate nu12 model.
- CT153's CLI accepted a known scalar and constructed public Q internally. CT154 instead accepts exactly six canonical finite-field coordinates for Q, **never** a scalar. External independent Python constructs Q=[k]G for known-answer public tests and audits [recovered]G=Q. The C++ implementation must reject invalid field encodings, off-curve Q and Q outside <G>.
- Reuse exactly CT153's C++17 arithmetic and complete BSGS/ordinary three-way rho, without changing that source. Add a 16-partition, deterministic r-adding **negation-quotiented** rho with mixed doubling and bounded retries. This is a candidate baseline, **not a claimed best/optimized rho**, and is not a transferred Jacobian solver.
- Literature/prior work reviewed before implementation: CT153 and CT125/CT143, crypto #4215 and #4178; Teske *On random walks for Pollard's rho method* (Math. Comp. 2001); Bos, Kleinjung, Lenstra *On the Use of the Negation Map in the Pollard Rho Method* (ANTS 2010), documenting short fruitless cycles and measured gains below sqrt(2). Do not assume reducing the state space improves total time.
- Research-KB server is not available in this connector runtime. Fallback: repo primary source, open PRs, root comments and lead atlas pointer. No novelty or prior-work absence inference.

## Prospective bounded test/measurement contract

1. Independently generate Q for six scalars **outside** the executable: 1,17,12345,159273,2300011,2773072; C++ sees Q coordinates only.
2. Control group-law relation invariants of the negation walk for 50 steps on each Q; require six complete BSGS and six negation-rho known-answer recoveries, checked outside C++ by the separate Python finite-field/group implementation. Record negative tests for malformed CLI, invalid coordinates, wrong source point and out-of-subgroup public point.
3. Run six targets, two blocks per target; per block alternate `bsgs,rho,neg-rho,neg-rho,rho,bsgs` and the reverse order, each in a **fresh OS process**. Expect 72 receipts. Include process spawn wall, measured solver ns, point/field primitive counters and child VmHWM memory. No target scalar may be passed to the executable. Collect every error/restart/exhaustion; never drop failures.
4. Report medians for all three arms, 12 paired block means for BSGS vs rho and BSGS vs neg-rho; independent fixed-case block bootstrap (seed 154, 4000 samples) 95% intervals, and A/A absolute drift. Timing on a non-isolated developer machine remains exploratory even if intervals exclude zero; not a calibrated cost or strongest baseline.
5. Preserve raw JSON, exact code and binary SHA256, commands, compiler flags, negative controls and host. Run C++17 `-O3 -Wall -Wextra -Werror`. Add source-only CI to run self-test and quick 12-record audit. PCC remains unsigned until independent verifier CI; no ledger promotion.
6. The actual priority remains independently checked 695/701 norm-point reuse, separately owner-admitted C169/C13a/C13b/D, and complete cold *transferred* single-target solve vs best matched rho/BSGS/IC with all setup, transfer, LA, correction, memory and verification accounted. Do not infer this from CT154.

## Pre-protocol developer reconnaissance disclosure

Before this protocol commit, a **non-timed** local build of the first mixed-negation-walk candidate encountered only fruitless exact-state loops and failed to solve the six-fixture self-test. A deterministic same-partition re-entry doubling escape was implemented experimentally and a self-test passed on one developer host. Treat both as design/debug feedback, **not prospective performance evidence**. Any later performance record must be run after this protocol is committed.
