# CT136 protocol — same-host batched-inversion rho control

Date 2026-11-15. Scope: **[pcc:unverified]**. Regular stacked child of cryptanalysis #1546 (CT135); root crypto #3877. Protocol is committed before prospective holdout runs. This does not modify or replace CT125–129/695/701 Jacobian fixtures, index-calculus code or the signed PCC ledger.

## Question, mathematics and fixed inputs

Test whether amortizing affine elliptic-point additions with Montgomery's product-of-denominators batch inversion closes the measured CT135 fourfold-rho gain, when the identical optimization is made available to the source and mapped-target arms. This only changes group-operation implementation, **not** the search-space order. The unchanged public curve is E/F_p: y^2=x^3+622683939x^2+2147483024x, p=2147483033, prime subgroup q=536857417, G=(911976709,415929193). Its degree-two isogeny maps to T: y^2=x^3+9x, H=(180482573,1535800095). Target alpha(x,y)=(-x,i*y), i=392507391, scalar eigenvalue lambda=390258842; source has only ± points as directly available degree-one automorphisms. Verify all these identities before any timed target.

## Five cold arms on identical public inputs

0. **source BSGS** fresh baby table for every Q.
1. **source negation-fold rho** existing CT135 32-jump affine reference.
2. **mapped target fourfold rho** existing CT135 affine reference (include phi(G), phi(Q)).
3. **source negation-fold rho, batch32**: 32 independent walk lanes per Q, one modular inverse per 32 denominators using the prefix-product trick, complete cold jump/setup and collision memory, individual scalar verification.
4. **mapped target fourfold rho, batch32**: identical batch implementation, except target fold and mapping phi(G), phi(Q) inside timer.

The batched arms must keep exact true scalar coefficients after folding, count *all* 32 lanes' group operations, precomputed jumps and inversions, and include map+verification and memory. Every collision is verified on original source. No scalar leakage or using k as a solver hint. Always report best matched source / best matched target, **including BSGS and affine references**, not just an isolated kernel throughput. Record if batching reduces or reverses the earlier advantage. Batch source versus unbatched target is diagnostic only; **both** optimized arms are required for a fair headline.

## Prospective fixed population and controls

Four as-yet-unused seeds **20261230, 20261231, 20261232, 20261233**, exactly **64 distinct nonzero public Q** per seed, ten complete solves (two repeats for five arms) per target. Alternate ABCDEEDCBA / EDCBAABCDE order across target indices; no selection or deletion of failing cases. The source generator and public scalar sequence is exactly CT135's frozen std::mt19937_64 construction. Both seed and all outputs must be reproduced by a separate Python arithmetic auditor; independent verified recovery of the same k, map, curve/order, operation counter schema, row order, every summary and raw identity are acceptance gates. Negative controls must reject corrupted scalar, public point, totals, row/arm, missing row, and timing under ordinary and `python3 -O`.

Build with `g++ -O3 -std=c++17 -Wall -Wextra -Werror` on the same CPU; retain compiler/OS/cgroup, raw stdout/stderr, SHA-256, independent audit, peak RSS, and per-arm ns, iterations, additions, inversions, restarts and states. Bounded at 6 restarts × 200000 rho transitions and 32 lanes (zero success is a valid negative, **never silently censor**). Run exploratory development seeds only before prospective holdout. GitHub-hosted CI is bounded to 15 minutes and uses no paid EKS/Spot. A/A controls and host/environment variability remain limitations if not separately performed.

## Decision criteria / limits

Any complete-source speed ratio above 1 must survive the strongest matched optimized source rho and IC, full 695/701 Jacobian corrections and original-prime cold setup/memory/linear algebra, matched independent PCC with a signed verdict, not merely this toy CM-neighbor test. This protocol **cannot** establish that broader success. If the source batch wins or is statistically indistinguishable, preserve the negative result and prioritize original-prime C169/C13a/C13b/D cold native pricing in #1534 and non-generic IC. If mapped batch wins, verify independent hosted replay and then move to the same full original-prime gates. No paid compute, protected merge, or automatic cost promotion.

Checked: crypto #3877/#4215; cryptanalysis #1523/#1534/#1545/#1546; crypto #4178 (GPU IC throughput-vs-rho gap); original CT135 C++/independent Python source; repo AGENTS; prior CT134 source-side CM pullback. Shared research-KB and local lead-atlas were not accessible from this runtime; no novelty or exhaustion claim.
