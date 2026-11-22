import Mathlib

/-- Recover a product shifted by 31 bits from its high and low 32-bit words.
The two components occupy disjoint bit positions, so their sum equals bitwise OR. -/
theorem shiftedProduct (v : ℕ) :
    2*(v/2^32) + (v%2^32)/2^31 = v/2^31 := by omega

theorem lowWordMask (v : ℕ) : (v%2^32)%2^31 = v%2^31 := by omega

theorem lanesFit (a b : ℕ) (ha : a < 2147483647) (hb : b < 2147483647) :
    2*((a*b)/2^32) < 2^32 ∧ (a*b)%2^31 + (a*b)/2^31 < 2^32 := by
  have h : a*b ≤ 2147483646*2147483646 :=
    Nat.mul_le_mul (by omega) (by omega)
  omega
