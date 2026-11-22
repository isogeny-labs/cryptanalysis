# Proof map for the public N131 block exclusion

Let `E_i(z)` be the 131 Boolean coordinate equations of the exact frozen public-target eliminant on 34 source bits, with `i=0..130`. Let `m_j(z)` range over source-bit monomials of degree zero, one, or two. The emitted certificate is a set `S` of 4,414 distinct `(i,j)` pairs satisfying the Boolean polynomial identity

`⊕_(i,j)∈S m_j(z) E_i(z) = 1`.

For any assignment `z`, if all coordinates `E_i(z)` were zero, the left side would evaluate to zero while the right side evaluates to one. Therefore the eliminant has no root for the left-code block `0..3` and any of the `2³²` right codes. The statement quantifies over all 34-bit Boolean assignments; the certificate replay checks the identity coefficient by coefficient in the Boolean quotient, using squarefree monomial union for multiplication.

| Statement or bridge | Declaration or evidence | Status |
| --- | --- | --- |
| A constant-one sum of equation multiples excludes simultaneous zeros | `../n41_w11_block_macaulay_20261019/BlockCertificate.lean`: `BlockCertificate.constant_one_block_certificate_sound` | Rechecked with `elan run leanprover/lean4:v4.34.1 lean` in this experiment. `lean.stdout` reports only `propext`, `Classical.choice`, and `Quot.sound` from `#print axioms`. The theorem quantifies over arbitrary assignments, coordinate and multiplier index types, a commutative ring, and the explicit nontriviality and certificate hypotheses. |
| Exact N131 public field equations and target identity | Prior `n41_n131_sparse_block_macaulay_20261019/audit_inputs_sage.py` plus `audit_result.json`; `n131_w33_freecode_resultant_20261018/coefficients.json` | The checked-Sage audit reconstructed every coordinate ANF and matched the public `.eqs` file. `verify_public.py` rechecks the audit protocol/source hashes and exact public point coordinates. |
| Concrete 4,414-row constant-one identity | `n131_t1_a0.stdout`, `verify_public.py`, `verification_result.json` | Independent Python replay XORed the original equation multiples and obtained exactly `{0}`. The certificate was not inferred from producer status alone. |
| Positive-control consistency | `witness_gate.py`, `witness_result.json`, prior checked-Sage N131 slice audit | The known `(3,16722)` code pair satisfies all 131 constructed-positive equations; prior Sage arithmetic independently located that root. |
| Resultant as a necessary condition for the source-point decomposition | `../n41_w11_freecode_resultant_20261018/FreeCodeElimination.lean`: `split_quadratic_norm`, `eliminated_zero_iff_shared_root`; prior N131 symbolic remainder and source audit | Generic structural declarations are Lean checked; the exact N131 source-to-curve bridge is represented by the prior frozen Sage and circuit audit. |

The full concrete theorem over the encoded `GF(2^131)` curve and the 4,414-row identity is not yet a Lean declaration. A faithful kernel proof would need the finite-field encoding, the public coefficient vector, and a feasible Boolean-polynomial certificate checker as Lean definitions. The present formalization is partial at that concrete bridge; the written argument above and independently replayed finite certificate remain the exact mathematical result. No custom axioms, `sorry`, or native evaluation are used in the checked generic theorem.
