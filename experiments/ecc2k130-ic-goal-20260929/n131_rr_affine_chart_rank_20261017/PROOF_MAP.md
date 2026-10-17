# Proof map

Toolchain: `leanprover/lean4:v4.34.1`, pinned in `lean-toolchain`.
`lean SpanObstruction.lean` exits 0. `#print axioms` reports only `propext`
for `fold_annihilated` and `constant_in_span_not_separable`. The theorem
source was carried forward unchanged from the earlier RR code-family
experiment; it has no `sorry`, `admit`, custom research axioms, or native
evaluation.

| Statement | Declaration or check | Exact scope |
| --- | --- | --- |
| A linear functional annihilating a span annihilates each XOR combination; a constant in that span cannot be separated | `SpanObstruction.fold_annihilated` and `constant_in_span_not_separable` | Abstract GF(2) words and the stated linearity hypotheses |
| The fourth chart's nonconstant coefficients span the full 131-bit field representation | `screen.py` rank basis, independently replayed by `audit_sage.py` | Frozen target, five fixed points, first two affine codes and both x roots |
| Sign ANF has no terms above degree three | Producer coefficient check and independent Sage Möbius replay | All eight selected 64-sign charts |
| Nonzero determinant outcomes match the actual curve equation | `audit_sage.py` determinant values and `group_audit_sage.py` direct sums | All 512 frozen sign assignments with seven distinct x coordinates |
| Four first-slot codes form a source-valid affine selector square with distinct folded columns | `prepare.py`, separate source/curve reconstruction in `audit_sage.py`, and independent orbit-key calculation in `column_audit_sage.py` | Masks `(3,515,1027,1539)`, seed `898618`, and all 18 selected/fixed columns |

The elliptic divisor criterion connecting a zero `L(7O)` determinant to a
seven-point group sum is used in the written argument and checked on these
512 assignments by independent curve addition. Its full concrete curve and
divisor formalization in Lean remains open. The Lean theorem proves the
structural rank obstruction, not the finite rank calculation or source
table construction.
