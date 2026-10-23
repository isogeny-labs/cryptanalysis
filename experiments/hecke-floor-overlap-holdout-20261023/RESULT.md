# Twelve norm-2 and four norm-3 floor directions remain independent

The preregistered high-density class `D = −1055`, conductor 6, `p = 10651` has **16 floor-only row-space directions**, matching the frozen prediction of 12 signed norm-2 cycle directions plus four period-three norm-3 directions. The checked-Sage class walk has 432 class points and 360 verified Hecke rows. Its exact rational full rank is 288 and its nonfloor projected rank is 272. Sixteen explicit integer row combinations have rank 16 modulo 23, 1000000007 and 2147483647, so the two degree families' floor spans are independent in this instance.

| Quantity | Frozen prediction | Observed |
| --- | ---: | ---: |
| Conductor-stratum point counts | 72, 72, 144, 144 | 72, 72, 144, 144 |
| Class points | 432 | 432 |
| Degree-2 / degree-3 rows | 216 / 144 | 216 / 144 |
| Signed norm-2 cycles | 12 of length 12 | 12 of length 12 |
| Norm-3 cycles | 2 of length 36 | 2 of length 36 |
| Degree-2 / degree-3 floor directions | 12 / 4 | 12 / 4 |
| Total floor-kernel dimension | **16** | **16** |

`selection_protocol.json` fixed the selection rule before a class-number or norm-order search. Among 92 inspected squarefree discriminants in `[624,3000]`, seven satisfied the split-class, norm-3 periodicity and nonzero-square-modulo-11 gates. The selector maximized predicted floor directions divided by floor-point count, then favored a larger absolute direction count and smaller discriminant. It chose `d = 1055`, where the relevant class numbers are 36, 36, 72 and 72, norm-2 has order 12 in conductor 3, and norm-3 has order 36 in conductor 2. The first permitted field is `p = 34² + 9·1055 = 10651`, with `u = 68` and `u² − 4p = −1055·6²`.

`producer_protocol.json` froze the 16-direction prediction, class and row counts, field and source hashes before the two-sheet gate or producer ran. The gate found two rational `X₀(11)` points over each of the 216 rational CM j-invariants. `audit.py` independently reconstructed all 432 saved points and 360 relations, checked conductors, Hecke-root and modular-polynomial root counts, and elliptic-curve group sums, then computed exact rational ranks. The degree-2 matrix has ranks 216 and 204 before and after nonfloor projection; the degree-3 matrix has ranks 144 and 140. Their union has ranks 288 and 272.

`certificates.py` constructs twelve alternating 12-row norm-2 sums whose nonfloor coefficients cancel and whose disjoint supports partition the 144 floor columns. It finds two norm-3 cycles of length 36; the projected row-dependency recurrence `aᵢ₋₁ + aᵢ + aᵢ₊₁ = 0` yields two period-three certificates per cycle. `validate.py` independently enumerates reduced quadratic forms, replays all 16 row combinations from the saved matrix and performs a separate dense modular rank check. The certificates' combined rank 16 matches the exact floor-kernel dimension, so they span that kernel.

The pinned [Lean module](/Volumes/SSD990/cryptanalysis/experiments/hecke-floor-overlap-holdout-20261023/formal/Cycle36.lean) proves that every rational three-term recurrence is three-periodic, that its third value is determined by the first two, and that a 36-step cycle satisfies the period condition. `lake env lean Cycle36.lean` passed and `#print axioms` reports only standard Lean foundations. The instance-specific identification of the projected Hecke rows with this recurrence, the twelve norm-2 cancellations, and the exact combined rank are independently replayed certificates; those bridges are not yet Lean-formalized.

This prospective pass strengthens the evidence for independent degree-family floor spans at a larger witness count. A general theorem still needs the ideal-class-to-Hecke-row bridge and an abstract proof of floor-span independence. The result is a relation-stage diagnostic with `candidate_id: null` and `timing_claim: null`. All local Sage commands use `/Volumes/SSD990/cryptanalysis/sage`; `SEAL.json` binds the protocols, runtime receipt, code, gate, data, audits, proof and report.
