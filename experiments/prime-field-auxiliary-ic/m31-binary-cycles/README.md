# First binary cycle in a uniform signed graph

Reducing a signed two-coordinate row modulo 2 erases its signs. A doubling loop becomes zero. Before the first binary dependency, the edges form a forest. The first dependency occurs when the next unseen edge lies within a tree. Reduction can lower rank, so an early binary dependency need not persist over an odd field.

Use the uniform order of the k² distinct row classes from the signed-graph model. For a tree with j vertices, there are j² internal classes, of which j−1 already belong to the tree. Assign vertex signs along the unique tree paths. For each unordered pair of distinct vertices, exactly one edge sign is consistent with those vertex signs and closes a balanced cycle. Thus there are choose(j,2)−(j−1) unseen internal classes that give an odd-field dependency immediately. Loops and the unused sign of an existing tree edge are included in the total internal classes.

The recurrence in FirstCycle.lean counts signed forests by removing the tree of the smallest vertex. To count a stopping event, mark the tree containing the next internal edge, choose its vertices freely, and multiply by the forest count for the remaining vertices. Divide by choose(k²,r)(k²−r) for a prefix of r classes and its next class. Summing over r counts each first event once.

At k=17 the first binary cycle also gives an odd-field dependency with probability 0.197434 under this model. The Lean calculation checks that the total probability sums to one and encloses the balanced probability between 0.19743 and 0.19744. Independent enumeration of five-vertex binary-independent subsets and their one-edge extensions using modular ranks gave 932/8855. The graph argument and model assumptions are given above; the formal calculation checks the recurrence values.

The archived M31 v2_batch seeds 0, 1 and 2 had binary rank failures at rows (14,15), (6,7,14) and (8,9), respectively. Their first odd-field dependencies were at rows 15, 14 and 9. All row numbers are one-based. These are three fixed traces; the probability calculation uses its own sampling model.
