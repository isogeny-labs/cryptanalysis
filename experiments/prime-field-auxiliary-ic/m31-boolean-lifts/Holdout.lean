import Mathlib

namespace M31SignatureHoldout

/-- Withholding a positive label leaves exactly a-1 positives and b
negatives among the other rows with that signature. Ties score half. -/
def twiceVotes (a b : ℕ) : ℕ :=
  if a = 0 then 0 else if a-1 > b then 2*a else if a-1 = b then a else 0

theorem groupScore (a b : ℕ) :
    twiceVotes a b + twiceVotes b a =
      if a = b then 0 else
      if a = b+1 then a else if b = a+1 then b else 2*max a b := by
  unfold twiceVotes
  split_ifs <;> omega

/-- Averaging over the next fair sign increases expected absolute imbalance
by exactly the probability that the current imbalance is zero. -/
theorem fairStep (z : ℤ) :
    |z+1| + |z-1| = 2*|z| + (if z = 0 then 2 else 0) := by
  rcases lt_trichotomy z 0 with hz | rfl | hz
  · rw [abs_of_nonpos (show z+1 ≤ 0 by omega), abs_of_nonpos (by omega : z-1 ≤ 0),
      abs_of_neg hz, ite_eq_right (by omega)]
    ring
  · decide
  · rw [abs_of_pos (show 0 < z+1 by omega), abs_of_nonneg (by omega : 0 ≤ z-1),
      abs_of_pos hz, ite_eq_right (by omega)]
    ring

theorem censusScores :
    (3839141:ℚ)/(2*3846525) < 1/2 ∧
    (3839141:ℚ)/(2*3846525) < 1924024/3846525 ∧
    (2194269:ℚ)/3846525 > 57/100 := by norm_num

end M31SignatureHoldout
