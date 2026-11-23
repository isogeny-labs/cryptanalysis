import Mathlib.Data.Nat.Basic

namespace M31SmoothBatch

/-- A surviving parent above the second-power threshold has exactly one
positive prime-power extension in range. -/
theorem single_child (x q limit : ℕ) (hq : 0 < q) (fits : x*q ≤ limit)
    (oneOnly : limit < x*q^2) (e : ℕ) (he : 0 < e) :
    x*q^e ≤ limit ↔ e = 1 := by
  constructor
  · intro h
    by_contra ne
    have ge : 2 ≤ e := by omega
    have powle : q^2 ≤ q^e := Nat.pow_le_pow_right hq ge
    exact (Nat.not_lt_of_ge (le_trans (Nat.mul_le_mul_left x powle) h)) oneOnly
  · rintro rfl
    simpa using fits

end M31SmoothBatch
