# Miss cost in sequential three-point queries

On the public 195-coordinate M31 basis, let N=2,147,505,292 denote the finite target population. The previously enumerated two-point support has b=76,050 members. The entire three-point support has h=9,864,802 members, including all trivial inverse-pair hits. Source and counts are pinned at c062bc0cb.

The archived solve_three loops over all k=390 signed basis points on a miss, calling its two-point routine once per point. A zero remainder ends the loop successfully, so it cannot reduce a miss's cost. For independent uniform targets the expected number of misses before a hit is (N−h)/h. Even charging zero calls on the successful query, expected two-point calls per three-point hit are at least 84,510.54. Standalone two-point queries need N/b = 28,238.07 calls per hit. The lower-bound ratio is 2.99278747. This is a call-count result for that loop on that basis under the specified input distribution. Weighted average call cost, outer-loop overhead, setup and relation rank are separate timing questions.

MissCost.lean derives the bound from the first-step expectation recurrence, checks the ratio identity and verifies that the ratio exceeds 2.9927. The recurrence assumes finite expected costs and independent retries. The proof does not model a particular executable or supply its support counts.

As a separate timing check, the depth-10 two- and three-point archives use the same 1,024 structured roots, the same random roots, and identical targets for seeds 0 through 3. All three-point comparisons missed and made 1,000 calls. For the chain encoding, the observed three-point/two-point total wall-time ratios were 708.4, 1327.5, 1100.2 and 1210.5 in seed order. The runs came from separate archived panels. These figures do not measure the call costs of the smaller smooth basis or a time to first hit.

Replay the theorem with Lean 4.34.1 in the mathlib environment. For the input counts see ../m31-smooth-triples/counts.json and for the measured times see ../snapshot/algebraic/structure_results/{field31_s10,three_field31_s10}/runs.json.
