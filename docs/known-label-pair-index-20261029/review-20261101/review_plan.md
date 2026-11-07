# Known-label Lean proof review plan

Pinned producer commit: `52baa40a94751916c0d8b83ec8691125bccdac3c`.
The two reviewed sources are `docs/known-label-next-leads-20261028/Algebra.lean`
(SHA-256 `d0e0fa1892bc800999e3b5330f543bf2e99811f607606901f363fce27bcb428d`)
and `docs/known-label-pair-index-20261029/PairIndex.lean`
(SHA-256 `68dd10106b5499ad8b3fba35b95980a5ed1e6c46c0433047e0d5034e90c135c8`).
The exact-head hosted native corpus run is 41344355706. Its log reports four
and seven named declarations, respectively, with zero failing or trusted
exceptions. This run is machine evidence, not a semantic verdict.

## Producer claim and review prior

The first note derives the triangle identity behind labels from verified
pair relations. The pair-index note presents affine path and cycle formulas,
label recovery, a signed-square identity, and a cleared addition identity.
Both notes reserve concrete elliptic-subgroup instantiation, executable
index correctness, coverage and complete cost. My prior is that the algebraic
statements are valid at their stated hypotheses, while the bridge from a
verified elliptic relation to the abstract module edge needs explicit work.
The review must check this prior, not treat it as the verdict.

## Joints, attacks, and owners

| Joint | Reviewer | Worked attack before verdict |
|---|---|---|
| J1: exact module/name/axiom coverage | source-fidelity reviewer | Compare all 11 elaborated names and transitive axioms with the two tracked sources; try a missing or renamed declaration and a custom-axiom premise against the gate's refusal rules. |
| J2: path and odd-cycle algebra | blind math reviewer | Re-derive the recurrence from `R_i+R_j=T_ij` without the producer proof; test a triangle and a four-cycle, including the coefficient that must be inverted. |
| J3: concrete elliptic-group bridge | source-fidelity reviewer | Look for a theorem constructing the `ZMod r` module edge from verified points/scalars and a nonzero coefficient; exhibit the exact missing hypothesis if absent. |
| J4: executable and cost bridge | source-fidelity reviewer | Trace the pair-index output to a checked relation and all charged work; reject a claim based on abstract path algebra alone. |

The source-fidelity reviewer may inspect the pinned producer sources, notes,
gate code and hosted receipts, and must list every source actually read.
The blind math reviewer receives only the mathematical definitions and task
below. They may read Mathlib reference definitions if needed but must not
read either producer Lean file, README, PR, receipt, another reviewer report,
or this plan's prior and attack table until after submitting their derivation.
The Coordinator will compare reports only after both are filed.

## Blind derivation prompt

Let `V` be an abelian group and suppose oriented vertices satisfy verified
edge equations `R_i + R_j = T_ij`. Derive the triangle formula for `2 R_0`
from edges 01, 12 and 20. For a path in a module over a field, derive how
an affine update `z ↦ a z + c` composes and what a closed path implies about
its start. State precisely when the start is uniquely recoverable. Give an
explicit finite-field/module counterexample when the recovery coefficient is
zero. Explain what additional construction is needed to apply this algebra
to elliptic subgroup points with known `P,Q` labels.

## Controls and decision rule

Known-false or proves-too-much cases: a path with no verified edges; a
bipartite even cycle whose affine coefficient is one; a characteristic-two
triangle where division by two is unavailable; a trivial module whose
identities say nothing about a nontrivial DLP. A passing Lean build cannot
convert any of these into a constructor or cost claim. A scoped fidelity
finding requires a checked exact declaration, independent derivation,
nonvacuity/exception review, and an explicit list of every missing bridge.
The separate machine, fidelity and review-outcome fields will be recorded
per claim. No hypothesis or official evidence status changes in this packet.
