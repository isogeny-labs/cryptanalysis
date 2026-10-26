import Mathlib.Tactic.Linarith

namespace RelativePoleBound

/-- Each monomial in the frozen weight-90 basis has pole degree at most 3312,
given degrees 48, 72, and 144 for the three coordinate functions. -/
theorem monomial_pole_bound (a b c : ℕ)
    (hweight : 2 * a + 3 * b + 2 * c ≤ 90) (hc : c ≤ 12) :
    48 * a + 72 * b + 144 * c ≤ 3312 := by
  nlinarith

/-- A zero of order 3313 exceeds the bound for every such monomial. -/
theorem q_order_exceeds_monomial_poles (a b c : ℕ)
    (hweight : 2 * a + 3 * b + 2 * c ≤ 90) (hc : c ≤ 12) :
    48 * a + 72 * b + 144 * c < 3313 := by
  have h := monomial_pole_bound a b c hweight hc
  nlinarith

#print axioms monomial_pole_bound
#print axioms q_order_exceeds_monomial_poles

end RelativePoleBound
