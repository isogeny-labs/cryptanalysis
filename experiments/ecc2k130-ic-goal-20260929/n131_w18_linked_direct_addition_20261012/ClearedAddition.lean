import Std

/- The circuit enforces u*N = d². Once d is nonzero, the ordinary
   field inverse law makes u the reciprocal of N/d². -/

universe u

theorem reciprocal_from_cleared_addition {F : Type u}
    (mul : F → F → F) (inv : F → F) (one dSquared numerator reciprocal : F)
    (mul_assoc : ∀ a b c : F, mul (mul a b) c = mul a (mul b c))
    (inverse_law : mul dSquared (inv dSquared) = one)
    (circuit_equation : mul reciprocal numerator = dSquared) :
    mul reciprocal (mul numerator (inv dSquared)) = one := by
  rw [← mul_assoc, circuit_equation, inverse_law]

#print axioms reciprocal_from_cleared_addition
