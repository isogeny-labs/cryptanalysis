import Mathlib

namespace M31Product

theorem signedHigh (a b : ℕ) (ha : a < 2147483647) (hb : b < 2147483647) :
    2*(a*b) < 2^63 ∧ 2*(a*b)/2^32 = a*b/2^31 := by
  have h := Nat.mul_le_mul (show a ≤ 2147483646 by omega) (show b ≤ 2147483646 by omega)
  constructor <;> omega

theorem unsignedMin (s : ℕ) (hs : s < 2*2147483647) :
    min s ((s+2^32-2147483647)%2^32) = s%2147483647 := by
  rw [min_def]
  split <;> omega
end M31Product
