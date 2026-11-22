# Proof and verification map

The new result here is an implementation and measurement of first-product substitution. No new statement about the elliptic curve or asymptotic complexity is asserted.

| Obligation | Evidence | Status |
| --- | --- | --- |
| Shared ANF equals the specialized four-atom field eliminant | Inherited independent ANF derivation and field arithmetic checks in `../n41_n131_fouratom_product_anf_20261012/audit.py`; exact archived source and input hashes are in the specialized protocol | Computationally checked for the inherited positive; a faithful Lean coefficient-to-field theorem remains open in the inherited proof map |
| AND and XOR clauses have the intended Boolean semantics | `and_gate_iff` and `xor_row_flip` in `../n41_n131_fouratom_product_anf_sat_20261012/Encoding.lean`, built with pinned Lean 4.34.1 and no axioms | Lean checked |
| Specialized positive XCNF has a satisfying source assignment | `source_first_product.small.json`: every clause and XOR row checked, second mask 3, direct field eliminant zero | Independently replayed model |
| Negative controls have no accepted second product | Terminal UNSAT receipts for mask 0 and 16 frozen masks; archived complete one-sided GCD scan found only the positive product family | Computational control; no UNSAT proof certificates archived |

The missing formal bridge is a Lean representation of the 220,172-term field-valued ANF, first-mask substitution with cancellation, and its emitted XCNF. The checked gate lemmas cover the per-gate Boolean encoding but not that whole generated object.
