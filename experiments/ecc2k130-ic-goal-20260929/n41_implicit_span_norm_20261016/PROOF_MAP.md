# Implicit N41 span-norm proof map

| Statement used | Formal declaration or evidence | Hypotheses and status |
| --- | --- | --- |
| A finite product is zero exactly when one factor is zero | `JointNorm.product_zero_iff` in `../n41_joint_fourpair_resultant_20261012/JointNorm.lean` | Abstract integral-domain-style hypotheses are explicit; predecessor Lean build and `#print axioms` passed |
| `Res_r(H,L_V)` equals the product of `H(v)` over all roots `v` of monic split `L_V` | Readable split-resultant proof in `RESULT.md`; rank-three Sage/native coefficient equality | General polynomial-resultant theorem is not available in this local Std-only Lean toolchain; formal bridge remains open |
| Reduction modulo `G_p` preserves values at every allowed `q_j` | Every factor `(q+q_j)` divides `G_p`; independent native coefficient oracle and rank-three Sage residue replay | Concrete 39 distinct values and exact source labels checked computationally; Lean polynomial quotient bridge remains open |
| The leading `r` coefficient of `H` is a unit modulo `G_p` | `unit_native_result.json` checks it is nonzero at all 39 distinct roots of squarefree `G_p` on both frozen charts | Uses the Chinese remainder theorem for products of distinct linear factors; the N41 field/tensor bridge is computational |

The rank-three symbolic computation is an exact equality control, not a
formal proof of the rank-seven resultant residue. The rank-seven symbolic
parent ended at its recorded time cap. The full native rank-seven product
is an independent exact oracle for future implicit implementations.
