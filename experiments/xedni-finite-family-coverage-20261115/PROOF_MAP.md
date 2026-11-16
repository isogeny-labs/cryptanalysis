# Proof map

The checked Lean module is `formal/FiniteFamilyCoverage.lean`; Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9` are pinned. `formal/build-output.txt` contains the successful build and each `#print axioms` output.

| Mathematical step | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| One relation selects a unique scalar | `relation_eq_candidate` | Field `K`; `a+b≠0`; reduced equation `(a+b)d=bt` | Checked |
| Relation enters finite coverage image | `relation_mem_winners` | Coefficient in `C`, offset in `T`, `a+b≠0`, reduced equation | Checked |
| Coverage cardinality | `card_winners_le` | Finite `C,T`; `winners` is the image of `C×T` | Checked |
| Explicit family and offset caps | `card_winners_le_cap` | `|C|≤B`, `|T|≤L` | Checked |
| Frozen effective integer family size | `effective_integer_family_card` | The exact 14-vector list, filtered by integer `a+b≠0` | Checked |

The step from an elliptic-curve relation to the reduced field equation and the identification of effective vectors modulo each `q` are verified across the eight specified groups by `audit.py`; they are not included as elliptic-curve Lean declarations. Uniform-target probability follows by dividing the checked coverage count by the `q−1` nonzero scalars. The census counts and earliest-query records are executable results checked independently by the Sage audit, not Lean theorems.
