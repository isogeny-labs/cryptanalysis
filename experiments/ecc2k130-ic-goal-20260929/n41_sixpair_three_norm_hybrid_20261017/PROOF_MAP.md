# Proof map for the six-slot hybrid

| Mathematical statement | Formal declaration / concrete bridge | Status |
| --- | --- | --- |
| Grouping six pair outputs into left and right triples preserves their ordered sum. | `HybridStructure.two_triples_are_six_sum` under `AddCommGroup`; Lean 4.34.1 `#print axioms` reports only `propext`. | Checked structural theorem. |
| If both source families are closed under negation, a group sum matching either orientation of the public point can be oriented to the public point. | `HybridStructure.orient_target` under explicit family-closure and `left+right=Q ∨ left+right=-Q` hypotheses; `#print axioms` reports only `propext`. | Checked structural theorem. |
| A common root of the two S3 quadratics makes the four-summation resultant vanish. | Prior `n41_three_code_nested_norm_20261015/QuadraticResultant.commonRootImpliesZero` under `CommRing` and characteristic two; prior checked Lean build. | Reused checked theorem. |
| Three-source nested norm eliminates its eight quadratic x-root choices exactly. | Prior `n41_three_code_nested_norm_20261015` written quadratic-algebra norm derivation and checked field/group panels; current independent Sage audit checks all 240 source quadratic roots and eight 64-state triples. | Concrete finite source bridge checked; full Lean norm theorem remains open. |
| The reciprocal S3 equations describe elliptic addition, including the sign branches and nonexceptional chart. | Current independent Sage replay of the archived six-pair target; prior direct-leaf `n41_s3_rationality_propagation_20261017` curve/S3 audit. | Concrete control checked; full curve-to-circuit Lean bridge remains open. |

The public XCNF leaves all six seven-bit source codes free. `audit_formula.py`
rebuilds it byte for byte and checks all 42 code wires. `build.py` checks a
complete assignment from the archived relation against every emitted CNF and
native-XOR row. These computational checks are separate from the structural
Lean theorems; a future SAT model needs its own independent curve replay.
