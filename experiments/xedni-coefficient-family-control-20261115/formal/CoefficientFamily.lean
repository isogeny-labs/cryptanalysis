import Mathlib

namespace XedniCoefficientFamily

/-- Two distinct projective coefficient directions can share a relation
only when both sampled point scalars vanish. -/
theorem distinct_directions_force_zero {F : Type*} [Field F]
    (a b c d x y : F) (hdet : a * d - b * c ≠ 0)
    (h₁ : a * x + b * y = 0) (h₂ : c * x + d * y = 0) :
    x = 0 ∧ y = 0 := by
  have hx : (a * d - b * c) * x = 0 := by
    linear_combination d * h₁ - b * h₂
  have hy : (a * d - b * c) * y = 0 := by
    linear_combination a * h₂ - c * h₁
  exact ⟨(mul_eq_zero.mp hx).resolve_left hdet,
    (mul_eq_zero.mp hy).resolve_left hdet⟩

/-- A vector with coefficient sum zero tests equality of the two sampled
scalars, so it cannot hit a distinct-point query. -/
theorem zero_sum_pair_relation {F : Type*} [Field F]
    (a x y : F) (ha : a ≠ 0) (hxy : x ≠ y) :
    a * x + (-a) * y ≠ 0 := by
  intro h
  have hdiff : a * (x - y) = 0 := by
    linear_combination h
  exact hxy ((mul_eq_zero.mp hdiff).resolve_left ha |> sub_eq_zero.mp)

/-- The second query offset is determined by the first on a relation line. -/
theorem relation_iff_second {F : Type*} [Field F]
    (a b w t₁ t₂ : F) (hb : b ≠ 0) :
    a * (w - t₁) + b * (w - t₂) = 0 ↔
      t₂ = w + a / b * (w - t₁) := by
  have hba : b * (a / b) = a := by field_simp
  constructor
  · intro h
    have he : b * (t₂ - (w + a / b * (w - t₁))) = 0 := by
      linear_combination -h - (w - t₁) * hba
    exact sub_eq_zero.mp ((mul_eq_zero.mp he).resolve_left hb)
  · intro h
    rw [h]
    linear_combination -(w - t₁) * hba

/-- Relation-line pairs whose first offset is not the target scalar. -/
def LineHit {F : Type*} [Field F] (a b w : F) :=
  {z : F × F // z.1 ≠ w ∧ a * (w - z.1) + b * (w - z.2) = 0}

/-- Projection onto the first offset is a bijection on the relation line. -/
noncomputable def lineHitEquiv {F : Type*} [Field F]
    (a b w : F) (hb : b ≠ 0) :
    LineHit a b w ≃ {t₁ : F // t₁ ≠ w} where
  toFun z := ⟨z.val.1, z.property.1⟩
  invFun t₁ := ⟨(t₁.val, w + a / b * (w - t₁.val)), t₁.property,
    (relation_iff_second a b w t₁.val _ hb).2 rfl⟩
  left_inv z := by
    apply Subtype.ext
    apply Prod.ext
    · rfl
    · exact ((relation_iff_second a b w z.val.1 z.val.2 hb).mp z.property.2).symm
  right_inv t₁ := rfl

noncomputable instance lineHitFintype {F : Type*} [Field F] [Fintype F]
    (a b w : F) : Fintype (LineHit a b w) := by
  classical
  letI : Finite (LineHit a b w) :=
    Finite.of_injective (fun z : LineHit a b w => z.val) Subtype.val_injective
  exact Fintype.ofFinite _

/-- An affine relation line has one hit for each first offset other than `w`. -/
theorem line_hit_count {F : Type*} [Field F] [Fintype F]
    (a b w : F) (hb : b ≠ 0) :
    Fintype.card (LineHit a b w) = Fintype.card F - 1 := by
  classical
  rw [Fintype.card_congr (lineHitEquiv a b w hb)]
  exact Set.card_ne_eq w

/-- Nonzero first coefficient and coefficient sum make every remaining line
point a query with two nonidentity, distinct sampled points. -/
theorem line_hit_admissible {F : Type*} [Field F]
    (a b w t₁ t₂ : F) (ha : a ≠ 0) (hC : a + b ≠ 0)
    (hfirst : t₁ ≠ w)
    (hrel : a * (w - t₁) + b * (w - t₂) = 0) :
    t₂ ≠ w ∧ t₁ ≠ t₂ := by
  constructor
  · intro hsecond
    subst t₂
    have hx : a * (w - t₁) = 0 := by simpa using hrel
    have hw : w = t₁ := sub_eq_zero.mp ((mul_eq_zero.mp hx).resolve_left ha)
    exact hfirst hw.symm
  · intro hequal
    subst t₂
    have hx : (a + b) * (w - t₁) = 0 := by
      linear_combination hrel
    have hw : w = t₁ := sub_eq_zero.mp ((mul_eq_zero.mp hx).resolve_left hC)
    exact hfirst hw.symm

/-- Exact admission rule for the two-point target-query panel. -/
def AdmissibleHit {F : Type*} [Field F] (a b w : F) :=
  {z : F × F // z.1 ≠ w ∧ z.2 ≠ w ∧ z.1 ≠ z.2 ∧
    a * (w - z.1) + b * (w - z.2) = 0}

noncomputable def admissibleHitEquiv {F : Type*} [Field F]
    (a b w : F) (ha : a ≠ 0) (hC : a + b ≠ 0) :
    AdmissibleHit a b w ≃ LineHit a b w where
  toFun z := ⟨z.val, z.property.1, z.property.2.2.2⟩
  invFun z := ⟨z.val, z.property.1,
    (line_hit_admissible a b w z.val.1 z.val.2 ha hC z.property.1 z.property.2).1,
    (line_hit_admissible a b w z.val.1 z.val.2 ha hC z.property.1 z.property.2).2,
    z.property.2⟩
  left_inv _z := Subtype.ext rfl
  right_inv _z := Subtype.ext rfl

noncomputable instance admissibleHitFintype {F : Type*} [Field F] [Fintype F]
    (a b w : F) : Fintype (AdmissibleHit a b w) := by
  classical
  letI : Finite (AdmissibleHit a b w) :=
    Finite.of_injective (fun z : AdmissibleHit a b w => z.val) Subtype.val_injective
  exact Fintype.ofFinite _

/-- Every nonzero-sum direction has exactly one fewer admissible hit than
the field cardinality. -/
theorem admissible_hit_count {F : Type*} [Field F] [Fintype F]
    (a b w : F) (ha : a ≠ 0) (hb : b ≠ 0) (hC : a + b ≠ 0) :
    Fintype.card (AdmissibleHit a b w) = Fintype.card F - 1 := by
  rw [Fintype.card_congr (admissibleHitEquiv a b w ha hC)]
  exact line_hit_count a b w hb

#print axioms distinct_directions_force_zero
#print axioms zero_sum_pair_relation
#print axioms relation_iff_second
#print axioms line_hit_count
#print axioms line_hit_admissible
#print axioms admissible_hit_count

end XedniCoefficientFamily
