import ProjectiveClassCoalescence
import Mathlib.Tactic

/-! A factored source chord represents its primitive vector after mapping to
a ring in which the factored scalar becomes a unit. -/
namespace XedniProjectiveGenericNormalization

open XedniProjectiveClassReduction
open WeierstrassCurve.Projective

variable {R S : Type*} [CommRing R] [CommRing S]

/-- For a distinct source chord, division by a common factor is valid at
the projective-class level after mapping that factor to a unit. This exposes
the exact algebraic bridge used by the rational generic fiber. -/
theorem mapClass_addMap_eq_primitive_of_unit_factor
    (f : R →+* S) (W : WeierstrassCurve R)
    (P Q U : Fin 3 → R) (c : R)
    (hSource : ¬P ≈ Q)
    (hFactor : WeierstrassCurve.Projective.addXYZ W P Q = c • U)
    (hc : IsUnit (f c)) :
    mapClass f (WeierstrassCurve.Projective.addMap W
      (⟦P⟧ : WeierstrassCurve.Projective.PointClass R) ⟦Q⟧) =
      mapClass f (⟦U⟧ : WeierstrassCurve.Projective.PointClass R) := by
  change (⟦f ∘ WeierstrassCurve.Projective.add W P Q⟧ :
    WeierstrassCurve.Projective.PointClass S) = ⟦f ∘ U⟧
  rw [WeierstrassCurve.Projective.add_of_not_equiv hSource, hFactor,
    WeierstrassCurve.Projective.comp_smul]
  exact WeierstrassCurve.Projective.smul_eq (f ∘ U) hc

/-- If the mapped inputs also remain distinct, the target `addMap` itself
equals the mapped primitive class. -/
theorem addMap_map_eq_primitive_of_unit_factor
    (f : R →+* S) (W : WeierstrassCurve R)
    (P Q U : Fin 3 → R) (c : R)
    (hMapped : ¬(f ∘ P) ≈ (f ∘ Q))
    (hFactor : WeierstrassCurve.Projective.addXYZ W P Q = c • U)
    (hc : IsUnit (f c)) :
    WeierstrassCurve.Projective.addMap (W.map f)
      (mapClass f ⟦P⟧) (mapClass f ⟦Q⟧) =
      mapClass f (⟦U⟧ : WeierstrassCurve.Projective.PointClass R) := by
  rw [← XedniProjectiveAddMapDistinct.mapClass_addMap_of_mapped_not_equiv
    f W P Q hMapped]
  exact mapClass_addMap_eq_primitive_of_unit_factor f W P Q U c
    (by
      intro hSource
      exact hMapped (XedniProjectiveClassReduction.map_equiv f hSource))
    hFactor hc

#print axioms mapClass_addMap_eq_primitive_of_unit_factor
#print axioms addMap_map_eq_primitive_of_unit_factor

end XedniProjectiveGenericNormalization
