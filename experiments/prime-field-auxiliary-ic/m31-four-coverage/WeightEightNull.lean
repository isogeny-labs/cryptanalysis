import Mathlib.Tactic

namespace M31WeightEightNull

/-- Choose k support coordinates, a positive composition, and k-1 free signs. -/
def signedCount (w : Nat) := ((List.range w).map fun j =>
  (Nat.choose 17 (j+1)) * ((w-1).choose j) * 2^j).sum

-- A nonprimitive vector of norm eight is divisible by two, hence is twice
-- a unique norm-four vector with the same overall sign convention.
theorem counts : signedCount 8 = 24331777 ∧ signedCount 4 = 28033 ∧
    signedCount 8 - signedCount 4 = 24303744 := by decide +kernel

/-- Pointwise second-order union bound for the number of witnessed identities. -/
theorem indicator_bounds (k : Nat) :
    (k : ℚ) - k*((k : ℚ)-1)/2 ≤ (if k=0 then 0 else 1) ∧
    (if k=0 then (0:ℚ) else 1) ≤ k := by
  rcases k with _ | k
  · norm_num
  rcases k with _ | k
  · norm_num
  · simp only [Nat.succ_ne_zero, ite_false, Nat.cast_succ]
    constructor <;> nlinarith [sq_nonneg (k : ℚ), Nat.cast_nonneg (α := ℚ) k]

abbrev q : ℚ := 2147505293
abbrev n : ℚ := 24303744
def firstMoment := n/q
def secondPairs := n*(n-1)/(2*q^2)

/-- Given the two moment bounds and the excluded probability mass, certify
the decimal envelope after conditioning on nonzero, distinct abscissae. -/
theorem conditional_bounds (hit retained joint : ℚ)
    (lower : firstMoment-secondPairs ≤ hit) (upper : hit ≤ firstMoment)
    (good : 1-289/q ≤ retained)
    (loss : hit-(1-retained) ≤ joint) (keep : joint ≤ hit) :
    11253/1000000 < joint/retained ∧ joint/retained < 11318/1000000 := by
  unfold firstMoment secondPairs at *
  have pos : 0 < retained := by linarith
  constructor
  · apply (lt_div_iff₀ pos).2
    linarith
  · apply (div_lt_iff₀ pos).2
    linarith

end M31WeightEightNull
