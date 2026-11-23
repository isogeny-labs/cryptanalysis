import Mathlib.Algebra.Group.Basic

namespace ReciprocalLifts

/-- Advancing a smooth product by one prime factor advances its orbit key and
the reciprocal key with the two precomputed factors. -/
theorem orbitKeyStep {G : Type*} [CommGroup G] (x q : G) :
    (x * q)^31 = x^31 * q^31 ∧
    ((x * q)^31)⁻¹ = (x^31)⁻¹ * (q^31)⁻¹ := by
  simp [mul_pow, mul_comm]

end ReciprocalLifts

#print axioms ReciprocalLifts.orbitKeyStep
