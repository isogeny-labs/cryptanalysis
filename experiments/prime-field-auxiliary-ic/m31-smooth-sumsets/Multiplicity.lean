import Mathlib.Tactic

namespace SumsetMultiplicity

/-- At a represented sum, the lost coverage is bounded by the number of
unordered pairs of different representations. -/
theorem duplicate_bound (k : ℕ) : k ≤ (k+1).choose 2 := by
  induction k with
  | zero => simp
  | succ k ih =>
    rw [Nat.choose_succ_succ]
    simp only [Nat.choose_one_right]
    omega

/-- When no finite sum has more than two representations, every collision
removes precisely one element from the maximum possible coverage. -/
theorem exact_at_two (m : ℕ) (hm : 1 ≤ m) (ht : m ≤ 2) :
    m = 1 + m.choose 2 := by
  interval_cases m <;> decide

end SumsetMultiplicity
