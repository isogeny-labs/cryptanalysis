# A checked first-hit bound for rational-lift relation searches

The Lean theorem `XedniFirstHitDominance.first_hit_dominance` proves that a rational-lift relation cannot occur before the first directly checkable public relation **for the same ordered query and coefficient schedule**. It applies to any finite number of sampled points, any finite query sequence, and integer coefficient vectors that may vary by query. The companion `relation_support_subset_public` theorem proves inclusion of the entire rational-relation query set in the public-relation query set.

Let `ρ : H →+ A` be an additive reduction map from a lift group `H` to a public group `A`. At query `i`, let lifted points be `Lᵢⱼ`, public points `Pᵢⱼ=ρ(Lᵢⱼ)`, and integer coefficients `cᵢⱼ`. Applying `ρ` to a relation gives

`Σⱼ cᵢⱼ Lᵢⱼ = O  ⇒  Σⱼ cᵢⱼ Pᵢⱼ = O`.

If every public relation test at indices below `k` is false, then every rational relation test below `k` is false. If `k` is the first public relation index and `i` is any rational relation index, the checked conclusion is `k ≤ i`. This is a structural bound on event positions; the proof does not assume independent query samples or a distribution for selected curves.

## Exact proof map

| Mathematical result | Lean declaration | Hypotheses |
| --- | --- | --- |
| One lifted relation reduces at the same query | `relation_reduces` | Additive commutative lift and public groups; additive homomorphism `ρ`; `ρ(Lᵢⱼ)=Pᵢⱼ` for every point; finite integer coefficient vector |
| All rational-relation queries are public-relation queries | `relation_support_subset_public` | Same assumptions; query-specific coefficients allowed |
| Public-relation-free prefix is rational-relation-free | `no_early_rational_relation` | Same assumptions and no public relation before index `k` |
| First rational hit has index at least first public hit | `first_hit_dominance` | Same assumptions, a public relation at `k`, no earlier public relation, and a rational relation at `i` |

The proof uses only preservation of integer scalar multiplication and finite sums by an additive homomorphism, then the order on the finite query indices. No elliptic-curve rank, height, or heuristic sampling premise is hidden in the Lean statement. For an elliptic-curve application, good reduction and point compatibility must establish the required additive map on the chosen points. The theorem does not price discovery of a coefficient vector: when coefficients are selected only after a curve search, a direct method must acquire them or use a predeclared family. In the frozen `(1,2)` experiments the vector is known before querying, so the theorem applies to that direct control without a coefficient-discovery step.

The existing checked `XedniDirectRelation.finite_group_identity` and `finite_relation_recovers` theorems separately establish scalar recovery when the coefficient sum is nonzero in the target field. This module proves the relation-event and first-hit implications; it does not claim an end-to-end runtime lower bound. The finite-panel witnesses and direct controls in the preceding PRs instantiate the public comparison, while the full elliptic-curve reduction homomorphism is an open Lean bridge for those exact models.

The formal project pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build FirstHitDominance` passed 9,040 jobs. `#print axioms` for all four theorems lists only `propext`, `Classical.choice`, and `Quot.sound`; the module has no `sorry`, `admit`, custom research axiom, or native evaluation. `lean4checker --fresh` was unavailable on this host.

Reproduce from the repository root with `(cd experiments/xedni-first-hit-dominance-20261115/formal && lake build FirstHitDominance)` and `python3 experiments/xedni-first-hit-dominance-20261115/verify.py`. The checked source, pinned dependency manifest, build output, proof map, and file seal accompany this report.
