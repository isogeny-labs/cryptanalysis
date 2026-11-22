# Pairwise dependence in the M31 walk model

The frozen curve uses the coordinate field of order 2147483647 and the prime group order N = 2147505293. The probability calculations use the latter. Consider a fixed query horizon, extending the walk through that horizon even if collection would have stopped earlier.

## Sampling assumptions

In the ideal model the 32 shared step elements and all lane starts are independent uniform points. Fix any schedule of step indices determined independently of those elements. For two observations on one lane fewer than N updates apart, the changes in step multiplicities are nonnegative and sum to the positive lag. Some step has a multiplicity change strictly between zero and N. Fix all other steps. In group scalar coordinates the observations are (u + av + s, u + bv + t), with u the uniform lane start, v the selected uniform step, and a ≠ b. The Lean equivalence proves this map permutes all ordered pairs. For different lanes, conditioning on all steps leaves two independent uniform starts translated by constants. Both arguments give the same uniform pair law for every admissible schedule.

Higher joint independence already fails for a schedule that selects the same step twice consecutively. The three observations then obey X₀ + X₂ = 2X₁. With independent uniform step indices this happens with probability at least 1/32, compared with 1/N for three independent uniform group elements. The archived implementation uses a single seeded mt19937_64 generator for both modularly reduced coefficients and table indices. The ideal model gives no probability guarantee for any particular archived seed.

## Fixed-horizon bounds

Let H count query points in a fixed hit set of mass h. Pairwise independence gives E[H(H−1)] = q(q−1)h² by summing the ordered pairs of distinct hit indicators. The audit requires at least three distinct contributing rows, so H ≥ 3 is necessary on the frozen one-row-per-query path. Hence its success probability is at most q(q−1)h²/6. Using the upper bound h ≤ 2k²/N gives the following necessary budgets. The median floor is the smallest integer q for which the probability upper bound reaches one half.

| Coordinates k | Upper probability at q = 100000 | Median query floor |
|---:|---:|---:|
| 17 | 0.012074% | 6435275 |
| 20 | 0.023129% | 4649486 |
| 32 | 0.151578% | 1816206 |

For the frozen 17-coordinate hit set of size 578 and the retrospective seed-1 horizon q = 19300166, 14 distinct rows require H ≥ 14. The integer polynomial (H−4)(H−5) is always nonnegative and at least 90 on that event. Its expectation is q(q−1)h² − 8qh + 20. Dividing by 90 gives an upper probability of 6.030156%. This calculation uses the exact hit mass in both terms. It bounds a raw hit count at a selected horizon and supplies neither an estimated runtime nor a significance test for the generator.

Pairwise.lean verifies the affine equivalence, the two pointwise majorants and the finite weighted sum inequality for the 14-hit threshold. The sampling argument, moment expansion and translation to query budgets are given above.
