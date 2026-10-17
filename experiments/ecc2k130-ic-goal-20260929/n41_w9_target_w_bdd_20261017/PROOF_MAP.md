# Target-translated final-pair domain proof map

For each final pair source state `E` with canonical code `c`, the frozen
public target `Q` determines one residual `P=Q−E`. In every recorded
state, `P` is finite and has nonzero x-coordinate. Put `w=1/x(P)`.
The exact table consists of the 284 triples `(w,c,state_id)`; all 284
`w` values are distinct. Consequently `w` determines the final code on
this source and target.

Let `R_c(W)` be the final-pair resultant for code `c` from the checked
[rootless theorem](../n41_w9_code_linear_tower_20261017/PROOF_MAP.md).
The addition law makes every translated table value a root of `R_c`.
The independent [Sage audit](audit_result.json) checks, for **each** of
the 71 allowed codes, that `R_c` has degree four and that its complete
field-root set is exactly the four distinct `w` values in the table.
The elementary degree bound then proves there are no additional roots.
Thus the table is equivalent to the final link after existentially
choosing its source code and signed state, in the audited nonexceptional
chart. The original resultant and source collision clauses remain in
the augmented formula.

The BDD uses the natural bit order `0,…,40`. At each node it partitions
the remaining table values by the next bit and imposes the exact
Shannon equation `output ↔ (bit ? high : low)` with Tseitin clauses.
The root is required true. By induction over the 41 levels, the root is
true exactly for one of the 284 table values. The builder evaluates all
284 positive assignments through every emitted clause, and the
independent table/root audit checks the mathematical set being encoded.

| Result | Formal or computational evidence | Scope/status |
| --- | --- | --- |
| Split-root resultant exactness | `FinalPairResultant.resultant_zero_iff_source_root` | Checked Lean theorem in predecessor; split allowed source |
| Four split factors have no other field roots | `TargetWDomain.split_quartic_exact` | Checked Lean structural implication; standard foundations only |
| Every allowed code has exactly four listed target `w` roots | `audit_roots_sage.py`, `audit_result.json` | Independently checked Sage over the exact N41 field and public point |
| BDD encodes the listed finite set | `build.py`, `build_result.json` | Exact recursive construction; emitted-CNF bridge checked computationally |

`lean TargetWDomain.lean` succeeded with pinned Lean 4.34.1;
[`lean.stdout`](lean.stdout) reports only `propext`,
`Classical.choice`, and `Quot.sound` under `#print axioms`.

The concrete quartic factorization certificates and the curve
addition-to-`S3` bridge are not kernel-checked Lean declarations here.
The full curve-specific theorem remains a partial formalization, with
those exact finite-field and elliptic-curve obligations open. The
readable proof above identifies the assumptions and the independent
checks used for the current experiment. The pinned toolchain is
`leanprover/lean4:v4.34.1`.
