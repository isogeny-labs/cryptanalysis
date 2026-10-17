# Proof map

The quotient uses the checked Lean 4 theorems
`NegationQuotient.tripleNegation` and
`NegationQuotient.lookupEitherSign` in
`../n41_partial_sum_compressibility_20261017/NegationQuotient.lean`.
Their pinned toolchain is `leanprover/lean4:v4.34.1`; the retained build and
axiom output are in that directory. The first theorem uses standard
`propext`; the second reports no axioms.

| Obligation | Evidence | Scope |
| --- | --- | --- |
| Negating all three pair sums negates their group sum | `tripleNegation` | Any additive commutative group |
| Looking up either representative sign against a public target is exact | `lookupEitherSign` | Exact point equality in an additive commutative group |
| Every source state has one same-column negated partner | Prior `state_audit.json`; `negation_join.cpp` rechecks all 960 rows before enumeration | Frozen N41 six-slot input |
| Keeping the smaller first-slot state ID retains one member of every three-state global-sign pair | Involution has no fixed state in slot zero, checked by the native guard; left count is exactly half the prior 3,750,144 | Frozen internally column-disjoint triple set |
| Both point-sign lookup paths produce valid state IDs and group points | Ordinary same-point hit and `flip_control_result.json` first-probe hit; `verify.py` binds both | Ordinary archived Q plus a constructed flipped-branch control |
| The ordinary six-pair hit equals the public point after source reconstruction | Prior independent checked-Sage `join_audit_result.json`; exact six-ID match | One frozen N41 public point |

This establishes the exact quotient on the frozen input. The group and
source-state proofs do not establish a relation-yield or complexity law on
N131; that remains a separate experimental gate.
