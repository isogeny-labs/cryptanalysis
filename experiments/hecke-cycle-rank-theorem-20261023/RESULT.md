# The rational three-term cycle kernel has dimension two exactly at multiples of three

For a cycle of length `n ≥ 1`, let `Aₙ` be the rational matrix with row `i` equal to the sum of the basis columns `i−1`, `i` and `i+1`, with indices taken modulo `n` and repeated positions counted with multiplicity. Its kernel has dimension **two when `3 | n` and zero otherwise**; equivalently, its rank is `n−2` or `n`. This gives a single length-independent explanation for the degree-3 projected dependencies observed in the saved Hecke class walks.

If `Aₙ a = 0`, the coordinate equations are `aᵢ₋₁ + aᵢ + aᵢ₊₁ = 0`. Subtracting the equation shifted by one index gives `aᵢ₊₃ = aᵢ`. When `3 ∤ n`, the periods three and `n` force all coordinates equal, and the recurrence forces that common rational value to zero. When `3 | n`, choose `a₀ = u` and `a₁ = v`; then `a₂ = −u−v`, and the triple repeats around the cycle. Every pair `(u,v) ∈ ℚ²` gives one solution, and its first two coordinates recover the pair uniquely.

The pinned [Lean theorem module](/Volumes/SSD990/cryptanalysis/experiments/hecke-cycle-rank-theorem-20261023/formal/GeneralCycleKernel.lean) formalizes the sequence classification over `ℚ`. `GeneralCycleKernel.nonmultiple_trivial` quantifies over every natural cycle length with `n % 3 ≠ 0`, every integer-indexed rational sequence obeying the recurrence and `n`-periodicity, and every index, proving its value zero. `periodicPair_recurrence` and `periodicPair_cycle` construct a recurrent, `n`-periodic sequence from each pair when `n % 3 = 0`. `recurrence_has_two_parameters`, `periodicPair_injective` and `periodic_solution_unique_pair` prove that every recurrent sequence has exactly one such pair. `lake env lean -o /private/tmp/GeneralCycleKernel-20261023.olean GeneralCycleKernel.lean` built the theorem module; [build.json](/Volumes/SSD990/cryptanalysis/experiments/hecke-cycle-rank-theorem-20261023/formal/build.json) records the pinned sources and output hash. The saved `#print axioms` output lists only `propext`, `Classical.choice` and `Quot.sound`. `lean4checker --fresh` was unavailable on this host.

`sweep.py`, run with the checked repository Sage launcher, computed exact `QQ` ranks of `Aₙ` for every `n` from 1 through 96. All 96 matched the theorem. It then reconstructed each saved conductor-2 degree-3 projected cycle row directly from the source Hecke matrices and verified exact equality with `Aₙ`:

| CM discriminant | Saved cycle lengths | Exact projected ranks | Kernel dimensions |
| --- | --- | --- | --- |
| `−527` | 18, 18 | 16, 16 | 2, 2 |
| `−623` | 22, 22 | 22, 22 | 0, 0 |
| `−1055` | 36, 36 | 34, 34 | 2, 2 |

`validate.py` independently rebuilt all 96 matrices and six saved projected cycle matrices, checked their ranks by dense elimination modulo 1000000007, and verified the source artifact hashes. The general Lean theorem and exact rational sweep establish the cycle-operator result. For the three saved Hecke instances, equality between the projected rows and that operator is an externally replayed certificate. A general geometric theorem deriving that row form from every eligible ideal-class walk remains open; the local equality must not be silently generalized beyond the audited instances. This is a relation-stage result with `candidate_id: null` and `timing_claim: null`.
