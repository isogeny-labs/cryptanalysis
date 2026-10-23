# The revised split-prime floor rule passes a fresh D = −527 holdout

The preregistered D = −527, conductor-6 class walk at `p = 11467` has **eight floor-only row-space directions, exactly as predicted from both norm-prime orders**. Its checked-Sage matrix has 216 class points and 180 verified Hecke rows. The exact full rank is 144 and the nonfloor projected rank is 136. Four directions come from signed degree-2 cycles; two degree-3 cycles contribute two period-three directions each. Eight explicit integer row combinations were independently replayed, and their rank is eight modulo 23, 1000000007, and 2147483647, so they span the eight-dimensional rational floor kernel.

| Quantity | Frozen prediction | Observed |
| --- | ---: | ---: |
| Conductor-stratum point counts | 36, 36, 72, 72 | 36, 36, 72, 72 |
| Class points | 216 | 216 |
| Degree-2 / degree-3 rows | 108 / 72 | 108 / 72 |
| Signed norm-2 cycles | 4 of length 18 | 4 of length 18 |
| Norm-3 cycles | 2 of length 18 | 2 of length 18 |
| Degree-2 / degree-3 floor directions | 4 / 4 | 4 / 4 |
| Total floor-kernel dimension | **8** | **8** |

`selection_protocol.json` fixed the selection rule before any class was chosen. Among squarefree `d` in `[432,1500]` with `d ≡ 23 (mod 24)`, it required split-prime class-number behavior, a norm-3 order divisible by 3, and a revised floor-rank prediction between 6 and 20 but different from the earlier measured value 10. `select.py` chose `d = 527` after four discriminants. The conductor-3 norm-2 class and conductor-2 norm-3 class both have order 18; their relevant class numbers are 36 and 18. The frozen rule therefore predicted `2·36/18 = 4` signed degree-2 cycles and `2·18/18 = 2` degree-3 cycles, each supplying two period-three directions. It selected the first permitted prime `p = 82² + 9·527 = 11467`, with `u = 164` and `u² − 4p = −527·6²`.

`producer_protocol.json` froze those eight rank directions, all class and row counts, the field, and source hashes before the two-sheet gate or producer ran. The gate passed with no exceptions. `audit.py` reconstructed all 216 saved points and all 180 rows, checked their endomorphism conductors, compared Hecke-root and classical-modular-polynomial root counts, verified each elliptic-curve group sum, and computed exact rational ranks. Pure-Python reduced-form enumeration independently confirmed class numbers 18, 18, 36, and 36 for conductors 1, 2, 3, and 6.

`certificates.py` verifies four alternating 18-row degree-2 sums whose nonfloor coefficients cancel and whose disjoint supports partition the 72 conductor-6 columns. It also reconstructs two length-18 conductor-2 degree-3 cycles. On each, a projected row touches its source and two cycle neighbors with coefficient 1; row-dependency coefficients thus obey `aᵢ₋₁ + aᵢ + aᵢ₊₁ = 0`. The period-three patterns `(1,−1,0)` and `(0,1,−1)` yield two signed certificates per cycle. `validate.py` independently sums all eight combinations from the saved matrix and uses a separate dense modular reducer to verify rank eight. The mathematical recurrence is proved by `CycleKernel.period_three` in the pinned [Lean module](/Volumes/SSD990/cryptanalysis/experiments/hecke-split3-holdout-20261023/formal/CycleKernel.lean); its exact hypotheses are the three-term row equation over ℚ. The module's checked axiom audit contains only standard Lean foundations. The bridge from this instance's 180 saved rows to the cyclic model and the exact rank remains an externally replayed certificate rather than a Lean theorem.

This is the first prospective pass of the **revised** rule after the D = −431 counterexample to the earlier rank-six forecast. Its general form still assumes that the rational sheets realize the stated ideal-class cycles and that the degree-2 and degree-3 floor spans are independent; this experiment checks both assumptions for one new class. The saved group `X₀(11)(F₁₁₄₆₇)` has order 11495 and largest prime factor 19. This is a relation-stage diagnostic with `candidate_id: null` and `timing_claim: null`. A next discriminant should stress a different pair of norm orders or a nontrivial overlap of the two floor spans, with its entire prediction frozen before production.

Run every Sage script through `/Volumes/SSD990/cryptanalysis/sage`. `SEAL.json` hashes the protocols, scripts, data, gate, audits, and report.
