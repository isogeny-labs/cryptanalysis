# Proof map for the final-pair two-quadratic gate

Write the fixed-seed source-pair equation as `C u²+p u+H=0`, with `C≠0`,
and the target S3 link as `A u²+B u+D=0`, where for public reciprocal `t`
and shared root `w`, `A=1+(tw)²`, `B=tw`, `D=t²+w²`. Let `L=A p+B C`
and `M=A H+C D`. In characteristic two, multiplying the pair equation
by `A` and the link by `C` gives `L u+M=0`. The exact eliminant identity is

`C·g(w) = C M²+p M L+H L²`,

where `g(w)=A D p²+B M p+M²+C H B²`. If both quadratics hold, then
`M=L u`, so the right-hand side is `L²(C u²+p u+H)=0`. Since `C≠0`,
`g(w)=0`.

For the converse, if `L≠0`, `u=M/L` is the only candidate and the same
identity makes it satisfy the pair equation; `L u+M=0` then gives the S3
equation. If `L=0`, `g=0` implies `M=0`; any field root of the pair equation
then satisfies the S3 equation. This last case requires the pair quadratic
to split in the field. The frozen N41 audit checked two distinct pair roots
and two distinct S3 roots for every allowed code, including all signed
states. Both directions of this elimination equivalence are Lean-checked
under their exact hypotheses.

| Result | Proof or audit | Exact status |
| --- | --- | --- |
| Two quadratics imply zero of the preceding quartic eliminant | [`PairQuadratics.common_root_implies_eliminant_zero`](PairQuadratics.lean) | Checked under an arbitrary field with explicit `∀x, x+x=0`, `C≠0`, and both quadratic equations. |
| Zero eliminant plus split pair quadratic implies a common root, including `L=0` | [`PairQuadratics.eliminant_zero_implies_common_root`](PairQuadratics.lean) | Checked under an arbitrary characteristic-two field, explicit `C≠0` and existence of a field root of the source-pair quadratic. The exact N41 split condition is independently checked by [`audit_sage.py`](audit_sage.py). |
| Every allowed N41 final code gives exactly two pair roots and four target roots equal the independently translated signed-state table | [`audit_result.json`](audit_result.json) against the prior [all-code root audit](../n41_w9_target_w_bdd_20261017/audit_result.json) | Checked for all 71 codes and 284 signed states, with no zero-leading S3 case. |
| The Boolean circuit preserves the exact source condition | [`build_result.json`](build_result.json) and [`verify.py`](verify.py) | One complete archived satisfying assignment, 32 rejected reachable controls, exact XCNF count and 163 unpinned inputs. The field/curve/source-table to Boolean-gate Lean bridge is open. |

Build: `lean PairQuadratics.lean > lean_check.log 2>&1` from this
directory with pinned Lean 4.34.1. [`#print axioms`](lean_check.log) for
both declarations reports only `propext`, `Classical.choice`, and
`Quot.sound`. The checked module has
no `sorry`, `admit`, `sorryAx`, custom research axiom or native evaluation.
`lean4checker --fresh` is unavailable on this host.
