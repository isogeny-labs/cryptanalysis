import Mathlib.Tactic

namespace FourPointNull

/-- For a fixed nonzero sum, discard the pairings with a shared sign orbit. -/
theorem disjoint_pairings (n : ℚ) :
    ((n-3)/2) * (((n-3)/2)-1)/2 - (n-5)/2 = (n-5)*(n-7)/8 := by ring

/-- Normalize the population count by the number of four-element subsets. -/
theorem mean_per_subset (n : ℚ) (hn : 7 < n) :
    ((n-1)*(n-5)*(n-7)/48) / ((n-1)*(n-3)*(n-5)*(n-7)/384) =
    8/(n-3) := by
  have h1 : n-1 ≠ 0 := by linarith
  have h3 : n-3 ≠ 0 := by linarith
  have h5 : n-5 ≠ 0 := by linarith
  have h7 : n-7 ≠ 0 := by linarith
  field_simp
  ring

theorem fixture_expectation :
    (500*499*498*497/24 : ℚ) * (8/(2147505293-3)) = 294060700/30678647 := by
  norm_num

end FourPointNull
