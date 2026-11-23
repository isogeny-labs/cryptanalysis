import Mathlib.Tactic

namespace MissCost

/-- First-step recurrence for a repeated independent query. On success the
conditional expected cost is s; on failure one pays k and starts again. -/
theorem lower_bound (q s k e : ℝ) (hq : 0 < q) (hs : 0 ≤ s)
    (h : e = q*s + (1-q)*(k+e)) :
    k*(1-q)/q ≤ e := by
  apply (div_le_iff₀ hq).2
  nlinarith [mul_nonneg hq.le hs]

/-- Ratio to a one-call query with hit probability b/N. -/
theorem ratio (k h b n : ℚ) (hn : n ≠ 0) (hh : h ≠ 0) (hb : b ≠ 0) :
    (k*(1-h/n)/(h/n))/(n/b) = k*(n-h)*b/(h*n) := by
  field_simp

theorem archive_ratio :
    (29927:ℚ)/10000 <
      390*(2147505292-9864802)*76050 / (9864802*2147505292) := by
  norm_num

end MissCost
