import Mathlib.Tactic.Ring

/-- The first and second differences used in the field-wide lift census. -/
theorem m31_count_recurrences {K : Type*} [CommRing K] (x : K) :
    ((x+1)^2+1) = (x^2+1)+(2*x+1) ∧
    ((x+1)^3+2*(x+1)+14) = (x^3+2*x+14)+(3*x^2+3*x+3) ∧
    3*(x+1)^2+3*(x+1)+3 = (3*x^2+3*x+3)+(6*x+6) := by
  constructor
  · ring
  constructor <;> ring
