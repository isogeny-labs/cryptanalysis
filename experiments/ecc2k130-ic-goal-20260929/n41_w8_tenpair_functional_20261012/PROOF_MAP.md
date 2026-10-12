# Proof map for the N41 functional reciprocal-root stage

The executed circuit uses `GF(2)[t]/(t^41+t^3+1)` and the curve
`y²+xy=x³+1`. The functional S3 chart is guarded to nonzero reciprocal
inputs and outputs. This map separates the checked structural Lean lemma
from the concrete field, group, and circuit bridge that remains open.

| Result | Formalization | Verification | Exact boundary |
| --- | --- | --- | --- |
| Replacing nine S3 links by sound forward-root links preserves source membership and the selected target equation in a 19-node witness | `N41ForwardRoot.forward_relation_sound` in [ForwardRoot.lean](ForwardRoot.lean) | `lean ForwardRoot.lean`, [output](lean_check.txt); `#print axioms` reports no axioms | Conditional on `rootSound` for each link; node topology is supplied as parameters. |
| For nonzero `p=ab` and `A=1+p²`, the two roots of `Az²+pz+C=0` with `C=(a+b)²` are `z=(p/A)(H(AC/p²)+e)` when `A≠0`, with `e∈GF(2)`; when `A=0`, `z=C` | Written proof below; no faithful Lean theorem yet | Independent checked-Sage positive chart and full Boolean assignment checks | A Lean model of the exact degree-41 field, half-trace, inversion circuit, `A=0` branch, and S3 equivalence is still required. This remains **partial**. |
| All ten source states and nine root choices in the frozen positive chart sum to raw target preimage one and project to the public point | Concrete receipt, no Lean declaration | [Sage chart audit](audit_result.json) and the earlier independent [factor-base replay](../n41_w8_tenpair_density_control_20261012/audit_result.json) | Signed group law, 20 distinct folded columns, Frobenius quotient, and target projection are checked computationally. |
| The generated control and ordinary XCNFs accept the positive primary assignment | Concrete circuit receipt, no Lean declaration | [control result](control_result.json): every CNF clause and native XOR row | A gate-by-gate Lean semantics for the Karatsuba multiplier, Itoh–Tsujii inverse, half-trace, and CNF/XOR emitter remains open. |

## Written root proof

For `p=ab` and `C=(a+b)²`, expanding
`(a+b+z)²=(abz)²+abz` gives
`Az²+pz+C=0` with `A=1+p²`. Since `p≠0`, if `A=0` then
`p²=1`, hence `p=1` in the field, and the equation reduces to `z=C`.
If `A≠0`, put `v=Az/p`. Multiplying the quadratic by `A/p²`
gives `v²+v=AC/p²`. In the odd-degree field, the half-trace `H(k)`
satisfies `H(k)²+H(k)=k` exactly when `Tr(k)=0`. The two solutions
are `v=H(k)` and `v=H(k)+1`, yielding the two displayed outputs.
The circuit enforces the Artin–Schreier check and the original S3
equation. Its zero-output guard restricts it to the stated chart.

The local Lean toolchain is pinned by [lean-toolchain](lean-toolchain) to
`leanprover/lean4:v4.34.1`; [lean_runtime.txt](lean_runtime.txt) records
the actual compiler. The module uses only `Std`, and `lean4checker` was
unavailable on this host. The arithmetic and circuit bridge remains open;
the structural theorem must not be read as a formal proof of that bridge.
