import Mathlib.Tactic.Ring

namespace J1728DiscriminantNorms

/-- The product formula for the two conjugate discriminants and their
    cross-resultant converts a sixth-power relative norm and a cube
    resultant norm into a sixth-power base discriminant norm. -/
theorem sixth_power_from_product {R : Type*} [CommRing R]
    (base relative pair relativeRoot pairRoot : R)
    (hproduct : base = relative * pair ^ 2)
    (hrelative : relative = relativeRoot ^ 6)
    (hpair : pair = pairRoot ^ 3) :
    base = (relativeRoot * pairRoot) ^ 6 := by
  rw [hproduct, hrelative, hpair]
  ring

#print axioms sixth_power_from_product

end J1728DiscriminantNorms
