# Proof map

Toolchain: `leanprover/lean4:v4.34.1`. The command
`lean NegationQuotient.lean` and its output are retained in `lean_build.*`.
`#print axioms` reports `propext` for `tripleNegation` and no axioms for
`lookupEitherSign`.

| Statement | Declaration or check | Scope |
| --- | --- | --- |
| Negating all three source pair points negates their partial sum | `NegationQuotient.tripleNegation` | Every additive commutative group |
| An exact target lookup may use either sign of a stored left representative | `NegationQuotient.lookupEitherSign` | Every additive commutative group, given point equality |
| Every signed source state has a distinct same-column partner whose raw sum is its point negation | `state_audit.json` | All 960 frozen N41 source states; direct check of the binary-curve rule `(x,y) -> (x,y xor x)` |
| The left triple output multiset closes under point negation | `run.stdout` census plus state audit and structural theorem | The 3,750,144 frozen internally column-disjoint left triples; full point labels enumerated |
| The sorted index's reported hit is a valid public-point relation | Prior independent checked-Sage `join_audit_result.json`, exact state-ID equality in `verify.py` | One frozen N41 public target and six source states |

The bridge from the abstract group theorem to the concrete binary curve is
the archived native group implementation and independent checked-Sage replay.
The census is finite-instance evidence; it does not prove compression on a
different field or factor base.
