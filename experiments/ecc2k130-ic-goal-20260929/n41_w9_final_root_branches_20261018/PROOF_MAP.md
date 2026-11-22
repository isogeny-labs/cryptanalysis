# Proof map for the final code/root selector

| Result | Lean declaration or finite audit | Exact hypotheses and status |
| --- | --- | --- |
| For a valid selected row, all guarded output clauses hold exactly when the code and root equal that row's table values | [`FinalRootSelector.guarded_pair_iff_selected_row`](Selector.lean) | Arbitrary finite table indexed by `Fin n`, arbitrary code and root types, selected `s : Fin n`. Checked. This proves the structural implication represented by the guarded clauses. |
| Every valid table row can be selected | [`FinalRootSelector.every_row_has_selector`](Selector.lean) | Same generic table, any row `i : Fin n`. Checked. |
| The concrete nine-bit circuit implements precisely the 284 valid rows and excludes the 228 invalid indices | [`verify.py`](verify.py) reconstructs all 14,144 intended clauses and matches them exactly to every clause mentioning a selector wire in the serialized XCNF | Exhaustive finite clause audit. A bit-level Lean model of the serialized CNF remains open. |
| The 284 table pairs are precisely the four roots of the final quartic for each of 71 allowed codes, translated from the public target and signed final source state | [Independent Sage audit](../n41_w9_target_w_bdd_20261017/audit_result.json) and [two-quartic audit](../n41_w9_two_quartic_resultant_20261017/run_result.json) | Finite N41 instance checked with frozen field, curve, source and target hashes. Full curve/source-table Lean bridge remains open. |
| Horner evaluation of the remaining preceding-pair quartic implements the exact `f(w)=0` field condition | [`DirectRoot.horner4_eq_poly4`](../n41_w9_direct_root_20261017/DirectRoot.lean) | Arbitrary commutative ring and quartic coefficients. Checked in the pinned prior module. |
| Nominal N131 guarded-output clause arithmetic | [`FinalRootSelector.nominal_n131_guard_count`](Selector.lean) | Closed natural-number equality `2^30 × (28+131) = 170724950016`. Checked with no axioms. The actual valid N131 table population is not asserted by this theorem. |

Build: `lean Selector.lean > lean_check.log 2>&1` from this directory,
using the pinned `lean-toolchain` (Lean 4.34.1). The [output](lean_check.log)
reports only `propext` for the two structural declarations and no axioms
for the arithmetic projection. The module contains no
`sorry`, `admit`, `sorryAx`, custom research axiom or native evaluation.
`lean4checker --fresh` is unavailable on this host.
