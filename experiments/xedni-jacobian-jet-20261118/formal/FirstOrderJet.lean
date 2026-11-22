import Mathlib.Tactic

namespace XedniJacobianJet

/-- The product rule for first-order perturbations in any commutative ring
with a square-zero perturbation. Applied separately to each of the four
coordinate-shift directions, this is the arithmetic rule used by the jet
evaluator. It does not assert correctness of elliptic Jacobian formulas. -/
theorem first_order_product {R : Type*} [CommRing R]
    (x y dx dy ε : R) (hε : ε ^ 2 = 0) :
    (x + ε * dx) * (y + ε * dy) =
      x * y + ε * (x * dy + dx * y) := by
  calc
    (x + ε * dx) * (y + ε * dy) =
        x * y + ε * (x * dy + dx * y) + ε ^ 2 * (dx * dy) := by ring
    _ = x * y + ε * (x * dy + dx * y) := by simp [hε]

#print axioms first_order_product

end XedniJacobianJet
