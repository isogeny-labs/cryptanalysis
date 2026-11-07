import Mathlib.Algebra.Field.Basic

namespace SignBranch

universe u

/-- Over a field where two is invertible, the affine sign involution
`(x,y) ↦ (x,-y)` fixes a point exactly when its y-coordinate is zero. -/
theorem negation_fixed_iff_y_zero {F : Type u} [Field F]
    (h2 : (2 : F) ≠ 0) (y : F) : y = -y ↔ y = 0 := by
  constructor
  · intro h
    have hsum : y + y = 0 := by
      calc
        y + y = y + -y := by rw [← h]
        _ = 0 := add_neg_cancel y
    have hmul : (2 : F) * y = 0 := by simpa [two_mul] using hsum
    rcases mul_eq_zero.mp hmul with hz | hy
    · exact False.elim (h2 hz)
    · exact hy
  · intro h
    subst y
    simp

/-- The derivative along the B tangent `(dx,dy)=(2y,3x²)` vanishes
precisely at the sign branch or when the x-coordinate derivative
itself vanishes. -/
theorem restricted_B_derivative_zero_iff {F : Type u} [Field F]
    (h2 : (2 : F) ≠ 0) (y dt : F) :
    (2 : F) * y * dt = 0 ↔ y = 0 ∨ dt = 0 := by
  constructor
  · intro h
    rcases mul_eq_zero.mp h with hleft | hdt
    · rcases mul_eq_zero.mp hleft with htwo | hy
      · exact False.elim (h2 htwo)
      · exact Or.inl hy
    · exact Or.inr hdt
  · intro h
    rcases h with hy | hdt
    · simp [hy]
    · simp [hdt]

theorem restricted_jacobian_zero_iff {F : Type u} [Field F]
    (h2 : (2 : F) ≠ 0) (dc y dt : F) :
    (dc = 0 ∧ (2 : F) * y * dt = 0) ↔
      (dc = 0 ∧ (y = 0 ∨ dt = 0)) := by
  constructor
  · intro h
    exact ⟨h.1, (restricted_B_derivative_zero_iff h2 y dt).mp h.2⟩
  · intro h
    exact ⟨h.1, (restricted_B_derivative_zero_iff h2 y dt).mpr h.2⟩

theorem observed_fiber_totals :
    864 + 864 + 1224 + 1800 + 1368 = 6120 ∧
    5968 + 152 = 6120 ∧
    5968 + 2 * 152 = 6272 := by decide

#print axioms negation_fixed_iff_y_zero
#print axioms restricted_B_derivative_zero_iff
#print axioms restricted_jacobian_zero_iff
#print axioms observed_fiber_totals

end SignBranch
