import ProjectiveAddMapDistinct
import Mathlib.Tactic

/-! Distinct source representatives that become the same vector under a ring
map expose the branch mismatch in raw projective `addMap`: source `addXYZ`
maps to the zero vector, while the target operation uses `dblXYZ`. -/
namespace XedniProjectiveCoalescenceObstruction

open XedniProjectiveClassReduction
open WeierstrassCurve.Projective

variable {R S : Type*} [CommRing R] [CommRing S]

/-- Distinct source representatives that become identical under a ring map
produce a zero vector when the source chord addition formula is mapped. -/
theorem mapped_source_add_vector_zero (f : R →+* S)
    (W : WeierstrassCurve R) (P Q : Fin 3 → R)
    (hSource : ¬P ≈ Q) (hMap : f ∘ P = f ∘ Q) :
    f ∘ WeierstrassCurve.Projective.add W P Q = ![0, 0, 0] := by
  rw [WeierstrassCurve.Projective.add_of_not_equiv hSource,
    ← WeierstrassCurve.Projective.map_addXYZ, hMap,
    WeierstrassCurve.Projective.addXYZ_self]

/-- The induced raw projective class map sends that source addition class
to the class of the zero vector. -/
theorem mapClass_source_addMap_zero (f : R →+* S)
    (W : WeierstrassCurve R) (P Q : Fin 3 → R)
    (hSource : ¬P ≈ Q) (hMap : f ∘ P = f ∘ Q) :
    mapClass f (WeierstrassCurve.Projective.addMap W
      (⟦P⟧ : WeierstrassCurve.Projective.PointClass R) ⟦Q⟧) =
      (⟦![0, 0, 0]⟧ : WeierstrassCurve.Projective.PointClass S) := by
  change (⟦f ∘ WeierstrassCurve.Projective.add W P Q⟧ :
    WeierstrassCurve.Projective.PointClass S) = ⟦![0, 0, 0]⟧
  rw [mapped_source_add_vector_zero f W P Q hSource hMap]

/-- If the target doubling representative has a nonzero projective `Z`
coordinate, the raw class map cannot commute with these additions. -/
theorem mapClass_addMap_ne_addMap_of_coalescence (f : R →+* S)
    (W : WeierstrassCurve R) (P Q : Fin 3 → R)
    (hSource : ¬P ≈ Q) (hMap : f ∘ P = f ∘ Q)
    (hZ : (WeierstrassCurve.Projective.dblXYZ (W.map f) (f ∘ P)) 2 ≠ 0) :
    mapClass f (WeierstrassCurve.Projective.addMap W
      (⟦P⟧ : WeierstrassCurve.Projective.PointClass R) ⟦Q⟧) ≠
      WeierstrassCurve.Projective.addMap (W.map f)
        (mapClass f ⟦P⟧) (mapClass f ⟦Q⟧) := by
  intro heq
  have hLeft := mapClass_source_addMap_zero f W P Q hSource hMap
  have hRight :
      WeierstrassCurve.Projective.addMap (W.map f)
        (mapClass f ⟦P⟧) (mapClass f ⟦Q⟧) =
        (⟦WeierstrassCurve.Projective.dblXYZ (W.map f) (f ∘ P)⟧ :
          WeierstrassCurve.Projective.PointClass S) := by
    change (⟦WeierstrassCurve.Projective.add (W.map f)
      (f ∘ P) (f ∘ Q)⟧ : WeierstrassCurve.Projective.PointClass S) = _
    rw [← hMap, WeierstrassCurve.Projective.add_self]
  rw [hLeft, hRight] at heq
  have hNotEquiv : ¬(![0, 0, 0] : Fin 3 → S) ≈
      WeierstrassCurve.Projective.dblXYZ (W.map f) (f ∘ P) :=
    WeierstrassCurve.Projective.not_equiv_of_Z_eq_zero_left (by simp) hZ
  exact hNotEquiv (Quotient.eq.mp heq)

#print axioms mapped_source_add_vector_zero
#print axioms mapClass_source_addMap_zero
#print axioms mapClass_addMap_ne_addMap_of_coalescence

end XedniProjectiveCoalescenceObstruction
