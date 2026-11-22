# Proof map

| Result | Formal or executable artifact | Scope and verification |
| --- | --- | --- |
| Folded coefficient of a repeated Frobenius column is `λ^a(1+λ^k)` | `linked_frobenius_factor` in [LinkedFactor.lean](LinkedFactor.lean) | Equality in `Nat`, for every `lambda`, `a`, and `k`. Standard Lean `propext` only. The transfer to a concrete subgroup eigenvalue uses modular reduction and the audited group-action interpretation; the latter is checked computationally on N41, not formalized in Lean. |
| Nine-code W18 source with distinct folded columns has at least `∏(33191-3i)` labeled assignments | [projection.py](projection.py), [projection_result.json](projection_result.json) | The source table and `source_conflicts()` enumerate 65 unequal conflicts, maximum degree two. The product follows by greedy counting. A faithful Lean theorem connecting the concrete table to pairwise column disjointness remains open; the executable census is exact. |
| Linked factor is nonzero for either N131 Frobenius eigenvalue at gap 16 | [projection.py](projection.py), [projection_result.json](projection_result.json) | Exact modular roots of `X²+X+2` and modular powers under subgroup order `680564733841876926932320129493409985129`; arithmetic check, not a Lean proof of the curve action. |
| N41 public relation, 18 nonzero columns, modular rank 3 to 4 | [audit_sage.py](audit_sage.py), [audit_result.json](audit_result.json) | Independently replayed on the exact frozen point through repository `./sage`; proof is computational, with source and runtime hashes. |

Toolchain: `leanprover/lean4:v4.34.1` in [lean-toolchain](lean-toolchain). Command: `lean LinkedFactor.lean`; output in [lean_check.log](lean_check.log), including `#print axioms`. `lean4checker --fresh` was not available in this environment. The full concrete curve-action implication remains a formalization task.
