# A residue-qualified nonperiodic Hecke holdout has four floor directions

The preregistered `D = −623`, conductor-6 class walk at `p = 11083` has **four floor-only row-space directions**, exactly the frozen prediction. Its 264 class points yield 220 verified degree-2 and degree-3 Hecke rows. The exact full rational rank is 176 and the nonfloor projected rank is 172. Four signed degree-2 cycles supply four independent floor vectors; the 88 degree-3 rows have full projected rank 88 and contribute no floor-only direction.

| Quantity | Frozen prediction | Observed |
| --- | ---: | ---: |
| Conductor-stratum point counts | 44, 44, 88, 88 | 44, 44, 88, 88 |
| Class points | 264 | 264 |
| Degree-2 / degree-3 rows | 132 / 88 | 132 / 88 |
| Signed norm-2 cycles | 4 of length 22 | 4 of length 22 |
| Norm-3 cycles | 2 of length 22 | 2 of length 22 |
| Degree-2 / degree-3 floor directions | 4 / 0 | 4 / 0 |
| Total floor-kernel dimension | **4** | **4** |

`selection_protocol.json` fixed the rule after the earlier `D = −551` fiber-gate failure and before this class was selected. It required the Frobenius characteristic-polynomial discriminant to be a nonzero square modulo 11, as well as the stated class-number, norm-order and field bounds. The first match was `d = 623`; its norm-3 class order is 22, which is not divisible by three. `producer_protocol.json` froze the class, `p = 11083`, the four-direction prediction, all class and row counts, and source hashes before the independent two-sheet gate and producer. The gate passed on all 132 rational CM j-invariants.

`audit.py` reconstructed all 264 saved points and 220 rows, checked the endomorphism conductors, compared Hecke-root and modular-polynomial root counts, checked every group sum, and computed exact rational ranks. `certificates.py` constructs four alternating 22-row degree-2 sums whose nonfloor entries cancel; their disjoint supports partition the 88 conductor-6 columns. Their floor vectors have rank four modulo 23, 1000000007 and 2147483647. `validate.py` independently enumerates reduced quadratic forms, replays all four combinations and performs a separate dense modular rank check. The rank and certificate evidence agree.

The degree-3 projected row-dependency recurrence is `aᵢ₋₁ + aᵢ + aᵢ₊₁ = 0`. It forces period three, so a length-22 cycle has only the zero rational dependency. The pinned [Lean module](/Volumes/SSD990/cryptanalysis/experiments/hecke-split3-qualified-holdout-20261023/formal/Cycle22.lean) proves this exact recurrence implication for every integer-indexed rational sequence with a 22-periodicity hypothesis. `lake env lean Cycle22.lean` passed and its axiom audit lists only standard Lean foundations. The identification of this instance's projected Hecke rows with the abstract cycle recurrence and the exact full matrix rank are externally replayed, not Lean-formalized.

This is a prospective pass of the nonperiodic branch of the revised floor rule. The general claim still requires an abstract bridge from ideal-class action to the rational Hecke row matrix and a proof that the two degree families have no additional overlap. This experiment records a relation-stage diagnostic with `candidate_id: null` and `timing_claim: null`; it does not use a one-target online timing comparison. Run every Sage script through `/Volumes/SSD990/cryptanalysis/sage`.
