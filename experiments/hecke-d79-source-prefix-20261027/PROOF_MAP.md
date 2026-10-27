# Proof map: first-hit degree-13 prefix rank

The frozen result is conditional on the exact 40-point class, the existing base-plus-direct matrix, and the newly checked degree-13 source rows. The readable argument is: before the stopping source, a nonzero integer vector annihilates every available row, so rational rank is at most 39; an independently selected 39-row minor gives the lower bound. At the stopping prefix, an invertible 40-row minor modulo the auxiliary prime gives rational rank 40. An actual order-q class-point log vector annihilates all final rows, while an invertible 39-row minor modulo q gives rank 39 over Fq. The independent group-law audit establishes the row equations on E(Fp).

| Result | Lean declarations in `RankPrefixP<p>.lean` | Exact status |
| --- | --- | --- |
| All final rows annihilate the displayed nonzero q-log vector | `q_logs_annihilate_all_rows`, `q_logs_nonzero` | Checked for each explicit matrix and frozen log vector. |
| Every row before the stopping source annihilates a nonzero integer vector | `pre_rows_annihilate_integer_kernel`, `pre_kernel_nonzero` | Checked for each explicit predecessor matrix. |
| Selected 39 and 40 rows have invertible minors | `q_selected_in_all`, `q_selected_in_pre`, `q_minor_matches`, `q_inverse_certificate`, `aux_selected_in_all`, `aux_minor_matches`, `aux_inverse_certificate` | Checked modulo q and 7 at p8597, modulo q and 3 at p12197. The 39 selected q rows are checked to belong to the predecessor matrix. |
| First-hit rank 40 over Q and rank 39 over Fq | The checked declarations above are the finite certificates. | **Partial formalization:** the general rank implication from these certificates has not yet been encoded as a Lean matrix theorem. The written proof gives the implication. |
| Curve and Hecke interpretation of those rows | No Lean curve declaration yet. | **Partial formalization:** define the finite-field curve, the 40 class points, the degree-13 lifted fibers and trace sums, and prove the bridge from audited rows and q-logs to the Lean matrices. |

The modules use `leanprover/lean4:v4.35.0-rc4` with no external dependencies. From `formal/`, run `lake build RankPrefixP8597 RankPrefixP12197`; `build-output.txt` retains the `#print axioms` audit. Run `python3 generate.py` to regenerate and compare the committed modules against hash-pinned receipts. `lean4checker --fresh` is unavailable on this host. No `sorry`, `admit`, `sorryAx`, custom claim axiom, or native evaluation is used.
