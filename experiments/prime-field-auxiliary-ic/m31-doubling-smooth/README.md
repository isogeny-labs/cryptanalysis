# Curve duplication on smooth M31 coordinates

At bounds 47, 67 and 89 use the set S of all positive smooth integers below p, including even representatives. For every x in S compute the x-coordinate duplication formula on y²=x³+2x+14. Count how many outputs lie in S. Compare with translations of those outputs by 1, 101 and 65537 modulo p and the exact all-translation mean |S|²/p. This comparison concerns ordinary integer smoothness.

Join x to its unshifted output when both lie in S. Count successful component merges. For this graph, knowing one lift label per component suffices, so the number of merges measures the exact reduction in separately evaluated labels achievable by using just these equalities. Check each retained edge with independent Euler tests on both endpoints. Costs of edge discovery are excluded from the label-count saving. No timing claim.
