# Block certificate proof map

Let `E_i(x)` be the 41 field-coordinate Boolean equations of the exact target-conditioned eliminant on 12 code bits. A producer row has the form `m_j(x)E_i(x)`, where `m_j` is a squarefree code monomial of degree zero, one, or two. If selected rows XOR to the constant polynomial `1` in the Boolean quotient, then no assignment can make all `E_i` zero: evaluating the identity at such an assignment would give `0=1`.

| Result | Lean declaration or finite bridge | Status |
| --- | --- | --- |
| A constant-one combination of equation multiples excludes every simultaneous zero | `BlockCertificate.lean`: `constant_one_block_certificate_sound` | Lean 4.34.1 checked for arbitrary assignment type `X`, field-coordinate index type `I`, multiplier index type `J`, commutative ring `R`, and explicit `1≠0` and certificate hypotheses. The arbitrary multiplier covers products of two code bits, unlike the earlier one-bit theorem. |
| Exact 13-term eliminant on the N41 source | `../n41_w11_freecode_resultant_20261018/FreeCodeElimination.lean`, prior checked-Sage symbolic export and finite census | Prior structural theorem and concrete coefficient/remainder audit; this experiment hashes the exact coefficient input. |
| Five block-specific constant-one identities | `result.json` selected `[field_bit, multiplier_mask]` rows; `audit_sage.py`, `audit_result.json` | Independent Sage field arithmetic recomputed every one of 24,576 input values and every squarefree ANF coefficient, then XORed each selected row to exactly `{constant: 1}`. |
| Retained positive block | `result.json`, `audit_result.json`, preceding public relation audit | The exact root `(253,63)` survives degree six; its group-sum replay is in the earlier source archive. |

Run from the repository root:

```sh
elan run leanprover/lean4:v4.34.1 lean experiments/ecc2k130-ic-goal-20260929/n41_w11_block_macaulay_20261019/BlockCertificate.lean
python3 experiments/ecc2k130-ic-goal-20260929/n41_w11_block_macaulay_20261019/verify.py
```

The Lean module's `#print axioms` output in `lean.stdout` reports only `propext`, `Classical.choice`, and `Quot.sound`; stderr is empty. The source contains no `sorry`, `admit`, or custom axiom for the research claim. The theorem proves the structural exclusion from a valid row identity. The finite-field coefficient expansion, source encoding, and five concrete identities are executable certificates checked with a separate Sage implementation; a bit-level Lean model of the concrete `GF(2^41)` representation remains open.
