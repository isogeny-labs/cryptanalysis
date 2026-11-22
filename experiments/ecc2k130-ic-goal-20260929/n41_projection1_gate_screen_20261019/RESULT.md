# One-coordinate resultant gate screen

Selecting one field coordinate, bit 5, from each of the two factored
resultant nodes and pruning all unreachable definitions retained **20,791 of
22,155 AND gates**, or 93.84%. The constructed ordinary N41 public-point
witness passes the complete projected formula. The screen therefore shows
that even the weakest single-coordinate projection leaves a larger nonlinear
circuit than the earlier 13,407-AND `table5` encoding.

This screen uses the same field, W9 source tables, five-pair addition tree,
oriented raw public point `(2105655159232,891719206310)`, and reference
assignment as the [24-coordinate run](../n41_projection_fivepair_resultant_20261019/RESULT.md).
The one coordinate is the first index of the same frozen affine permutation
`(17i+5) mod 41`. The [build receipt](build_result.json) records 68,289 CNF
clauses and 3,285 XOR rows before slicing. The [slice receipt](slice_result.json)
records 20,791 retained AND gates, 3,026 retained XOR definitions, and 24,021
reachable variables. The [audit](audit_result.json) checks both frozen
protocols, 13 source hashes, formula hashes, and the constructed witness.

The one-coordinate formula was used for circuit-size screening. The
measured 24-coordinate query remains the relevant capped solver row. The
next method change must remove field products themselves or reject source
families before constructing the complete five-pair circuit.
