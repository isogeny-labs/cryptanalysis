import ProjectiveCoalescenceObstruction
import Mathlib.Tactic

/-! The raw projective addition obstruction depends on equality of reduced
projective classes, not equality of chosen coordinate vectors. -/
namespace XedniProjectiveClassCoalescence

open XedniProjectiveClassReduction
open WeierstrassCurve.Projective

variable {R S : Type*} [CommRing R] [CommRing S]

/-- If two distinct source classes coalesce after a ring map, their source
chord addition polynomial maps to the zero vector. -/
theorem mapped_source_add_vector_zero_of_equiv (f : R →+* S)
    (W : WeierstrassCurve R) (P Q : Fin 3 → R)
    (hSource : ¬P ≈ Q) (hMap : (f ∘ P) ≈ (f ∘ Q)) :
    f ∘ WeierstrassCurve.Projective.add W P Q = ![0, 0, 0] := by
  rcases hMap with ⟨u, hu⟩
  rw [WeierstrassCurve.Projective.add_of_not_equiv hSource,
    ← WeierstrassCurve.Projective.map_addXYZ, ← hu]
  have hs := WeierstrassCurve.Projective.addXYZ_smul
    (W' := W.map f) (f ∘ Q) (f ∘ Q) (u : S) (1 : S)
  simpa [Units.smul_def, WeierstrassCurve.Projective.addXYZ_self,
    WeierstrassCurve.Projective.smul_fin3] using hs

/-- The corresponding source `addMap` class reduces to the class of the zero
vector, independently of the unit scaling chosen for the target representative. -/
theorem mapClass_source_addMap_zero_of_equiv (f : R →+* S)
    (W : WeierstrassCurve R) (P Q : Fin 3 → R)
    (hSource : ¬P ≈ Q) (hMap : (f ∘ P) ≈ (f ∘ Q)) :
    mapClass f (WeierstrassCurve.Projective.addMap W
      (⟦P⟧ : WeierstrassCurve.Projective.PointClass R) ⟦Q⟧) =
      (⟦![0, 0, 0]⟧ : WeierstrassCurve.Projective.PointClass S) := by
  change (⟦f ∘ WeierstrassCurve.Projective.add W P Q⟧ :
    WeierstrassCurve.Projective.PointClass S) = ⟦![0, 0, 0]⟧
  rw [mapped_source_add_vector_zero_of_equiv f W P Q hSource hMap]

/-- When the target doubling vector has nonzero `Z`, raw class reduction
cannot preserve `addMap` across coalescence of projective classes. -/
theorem mapClass_addMap_ne_addMap_of_equiv (f : R →+* S)
    (W : WeierstrassCurve R) (P Q : Fin 3 → R)
    (hSource : ¬P ≈ Q) (hMap : (f ∘ P) ≈ (f ∘ Q))
    (hZ : (WeierstrassCurve.Projective.dblXYZ (W.map f) (f ∘ P)) 2 ≠ 0) :
    mapClass f (WeierstrassCurve.Projective.addMap W
      (⟦P⟧ : WeierstrassCurve.Projective.PointClass R) ⟦Q⟧) ≠
      WeierstrassCurve.Projective.addMap (W.map f)
        (mapClass f ⟦P⟧) (mapClass f ⟦Q⟧) := by
  intro heq
  have hLeft := mapClass_source_addMap_zero_of_equiv f W P Q hSource hMap
  have hRight :
      WeierstrassCurve.Projective.addMap (W.map f)
        (mapClass f ⟦P⟧) (mapClass f ⟦Q⟧) =
        (⟦WeierstrassCurve.Projective.dblXYZ (W.map f) (f ∘ P)⟧ :
          WeierstrassCurve.Projective.PointClass S) := by
    change (⟦WeierstrassCurve.Projective.add (W.map f)
      (f ∘ P) (f ∘ Q)⟧ : WeierstrassCurve.Projective.PointClass S) = _
    rw [WeierstrassCurve.Projective.add_of_equiv hMap]
  rw [hLeft, hRight] at heq
  have hNotEquiv : ¬(![0, 0, 0] : Fin 3 → S) ≈
      WeierstrassCurve.Projective.dblXYZ (W.map f) (f ∘ P) :=
    WeierstrassCurve.Projective.not_equiv_of_Z_eq_zero_left (by simp) hZ
  exact hNotEquiv (Quotient.eq.mp heq)

#print axioms mapped_source_add_vector_zero_of_equiv
#print axioms mapClass_source_addMap_zero_of_equiv
#print axioms mapClass_addMap_ne_addMap_of_equiv

end XedniProjectiveClassCoalescence
