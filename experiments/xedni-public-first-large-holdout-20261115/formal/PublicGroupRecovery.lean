import PublicRecovery

namespace XedniPublicFirstLargeHoldout

/-- In a public cyclic subgroup represented by an injective linear map from
its scalar field, the point-group relation is equivalent to direct target
scalar recovery. The map hypothesis is the explicit group-coordinate bridge. -/
theorem public_group_relation_iff_recovered_scalar
    {F A : Type*} [Field F] [AddCommGroup A] [Module F A]
    (φ : F →ₗ[F] A) (hφ : Function.Injective φ)
    (a b w t₁ t₂ : F) (hs : a + b ≠ 0) :
    a • φ (w - t₁) + b • φ (w - t₂) = 0 ↔
      w = (a * t₁ + b * t₂) / (a + b) := by
  have hmap : a • φ (w - t₁) + b • φ (w - t₂) =
      φ (a * (w - t₁) + b * (w - t₂)) := by
    calc
      _ = φ (a • (w - t₁)) + φ (b • (w - t₂)) := by
        rw [map_smul, map_smul]
      _ = φ (a • (w - t₁) + b • (w - t₂)) := by rw [map_add]
      _ = _ := by simp only [smul_eq_mul]
  rw [hmap]
  have hzero : φ (a * (w - t₁) + b * (w - t₂)) = 0 ↔
      a * (w - t₁) + b * (w - t₂) = 0 := by
    constructor
    · intro h
      apply hφ
      simpa using h
    · intro h
      simp [h]
  rw [hzero]
  exact public_relation_iff_recovered_scalar a b w t₁ t₂ hs

#print axioms public_group_relation_iff_recovered_scalar

end XedniPublicFirstLargeHoldout
