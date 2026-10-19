# Proof map for the cubic resultant transformation

| Result | Formal declaration or exact evidence | Scope |
| --- | --- | --- |
| `p·F=0` and `F=0` have the same solutions for `p≠0` | `DegreeFall.scaled_zero_iff` | Any field, arbitrary `p,F`; checked Lean 4.34.1. |
| The scaled equation accepts every `p=0` assignment | `DegreeFall.zero_product_exception` | Any commutative ring; checked Lean 4.34.1. The standalone N131 solver adds an explicit nonzero-code guard; the hybrid retains `F`. |
| Squaring and fourth powers of binary-linear code products remain binary-linear | `DegreeFall.fourth_additive`, `DegreeFall.binary_bit_fourth`; prior `SourceProductLinear.source_product_additive` | Characteristic two and idempotent code bits. The prior module proves fixed-seed source-product additivity. The list-level field-basis and quotient-polynomial bridge is not one Lean declaration. |
| Every monomial in the 13-term `pF` support has code degree at most three | `DegreeFall.scaled_support_degree` plus the written power-factor proof in `RESULT.md` | Exact displayed exponent list, binary degree of powers `0..5`, and characteristic-two Frobenius. The complete field-valued ANF multiplication is checked by finite audit, not formally implemented in Lean. |
| N41 and N131 ANF degree and count | [profile_result.json](profile_result.json), [result.json](result.json) | Exact integer-bit field implementation; N41 full width-five blocks exhausted, N131 seeded evaluations and known positive checked. Prior independent Sage audits pin field representation and source coefficients. |
| Positive source-code preservation | [n41_gate.json](n41_gate.json), [hybrid_n41_gate.json](hybrid_n41_gate.json), prior N131 positive replay | N41 complete solver outputs and independent public-relation replay; N131 cubic and hybrid jobs ended at the measured RSS cap. |

The Lean command was `lean DegreeFall.lean` under `leanprover/lean4:v4.34.1`; `lean.stdout` contains each `#print axioms` result. `lean4checker --fresh` was unavailable on this host. The full theorem connecting the concrete `GF(2^n)` quotient implementation, the 13 coefficient values, and the Boolean ANF dictionary remains a partial formalization. The original field statement and its finite evaluation checks remain explicit in the result.
