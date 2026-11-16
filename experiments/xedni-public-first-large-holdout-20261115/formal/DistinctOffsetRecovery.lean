import ExceptionalRelation

namespace XedniPublicFirstLargeHoldout

/-- A relation on two distinct public offsets with nonzero first coefficient
necessarily has nonzero coefficient sum and directly determines the target. -/
theorem distinct_offset_public_hit_recovers_scalar
    (q : ℕ) [Fact (Nat.Prime q)]
    {A : Type*} [AddCommGroup A] [Module (ZMod q) A]
    (G : A) (hG : G ≠ 0) (a b w t₁ t₂ : ZMod q)
    (ha : a ≠ 0) (ht : t₁ ≠ t₂)
    (hrel : a • ((w - t₁) • G) + b • ((w - t₂) • G) = 0) :
    a + b ≠ 0 ∧ w = (a * t₁ + b * t₂) / (a + b) := by
  have hs : a + b ≠ 0 := by
    intro hzero
    exact ht ((zero_sum_group_relation_iff_equal_offsets q G hG
      a b w t₁ t₂ hzero ha).mp hrel)
  exact ⟨hs, (prime_order_public_relation_iff_recovered_scalar q G hG
    a b w t₁ t₂ hs).mp hrel⟩

/-- The public relation is a complete certificate for the direct recovery
formula when offsets differ and the first coefficient is nonzero. -/
theorem distinct_offset_public_relation_iff_recovery
    (q : ℕ) [Fact (Nat.Prime q)]
    {A : Type*} [AddCommGroup A] [Module (ZMod q) A]
    (G : A) (hG : G ≠ 0) (a b w t₁ t₂ : ZMod q)
    (ha : a ≠ 0) (ht : t₁ ≠ t₂) :
    a • ((w - t₁) • G) + b • ((w - t₂) • G) = 0 ↔
      a + b ≠ 0 ∧ w = (a * t₁ + b * t₂) / (a + b) := by
  constructor
  · exact distinct_offset_public_hit_recovers_scalar q G hG a b w t₁ t₂ ha ht
  · rintro ⟨hs, hw⟩
    exact (prime_order_public_relation_iff_recovered_scalar q G hG
      a b w t₁ t₂ hs).mpr hw

#print axioms distinct_offset_public_hit_recovers_scalar
#print axioms distinct_offset_public_relation_iff_recovery

end XedniPublicFirstLargeHoldout
