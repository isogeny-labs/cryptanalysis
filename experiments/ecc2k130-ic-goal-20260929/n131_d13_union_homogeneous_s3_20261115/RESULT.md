# Homogeneous S3 encoding for the N131 adjacent-union source

The three-chart homogeneous identity is checked in
[Lean](HomogeneousS3.lean) and retains the exact S3 zero set whenever its
three chart denominators are nonzero. For an adjacent-branch d13 source
leaf, set `n=phi+b*phi²` and `d=1+b*(phi²+phi)`, with Boolean `b`.
The prior exact census establishes `phi != 0` and
`1+phi²+phi != 0` on every valid selector, so the chart denominator
is nonzero for both branches. The [proof map](PROOF_MAP.md) records the
field and curve bridges.

The homogeneous circuit carries each leaf as `(n,d)` and uses
`U=n²+nd=n(n+d)` inside the nine S3 links. In characteristic two,
`n+d=1+phi+b*phi`, so a leaf's `U` can be formed from sparse
13-bit selector products. Every S3 link clears denominators with the
Lean-checked identity. The source bits, branch bits, partial charts, and
four official-point cofactor endpoints follow the same frozen input law
as the prior ten-leaf formula.

The complete [official-point XCNF](official_q_homogeneous_m10_v1.xcnf)
builds at **431,497 variables, 331,029 clauses, and 333,883 native XOR
rows** (17,149,886 bytes). The prior exact branch formula has
337,789 variables, 309,161 clauses, and 246,591 XOR rows
(14,521,119 bytes). This implementation is therefore larger in every
recorded formula-size measure: approximately 27.7% more variables,
7.1% more clauses, 35.4% more XOR rows, and 18.1% more bytes.
These are exact source-bound formula counts, not solver runtimes.

A [complete planted assignment](planted_result.json) with both branch
values passed all 332,220 clauses after 1,191 primary pins and all
333,883 XOR rows. The frozen witness was independently group-replayed
in the prior [Sage audit](../n131_d13_union_m10_formula_20261115/sage_result.json).
This establishes circuit correctness on that control. The cost screen
rejects this straightforward homogeneous encoding for an ordinary
solver run: its complete formula exceeds the existing verified circuit.
A useful revision would need to reduce the full S3-link product cost,
then repeat the same formula and planted gates before public-point
measurement. The proposal retains `candidate_id: null`.
