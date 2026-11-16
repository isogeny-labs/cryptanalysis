# Prefix equality-pattern bridge proof map

Lean 4 v4.35.0-rc4; Mathlib revision
021c46bdd042f67b538b9f9871d556a93713a9a9.

| Mathematical result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Same trace equality pattern admits a domain permutation | `equal_pattern_perm` | Finite group-element domain; `x i = x j ↔ y i = y j` for every index pair |
| Same pattern gives equal label-event counts | `equal_pattern_label_event_card_eq` | Finite group-element and label domains; same equality pattern; arbitrary event on visible labels |
| Eligible evaluations match symbolic equality | `eval_eq_iff_form_eq` | Finite field; scalar outside informative collision set |
| Eligible scalars share each visible-label event count | `eligible_label_event_card_eq` | Both scalars outside the prefix collision set |
| Eligible scalar lower bound | `eligible_card_lower` | Finite field; `n` old forms; lower bound `q − n²` |
| New candidate upper bound and membership | `next_candidates_card_le`, `new_eq_mem_candidates` | Finite field; one next form; symbolically distinct equality for membership |
| Weighted next-candidate bound | `weighted_next_candidate_bound` | Fixed old form list, next form, and visible label tuple |
| Weighted first-hit bound | `weighted_first_hit_bound` | Same fixed prefix; designated first-hit finset contained in eligible next candidates |

The one-step theorem quantifies over any fixed affine form list and visible
label tuple. It does not yet quantify over a complete adaptive program or
establish that every run is placed in exactly one compatible prefix bucket.
That connection needs the prior `formsFromTranscript` theorem, the program
run invariant, and a stopping partition that recognizes known symbolic
repeats. The earlier first-collision ledger then aggregates the resulting
stage inequalities. A coordinate-guided selection rule requires its own
model of observations and encoding law.

`lake build PrefixPatternBridge` completed 3,145 jobs. All twelve new
`#print axioms` lines list only `propext`, `Classical.choice`, and
`Quot.sound`. The source has no placeholder, custom research axiom, or
native evaluation. `lean4checker --fresh` is unavailable on this host.
