# Corrected bounded-witness implication for xedni lifting

This successor corrects the circular hypothesis in the sealed 2026-10-28
formalization. It preserves that entire original bundle and does not reuse its
successful build receipt as validation of this new source. The five successor
theorems are implemented; fresh native compilation and foundation audit are
pending.

## Exact correction

The original hypothesis required every nontrivial integer relation among a
lift tuple to lie in a fixed coefficient box. If a nonzero relation exists,
its arbitrary integer multiples leave every fixed box, so the hypothesis
already implies independence.

The corrected hypothesis is:

`(there exists a nontrivial lifted relation) ->
 (there exists a nontrivial lifted relation with every coefficient <= B in absolute value)`.

The bounded witness may differ from the relation that established dependence.
This matches the conclusion of Jacobson et al., *Analysis of the Xedni
Calculus Attack*, Lemma 4.1: under its height/discriminant assumption and
Lang's conjecture, dependence supplies a bounded relation. The primary paper,
sections 3-4, was read at
https://pages.cpsc.ucalgary.ca/~jacobs/PDF/xedni.pdf.

Let `rho : H -> G` be an additive homomorphism. A lifted relation reduces with
the same integer coefficients. If dependence supplies a bounded witness but
the fixed reduced tuple has no nontrivial relation within that bound, reducing
the witness gives a contradiction. The all-compatible-lifts theorem assumes
this witness property separately for each compatible lift, with the same
bound `B`; its witness may vary with the lift.

Two controls distinguish the hypotheses: the dependent zero tuple has a
nontrivial witness bounded by one, and also has relations beyond every fixed
bound. Thus the corrected witness property can hold for a dependent tuple.

## Proof map and current status

| Obligation | Declaration in `XedniBoundedWitness` | Status |
| --- | --- | --- |
| Integer relations commute with reduction | `relation_reduces` | Implemented; native verification pending |
| Bounded witness excludes one lift tuple | `no_dependent_lift` | Implemented; native verification pending |
| Uniform witness property excludes all compatible lifts | `all_compatible_lifts_blocked` | Implemented; native verification pending |
| Witness hypothesis is consistent with dependence | `zero_tuple_has_bounded_witness` | Implemented; native verification pending |
| Universal bound fails for that same tuple | `zero_tuple_has_unbounded_relations` | Implemented; native verification pending |
| Height-theoretic existence of a bounded witness | No declaration | Open |
| Full paper theorem and actual curve-selection distribution | No declaration | Open |

Lean and Mathlib retain the exact reviewed pins from the original project.
The existing corpus workflow discovers this `experiments/xedni-*/formal/`
source, compiles it natively in the pinned workspace and audits every printed
declaration. No escape or trusted native evaluation is added. Dependency
hashes bind the new inputs; they are not a completed-build receipt.

The original finite-field counting and fixed-sample-law results remain in
their sealed source; this correction makes no new sampling, general
impossibility, cryptographic security or cost claim. No experiment ran.

The accompanying editable diagram and report PDF present this exact
conditional implication and the still-open height bridge. Existing canonical
experiment graphs were checked for this proof-only correction: it changes no
curve, measured row, atlas status or performance edge.
