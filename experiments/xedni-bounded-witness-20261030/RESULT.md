# Corrected bounded-witness implication for xedni lifting

This successor corrects the circular hypothesis in the 2026-10-28 formalization.
Its initial source-custody receipt preserves the original bundle at its stated
historical revision; main subsequently corrected that original module too.
The five successor theorems independently passed native compilation and the
required five-declaration foundation checks on Lean4.35.0-rc4 and pinned Mathlib.
See the [source-bound native qualification](../../reports/ci-lean-source-admission-20261030/native-witness-verification.json)
and its complete decoded CI job log. No original build receipt substitutes for
this successor's own verification.

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
| Integer relations commute with reduction | `relation_reduces` | Native verified; standard foundations only |
| Bounded witness excludes one lift tuple | `no_dependent_lift` | Native verified; standard foundations only |
| Uniform witness property excludes all compatible lifts | `all_compatible_lifts_blocked` | Native verified; standard foundations only |
| Witness hypothesis is consistent with dependence | `zero_tuple_has_bounded_witness` | Native verified; standard foundations only |
| Universal bound fails for that same tuple | `zero_tuple_has_unbounded_relations` | Native verified; standard foundations only |
| Height-theoretic existence of a bounded witness | No declaration | Open |
| Full paper theorem and actual curve-selection distribution | No declaration | Open |

Lean and Mathlib retain the exact reviewed pins from the original project.
The existing corpus workflow discovers this `experiments/xedni-*/formal/`
source, compiles it natively in the pinned workspace and audits every printed
declaration. No escape or trusted native evaluation is added. Dependency
hashes bind the inputs; the separate native qualification binds the completed
build to its exact source, command evidence and checker contract.

The original finite-field counting and fixed-sample-law results remain in
their sealed source; this correction makes no new sampling, general
impossibility, cryptographic security or cost claim. No experiment ran.

The accompanying editable diagram and report PDF present this exact
conditional implication and the still-open height bridge. Existing canonical
experiment graphs were checked for this proof-only correction: it changes no
curve, measured row, atlas status or performance edge.

The initial source-validation receipt and report PDF remain historical records
of the initial pending state. The theorem statements, editable implication
diagram, scientific hypotheses and open height bridge have not changed.
The separate three-lemma compiler regression source is now explicitly admitted
at its exact source hash and proof context; its fresh pinned CI run is pending.
