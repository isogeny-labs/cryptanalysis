# Short outside-trace cancellations complete the p=179 order-13 class relation space

Eight exact signed combinations of the degree-13 outside-trace equations raise the D=-79, conductor-2 class relation matrix from **rank 11 to rank 19 over both ℚ and F₁₃**. The 20 class points all have nonzero projection into the order-13 subgroup of X_0(11)(F_179), and their projection vector annihilates every verified group-law row. It gives the matching rank ceiling 19. Thus these short cancellations span the full 19-dimensional relation space modulo 13 for this fixed class.

| Stage | Rank over ℚ | Rank over F₁₃ | New independent rows |
| --- | ---: | ---: | ---: |
| Degree-2/5 baseline plus one individually closed degree-13 trace | 11 | 11 | — |
| Three support-two outside-sum cancellations | 14 | 14 | 3 |
| Five support-three outside-sum cancellations | 19 | 19 | 5 |

The [frozen protocol](PROTOCOL.md) searched all support-one, support-two and support-three subsets of the 19 outside degree-13 source equations, with first coefficient +1 and later coefficients in fixed `(-1,+1)` order. It accepted a combination only when its **sum of auxiliary trace points in the elliptic-curve group** was identity. This is broader than matching the complete outside-trace multiset: the preceding exact-pair check found zero, while group addition finds four valid support-two and thirteen valid support-three combinations. There were no support-one cancellations. The [complete result](result.json) retains all 17 candidates, including dependent rows, and the first eight rank-increasing choices.

For each source equation, write `C_i + U_i = 0`, where `C_i` is its integer class-point row and `U_i` is the sum of outside Frobenius-orbit traces. The search checks `Σ ε_i U_i = 0` using only F_179 group arithmetic, then obtains the exact class relation `Σ ε_i C_i = 0`. It does not query scalar logarithms to generate rows. The checked-Sage [validator](verify.py) independently rebuilt all 19 source sums, enumerated every signed combination, checked every accepted class relation, and reproduced the exact ℚ/F₁₃ rank path. It returned `D79_P179_SHORT_CANCELLATIONS_PASS candidates 17 rank_mod13 11 -> 19` in [validation-stdout.txt](validation-stdout.txt).

For the rank ceiling, multiply each class point by cofactor 15 into the subgroup of order 13. All 20 projections are nonzero and are represented by the saved [projection coordinates](result.json) relative to the first projection. Every relation row annihilates that nonzero vector modulo 13, so its row space has dimension at most 19. An explicit 19×19 minor of the eleven baseline rows plus eight selected rows has an inverse modulo 13, giving dimension at least 19. The pinned Lean [finite certificate](formal/ShortP179.lean) checks the projection annihilation for all 28 baseline and candidate rows, the minor/inverse product, and the eight signed row identities. The build and `#print axioms` audit passed; only standard `propext` appears where reported. The [proof map](formal/PROOF_MAP.json) names the remaining elliptic-curve and abstract linear-algebra formalization bridge.

This result shows that zero exact auxiliary-trace matches did not prevent complete order-13 closure at p=179. The 17 valid group-sum combinations arise in a group of order 195 and should be tested against larger fields and classes before any scaling inference. A next prespecified experiment should use the same support and coefficient rule at a third eligible D=-79 prime or at a larger class, retaining the full failure/zero-yield census. This is relation-stage evidence; `candidate_id` and target-dependent costs are null.

Reproduce from the repository root:

```sh
gtimeout 60 python3 experiments/hecke-d79-p179-short-cancellations-20261027/run.py
./sage --runtime-info > experiments/hecke-d79-p179-short-cancellations-20261027/sage-runtime-info.txt
gtimeout 90 ./sage -python experiments/hecke-d79-p179-short-cancellations-20261027/verify.py
cd experiments/hecke-d79-p179-short-cancellations-20261027/formal
python3 generate.py
lake build ShortP179
```
