# A split-degree-3 holdout exposes a second floor-kernel mechanism

The prospective D = −431, conductor-6 class walk at `p = 12343` **falsified the frozen floor-rank prediction of 6**. Its checked-Sage relation matrix has 252 points, 210 verified Hecke rows, full rank 168, and nonfloor projected rank 158, so its floor kernel has dimension **10**. Six directions are the predicted signed degree-2 cycles. Four more come from two conductor-2 degree-3 cycles of length 21, each with a two-dimensional period-three kernel. Ten exact signed row combinations were independently replayed and have rank 10 modulo three primes; combined with the exact rational rank difference, they span this matrix's floor kernel.

| Quantity | Frozen prediction | Observed |
| --- | ---: | ---: |
| Rational class points | 252 | 252 |
| Degree-2 / degree-3 rows | 126 / 84 | 126 / 84 |
| Signed degree-2 cycles | 6 of length 14 | 6 of length 14 |
| Conductor-2 degree-3 lower signatures | All distinct | All distinct |
| Floor-only row-space dimension | **6** | **10** |
| Degree-3 contribution to that dimension | Implicitly 0 | 4 |

## Frozen selection and producer evidence

`search_protocol.json` selected the first squarefree `d` in `[300,1500]` with `d ≡ 23 (mod 24)`, `h(−9d) = 2h(−d)`, and a predicted signed norm-2 orbit count between 6 and 12. `select.py` selected `d = 431` after six eligible discriminants: `h(−431) = 21`, `h(−3879) = 42`, and the norm-2 class in the conductor-3 order has order 14. The first permitted prime is `p = 92² + 9·431 = 12343`, with `u = 184` and `u² − 4p = −431·6²`. `producer_protocol.json` froze that instance, source hashes, class/row counts, and the rank-six hypothesis before the gate or producer ran.

The two-sheet gate passed with conductor-stratum point counts 42, 42, 84, and 84. `audit.py` reconstructs every saved point and row, checks each point's endomorphism conductor and the classical modular-polynomial root counts, verifies the elliptic-curve group sums, and computes exact ranks over ℚ. Pure-Python reduced-form enumeration independently confirms class numbers 21, 21, 42, and 42. The saved group `X₀(11)(F₁₂₃₄₃)` has order 12125, whose largest prime factor is 97.

## Revised cycle explanation

The 84 conductor-3 degree-2 rows form six signed incidence components of length 14. Each alternating row sum cancels all nonfloor terms and leaves 14 `{−1,1}` floor coefficients. Their supports partition the 84 conductor-6 columns, giving six independent floor directions as forecast.

The 42 conductor-2 degree-3 rows project to **two 21-point cycles**. On each cycle the row sourced at point `i` has coefficient 1 at its source and its two adjacent conductor-2 points, and no other nonfloor coefficient. A dependency with row coefficients `aᵢ` therefore obeys

`aᵢ₋₁ + aᵢ + aᵢ₊₁ = 0`.

Subtracting consecutive equations gives `aᵢ₊₃ = aᵢ`. Over ℚ, a cycle of length `L` has no nonzero solutions when `3 ∤ L`; when `3 | L`, the coefficients repeat a triple `(a,b,c)` with `a+b+c=0`, giving dimension 2. The norm-3 ideal class has order 21 in the conductor-2 order, matching both observed cycle lengths. Each 21-cycle supplies two explicit signed row certificates, for four additional floor directions. Although every degree-3 row has a distinct lower signature, groups of rows cancel together; pairwise-signature uniqueness was therefore too weak a rank gate.

`cycle_model.py` replays this rule on the earlier D = −215 control, whose two norm-3 cycles have length 14 and projected nullity 0, and on the D = −431 holdout, whose two cycles have length 21 and projected nullity 4. `combined.py` independently sums the six degree-2 and four degree-3 certificates from the saved rows, checks that every result is floor-supported, and obtains rank 10 modulo 23, 1000000007, and 2147483647. The rational rank difference is also 10. The revised cycle rule was formulated after the D = −431 mismatch; it needs a fresh prospective class before being treated as a predictive law.

## Proof map and next gate

The written recurrence proof above covers the cycle-rank step. `formal/CycleKernel.lean` proves `CycleKernel.period_three` and the length-14 trivial-kernel consequence `CycleKernel.cycle14_trivial` in Lean `v4.35.0-rc4` with Mathlib pinned to `021c46bdd042f67b538b9f9871d556a93713a9a9`. The actual 21-cycle incidence and four explicit row combinations are replayed in `cycle_model.json`; their union with the six degree-2 certificates is verified in `combined.json`. The exact matrix-rank bridge and a general Lean theorem for all cycle lengths remain open. `#print axioms` reports only `propext`, `Classical.choice`, and `Quot.sound`; `lean4checker --fresh` was unavailable.

The next experiment should freeze the revised prediction for a third fundamental discriminant with split 2 and 3, including both norm-prime orders and their divisibility by 3, before running a producer. It must retain failed gates and test whether the degree-2 and degree-3 floor spans stay independent. This bundle is a relation-stage diagnostic with `candidate_id: null` and `timing_claim: null`. Run Sage through `/Volumes/SSD990/cryptanalysis/sage`; use `lake env lean CycleKernel.lean` in `formal/` for the checked proof. `SEAL.json` binds the scripts, protocols, data, receipts, and report.
