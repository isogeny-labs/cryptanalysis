import Std

/-! A repeated Frobenius orbit column may use either output sign. -/
namespace LinkedSign

theorem coefficient_factor (lambda epsilon : Int) (a k : Nat) :
    lambda ^ a + epsilon * lambda ^ (a + k) =
      lambda ^ a * (1 + epsilon * lambda ^ k) := by
  rw [Int.pow_add]
  simp [Int.mul_add, Int.mul_left_comm]

theorem same_sign (lambda : Int) (a k : Nat) :
    lambda ^ a + lambda ^ (a + k) =
      lambda ^ a * (1 + lambda ^ k) := by
  simpa using coefficient_factor lambda 1 a k

theorem opposite_sign (lambda : Int) (a k : Nat) :
    lambda ^ a - lambda ^ (a + k) =
      lambda ^ a * (1 - lambda ^ k) := by
  simpa [Int.sub_eq_add_neg, Int.neg_mul] using
    coefficient_factor lambda (-1) a k

#print axioms LinkedSign.coefficient_factor
#print axioms LinkedSign.same_sign
#print axioms LinkedSign.opposite_sign

end LinkedSign
