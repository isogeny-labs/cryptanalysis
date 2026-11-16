# Typed adaptive prefix proof map

Lean 4 v4.35.0-rc4; Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9.

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Extract a typed prefix program | `takeAt` | `Program L n m`, requested `k`, proofs `n≤k≤m` |
| Group execution of prefix equals complete execution prefix | `runGroup_takeAt` | Additive group, bijective encoding, initial points, same stage bounds |
| Affine reconstruction of prefix equals complete reconstruction prefix | `formsFromTranscript_takeAt` | Field, prescribed complete labels, initial forms, same stage bounds |
| Reconstructed form prefix ignores unseen suffix labels | `form_prefix_depends_only_on_visible_labels` | Two complete label tuples agreeing in their first `k` positions |
| Actual and symbolic public-input prefix label predicates agree | `dlp_prefix_labels_iff_symbolic` | Field, group/module, `Program L 2 m`, encoding, `G,w`, `2≤k≤m` |
| Actual and symbolic prefix encoding counts agree | `actual_prefix_fiber_count_eq_symbolic` | Finite group and label domains plus the public-input conditions above |

`restrictLabels` and `prefixSymbolicFiberCount` define the restricted
visible tuple and exact symbolic encoding cardinality. The prefix theorem
quantifies over every proposed complete label tuple; its conclusion
uses only the first `k` labels and forms, as shown by the suffix
independence theorem. The group and affine prefix equalities are
structural statements about the typed adaptive program, not empirical
assumptions.

The remaining bridge to `aggregate_bucket_bound` is the first-hit
predicate: establish for each scalar and encoding that being live at stage
`k` is equivalent to eligibility of the reconstructed old forms, and
that a new informative equality lies in the eligible next-candidate
set. Then partition by prefix labels and use the exact fiber counts
established here to discharge the aggregate theorem's two mass identities.
The initial `G=Q` event requires a separate term.

`lake build TypedPrefixProgram` completed 3,148 jobs. All eight new
`#print axioms` receipts contain only `propext`, `Classical.choice`, and
`Quot.sound` where applicable. The source has no placeholder, custom
research axiom, or native evaluation. `lean4checker --fresh` is
unavailable on this host.
