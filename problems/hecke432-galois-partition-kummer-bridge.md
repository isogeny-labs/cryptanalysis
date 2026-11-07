# Galois pair partitions and degree-four Kummer isomorphism

- **Status:** open
- **Kind:** proof gap; concrete algebraic encoding is incomplete
- **Affected work:** [PR #1186 review addendum](../docs/quartic-review-20261029/1186.md) and [original result](../experiments/hecke-432-j1728-relative-quartic-galois-resolvent-20261026/RESULT.md)
- **Next action owner:** unassigned; next formalization task
- **Last updated:** 2026-10-29

## Problem

The universal cubic-resolvent identities do not yet prove the concrete V4 Galois group or identify its splitting field with the stated rank-two Kummer extension.

The exact instance is the original hash-pinned source field, factors, elements and selected places in `experiments/hecke-432-j1728-relative-quartic-galois-resolvent-20261026`. This is a missing formal bridge, not an observed contradiction or a proved obstruction. No deployed-curve or subgroup-transfer conclusion follows from the partial certificate map.

## Evidence and uncertainty

- **Observed:** the original computational receipts and sources are preserved, and the original integer validators replay successfully. The shared exact Lean project audits the submitted theorem declarations without claim-specific axioms. See [the manifest](../tools/ci/quartic_certificates.json) and [portable replay](../docs/quartic-review-20261029/portable-replay/results.json).
- **Derived or proved:** only the declarations identified in the original report's proof map; saved integer identities are not a proof of their concrete number-field interpretation.
- **Suspected explanation:** none asserted; the gap is the missing encoding and connecting lemmas.
- **Missing capability:** Encode the pinned number field and both irreducible quartics, the action on four roots and pair partitions, and the serialized resolvent roots/radicands. Prove independence of two square classes, degree four, and the explicit splitting-field/Kummer isomorphism. Retain the distinction between algebraic diagnostic timings and ECDLP costs.
- **What this evidence does not establish:** full formalization of the concrete claim, a general impossibility result, prospective registration, scalar recovery, or an end-to-end speedup. Original errors and bounded timeouts remain unchanged.

## What would unblock it

- [ ] Encode the pinned number field and both irreducible quartics, the action on four roots and pair partitions, and the serialized resolvent roots/radicands. Prove independence of two square classes, degree four, and the explicit splitting-field/Kummer isomorphism. Retain the distinction between algebraic diagnostic timings and ECDLP costs.
- [ ] Build the connecting declarations with the exact pinned Lean/Mathlib project, audit all theorem axioms, and provide an exact source-to-certificate map with at least one independent positive instance and an invalid-hypothesis refusal control.

These conditions establish the named bridge only. They do not discharge other field, isogeny, subgroup, measurement or transport obligations.

## Next discriminating step

- **Action or proof obligation:** Derive the action on the three pair partitions from four distinct roots, then connect a single saved Delta_j to the square of the corresponding pair-sum difference.
- **Inputs and controls:** use the original manifest's exact field/factor/ideal data; preserve the saved positive and negative rows and check required nonzero/unit/unramified hypotheses explicitly.
- **Execution limits and stop condition:** this is a proof task, not a newly launched search. Preserve all existing producer timeouts; any new experiment needs its own protocol and distinct output directory.
- **Outcomes and next actions:** a checked bridge narrows the open proof map; a counterexample requires a dated correction without rewriting frozen evidence; an unfinished proof or unavailable tool leaves this record open.
- **Recheck trigger:** a new exact connecting declaration and axiom-audited build, or a concrete counterexample.

## Resolution and history

2026-10-29: recorded the previously disclosed open obligation and its acceptance criteria during the review repair. **Unresolved.** Creating or merging this record does not complete the mathematical theorem.
