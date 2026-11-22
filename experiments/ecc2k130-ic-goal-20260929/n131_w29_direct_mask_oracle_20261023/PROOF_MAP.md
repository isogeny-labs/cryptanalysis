# Proof map

| Result | Checked declaration or audit | Boundary |
| --- | --- | --- |
| The fixed-seed source product `a(a+s)` is additive in characteristic two | `SourceProductLinear.fixed_seed_product_additive` | Arbitrary commutative ring of characteristic two; no field or curve claim. |
| A Frobenius image of the source product remains additive | `SourceProductLinear.frobenius_product_additive` | Assumes the supplied Frobenius map is additive. The concrete `2^18` field automorphism is checked computationally through the N131 finite-field basis construction. |
| A nonzero pair-output reciprocal recovers its source product coefficient | `OracleComplete.quadratic_code_decode` in the preceding N41 oracle directory | Arbitrary characteristic-two field, nonzero leading coefficient and root, and the exact pair quadratic. The present checked-Sage producer verifies that equation on every enumerated control root. |
| Concrete rank-28 inverse on the N131 W29 canonical mask space | `run_sage.py` | The checked-Sage producer builds 28 pivot rows, asserts full rank, and replays inversion on 128 source-valid masks plus the positive right mask. Additivity from the Lean theorem makes a full-rank 28-column map injective on all canonical masks; the exact field representation and bit encoding are checked by Sage. |
| Positive constructed group sum and source geometry | `audit_sage.py` | Independent Sage implementation checks 128 source-valid, orbit-distinct mask pairs, both signed pair-output roots for each, the rotated positive right pair, and the complete two-pair group sum whose reciprocal is the frozen target input. |

Pinned toolchain: `leanprover/lean4:v4.34.1`. Run `lean SourceProductLinear.lean` in this directory. `lean.stdout` reports only standard `propext`, `Classical.choice`, and `Quot.sound`; `lean.stderr` is empty. `lean4checker --fresh` was unavailable on this host. The full concrete elliptic-curve group law to S3 polynomial bridge and the bit-encoding linearity bridge have computational checks, but a faithful Lean formalization of those particular objects remains open. The source-product linearity and generic quadratic decoder are checked Lean theorems.
