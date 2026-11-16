# Symbolic collision proof map

The module pins Lean `v4.35.0-rc4` and Mathlib
`021c46bdd042f67b538b9f9871d556a93713a9a9`.

| Mathematical step | Lean declaration | Scope |
| --- | --- | --- |
| Addition and scaling preserve affine scalar expressions | `eval_plus`, `eval_scale` | Commutative ring `F`; fixed forms |
| Unequal-slope equality names one target scalar | `unequal_slope_eq_iff_candidate` | Field `F`; slopes differ |
| Equal-slope distinct forms never collide | `same_slope_distinct_ne` | Field `F`; equal slopes, distinct forms |
| Equality of represented public points reflects scalar equality | `public_group_equality_iff` | Additive `F`-module; injective scalar-to-point map at `G` |
| Exact collision set equals pair-candidate image | `collision_set_eq_candidates` | Finite field; fixed indexed forms; informative unequal-slope pairs |
| Collision-set cardinal bounds | `collision_card_le_active_pairs`, `symbolic_collision_bound` | Finite field; fixed indexed forms; at most active pairs and at most `n²` |

These theorems analyze a fixed symbolic trace. The choice of its forms may
depend on public randomness fixed independently of the unknown scalar. A
generic-group algorithm that adapts to equality observations requires a
decision-tree/coupling argument; an algorithm using concrete point encodings
or curve coordinates requires a different model. The theorem does not assume
that all such algorithms have a fixed trace.

`lake build SymbolicCollision` completed 3,138 jobs. All eight `#print axioms`
reports list only standard foundations (`propext`, `Classical.choice`, and
`Quot.sound` where used). The source has no `sorry`, `admit`, custom axiom, or
native evaluation. `lean4checker --fresh` was unavailable on this host.
