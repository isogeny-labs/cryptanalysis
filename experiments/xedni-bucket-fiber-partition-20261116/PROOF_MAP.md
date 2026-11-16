# Visible bucket proof map

Lean 4 v4.35.0-rc4 and Mathlib revision
`021c46bdd042f67b538b9f9871d556a93713a9a9`.

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Encoding fiber and accepted execution counts | `encodingFiber`, `acceptedCount`, `bucketMass` | Finite scalar, encoding and bucket types |
| Accepted count equals sum of bucket/scalar fibers | `accepted_count_eq_bucket_mass` | Arbitrary bucket function and bucket-dependent scalar predicate |
| Visible labels and reconstructed old forms for a typed program | `executionPrefixBucket`, `formsInBucket` | `Program L 2 m`, `2≤k≤m` for old forms |
| Actual live event iff bucket eligibility | `execution_live_iff_bucket_eligible` | Finite execution space; injective `s ↦ s • G` |
| Actual live cardinality equals eligible bucket mass | `execution_live_card_eq_bucket_mass` | Same hypotheses and `2≤k≤m` |
| Form at index `i` depends only on labels before `i` | `form_at_depends_on_earlier_labels` | Arbitrary finite typed program and field |
| Suffix completion and bucket next form | `extendBucket`, `nextFormInBucket`, `execution_next_form_eq_bucket` | `k<m`; arbitrary fallback label |
| Actual first hit iff bucket eligible next-candidate root | `execution_first_hit_iff_bucket_candidates` | `2≤k<m`; finite execution space; injective scalar-to-group map |
| Actual first-hit cardinality equals eligible candidate bucket mass | `execution_hit_card_eq_bucket_mass` | Same hypotheses and any fallback label |

The next-form theorem makes the fallback label irrelevant to the result:
every completion agreeing on the visible prefix yields the same stage form.
The hit identity therefore uses the old prefix's encoding fiber, including
failed and zero-fiber label tuples in the exact sum.

All 14 declarations have `#print axioms` receipts in the saved build output.
Their dependencies are limited to `propext`, `Classical.choice`, and
`Quot.sound` where applicable. The new module contains no placeholder,
custom research axiom, or unverified native evaluation.
`lean4checker --fresh` is unavailable on this host.
