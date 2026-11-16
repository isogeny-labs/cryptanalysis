# Two nonisomorphic rank-one lifts expand bounded pair admission

Two curves selected from a frozen 24-candidate screen have proved rank one, trivial rational torsion, and rational generators whose reductions are `3G` on the fixed finite-field curve. They occur at field primes **571** and **677**. Adding each to the base rank-one curve, whose generator reduces to `G`, expands that field's bounded `|k|≤4` ordered-pair image from 81 to **153** points. The two checked Lean theorems `pair_union_card_599` and `pair_union_card_353` prove the exact 153 count for the corresponding subgroup orders.

Across the complete eight-field public-pair law, the qualified family admits **736** ordered pairs versus **592** for the base curves: 144 additional pairs. The post-screen census charges **1,954,522 candidate pair-membership tests** across 1,471,112 public queries. These are exact component counts; the rank screen and generator checks are separate setup work.

## Frozen curve screen

For each selected field, take `uG` for `u=1,2,3`, center its coordinates `(x,y)`, and construct `E_u/Q: Y²=X³−X+B` with `B=y²−x³+x` and rational point `(x,y)`. Every model is nonsingular and reduces to the fixed finite-field curve at its field prime. The checked-Sage worker attempted `E.rank(proof=True)` under a 12-second per-candidate cap and computed rational torsion exactly. Every candidate point was checked to be nontorsion.

| Outcome | Candidate curves |
| --- | ---: |
| Rank 1 proved | 9 |
| Rank 2 proved | 5 |
| Rank 3 proved | 5 |
| Rank 4 proved | 3 |
| Exact rank unresolved, lower bound 1 reported | 2 |
| Worker failure or timeout | 0 |

The unresolved cells are `(p,u)=(571,2)` and `(593,3)`; both have trivial torsion and valid reduction, but their exact ranks are left unknown. The screen retains their Sage diagnostics and raw stdout. It does not promote them into the rank-one family.

The nonbase rank-one cells are:

| Field prime | Subgroup order | `u` | Rational `B` | Proved rational generator | Pair union with base | Additional pairs |
| ---: | ---: | ---: | ---: | --- | ---: | ---: |
| 571 | 599 | 3 | 4,175,721 | `(-161,-51)` up to sign | 153 | 72 |
| 677 | 353 | 3 | 14,997,579 | `(-246,333)` up to sign | 153 | 72 |

An independent checked-Sage audit reran the rank and generator proofs for these two curves, verified their torsion orders, compared their exact `j` invariants with the base curve, checked the rational points and reductions, and replayed all saved pair masks. The generator check found each selected point equal up to sign to the returned Mordell–Weil generator. The curves are genuinely nonisomorphic to the base over `Q`, as their exact `j` invariants differ.

## Admission and proof boundary

The base curve is retained on all eight fields, including `p=593`, where its generator reduction has order `2q` and yields 25 admitted pairs. The two new curves add distinct bounded images only on `p=571` and `p=677`:

| Field prime | Qualified models | Base pairs | Union pairs | Candidate pair tests |
| ---: | ---: | ---: | ---: | ---: |
| 313 | 1 | 81 | 81 | 109,561 |
| 421 | 1 | 81 | 81 | 192,721 |
| 431 | 1 | 81 | 81 | 175,561 |
| 547 | 1 | 81 | 81 | 326,041 |
| 571 | 2 | 81 | 153 | 717,602 |
| 593 | 1 | 25 | 25 | 97,969 |
| 617 | 1 | 81 | 81 | 85,849 |
| 677 | 2 | 81 | 153 | 249,218 |
| **Total** | **10 field-model cells** | **592** | **736** | **1,954,522** |

For either qualifying subgroup, the two 9-element generator images overlap in three elements (`−3G, O, 3G`). Their pair squares overlap in nine pairs, giving `81+81−9=153`. The prior checked `family_pair_capacity` theorem applies to this selected finite family. `formal/UnionCount.lean` proves the exact modular counts with kernel-checked `decide`, then combines them through the finite-set union cardinality identity; it does not use native evaluation. The preceding checked `AdaptiveInverseLift.reduction_model` theorem covers the rational-model coefficient reduction rule. The exact rank, torsion, generator, and `j` certificates are checked in Sage; those elliptic-curve facts have not been formalized in Lean, so the formalization of the full arithmetic witness is partial.

The family was selected **after** inspecting the 24 rank-screen outcomes. Its gain is a measured finite-panel admission result, not an unseen-field yield estimate. Pair admission alone is not a rational relation: the next experiment must test a frozen relation-vector family on every qualified pair, retain failed relation rows, and charge the 24-curve rank screen and pair-membership work when comparing a full procedure.

## Reproduction

The initial `protocol.json` pins all eight fields, `u=1,2,3`, the curve law, and rank timeout. `post-protocol.json` pins the screen result and the rule selecting only proved rank-one, trivial-torsion nonbase curves. The checked Sage launcher and runtime receipt were used for every Sage worker and audit. From the repository root, run `python3 experiments/xedni-nonisomorphic-family-screen-20261115/screen.py`, then the corresponding `post.py`, the checked `./sage -python experiments/xedni-nonisomorphic-family-screen-20261115/audit.py`, and `verify.py`. The two protocol files, all 24 worker stdout/stderr records, two generator-check records, every post-screen pair mask, formal build output, and file seal are retained.
