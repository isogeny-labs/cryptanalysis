import Mathlib.Tactic

namespace ReciprocalLifts

/-- One unit of work per downstream pair test and cost c per screened input.
The counts are, in order, screened inputs, passing inputs and retained successes. -/
def screenedRate (inputs passing retained c : ℚ) : ℚ :=
  retained / (inputs * c + passing)

/-- Counts at exact reciprocal alignment in phases.csv. -/
theorem curve_rate_strictly_lower (c : ℚ) (hc : 0 ≤ c) :
    screenedRate 102362 51241 12649 c < 25331 / 102362 := by
  unfold screenedRate
  rw [div_lt_div_iff₀ (by positivity) (by norm_num)]
  linarith

theorem twist_rate_improves_iff (c : ℚ) (hc : 0 ≤ c) :
    25739 / 102362 < screenedRate 102362 51241 12983 c ↔
      c < 10073747 / 2634695518 := by
  unfold screenedRate
  rw [div_lt_div_iff₀ (by norm_num) (by positivity)]
  constructor <;> intro h <;> linarith

/-- A free screen gives the largest possible throughput at nonnegative cost. -/
theorem twist_speedup_ceiling (c : ℚ) (hc : 0 ≤ c) :
    screenedRate 102362 51241 12983 c / (25739 / 102362) ≤
      (12983 * 102362) / (51241 * 25739) := by
  unfold screenedRate
  rw [div_le_iff₀ (by norm_num), div_le_iff₀ (by positivity)]
  linarith

end ReciprocalLifts
