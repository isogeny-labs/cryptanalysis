import Mathlib

namespace HighSquare
abbrev p : Nat := 2147483647

/-- The doubled product fits in the positive range of signed 64-bit arithmetic. -/
theorem noSaturation (x : Nat) (hx : x < p) : 2*(x*x) < 2^63 := by
  have hx' : x ≤ 2147483646 := by unfold p at hx; omega
  have h := Nat.mul_le_mul hx' hx'
  omega

theorem highWord (x : Nat) : 2*(x*x) / 2^32 = x*x / 2^31 := by omega

end HighSquare
