# Proof map

| Reported result | Check | Exact scope and formalization status |
| --- | --- | --- |
| Fourteen source leaves sum to the raw preimage and project to the archived ordinary subgroup point | `audit_sage.py`, `audit_result.json` | Checked Sage reconstructs each point in the pinned `GF(2^41)` model from masks and raw lifts independently of the C++ join. This finite curve-specific equality has not been imported into Lean. |
| Fourteen distinct folded columns give a row with nonzero entries whose group evaluation is the public point and whose rank from an empty matrix is one | `row_audit_sage.py`, `row_result.json` | Checked Sage finds the unique Frobenius/sign representative of each leaf, verifies the eigenvalue, re-evaluates the complete row on the curve, and computes rank over `GF(r)`. A Lean representation of this field, curve, quotient map, and 77-column vector is the missing bridge. |
| The same relation satisfies the exact functional-root XCNF for the ordinary point | `build_sat.py`, `build_result.json` | Every clause and native XOR row is evaluated by the frozen Boolean circuit checker. This is an executable finite certificate, not a Lean theorem. |

The prior [sign-lift theorem](../n41_w8_sign_label_closure_20261013/PROOF_MAP.md) gives an abstract tree implication under its explicit sum/difference-class assumptions. It does not formalize this curve-specific row. The present experiment reports the finite Sage and XCNF checks as such; its Lean formalization remains partial at the concrete curve and folded-column bridge.
