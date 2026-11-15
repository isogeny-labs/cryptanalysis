# A checked sample-weight bound for selected xedni lifts

`XedniSelectionLaw.selected_dependent_lift_weight_bound` extends the finite dependent-lift count to an arbitrary nonnegative integer weight on sampled reduction tuples. If each admitted tuple has weight at most `M`, the selected dependent event has total weight `W_dep` satisfying

`W_dep * q <= M * |S| * q^r`,

where `S` is a fixed complete list of nontrivial integer coefficient vectors within the declared bound, `q` is the prime subgroup order, and `r` is the number of sampled points. The proof combines the checked absolute event count with the exact finite sum bound `W_dep <= M * |event|`. It keeps the compatibility and bounded-witness hypotheses explicit on the admitted set.

If the total admitted weight is `W > 0`, division gives the derived probability bound `Pr(dependent | admitted) <= (M*q^r/W) * (|S|/q)`. For unit weights on the full sample space, the density factor is one. For unit weights on an admitted subset, it is `q^r/|admitted|`. A selection law that concentrates weight on a small set therefore requires its own density estimate before the `1/q` scale follows.

## Proof map and limits

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Nonuniform selected-event mass | `XedniSelectionLaw.selected_dependent_lift_weight_bound` | Prime `q`, compatible selected lifts, bounded witness `B < q`, complete fixed candidate list, point weights bounded by `M` on the admitted set |

The imported `XedniObstruction.lean` is an exact copy of the corrected source at PR #1554 commit `03525133f5b6f5110ad1ab1322d1ee9eec9f54a6`; its SHA-256 is recorded in `DEPENDENCIES.json`. The new theorem depends on its `selected_dependent_lift_sample_count`. The height-theoretic bounded-witness principle and an actual density bound for any particular curve-selection procedure remain separate proof obligations.

Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9` are pinned. The saved `lake build SelectionLaw` output records `#print axioms` for the new theorem and the 16 imported results; all use only standard Lean foundations (`propext`, `Classical.choice`, `Quot.sound`). `verify.py` checks source and build hashes and rejects admitted proof placeholders. `lean4checker --fresh` was unavailable on this host.
