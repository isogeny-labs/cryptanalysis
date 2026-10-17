import Std

namespace RRQuotient

/-- The two-dimensional characteristic-two quotient determinant. -/
def det2 (mul : Nat → Nat → Nat) (a b c d : Nat) : Nat :=
  (mul a d) ^^^ (mul b c)

theorem xor_zero_iff_equal (a b : Nat) : (a ^^^ b = 0) ↔ a = b := by
  constructor
  · intro h
    have h' := congrArg (fun x : Nat => x ^^^ b) h
    simpa [Nat.xor_assoc, Nat.xor_self] using h'
  · intro h
    rw [h, Nat.xor_self]

/-- The quotient determinant vanishes exactly at cross-product equality. -/
theorem det2_zero_iff_cross_equal (mul : Nat → Nat → Nat) (a b c d : Nat) :
    det2 mul a b c d = 0 ↔ mul a d = mul b c := by
  exact xor_zero_iff_equal (mul a d) (mul b c)

#print axioms RRQuotient.xor_zero_iff_equal
#print axioms RRQuotient.det2_zero_iff_cross_equal

end RRQuotient
