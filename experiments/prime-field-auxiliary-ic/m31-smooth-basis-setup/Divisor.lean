import Mathlib.Data.Nat.Factorization.Basic

namespace SmoothDivisor

/-- A multiple with sufficient exponents on the allowed primes and no
exponents outside them recognizes smooth representatives by divisibility. -/
theorem recognizes (x M B : ℕ) (hx : x ≠ 0) (hM : M ≠ 0)
    (inside : ∀ q ≤ B, x.factorization q ≤ M.factorization q)
    (outside : ∀ q > B, M.factorization q = 0) :
    x ∣ M ↔ ∀ q > B, x.factorization q = 0 := by
  rw [← Nat.factorization_le_iff_dvd hx hM]
  constructor
  · intro h q hq
    exact Nat.eq_zero_of_le_zero ((outside q hq) ▸ h q)
  · intro h q
    by_cases hq : q ≤ B
    · exact inside q hq
    · rw [h q (Nat.lt_of_not_ge hq)]
      exact Nat.zero_le _

end SmoothDivisor
