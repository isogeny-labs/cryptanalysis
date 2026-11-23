# Exact signed-triple coverage on the archived M31 curve bases

On the curve y² = x³ + 2x + 14 over the field of order 2,147,483,647, the auxiliary and plain 500-point bases cover 160,361,708 and 160,352,874 group elements, respectively. Coverage means representability by three signed basis terms, allowing repeated indices. The denominator for a uniform group query is the archived group order 2,147,505,293.

| Outcome | Number of group elements |
|---|---:|
| Both bases | 11,978,578 |
| Auxiliary only | 148,383,130 |
| Plain only | 148,374,296 |
| Neither | 1,838,769,289 |

The four counts partition the group. The auxiliary basis has a net advantage of 8,834 elements, or 0.000411361 percentage points of uniform coverage. With 5,000 trials whose marginal distributions are uniform, the expected excess is 0.02057 auxiliary hits. Linearity of expectation suffices. The observed differences of −7, +27, and +24 on the three archived walks concern different quantities from that population difference.

## Replay and checks

Run `python3 replay.py` with a C++20 compiler. The script retrieves both exact public inputs and the arithmetic header from Git revision efb9330c1ee7e30743b7674f686cccb49f1cb25e. Only the basis points enter the census. The first traversal evaluates every unordered triple of signed terms with the archived batch arithmetic. The second uses scalar addition, visits the canonical descriptions in [TripleCoverage.lean](../m31-reflection-count/TripleCoverage.lean), and uses sign symmetry. The two traversals must agree on every occupied abscissa and on the identity flag for each basis. They share the field operations. Each finite output is checked against the curve equation and checked to have nonzero ordinate. Neither set contains the identity, as also follows from the even output counts.

[AffineCount.lean](AffineCount.lean) proves that doubling the number of occupied abscissas counts all affine points of any sign-closed set satisfying the curve equation and with no fixed points under sign change. This applies also to the intersection of the two sign-closed sets; for a common abscissa both roots occur in both sets. The native traversals determine the occupancy counts. Replay the theorem with `lake env lean /absolute/path/to/AffineCount.lean` in the same mathlib project as the sibling certificate.
