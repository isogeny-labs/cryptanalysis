# First dependence in uniform signed two-point rows

For k public coordinates we model one doubling row per vertex and two relative signs per unordered pair, giving k² row classes up to overall sign. Assume that every row class is hit by two distinct group points, all these pairs are disjoint, each query is an independent uniform draw in a group of order 2,147,505,293, and repeated classes are discarded. The stopping event is the first linear dependence in these rows over a field of odd characteristic. Timing, nonuniform walks and any checks after the first dependence fall outside this model.

| Coordinates | Mean distinct rows through first dependence | Mean eligible hits including repeats | Mean uniform queries |
|---:|---:|---:|---:|
| 17 | 12.824 | 13.108 | 48,700,442 |
| 20 | 14.594 | 14.862 | 39,894,018 |

The expected query-count ratio is 1.22075. The corresponding hit-rate ratio alone is 400/289, or 1.38408. Dense rank checks of successive prefixes in the archived v2_batch records for field31_s5_base0 put the first dependence at rows 15, 14 and 9 for seeds 0, 1 and 2. The three observations do not establish the sampling assumptions.

## Counting independent subsets

Represent each row by an edge. A doubling gives a loop with coefficient 2. A connected tree on j labeled vertices contributes j−1 independent edges, by leaf elimination. A connected component with exactly one cycle contributes j independent edges precisely when that cycle is unbalanced. Removing attached trees leaves a cycle matrix with determinant ±2 in the unbalanced case and zero in the balanced case. This includes a doubling loop and a pair of oppositely signed parallel edges. More than j edges force dependence.

There are 2^(j−1) j^(j−2) signed trees, with the one-vertex case counted as one. For a component with a single cycle, choose its vertices and then attach a rooted forest. On a chosen set of l cycle vertices the number of unbalanced signed cycles is one for a loop or a parallel pair, and (l−1)! 2^(l−2) for l ≥ 3. When j > l the number of signed forests rooted at those vertices is l j^(j−l−1) 2^(j−l). When j = l it is one. The implementation counts loops separately as j choices of attachment vertex on a signed tree. Decomposing at the connected component of the smallest remaining label counts each independent subset once.

For r distinct classes already seen, the probability of still having independent rows is the independent r-subset count divided by the number of all r-subsets. Conditional on reaching this stage, the mean wait for the next unseen row is the group order divided by 2(k²−r). Summing the products gives the expected query count through the first dependence.

Counts.lean checks exact rational bounds on the numerical ratio computed by this recurrence. The graph-counting argument above is a mathematical derivation. As an independent finite check, exhaustive modular row-rank enumeration agreed at every subset size through k = 5, where the counts for sizes 0 through 5 were 1, 25, 300, 2,220, 10,410 and 25,218. Check the file with Lean 4.28 and matching Mathlib using `lake env lean /absolute/path/to/Counts.lean`.
