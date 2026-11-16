# Fixed-curve selected admission has a quadratic pair bound

For one fixed rank-one rational curve, one fixed reduction map, a coordinate cap `|k|≤K`, and `T` torsion labels, the checked theorem `selected_pair_capacity` bounds the number of ordered admitted reduced-point pairs by

`|A| ≤ [T(2K+1)]²`.

It applies to any selected pair set `A` whose two coordinates each have such a representation. The proof takes the image of the finite coordinate-and-torsion domain and places `A` inside its Cartesian square. It does not assume independent sampling or a particular admission algorithm.

## Complete fixed-curve census

The frozen curve is `E/Q: y²=x³−x−2`, with rational generator `P=(2,2)`, rank one, and trivial torsion as checked in the pinned parent Sage control. For each selected field, `G=m(P mod p)` has subgroup order `q`; the public-point workload uses `Q=17G`, `R(t)=Q−tG`, and every ordered offset pair in `[0,q)²`. The admission rule is exactly `R(t)=k(P mod p)` for some integer `−4≤k≤4`.

| Field prime | `q` | `m` | Admitted offsets | Full admitted pair support | Distinct nonidentity admitted pairs |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 313 | 331 | 1 | 9 | 81 | 56 |
| 421 | 439 | 1 | 9 | 81 | 56 |
| 431 | 419 | 1 | 9 | 81 | 56 |
| 547 | 571 | 1 | 9 | 81 | 56 |
| 571 | 599 | 1 | 9 | 81 | 56 |
| 593 | 313 | 2 | 5 | 25 | 12 |
| 617 | 293 | 1 | 9 | 81 | 56 |
| 677 | 353 | 1 | 9 | 81 | 56 |
| **Total** | | | **68** | **592** | **404** |

The complete query law has **1,471,112 ordered pairs**. Seven fields attain the theorem's 81-pair bound. At `p=593`, the reduction of `P` has order `2q`; only the five even coordinates `−4,−2,0,2,4` land in the target subgroup, so that field has 25 admitted pairs. Filtering identity points and duplicates leaves the final 404 distinct nonidentity pairs. The raw gzip rows retain the status of every ordered pair, including all rejected pairs. The target scalar 17 constructs and checks the public fixture; it is not used in the admission decision.

The producer used the pinned finite-group implementation. An independent checked-Sage audit recomputed the curve, orders, generator and target, all 3,318 offset memberships, and all 1,471,112 pair statuses from the raw rows. Its status is `PASS`; stderr is empty. `./sage --runtime-info` was saved before that run. These are exact counts, with no wall-time comparison.

## Proof map and scope

| Result | Lean declaration | Exact hypotheses |
| --- | --- | --- |
| Selected ordered-pair capacity | `XedniFixedCurveAdmission.selected_pair_capacity` | One fixed `g:ZMod q`, one fixed torsion-label map `Fin T→ZMod q`, one common cap `K`, and a representation of both entries of every pair in `A` |

The module pins Lean `v4.35.0-rc4` and Mathlib `021c46bdd042f67b538b9f9871d556a93713a9a9`. `cd formal && lake build SelectedAdmission` succeeds; `#print axioms` lists only `propext`, `Classical.choice`, and `Quot.sound`. There is no `sorry`, `admit`, custom research axiom, or native proof step. The exact fixed-curve rank and torsion assertions are from the pinned Sage parent control; the Lean theorem itself is a statement about its finite reduction image. `lean4checker --fresh` was unavailable on this host.

The square bound needs the **same** generator image and torsion-label map for both points and all selected pairs. A policy that chooses a different rational curve, generator, or reduction map after seeing each pair is outside these hypotheses; applying 81 to such a policy would be invalid. The next experiment should freeze a family of allowed curve choices and count its union of admitted pair images, including every curve-search probe and failed candidate.
