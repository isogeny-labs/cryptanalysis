import BoxBound

namespace XedniPublicFirstLargeHoldout

/-- A nonzero-sum coefficient relation on the two public offset scalars
determines the target scalar directly. -/
theorem public_relation_iff_recovered_scalar {F : Type*} [Field F]
    (a b w t₁ t₂ : F) (hs : a + b ≠ 0) :
    a * (w - t₁) + b * (w - t₂) = 0 ↔
      w = (a * t₁ + b * t₂) / (a + b) := by
  have hden : (a + b) * ((a * t₁ + b * t₂) / (a + b)) =
      a * t₁ + b * t₂ := by field_simp
  constructor
  · intro h
    have he : (a + b) * (w - (a * t₁ + b * t₂) / (a + b)) = 0 := by
      linear_combination h - hden
    exact sub_eq_zero.mp ((mul_eq_zero.mp he).resolve_left hs)
  · intro h
    rw [h]
    linear_combination hden

/-- Two target scalars compatible with the same nonzero-sum public relation
and offsets are equal. -/
theorem public_relation_target_unique {F : Type*} [Field F]
    (a b w w' t₁ t₂ : F) (hs : a + b ≠ 0)
    (hw : a * (w - t₁) + b * (w - t₂) = 0)
    (hw' : a * (w' - t₁) + b * (w' - t₂) = 0) : w = w' := by
  calc
    w = (a * t₁ + b * t₂) / (a + b) :=
      (public_relation_iff_recovered_scalar a b w t₁ t₂ hs).mp hw
    _ = w' := ((public_relation_iff_recovered_scalar a b w' t₁ t₂ hs).mp hw').symm

#print axioms public_relation_iff_recovered_scalar
#print axioms public_relation_target_unique

end XedniPublicFirstLargeHoldout
