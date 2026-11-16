import PrimeOrderRecovery

namespace XedniPublicFirstLargeHoldout

/-- With zero coefficient sum, the target scalar cancels from the relation. -/
theorem zero_sum_scalar_relation_iff
    {F : Type*} [Field F] (a b w t₁ t₂ : F) (hs : a + b = 0) :
    a * (w - t₁) + b * (w - t₂) = 0 ↔ a * (t₂ - t₁) = 0 := by
  have hb : b = -a := by linear_combination hs
  rw [hb]
  constructor <;> intro h <;> linear_combination h

/-- For nonzero coefficients, a zero-sum hit is precisely equal offsets,
independent of the target. -/
theorem zero_sum_scalar_relation_iff_equal_offsets
    {F : Type*} [Field F] (a b w t₁ t₂ : F)
    (hs : a + b = 0) (ha : a ≠ 0) :
    a * (w - t₁) + b * (w - t₂) = 0 ↔ t₁ = t₂ := by
  rw [zero_sum_scalar_relation_iff a b w t₁ t₂ hs]
  constructor
  · intro h
    have hdiff : t₂ - t₁ = 0 := (mul_eq_zero.mp h).resolve_left ha
    exact (sub_eq_zero.mp hdiff).symm
  · intro h
    simp [h]

/-- The same cancellation holds for public point-group operations in a
prime-order scalar module with a nonzero generator. -/
theorem zero_sum_group_relation_iff_equal_offsets
    (q : ℕ) [Fact (Nat.Prime q)]
    {A : Type*} [AddCommGroup A] [Module (ZMod q) A]
    (G : A) (hG : G ≠ 0) (a b w t₁ t₂ : ZMod q)
    (hs : a + b = 0) (ha : a ≠ 0) :
    a • ((w - t₁) • G) + b • ((w - t₂) • G) = 0 ↔ t₁ = t₂ := by
  have hcombine : a • ((w - t₁) • G) + b • ((w - t₂) • G) =
      (a * (w - t₁) + b * (w - t₂)) • G := by
    rw [add_smul, mul_smul, mul_smul]
  rw [hcombine]
  have hzero : (a * (w - t₁) + b * (w - t₂)) • G = 0 ↔
      a * (w - t₁) + b * (w - t₂) = 0 := by
    constructor
    · intro h
      exact (smul_eq_zero.mp h).resolve_right hG
    · intro h
      simp [h]
  rw [hzero]
  exact zero_sum_scalar_relation_iff_equal_offsets a b w t₁ t₂ hs ha

#print axioms zero_sum_scalar_relation_iff
#print axioms zero_sum_scalar_relation_iff_equal_offsets
#print axioms zero_sum_group_relation_iff_equal_offsets

end XedniPublicFirstLargeHoldout
