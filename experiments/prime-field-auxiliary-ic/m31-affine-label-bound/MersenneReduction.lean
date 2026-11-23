import Mathlib

namespace M31Reduction

abbrev p : Nat := 2147483647
def fold (x : Nat) := x % 2147483648 + x / 2147483648
def canonical (s : Nat) := if s ≥ p then s-p else s

theorem bits (x : Nat) : (x &&& (2^31-1)) + (x >>> 31) = fold x := by
  rw [Nat.and_two_pow_sub_one_eq_mod, Nat.shiftRight_eq_div_pow]
  rfl

/-- Exact initial interval on which one fold and one subtraction suffice. -/
theorem oneFold (x : Nat) (hx : x < 2^62-1) : canonical (fold x) = x % p := by
  unfold canonical fold p
  norm_num at hx
  split <;> omega

theorem firstFailure : canonical (fold (2^62-1)) ≠ (2^62-1) % p := by decide

theorem singleProduct {a b : Nat} (ha : a < p) (hb : b < p) :
    canonical (fold (a*b)) = (a*b) % p := by
  apply oneFold
  have h := Nat.mul_le_mul (Nat.le_pred_of_lt ha) (Nat.le_pred_of_lt hb)
  exact lt_of_le_of_lt h (by decide)

theorem foldResidue (x : Nat) : fold x % p = x % p := by
  have eq : x = fold x + p * (x / 2147483648) := by unfold fold p; omega
  conv_rhs => rw [eq]
  simp

theorem twoFolds (x : UInt64) :
    canonical (fold (fold x.toNat)) = x.toNat % p := by
  have limit := x.toNat_lt
  have small : fold x.toNat < 2^62-1 := by unfold fold; omega
  rw [oneFold _ small, foldResidue]

theorem accumulatorCapacity :
    4*(p-1)^2 < 2^64 ∧ 2^64 ≤ 5*(p-1)^2 := by decide

theorem twoProductsNeedSecondFold :
    canonical (fold (2*(p-1)^2)) = p+2 ∧ (2*(p-1)^2) % p = 2 := by decide

end M31Reduction
