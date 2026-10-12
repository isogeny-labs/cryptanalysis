# Encoding proof map

| Claim | Lean declaration | Exact scope | Status |
| --- | --- | --- | --- |
| Three CNF clauses encode one Boolean AND gate | `and_gate_iff` in `Encoding.lean` | All Boolean inputs `v,a,b`; no field assumptions | Checked with pinned Lean 4.34.1 |
| Negating the first XCNF literal flips the XOR row right-hand side | `xor_row_flip` in `Encoding.lean` | All Boolean `x,tail,rhs` | Checked with pinned Lean 4.34.1 |
| The entire generated XCNF is equivalent to the specialized four-atom field eliminant | None | Frozen N41/N131 field, polynomial, source bases and coefficients | Formalization partial. The remaining bridge is a Lean definition of the generated ANF coefficient map and XCNF output rows, connected to the inherited resultant and binary-field arithmetic. The N41 positive model was checked against every emitted row and directly against the field equation; the N41 control was independently exhausted over all 16,384 product assignments in the inherited ANF audit. |

The generic Lean lemmas establish the gate and parity conventions actually used by the emitter. They do not replace the open coefficient-to-field bridge.
