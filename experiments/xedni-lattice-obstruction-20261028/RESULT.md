# A checked reduction-map obstruction for the original xedni calculus

The Lean development proves a conditional obstruction for the original lift-and-dependence xedni method. If every nontrivial relation among admissible rational lifts has coefficients bounded by `B`, and the reduced points have no nontrivial relation within that bound, then **every compatible lift is independent**. Selecting a different lifted curve by auxiliary conditions cannot create a relation for that same reduced tuple under the stated bound. For independently uniform points in a prime-order subgroup, the development also proves the exact one-over-subgroup-order fiber count for each nonzero coefficient vector and a finite-list union bound.

This formalizes the structural and finite counting steps underlying Jacobson, Koblitz, Silverman, Stein, and Teske, [*Analysis of the Xedni Calculus Attack*](https://pages.cpsc.ucalgary.ca/~jacobs/PDF/xedni.pdf), §§3–4, especially Theorem 4.1 and Lemma 4.1. The paper's asymptotic result is conditional on a height/discriminant hypothesis and Lang's conjectural lower height bound; its final `C₀/p` estimate additionally models the reduced points as randomly distributed. The Lean module does **not** establish those arithmetic hypotheses for arbitrary elliptic curves or prove that every possible lifting method fails.

## Mathematical proof and exact hypotheses

Let `ρ : H → G` be an additive homomorphism from the group of lifted points to the reduced group, let `Lᵢ ∈ H` reduce to `Pᵢ ∈ G`, and let `aᵢ ∈ ℤ`. Homomorphism of integer scalar multiplication and finite sums gives

`ρ(Σᵢ aᵢ Lᵢ) = Σᵢ aᵢ Pᵢ`.

Therefore a lifted relation `Σᵢ aᵢ Lᵢ = 0` gives the same relation downstairs. Assume that every nontrivial lifted relation has `|aᵢ| ≤ B` for all `i`. If the reduced tuple has no nontrivial relation in that finite coefficient box, a lifted relation would contradict the reduced test. The theorem quantifies over **all** lift tuples compatible with the fixed reduced tuple. The coefficient bound must be supplied for every lift included in that quantifier; the Lean theorem does not hide a curve-dependent height assumption.

For the counting result, choose a generator of a subgroup of prime order `q` and identify its points with the field `F_q`. For a fixed coefficient vector `a` with some `aᵢ ≠ 0`, the map `x ↦ Σᵢ aᵢ xᵢ` is surjective: set only coordinate `i` to `y/aᵢ` to obtain any desired `y`. Its kernel has cardinality `|F_q|^(r−1)`, equivalently `|ker| · |F_q| = |F_q|^r`. The union of zero-relation fibers for a fixed finite set `S` of nonzero coefficient vectors has at most `|S|` times one fiber's cardinality. Thus independent uniform samples obey `Pr[∃ a∈S : Σᵢ aᵢ xᵢ=0] ≤ |S|/q`. If `S` comes from integer coefficients with `|aᵢ|≤B`, mapping nonzero integer vectors to nonzero vectors over `F_q` requires an additional condition such as `B<q`; the module's counting theorem takes the already reduced, nonzero set `S` as input.

## Proof map and verification

| Result | Lean declaration | Hypotheses and status |
| --- | --- | --- |
| Integer relation commutes with reduction | `XedniObstruction.relation_reduces` | Any two abelian groups and additive homomorphism; checked |
| One lifted tuple excluded by bounded reduced test | `XedniObstruction.no_dependent_lift` | Supplied coefficient bound and absence of bounded reduced relations; checked |
| All compatible lifts excluded | `XedniObstruction.all_compatible_lifts_blocked` | Uniform bound over the admissible lift tuples and fixed reduced tuple; checked |
| Nonzero finite-field relation map is surjective | `XedniObstruction.dotHom_surjective` | Field and a nonzero coefficient coordinate; checked |
| Exact zero-fiber size | `XedniObstruction.zeroFiber_count` | Finite field and nonzero coefficient vector; checked |
| Finite candidate union count | `XedniObstruction.bounded_relation_union_count` | Finite field, finite candidate set, all vectors nonzero; checked |
| Height-theoretic coefficient bound of the original paper | — | Lang-type height lower bound, discriminant-to-point-height ratio, and geometry-of-numbers estimate; **not formalized here** |
| Full original Theorem 4.1 for xedni's curve-selection distribution | — | Requires the preceding height bridge and exact sampling/selection law; **open** |

The pinned toolchain is Lean `v4.35.0-rc4`; Mathlib is pinned to `021c46bdd042f67b538b9f9871d556a93713a9a9` in the local Lake files. `lake build XedniObstruction` completed successfully. The build output includes `#print axioms` for all seven reported declarations: each uses only `propext`, `Classical.choice`, and `Quot.sound`; no `sorry`, `admit`, `sorryAx`, custom research axiom, native evaluation, or kernel bypass occurs in the source. `lean4checker --fresh` is unavailable on this host. The checked build command, output, manifest, and source digests are retained in `formal/`.

The next formal step is to encode the paper's canonical-height and regulator assumptions as explicit hypotheses, then prove that they imply a uniform finite coefficient bound for its `2≤r≤9` lift family. That would connect the checked structural theorem to the paper's full conditional asymptotic statement without treating its unproved arithmetic inputs as axioms.
