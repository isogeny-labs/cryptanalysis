# Local quartic factorization and Frobenius interpretation

- **Status:** open
- **Kind:** proof gap; concrete algebraic encoding is incomplete
- **Affected work:** [PR #1184 review addendum](../docs/quartic-review-20261029/1184.md) and [original result](../experiments/hecke-432-j1728-relative-quartic-local-factor-20261026/RESULT.md)
- **Next action owner:** unassigned; next formalization task
- **Last updated:** 2026-10-29

## Problem

The exact local-factor census and ring identities lack the full Lean Hensel, scaled Taylor and Frobenius-discriminant bridges for the pinned L/K quartics.

The exact instance is the original hash-pinned source field, factors, elements and selected places in `experiments/hecke-432-j1728-relative-quartic-local-factor-20261026`. This is a missing formal bridge, not an observed contradiction or a proved obstruction. No deployed-curve or subgroup-transfer conclusion follows from the partial certificate map.

## Evidence and uncertainty

- **Observed:** the original computational receipts and sources are preserved, and the original integer validators replay successfully. The shared exact Lean project audits the submitted theorem declarations without claim-specific axioms. See [the manifest](../tools/ci/quartic_certificates.json) and [portable replay](../docs/quartic-review-20261029/portable-replay/results.json).
- **Derived or proved:** only the declarations identified in the original report's proof map; saved integer identities are not a proof of their concrete number-field interpretation.
- **Suspected explanation:** none asserted; the gap is the missing encoding and connecting lemmas.
- **Missing capability:** Encode L/K, both quartics, selected prime ideals and residue maps. Prove simple-root Hensel lifting, the scaled Taylor factorization at doubled roots, and Frobenius sign versus discriminant square status under the required unramified hypotheses. Connect each saved row to these definitions.
- **What this evidence does not establish:** full formalization of the concrete claim, a general impossibility result, prospective registration, scalar recovery, or an end-to-end speedup. Original errors and bounded timeouts remain unchanged.

## What would unblock it

- [ ] Encode L/K, both quartics, selected prime ideals and residue maps. Prove simple-root Hensel lifting, the scaled Taylor factorization at doubled roots, and Frobenius sign versus discriminant square status under the required unramified hypotheses. Connect each saved row to these definitions.
- [ ] Build the connecting declarations with the exact pinned Lean/Mathlib project, audit all theorem axioms, and provide an exact source-to-certificate map with at least one independent positive instance and an invalid-hypothesis refusal control.

These conditions establish the named bridge only. They do not discharge other field, isogeny, subgroup, measurement or transport obligations.

## Next discriminating step

- **Action or proof obligation:** Prove the two-simple-plus-one-double reduction case for one exact selected place, including denominator units and discriminant valuation hypotheses.
- **Inputs and controls:** use the original manifest's exact field/factor/ideal data; preserve the saved positive and negative rows and check required nonzero/unit/unramified hypotheses explicitly.
- **Execution limits and stop condition:** this is a proof task, not a newly launched search. Preserve all existing producer timeouts; any new experiment needs its own protocol and distinct output directory.
- **Outcomes and next actions:** a checked bridge narrows the open proof map; a counterexample requires a dated correction without rewriting frozen evidence; an unfinished proof or unavailable tool leaves this record open.
- **Recheck trigger:** a new exact connecting declaration and axiom-audited build, or a concrete counterexample.

## Resolution and history

2026-10-29: recorded the previously disclosed open obligation and its acceptance criteria during the review repair. **Unresolved.** Creating or merging this record does not complete the mathematical theorem.
