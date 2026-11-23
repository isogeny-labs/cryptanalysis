# Exact two-point coverage after M31 smoothness filtering

For a base with m liftable x-coordinates on this odd prime-order target curve, include both signs of each point. There are (2m)(2m+1)/2 unordered pairs allowing repeats. Exactly m pairs sum to infinity. Therefore at most 2m² distinct finite group points can be covered. Counting distinct sums gives the exact probability of a hit under the uniform finite-target distribution.

All four bound-211 filtered bases attained the maximum. The three deterministic uniform subsets of the same cardinality drawn from each parent liftable base attained it as well. The structured signed case covers exactly 76,050 of 2,147,505,292 finite group points. For independent uniform draws the expected wait for the first hit is 28,238.07 queries. This is a distributional calculation, with no timing or rank assumptions. A different set of 195 liftable coordinates cannot improve this two-point coverage ceiling.

The canonical representative is x in [1,p−1]; the signed representative is min(x,p−x). The smoothness test bounds every prime factor of the representative by 211. The runner checks every unordered pair, the count of inverse pairs, and invariance of multiplicities under negation. A positive control on ±{P,2P,3P} has 18 finite representations but only 12 distinct sums. This checks that the counting procedure detects genuine collisions.

Run `uv run --isolated --with sympy --python 3.13 python replay.py` and compare stdout with counts.csv. Multiplicity.lean proves the per-sum collision bound and its equality for multiplicities one and two. The particular coverage values come from exhaustive group addition on the pinned archive.
