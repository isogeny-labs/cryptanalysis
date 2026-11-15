# CT134 protocol — source-side transported CM control (frozen before new code)

2026-11-15 · [pcc:unverified] · stacked on CT133 #1542, CT132 #1541, root crypto #3877.

## Purpose
CT133 found a scoped ~1.33x independent-host speed advantage for an explicit isogeny to a j=1728 curve over two *portable* source solvers, but no source-side conjugated-CM comparison. We must test that control before claiming any intrinsic transfer speedup. Do not change the 695/701 Jacobian fixtures, CT133's four original panels, protocol, benchmarks or raw evidence.

## Frozen mathematical experiment
Source E: y²=x³+622683939 x²+2147483024 x over p=2147483033, subgroup order q=536857417 and G=(911976709,415929193). Target T: y²=x³+9x, H=(180482573,1535800095). Use CT133's phi to T, and independently reconstruct the normalized dual psi by undoing the target x-shift and x/4,y/8 scaling, applying raw degree-2 Vélu with a'=-2a, b'=a²-4b, then dividing x by 4 and y by 8.

For alpha_T(X,Y)=(-X, iY), i=392507391, lambda=390258842 mod q, define beta=psi alpha_T phi and A_q=[(q+1)/2] beta on E[q]. On this subgroup expect beta=[2 lambda], beta²=[-4], A_q=[lambda], A_q²=[-1], phi psi=[2] and psi phi=[2]. Check the 7 fixed boundary scalars {1,2,3,17,12345,456789,q-1} plus 16 seeded random scalars. Check all point memberships, kernel behavior, zero/exceptional handling and subgroup order; fail closed, including Python -O.

## Timings and acceptance
Bounded single-host, interleaved ABBA/BAAB point-map microbenchmark for source A_q vs target alpha_T (same pinned input points), reporting raw samples and **counts** of source group additions/inversions. Microbenchmark only: do NOT call it a complete-solve speedup or a lower bound for every possible source implementation. An independent same-host *complete* source rho using A_q, strongest optimized source rho, BSGS and IC, plus actual Jacobian setup/corrections and C169/C13/D remain necessary before owner acceptance. No paid EKS/Spot.

## Logical obstruction (conditional on standard automorphism classification)
Since char p > 3 and j(E)=287496 is neither 0 nor 1728, Aut(E) fixing infinity has only +/-1. Therefore no order-4 **degree-one algebraic automorphism** exists on E; A_q is an efficiently computable group action on E[q] only through a higher-degree map plus subgroup inversion of [2]. This does NOT rule out a faster optimized source solver, a degree>1 endomorphism, or a benefit from using the target representation.

## Sources/limitations
Reviewed active CT130–133 #1539–1542, CT126 #1534, root #3877; standard Vélu duals and finite-field isogeny homomorphisms (see https://www.math.u-bordeaux.fr/~damienrobert/pro/publications/reports/SQISign-nist2-spec.pdf), CM/GLV literature. Research-KB MCP and checkout-local catalog unavailable in this runtime; no novelty/absence claims. All new execution and PCC standing remain unverified until separately audited.