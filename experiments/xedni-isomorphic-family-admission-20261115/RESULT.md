# Finite-family admission bound and translated-model control

For a fixed finite family of reduction images `S_i`, the checked Lean theorem `family_pair_capacity` bounds any ordered-pair set admitted by at least one member by

`|A| ≤ Σ_i |S_i|²`.

The bound counts the union of each image's pair square; it does not require independence or disjointness. When images coincide, the union is just one square. The companion Lean identities show that translating `x` by an integer `a` transforms `y²=x³−x−2` into `Y²=X³−3aX²+(3a²−1)X+(-a³+a−2)`, and that `a≡0 (mod p)` returns the original coefficients modulo `p`.

## Four rational models per field

For each of the eight frozen fields, take `a=jp`, `j∈{0,1,2,3}`. These are 32 distinct integral rational models with generator `P_j=(2+a,2)`. The explicit translation gives a rational isomorphism with the fixed rank-one curve. Each model reduces to `y²=x³−x−2` at its field prime, and `P_j` reduces to the same point `(2,2)`. The checked-Sage audit verified the discriminant, point equations, mapped multiples `kP_j` for every `−4≤k≤4`, and the complete finite-field image equality.

| Field prime | Subgroup order | Per-model admitted pairs | Four-model union | Additional pairs | Candidate pair tests |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 313 | 331 | 81 | 81 | 0 | 438,244 |
| 421 | 439 | 81 | 81 | 0 | 770,884 |
| 431 | 419 | 81 | 81 | 0 | 702,244 |
| 547 | 571 | 81 | 81 | 0 | 1,304,164 |
| 571 | 599 | 81 | 81 | 0 | 1,435,204 |
| 593 | 313 | 25 | 25 | 0 | 391,876 |
| 617 | 293 | 81 | 81 | 0 | 343,396 |
| 677 | 353 | 81 | 81 | 0 | 498,436 |
| **Total** | | **592** | **592** | **0** | **5,884,448** |

The complete ordered query law contains **1,471,112 pairs**. The producer tested all four model images for every pair and saved a four-bit mask for every query, including zero-mask failures. It constructed 32 model records and charged four membership probes per pair. The independent checked-Sage audit replayed all 1,471,112 masks and returned `PASS` with empty stderr. These are exact candidate counts, not wall times. The formal sum-of-squares bound evaluates to 2,368 across the eight fields before accounting for identical images; the observed union is 592.

## Proof map and scope

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Family union bound | `XedniFamilyAdmission.family_pair_capacity` | Finite model index set, fixed image set per model, and each admitted pair contained in one model's image square |
| Rational translation identity | `translated_polynomial` | All integers `a,x` |
| Coefficients recover the fixed model modulo `p` | `translated_coefficients_reduce`, `multiple_shift_reduces` | Any `a` vanishing in `ZMod p`; in particular `a=j p` |

The formal package pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `lake build FamilyAdmission` passes. Each `#print axioms` reports only standard Lean foundations (`propext`, `Classical.choice`, `Quot.sound` as applicable). There is no `sorry`, `admit`, custom research axiom, or unverified native proof step. `lean4checker --fresh` was unavailable on this host.

The experiment varies equations inside **one rational isomorphism class with identity reduction**. It shows that counting distinct rational models overstates the number of distinct bounded reduction images in this family. A nonisomorphic family can have different images and must be evaluated with its own rank, torsion, reduction, admission union, and candidate-search costs. The next test is to construct such a finite family under a frozen resource cap and measure whether its union grows faster than its charged candidate work.
