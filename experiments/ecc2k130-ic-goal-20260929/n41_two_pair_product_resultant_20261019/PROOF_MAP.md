# Proof map

| Result | Lean or computational evidence | Exact scope and open bridge |
| --- | --- | --- |
| A common root of two characteristic-two quadratics forces their determinant-form resultant to vanish, including zero leading coefficients | [`QuadraticResultant.common_root_implies_zero`](QuadraticResultant.lean); Lean 4.34.1 `lean.stdout` prints only `propext`, `Classical.choice`, `Quot.sound` | Faithful for any field with `∀x, x+x=0`; no curve assumptions. |
| Eliminating the two N41 pair-output reciprocals from their source quadratics and S3 yields the 37-term `R(p,q,t)` with degrees `(4,4,8)` | Checked-Sage [`derive.py`](derive.py), frozen [protocol](derive_protocol.json), [coefficients](resultant.json), [runtime receipt](sage_runtime_info.json) | The full two-stage elimination and equality to the 37-term expanded polynomial are not yet formalized in Lean. This is the central open formalization bridge. |
| Source-valid pair sum implies `R(p,q,t)=0` | Quadratic-resultant lemma supplies the elimination implication; checked-Sage source reconstruction and S3 group replay in [verify_result.json](verify_result.json) and [holdout_verify_result.json](holdout_verify_result.json) | A Lean definition connecting the binary curve's reciprocal x coordinate, source pair law, and S3 to the expanded `R` remains open. |
| The frozen N41 holdout has one valid zero for each member and none for each nonmember | Exhaustive 4,964-code-pair-per-key checked-Sage census; independent SAT model and group replay in [holdout_replay_result.json](holdout_replay_result.json) | Finite-instance certificate, not a general sufficiency theorem for the resultant. |

The proof build used the pinned [`lean-toolchain`](lean-toolchain).
`lean.stdout` retains the exact `#print axioms` result; `lean.stderr` is empty.
The reported Lean theorem contains no `sorry`, `admit`, custom research axiom,
or native-evaluation bypass. The full algebraic-to-curve theorem remains
partial at the precise bridges identified above.
