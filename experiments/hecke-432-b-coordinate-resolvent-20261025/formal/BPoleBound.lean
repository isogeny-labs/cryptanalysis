import Mathlib.Tactic.Linarith

namespace BPoleBound

/-- The degree-24 maps to C and B give coordinate degrees 48, 72, 48.
Every weight-44 monomial therefore has pole degree at most 1056. -/
theorem monomial_pole_bound (a b c : ℕ)
    (hweight : 2 * a + 3 * b + 2 * c ≤ 44) :
    48 * a + 72 * b + 48 * c ≤ 1056 := by
  nlinarith

/-- The checked zero order 1057 exceeds the pole bound. -/
theorem q_order_exceeds_monomial_poles (a b c : ℕ)
    (hweight : 2 * a + 3 * b + 2 * c ≤ 44) :
    48 * a + 72 * b + 48 * c < 1057 := by
  have h := monomial_pole_bound a b c hweight
  nlinarith

#print axioms monomial_pole_bound
#print axioms q_order_exceeds_monomial_poles

end BPoleBound
