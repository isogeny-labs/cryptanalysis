# Highest-degree span and projection proof map

Write the first and second source products as binary-linear forms
`p=p₀+Σ x_i P_i` and `q=Σ y_j Q_j`, with Boolean code bits. In
characteristic two, the coefficient of `x_i x_j` in `p³` is
`A_ij=P_i²P_j+P_iP_j²`; the corresponding coefficient of `y_u y_v` in
`q³` is `B_uv=Q_u²Q_v+Q_uQ_v²`. In the frozen 13-term resultant, the
only term that can contribute a monomial quadratic in both source-code
families is `c₃₃ p³q³`. Its degree-four coefficient is therefore
`c₃₃ A_ij B_uv`. A constant first-code block offset changes lower
degrees but leaves this coefficient unchanged.

| Step | Evidence | Status |
| --- | --- | --- |
| Source cube expansion | `JointSourceExpansion.weighted_cube` and `joint_resultant_expansion` in the [preceding Lean module](../joint_block_gb_20261018/JointSourceExpansion.lean) | Kernel checked under `2=0` and Boolean-weight hypotheses |
| Frozen 13-term support and nonzero `c₃₃` | [N41 coefficient input](../n41_w11_freecode_resultant_20261018/resultant_input.tsv), [N131 coefficient export](../n131_w33_freecode_resultant_20261018/coefficients.json), [rank producer](rank.py) | Computationally checked for both target indices |
| Exact coefficient ranks | [binary-field producer](rank.py), 131 or 41 independent stored pivots where full rank is reported, and independent [Sage field/matrix audit](audit_result.json) | Complete finite-rank computation on frozen instances |
| Full span has zero annihilator | `TopDegreeSpan.full_span_annihilator_zero` in [TopDegreeSpan.lean](TopDegreeSpan.lean) | Kernel checked, with explicit additive-map and finite-sum span hypotheses |

The written structural implication is: if the degree-four coefficient
vectors span the whole binary output space, any additive output map
that kills every degree-four coefficient is zero on every output.
Hence no nonzero binary-linear combination of the field-coordinate
equations makes this resultant degree at most three. The result does
not constrain nonlinear combinations, combinations that retain some
degree-four terms, or another point-decomposition encoding.

The pinned toolchain is `leanprover/lean4:v4.34.1`. The command
`lean TopDegreeSpan.lean` built the theorem, and
[lean_check.log](lean_check.log) records `#print axioms`: only
`propext`, `Classical.choice`, and `Quot.sound`. The theorem source
contains no `sorry`, `admit`, `sorryAx`, custom research axiom,
`unsafe`, native proof shortcut, or kernel bypass.
`lean4checker --fresh` was unavailable.

The connection from the concrete 131-bit pivot list to Lean's
`fullSpan` predicate, and the exact coefficient-extraction identity
for the full frozen polynomial, are not yet formalized as Lean
declarations. The former is checked by two independent rank
implementations; the latter follows from the cube expansion and is
checked by the producer's term support. The formalization of these
concrete bridges is partial and remains open.
