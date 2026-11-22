import ProjectivePrimitiveCurveEquation
import ProjectiveGenericNormalization
import Mathlib.Tactic

/-! A unit-content factorization of an integral addition triple identifies
the rational sum and makes primitive reduction commute with addition when
the mapped inputs remain distinct. -/
namespace XedniProjectivePrimitiveAddition

open XedniProjectivePrimitiveReductionMap
open XedniProjectivePrimitiveUniqueness
open XedniProjectiveGenericNormalization
open XedniProjectiveClassReduction
open WeierstrassCurve.Projective

private def q : ℤ →+* ℚ := Int.castRingHom ℚ

/-- The exact factorization identifies the rational projective sum, when
the source classes are distinct and the factor is nonzero. -/
theorem rational_add_eq_of_factor (W : WeierstrassCurve ℤ)
    (C D E : NonzeroClass ℚ) (c : ℤ)
    (hSource : ¬(representative C) ≈ (representative D))
    (hFactor : WeierstrassCurve.Projective.addXYZ W
      (representative C) (representative D) = c • representative E)
    (hc : c ≠ 0) :
    WeierstrassCurve.Projective.addMap (W.map q) C.val D.val = E.val := by
  have hMapped : ¬(q ∘ representative C) ≈ (q ∘ representative D) := by
    intro h
    exact hSource (int_equiv_of_rational_equiv_primitive
      (representative C) (representative D)
      (representative_primitive C) (representative_primitive D) h)
  have hcQ : IsUnit (q c) := by
    have hn : (c : ℚ) ≠ 0 := by exact_mod_cast hc
    exact hn.isUnit
  have h := addMap_map_eq_primitive_of_unit_factor q W
    (representative C) (representative D) (representative E)
    c hMapped hFactor hcQ
  have hC : mapClass q (⟦representative C⟧ : PointClass ℤ) = C.val :=
    representative_class C
  have hD : mapClass q (⟦representative D⟧ : PointClass ℤ) = D.val :=
    representative_class D
  have hE : mapClass q (⟦representative E⟧ : PointClass ℤ) = E.val :=
    representative_class E
  rw [hC, hD, hE] at h
  exact h

/-- On a branch where mapped inputs remain distinct and the factored
content maps to a unit, primitive reduction commutes with addition. -/
theorem reduceNonzero_add_eq_of_unit_factor {S : Type*}
    [CommRing S] [Nontrivial S]
    (W : WeierstrassCurve ℤ) (g : ℤ →+* S)
    (C D E : NonzeroClass ℚ) (c : ℤ)
    (hMapped : ¬(g ∘ representative C) ≈ (g ∘ representative D))
    (hFactor : WeierstrassCurve.Projective.addXYZ W
      (representative C) (representative D) = c • representative E)
    (hc : IsUnit (g c)) :
    WeierstrassCurve.Projective.addMap (W.map g)
      (reduceNonzero g C).val (reduceNonzero g D).val =
      (reduceNonzero g E).val := by
  change WeierstrassCurve.Projective.addMap (W.map g)
    (mapClass g (⟦representative C⟧ : PointClass ℤ))
    (mapClass g (⟦representative D⟧ : PointClass ℤ)) =
    mapClass g (⟦representative E⟧ : PointClass ℤ)
  exact addMap_map_eq_primitive_of_unit_factor g W
    (representative C) (representative D) (representative E)
    c hMapped hFactor hc

/-- The same factorization identifies the rational sum and its reduction in
one statement. -/
theorem rational_and_reduced_add_of_unit_factor {S : Type*}
    [CommRing S] [Nontrivial S]
    (W : WeierstrassCurve ℤ) (g : ℤ →+* S)
    (C D E : NonzeroClass ℚ) (c : ℤ)
    (hMapped : ¬(g ∘ representative C) ≈ (g ∘ representative D))
    (hFactor : WeierstrassCurve.Projective.addXYZ W
      (representative C) (representative D) = c • representative E)
    (hc : IsUnit (g c)) :
    WeierstrassCurve.Projective.addMap (W.map q) C.val D.val = E.val ∧
      WeierstrassCurve.Projective.addMap (W.map g)
        (reduceNonzero g C).val (reduceNonzero g D).val =
        (reduceNonzero g E).val := by
  have hSource : ¬(representative C) ≈ (representative D) := by
    intro h
    exact hMapped (map_equiv g h)
  have hc0 : c ≠ 0 := by
    intro hzero
    subst c
    simpa using hc.ne_zero
  exact ⟨rational_add_eq_of_factor W C D E c hSource hFactor hc0,
    reduceNonzero_add_eq_of_unit_factor W g C D E c hMapped hFactor hc⟩

#print axioms rational_add_eq_of_factor
#print axioms reduceNonzero_add_eq_of_unit_factor
#print axioms rational_and_reduced_add_of_unit_factor

end XedniProjectivePrimitiveAddition
