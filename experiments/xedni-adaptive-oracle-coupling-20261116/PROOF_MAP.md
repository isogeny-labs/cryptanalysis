# Adaptive fresh-oracle coupling proof map

Lean v4.35.0-rc4; Mathlib 021c46bdd042f67b538b9f9871d556a93713a9a9.

| Result | Lean declaration | Hypotheses |
| --- | --- | --- |
| Count complete visible-label events in one selected branch | `branchCount` | Finite group and label sets, additive operation, indexed prior trace, deterministic label-based chooser |
| Matching counts in a chosen fresh branch | `fresh_branch_count_eq` | Both prior traces injective; the selected addition output is fresh in both; same chooser and event |
| Matching counts summed over all adaptive branches | `adaptive_fresh_event_count_eq` | Both traces injective; every candidate addition output fresh in both; same chooser and event |

`branchCount` includes the condition that the chooser applied to the prior
visible labels actually selects that branch. Thus the sum counts each encoding
once, for its chosen command. The proof applies the prior fresh-step theorem
to each branch, then sums equal counts. The two imported modules are symlinked
to their pinned sources in the preceding experiments.

The statement is conditional on freshness of every candidate branch. It does
not handle a branch whose group result collides with a prior element, or prove
an arbitrary-length induction. Those are the next proof obligations. The
model exposes abstract random labels, not finite-field curve coordinates.

`lake build AdaptiveOracleCoupling` passed 3,140 jobs. `#print axioms` of all
three declarations reports only `propext`, `Classical.choice`, and
`Quot.sound`. `lean4checker --fresh` was unavailable on this host.
