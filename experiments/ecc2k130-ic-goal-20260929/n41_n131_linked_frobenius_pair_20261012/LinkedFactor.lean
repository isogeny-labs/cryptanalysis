import Std

/-! A repeated factor-base point in Frobenius slots `a` and `a + k`
contributes a single folded coefficient. -/

theorem linked_frobenius_factor (lambda a k : Nat) :
    lambda ^ a + lambda ^ (a + k) = lambda ^ a * (1 + lambda ^ k) := by
  rw [Nat.pow_add]
  simp [Nat.mul_add]

#print axioms linked_frobenius_factor
