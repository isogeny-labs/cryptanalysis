# Short trace sums span the order-61 relation space of a 39-point conductor-four class

At the prespecified D=-79, conductor-four prime **p=317**, 15 rank-increasing short group-law cancellations raise the rational X_0(11) class matrix from **rank 23 to 38 over both ℚ and F₆₁**. The ambient group has order 305=5·61. A nonzero 39-coordinate order-61 projection vector annihilates every verified class row, giving the matching F₆₁ rank ceiling 38. This extends the short trace-closure observation from the preceding 20-point conductor-two panels to a **39-point** class.

| Stage | Rows or candidates | Rank over ℚ | Rank over F₆₁ |
| --- | ---: | ---: | ---: |
| Individually class-closed degree-2/5 rows | 18 rows | 18 | 18 |
| Plus individually closed degree-13 orbit traces | 5 rows | 23 | 23 |
| Plus support-two auxiliary-sum cancellations | 4 independent of 4 valid | 27 | 27 |
| Plus support-three auxiliary-sum cancellations | 11 independent of 76 valid | 38 | 38 |

The [protocol](PROTOCOL.md) predicted 40 rational points from ring class numbers 5, 5 and 10 under a two-rational-lifts-per-j assumption. The [independent exhaustive class audit](class_audit.py) found conductor-stratum point counts **10, 9 and 20** instead: the conductor-two root `j=196` has exactly one rational X_0(11) lift in F_317. Exhaustively scanning the 305-point ambient curve found precisely the saved 39 class points. The prediction failed by one point, and the frozen p=317 instance was retained.

The other frozen prediction held: modulo 13, `X²−2X+317` has distinct roots 4 and 11, whose projective ratio `4/11=11` has exact order twelve. All **39** degree-13 neighbor-x polynomials factor as `(1)(1)(12)`. The checked-Sage [producer](run.py) lifted all squarefree fibers into F_(317¹²), reconstructed fourteen y-coordinates from power moments, checked their curve equations and Hecke group sums, and saved every Frobenius orbit trace in [result.json](result.json). Five source equations close individually; 34 retain outside traces. Sources 7 and 22 each have one lifted neighbor at x=16, the pole of the rational j-map: their other thirteen neighbors passed finite-j modular-polynomial checks, and all fourteen remained in the moment, curve, group-sum and orbit checks. The initial finite-j assertion failed at source 7; [ATTEMPTS.json](ATTEMPTS.json) retains that failed source and logs alongside the completed rerun.

The [independent integer-field replay](verify.py) re-counted the 305 curve points, matched the exhaustive 39-point class census, checked every saved trace and class relation by separate F_317 group arithmetic, and reproduced ranks 18→23→27 over ℚ and F₆₁. A [separate checked-Sage audit](validate_sage.py) refactored all 39 neighbor-x polynomials, re-enumerated class membership, and found x=16 roots exactly at sources 7 and 22. Both validation receipts are saved as [validation.json](validation.json) and [sage-validation.json](sage-validation.json).

The [search manifest](search_inputs.json) hash-binds those outputs and the class audit. The pure-Python [search](search.py) exhausted all signed source supports of size one, two and three, accepting only an identity sum of outside Frobenius-orbit **group points**. It retained **zero support-one, four support-two and 76 support-three** valid combinations in [search-result.json](search-result.json), including dependent rows. The four support-two rows are exactly the four equal-outside-trace pairs `(8,38)`, `(9,21)`, `(12,19)` and `(23,36)`. The independent checked-Sage [search replay](verify_search.py) rebuilt all 80 accepted combinations, independently checked their group identities and deterministic rank path, and found a one-dimensional F₆₁ right kernel in [search-validation.json](search-validation.json).

For the rank ceiling, multiplying each class point by cofactor five gives its order-61 projection. Thirty-eight projections are nonzero and point 0 projects to identity. Their saved coordinate vector is nonzero and annihilates all 103 baseline and accepted rows. The **23 baseline rows and 15 selected rows** contain an explicit invertible 38×38 minor modulo 61, giving the lower bound. The pinned Lean [finite certificate](formal/ShortP317.lean) checks all 103 row annihilations, the minor and inverse, the 15 signed integer row identities, and the modulo-13 eigenvalue-ratio order twelve; [formal/CHECK.md](formal/CHECK.md) records the build and axiom audit. The written group argument is `C_i+U_i=0` and `Σ ε_i U_i=0` imply `Σ ε_i C_i=0`. The [proof map](formal/PROOF_MAP.json) identifies the curve, Hecke and abstract-rank formalization bridge still open in Lean.

This is a complete F₆₁ relation-space result for the fixed 39-point class under the saved group-law equations, with `candidate_id: null` and `target_online_ms: null`. The next discriminatory experiment should increase the class further or change the fundamental discriminant while keeping the same support cap and preserving zero-yield cells. It should measure how accepted short cancellations and rank increments scale with class size, rather than infer scaling from these two class sizes alone.

Reproduce from the repository root:

```sh
./sage --runtime-info > experiments/hecke-d79-conductor4-20261027/sage-runtime-info.txt
gtimeout 120 ./sage -python experiments/hecke-d79-conductor4-20261027/class_audit.py
gtimeout 1200 ./sage -python experiments/hecke-d79-conductor4-20261027/run.py
python3 experiments/hecke-d79-conductor4-20261027/verify.py
gtimeout 180 ./sage -python experiments/hecke-d79-conductor4-20261027/validate_sage.py
gtimeout 120 python3 experiments/hecke-d79-conductor4-20261027/search.py
gtimeout 120 ./sage -python experiments/hecke-d79-conductor4-20261027/verify_search.py
cd experiments/hecke-d79-conductor4-20261027/formal
python3 generate.py
lake build ShortP317
```
