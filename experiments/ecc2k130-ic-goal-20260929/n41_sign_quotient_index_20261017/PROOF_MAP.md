# Proof map

Toolchain: `leanprover/lean4:v4.34.1`, pinned in `lean-toolchain`.
Command: `lean NegationQuotient.lean`; exit code 0, output `lean.stdout`.
The module contains no `sorry`, `admit`, custom axioms, or native evaluation.
`#print axioms` reports `propext` for `tripleNegation` and no axioms for
`lookupEitherSign`.

| Result | Declaration or check | Exact scope |
| --- | --- | --- |
| Simultaneous negation of three points negates their sum | `NegationQuotient.tripleNegation` | Any additive commutative group |
| Either sign of a stored left sum gives an exact target-conditioned lookup key | `NegationQuotient.lookupEitherSign` | Any additive commutative group and exact point equality |
| One unique same-column sign partner per input state, with partner involution | `sign_join.cpp` startup assertions | All 960 frozen N41 source states |
| One stored representative per admissible triple sign orbit | First-slot representative rule and partner involution; `LEFT_ENUM` count exactly half the archived 3,750,144 rows | Frozen three-slot source and column rule |
| Returned six IDs sum to the public raw target with twelve distinct columns | `audit_sage.py`, `audit_result.json` | Frozen N41 field, curve, source, and target |

The abstract theorem does not define the concrete binary curve or source
table. The checked-Sage audit and C++ state checks supply that finite-instance
bridge. The exact sign quotient is independent of the selected public target;
its measured search cost is specific to this source and target.
