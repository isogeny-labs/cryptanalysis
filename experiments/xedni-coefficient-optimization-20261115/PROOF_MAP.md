# Proof map

The formal project pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. It imports an exact copy of the checked `FiniteFamilyCoverage.lean` from PR #1616 (source SHA-256 `fdf811a13b55e09acac1665a9c282b37b8ddd89fffee6c504cfcaabb82067381`). The build and all `#print axioms` outputs are in `formal/build-output.txt`.

| Result | Lean declaration | Exact hypotheses | Status |
| --- | --- | --- | --- |
| Selected integer family has 13 distinct vectors | `selected_integer_card` | Exact listed selected family | Checked |
| All selected integer sums are nonzero | `selected_integer_effective` | Exact listed family | Checked |
| Field reduction has at most 13 vectors | `selected_field_card_le` | Any field `K`, any ring map `ℤ→K` | Checked |
| Reduced selected-family coverage bound | `selected_coverage_bound` | Any field `K`, ring map `ℤ→K`, finite offset set `T`; winners are the reduced relation candidates | Checked |
| A reduced relation selects one scalar | imported `relation_eq_candidate` | Effective coefficient sum, reduced equation | Checked in imported module |
| Every reduced relation lies in winners | imported `relation_mem_winners` | Effective coefficient, membership in family and offset set, reduced equation | Checked in imported module |

`audit.py` verifies that all selected vectors remain effective modulo each validation subgroup order, checks curve and subgroup orders, and connects the reduced equation to every recorded elliptic-curve hit. The exact hit counts and abstract add-call totals are independently audited executable results, not Lean theorems. `lean4checker --fresh` was unavailable on this host.
