import Mathlib.Data.Nat.Basic

namespace XedniHenselHeight

/-- A nonzero exact numerator at p-adic depth at least k has size at least p^k. -/
theorem numerator_height_lower_bound (p k n : ℕ)
    (hn : n ≠ 0) (hdepth : p ^ k ∣ n) :
    p ^ k ≤ n := by
  exact Nat.le_of_dvd (Nat.pos_of_ne_zero hn) hdepth

/-- An integer numerator whose absolute height is below the modulus cannot
be both nonzero and divisible by that modulus. This arithmetic bridge needs
an independent bound on the exact relation numerator to apply to a lift. -/
theorem numerator_zero_of_depth_and_height (p k n : ℕ)
    (hheight : n < p ^ k) (hdepth : p ^ k ∣ n) :
    n = 0 := by
  by_contra hn
  have hle : p ^ k ≤ n := numerator_height_lower_bound p k n hn hdepth
  exact Nat.not_le_of_gt hheight hle

#print axioms numerator_height_lower_bound
#print axioms numerator_zero_of_depth_and_height

end XedniHenselHeight
