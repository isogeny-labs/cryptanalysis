import Mathlib.Tactic

/-! A shared scalar target gives one affine relation equation per fixed
coefficient vector and offset pair. -/
namespace XedniSharedTargetRelation

variable {F : Type*} [Field F]

theorem relation_iff_linear_equation (a b t₁ t₂ w : F) :
    a * (w - t₁) + b * (w - t₂) = 0 ↔
      (a + b) * w = a * t₁ + b * t₂ := by
  constructor <;> intro h <;> linear_combination h

/-- For fixed coefficients and offsets, a nonzero coefficient sum determines
the only target scalar that can give the public relation. -/
theorem unique_target (a b t₁ t₂ : F) (hab : a + b ≠ 0) :
    ∃! w : F, a * (w - t₁) + b * (w - t₂) = 0 := by
  refine ⟨(a * t₁ + b * t₂) / (a + b), ?_, ?_⟩
  · change a * ((a * t₁ + b * t₂) / (a + b) - t₁) +
      b * ((a * t₁ + b * t₂) / (a + b) - t₂) = 0
    rw [relation_iff_linear_equation]
    field_simp [hab]
  · intro w hw
    rw [relation_iff_linear_equation] at hw
    rw [mul_comm (a + b) w] at hw
    exact (eq_div_iff hab).2 hw

theorem unique_target_mod_prime (q : ℕ) [Fact (Nat.Prime q)]
    (a b t₁ t₂ : ZMod q) (hab : a + b ≠ 0) :
    ∃! w : ZMod q, a * (w - t₁) + b * (w - t₂) = 0 :=
  unique_target a b t₁ t₂ hab

#print axioms relation_iff_linear_equation
#print axioms unique_target
#print axioms unique_target_mod_prime

end XedniSharedTargetRelation
