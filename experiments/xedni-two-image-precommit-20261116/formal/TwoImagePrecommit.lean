import Mathlib

namespace XedniTwoImagePrecommit

variable {K : Type*} [Field K]

def interpA (x₁ y₁ x₂ y₂ : K) : K :=
  ((y₁ ^ 2 - x₁ ^ 3) - (y₂ ^ 2 - x₂ ^ 3)) / (x₁ - x₂)

def interpB (x₁ y₁ x₂ y₂ : K) : K :=
  y₁ ^ 2 - x₁ ^ 3 - interpA x₁ y₁ x₂ y₂ * x₁

/-- The first lifted coordinate pair lies on its interpolated short Weierstrass equation. -/
theorem first_point_equation (x₁ y₁ x₂ y₂ : K) :
    y₁ ^ 2 = x₁ ^ 3 + interpA x₁ y₁ x₂ y₂ * x₁ + interpB x₁ y₁ x₂ y₂ := by
  unfold interpB
  ring

/-- Distinct x coordinates make the second lifted pair lie on the same equation. -/
theorem second_point_equation (x₁ y₁ x₂ y₂ : K) (hx : x₁ ≠ x₂) :
    y₂ ^ 2 = x₂ ^ 3 + interpA x₁ y₁ x₂ y₂ * x₂ + interpB x₁ y₁ x₂ y₂ := by
  dsimp [interpA, interpB]
  field_simp [sub_ne_zero.mpr hx]
  ring

/-- The coefficient of x is uniquely determined by two points with distinct x coordinates. -/
theorem interpA_eq_of_two_equations (x₁ y₁ x₂ y₂ A B : K) (hx : x₁ ≠ x₂)
    (h₁ : y₁ ^ 2 = x₁ ^ 3 + A * x₁ + B)
    (h₂ : y₂ ^ 2 = x₂ ^ 3 + A * x₂ + B) :
    interpA x₁ y₁ x₂ y₂ = A := by
  unfold interpA
  apply (div_eq_iff (sub_ne_zero.mpr hx)).2
  linear_combination h₁ - h₂

/-- The constant coefficient is uniquely determined after the first coefficient. -/
theorem interpB_eq_of_two_equations (x₁ y₁ x₂ y₂ A B : K) (hx : x₁ ≠ x₂)
    (h₁ : y₁ ^ 2 = x₁ ^ 3 + A * x₁ + B)
    (h₂ : y₂ ^ 2 = x₂ ^ 3 + A * x₂ + B) :
    interpB x₁ y₁ x₂ y₂ = B := by
  rw [interpB, interpA_eq_of_two_equations x₁ y₁ x₂ y₂ A B hx h₁ h₂]
  linear_combination h₁

/-- Distinct points on a short Weierstrass curve with one x coordinate have opposite y coordinates. -/
theorem same_x_opposite (y₁ y₂ : K) (hsq : y₁ ^ 2 = y₂ ^ 2) (hne : y₁ ≠ y₂) :
    y₁ = -y₂ := by
  have hprod : (y₁ - y₂) * (y₁ + y₂) = 0 := by
    calc
      (y₁ - y₂) * (y₁ + y₂) = y₁ ^ 2 - y₂ ^ 2 := by ring
      _ = 0 := sub_eq_zero.mpr hsq
  rcases mul_eq_zero.mp hprod with hleft | hright
  · exact False.elim (hne (sub_eq_zero.mp hleft))
  · calc
      y₁ = y₁ + y₂ - y₂ := by ring
      _ = -y₂ := by rw [hright]; ring

/-- Reduction of a relation between two fixed lifts gives the same public relation. -/
theorem relation_transfer {R F : Type*} [AddCommGroup R] [AddCommGroup F]
    (reduce : R →+ F) (P Q : R) (U V : F) (a b : ℤ)
    (hP : reduce P = U) (hQ : reduce Q = V)
    (hrel : a • P + b • Q = 0) : a • U + b • V = 0 := by
  calc
    a • U + b • V = reduce (a • P + b • Q) := by simp [map_zsmul, hP, hQ]
    _ = 0 := by simp [hrel]

/-- A public nonrelation rules out the same relation for every pair of lifts with these reductions. -/
theorem no_lift_relation_of_no_public {R F : Type*} [AddCommGroup R] [AddCommGroup F]
    (reduce : R →+ F) (P Q : R) (U V : F) (a b : ℤ)
    (hP : reduce P = U) (hQ : reduce Q = V)
    (hpub : a • U + b • V ≠ 0) : a • P + b • Q ≠ 0 := by
  intro hrel
  exact hpub (relation_transfer reduce P Q U V a b hP hQ hrel)

#print axioms first_point_equation
#print axioms second_point_equation
#print axioms interpA_eq_of_two_equations
#print axioms interpB_eq_of_two_equations
#print axioms same_x_opposite
#print axioms relation_transfer
#print axioms no_lift_relation_of_no_public

end XedniTwoImagePrecommit
