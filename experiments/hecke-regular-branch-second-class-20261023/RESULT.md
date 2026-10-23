# A second CM class confirms the regular-branch matrix contribution

At `D_K = −215`, conductor `f = 6`, and `p = 2131`, the regular point `(16 : 60 : 1)` belongs to the conductor-6 class and restores **one class column, two verified Hecke rows, and one independent row-space direction**. The regularized class walk has 168 columns, 140 rows, and rank 112; the original `x = 16` guard gives 167 columns, 138 rows, and rank 111. A point-identity comparison preserves all 138 original rows and finds exactly two new rows, both containing the restored point. The nonfloor projected rank is 108 in both matrices, so this new direction is supported in the floor kernel of the projection.

| Quantity | Frozen pre-run expectation | Original guard | Regularized evaluator |
| --- | ---: | ---: | ---: |
| Rational class points | 168 | 167 | 168 |
| Degree-2 rows | 84 | 83 | 84 |
| Degree-3 rows | 56 | 55 | 56 |
| Full rank over ℚ | Unspecified | 111 | 112 |
| Nonfloor projected rank over ℚ | Unspecified | 108 | 108 |

## Selection and pre-run gates

The first frozen search, `search_protocol.json`, tested the D = −1407, conductor-6 family for `11 ≤ v ≤ 5000`, with `p = v² + 12663` and `u = 2v`. It examined 336 prime cases and found no second prime whose `j = −121` reduction had the required class trace and compatible endomorphism conductor. The broader search rule was then frozen in `general_search_protocol.json`: select the first prime in `[2000,100000]` for which the `j = −121` Frobenius discriminant is a fundamental discriminant times `6²` and the endomorphism-order conductor is 6. It selected `p = 2131` after 18 primes. Here `|t| = 28`, `t² − 4p = −215 · 6²`, and `j = −121 ≡ 2010 (mod 2131)`. A direct Legendre-symbol count on an independent short-Weierstrass model confirms `|t| = 28`; the sign differs by a quadratic twist, as expected for a fixed `j`.

Before either producer run, `fiber_gate.py` found two rational X₀(11) points above every relevant class `j`, with point counts 28, 28, 56, and 56 for conductors 1, 2, 3, and 6. Pure-Python reduced-form enumeration independently gives the corresponding class numbers 14, 14, 28, and 28. `producer_protocol.json` froze the selected field, source hashes, class and row-count expectations, and paired original/regularized source paths before production. The rank was left unspecified because the earlier signed-floor model assumes a different behavior of the degree-3 prime for its D1407 forecast.

## Verification and scope

`audit.py` reconstructs all 168 regularized points and all 140 saved rows, checks the endomorphism conductor of each `j`, compares Hecke-root and classical-modular-polynomial root counts, verifies every elliptic-curve group sum, and computes full and nonfloor projected ranks over ℚ. It locates `(16 : 60 : 1)` at conductor 6. `compare.py` maps both matrices by encoded point identity and verifies the exact row delta and ranks modulo 11, 23, 1000000007, and 2147483647. `validate.py` independently recounts the 18 search primes by Legendre symbols, rechecks the fundamental discriminant and class numbers, and binds the producer and audit receipts. The checked Sage runtime receipt precedes the Sage runs. All audits passed.

The saved curve has `#X₀(11)(F₂₁₃₁) = 2200`; its largest prime-order factor is 11. This experiment measures a class-walk relation matrix, with `candidate_id: null` and `timing_claim: null`. The next mathematical step is to derive the D = −215 floor-kernel rank 4 from its ideal-class quotient and signed incidence structure, then test that rule on a new frozen class with the same split-prime behavior.

Use `/Volumes/SSD990/cryptanalysis/sage` for all Sage reproduction commands. `SEAL.json` hashes the exact scripts, protocols, data, and receipts.
