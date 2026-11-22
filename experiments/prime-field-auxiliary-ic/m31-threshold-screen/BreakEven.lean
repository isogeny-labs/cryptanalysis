import Mathlib

/-- A fallback runs on a fraction q of attempts. Its conditional mean cost c
and success probability b determine whether cost per acceptance decreases. -/
theorem fallbackBreakEven (a b q A c : ℚ) (ha : 0 < a) (hq : 0 < q) (hb : 0 ≤ b) :
    (A+q*c)/(a+q*b) < A/a ↔ a*c < A*b := by
  have hden : 0 < a+q*b := by positivity
  rw [div_lt_div_iff₀ hden ha]
  constructor
  · intro h
    by_contra! hh
    nlinarith [mul_nonneg hq.le (sub_nonneg.mpr hh)]
  · intro h
    nlinarith [mul_pos hq (sub_pos.mpr h)]
