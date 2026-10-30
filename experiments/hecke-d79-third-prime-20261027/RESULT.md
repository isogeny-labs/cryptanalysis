# Third-prime holdout confirms order-four fibers and complete F₄₁ class relation rank

At the prespecified D=-79, conductor-2 prime **p=223**, all 20 degree-13 Hecke neighbor-x fibers have the predicted squarefree pattern `(1)(1)(4)(4)(4)`. Their 20 source equations each contain outside-class Frobenius traces. A frozen support-at-most-three group-law search finds 24 exact cancellations; nine selected rows raise the fixed class relation matrix from **rank 10 to 19 over both ℚ and F₄₁**. The nonzero order-41 projection of the 20 class points gives the matching F₄₁ rank ceiling.

| Stage | Rank over ℚ | Rank over F₄₁ | New independent rows |
| --- | ---: | ---: | ---: |
| Ten individually class-closed degree-2/5 rows | 10 | 10 | — |
| Degree-13 individually closed rows | 10 | 10 | 0 |
| Four support-two auxiliary-sum cancellations | 14 | 14 | 4 |
| Five selected support-three cancellations | 19 | 19 | 5 |

The [protocol](PROTOCOL.md) fixed the first-prime selector, the order-four prediction, degree-13 lift cap, and complete signed-combination rule before output. Here `p=12²+79=223` and the CM trace magnitude is 24. Modulo 13, `X²−24X+223` has distinct roots 4 and 7. Their ratio `7/4=5` has exact order four, predicting two fixed kernel lines and three four-cycles when the neighbor-x image is injective. The pinned Lean [module](formal/ShortP223.lean) checks these modular root and order identities. Every saved degree-13 factorization matches the prediction; the projective-kernel-to-neighbor-x bridge remains an explicit formalization obligation.

The checked-Sage [orbit producer](run.py) rebuilt the 20-point class, lifted all 20 degree-13 fibers into F_(223⁴), verified the fourteen y-coordinates by moments, modular-polynomial roots and Hecke sums, then saved every Frobenius orbit trace in [result.json](result.json). Its cap was 900 seconds and it completed. An independent integer-field [replay](verify.py) counted the 205-point ambient curve, checked every saved group equation and rational/F₄₁ rank. A separate checked-Sage [exhaustive audit](validate_sage.py) scanned the whole ambient group for j-trace magnitude 24, found exactly the saved 20 class points, and refactored every degree-13 neighbor polynomial. Both audits passed and are saved as [validation.json](validation.json) and [sage-validation.json](sage-validation.json).

The [search inputs](search_inputs.json) hash-bind those three completed receipts. The pure-Python [search](search.py) enumerated every source support of size one, two and three with the fixed coefficient order, accepting only combinations whose outside trace **group-point sum** is identity. It retained zero support-one, four support-two and twenty support-three candidates in [search-result.json](search-result.json). The independent checked-Sage [search replay](verify_search.py) rebuilt every auxiliary sum, all 24 class rows, the deterministic selection order, and the exact rank path; [search-validation.json](search-validation.json) records `PASS` and a one-dimensional right kernel over F₄₁.

For the upper bound, multiply each class point by cofactor five into the order-41 subgroup. Every projection is nonzero; the saved 20-coordinate projection vector annihilates all ten baseline and 24 accepted rows. For the lower bound, the ten baseline rows and nine selected rows contain an invertible 19×19 minor over F₄₁. The Lean finite certificate checks the 34 row annihilations, a nonzero vector, the minor and its explicit inverse, and all nine signed row identities. The written group-law implication is direct: if `C_i+U_i=0` for each source and `Σ ε_i U_i=0`, then `Σ ε_i C_i=0`. The [proof map](formal/PROOF_MAP.json) identifies the remaining curve and abstract-rank bridge in Lean; the checked-Sage validator covers the instantiated group and rank computations.

The matched p=179 and p=223 support-three searches now show full F_q relation rank in two different degree-13 Frobenius orbit geometries: order three with four length-three orbits at p=179, and order four with three length-four orbits at p=223. Both have only 20 class points and small ambient groups. The next discriminatory experiment should increase the class size, for example by freezing D=-79 conductor four with an eligible field prime, then apply the same support cap and preserve the complete zero-yield and rank census. These are relation-stage results with `candidate_id` and target online timing null.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/hecke-d79-third-prime-20261027/sage-runtime-info.txt
gtimeout 900 ./sage -python experiments/hecke-d79-third-prime-20261027/run.py
python3 experiments/hecke-d79-third-prime-20261027/verify.py
gtimeout 180 ./sage -python experiments/hecke-d79-third-prime-20261027/validate_sage.py
gtimeout 60 python3 experiments/hecke-d79-third-prime-20261027/search.py
gtimeout 90 ./sage -python experiments/hecke-d79-third-prime-20261027/verify_search.py
cd experiments/hecke-d79-third-prime-20261027/formal
python3 generate.py
lake build ShortP223
```
