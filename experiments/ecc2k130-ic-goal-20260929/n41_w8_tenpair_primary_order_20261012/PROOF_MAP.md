# Proof map

| Result | Lean declaration | Exact hypotheses and status |
| --- | --- | --- |
| Renaming each literal transports clause and XOR-row evaluation | `VariableOrder.evalLit_rename`, `evalClause_rename`, `evalXor_rename` | Any `WirePerm` on natural wire IDs, any Boolean assignment, any literal row. Checked. |
| Formula satisfiability is invariant under a wire permutation | `VariableOrder.formula_rename`, `satisfiable_rename` | Any two lists of CNF and odd-parity XOR rows, any bijective natural-ID map with explicit left/right inverses. Checked. |
| Ten literal N131 one-hot slots exceed the 4-GiB cap even at one bit each | `VariableOrder.n131_onehot_memory_gate` | Exactly 34,482,792,912 choices in each of ten independent slots; arithmetic bound only. Checked. |
| The generated XCNF is a concrete permutation of the frozen source XCNF | Python `experiment.py build`, `verify_permutation.py`, `permutation_audit_result.json` | Independent row-by-row literal comparison with a checked permutation of `1..289065`; all 731,771 rows replayed on the constructed assignment. The concrete file identity is an independently reproducible computation, not a Lean theorem. |
| Raw curve relation and N131 source census | Upstream checked-Sage and census artifacts linked in `RESULT.md` | The N41 relation and N131 source-state count are inherited frozen inputs. This module does not formalize finite-field curve arithmetic or the source census. |

Toolchain is pinned in [lean-toolchain](lean-toolchain). `lean VariableOrder.lean > lean_check.txt` passed on Lean 4.34.1; [lean_check.txt](lean_check.txt) records `#print axioms` for every theorem. Only Lean's standard `propext` and `Quot.sound` appear in the formula/list proofs; the arithmetic theorem has no axioms. `lean4checker --fresh` was unavailable on this host. There is no `sorry`, `admit`, custom research axiom, or native proof evaluation in this module.
