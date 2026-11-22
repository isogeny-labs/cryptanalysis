# Proof map: RR function selectors

Pinned toolchain: `leanprover/lean4:v4.34.1` in `lean-toolchain`. Build from this directory with `lean FunctionSelector.lean`; recorded standard foundations are `propext`, `Classical.choice`, and `Quot.sound`. The command output is `lean_check.stdout`; `lean_check.stderr` is empty. `lean4checker --fresh` was unavailable on this host.

| Mathematical statement | Lean declaration | Exact scope | Status |
| --- | --- | --- | --- |
| A nonzero 7-vector has a first nonzero entry | `FunctionSelector.first_nonzero` | Arbitrary field `K`, `Fin 7 → K` coefficient vector with an explicit nonzero entry | Checked |
| Scaling at that entry sets it to one and earlier entries to zero | `FunctionSelector.normalized_chart` | Arbitrary field `K`, specified first nonzero coordinate | Checked |
| Scaling a linear evaluation scales its value | `FunctionSelector.dot_scale` | Arbitrary field `K`, finite list of coefficient/row pairs | Checked |
| Scaling preserves a vanishing evaluation | `FunctionSelector.scaled_zero` | Arbitrary field `K`, finite list with evaluation zero | Checked |
| Sequential prefix clauses prevent any two selected states | `FunctionSelector.sequential_amo_sound` | Arbitrary selected and prefix predicates over natural positions satisfying forward, propagation, and exclusion implications | Checked |
| Seven distinct affine points on `y²+xy=x³+1` satisfy the group relation exactly when some nonzero `f ∈ L(7O)` vanishes at them | No Lean declaration | Curve and divisor-group bridge, including rationality and point distinctness | Open formalization obligation; written proof in `RESULT.md` |
| The Boolean/XOR circuit is equivalent to six source point selections and seven vanishing evaluations | No Lean declaration | Concrete XCNF gate semantics and source table | Witness assignment checks every generated row; general circuit equivalence remains an open formalization obligation |

The projective normalization proof preserves all seven possible leading-coefficient charts. It does not assume that the known witness lies in chart zero when making the completeness statement.
