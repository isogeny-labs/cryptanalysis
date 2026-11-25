# Depth-15 reciprocal sibling census

Run `python3 census.py` to verify the archived root digest, pair each first-half root with its second-half reciprocal, recompute signed 211-smoothness and target lifting, and compare the ordered accepted coordinates with the Lean input.

| Condition | Neither | First only | Second only | Both |
| --- | ---: | ---: | ---: | ---: |
| Signed smoothness | 15994 | 207 | 181 | 2 |
| Signed smoothness and target lift | 16189 | 102 | 93 | 0 |

Skipping the second coordinate after a smooth first coordinate loses the accepted coordinate 659905380 paired with 1871385097. Testing the complete acceptance condition first permits at most 102 skipped sibling checks in frozen traversal order (0.3113% of 32768 checks). Even perfect ordering permits at most 195 skips. These are counts of predicate evaluations, with no timing assumption. Cut.lean kernel-checks that the 195-coordinate list contains no two entries whose product is one modulo M31. The finite certificate is specific to the depth-15 list.
