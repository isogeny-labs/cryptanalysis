import ProjectiveClassReduction
import Mathlib.Tactic

/-! A ring map commutes with projective point-class addition whenever the
mapped representatives remain inequivalent. Both sides then use the same
denominator-free chord branch. -/
namespace XedniProjectiveAddMapDistinct

open XedniRegularChainReduction XedniSourceChordAddition
open XedniProjectiveClassReduction
open WeierstrassCurve.Projective

variable {R S : Type*} [CommRing R] [CommRing S]

/-- If the mapped representatives are inequivalent, the source and target
`addMap` operations both use `addXYZ`, whose polynomial formulas commute
with any ring homomorphism. No curve equation is needed for this identity. -/
theorem mapClass_addMap_of_mapped_not_equiv (f : R →+* S)
    (W : WeierstrassCurve R) (P Q : Fin 3 → R)
    (h : ¬(f ∘ P) ≈ (f ∘ Q)) :
    mapClass f (WeierstrassCurve.Projective.addMap W
      (⟦P⟧ : WeierstrassCurve.Projective.PointClass R) ⟦Q⟧) =
      WeierstrassCurve.Projective.addMap (W.map f)
        (mapClass f ⟦P⟧) (mapClass f ⟦Q⟧) := by
  have hSource : ¬P ≈ Q := by
    intro hPQ
    exact h (map_equiv f hPQ)
  change (⟦f ∘ WeierstrassCurve.Projective.add W P Q⟧ :
    WeierstrassCurve.Projective.PointClass S) =
    ⟦WeierstrassCurve.Projective.add (W.map f) (f ∘ P) (f ∘ Q)⟧
  rw [WeierstrassCurve.Projective.add_of_not_equiv hSource,
    WeierstrassCurve.Projective.add_of_not_equiv h]
  simp only [WeierstrassCurve.Projective.map_addXYZ]

/-- Unequal reduced affine x-coordinates imply the mapped chord branch
remains distinct, so reduction commutes with projective class addition. -/
theorem mapClass_affine_add_of_x_ne (f : R →+* S) {A B : R}
    (P T : CurvePoint R A B)
    (hx : f (T.x - P.x) ≠ 0) :
    mapClass f
      (WeierstrassCurve.Projective.addMap
        (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
        (⟦affineTriple P⟧ : WeierstrassCurve.Projective.PointClass R)
        ⟦affineTriple T⟧) =
      WeierstrassCurve.Projective.addMap
        ((⟨0, 0, 0, A, B⟩ : WeierstrassCurve R).map f)
        (mapClass f ⟦affineTriple P⟧)
        (mapClass f ⟦affineTriple T⟧) := by
  apply mapClass_addMap_of_mapped_not_equiv
  apply WeierstrassCurve.Projective.not_equiv_of_X_ne
  have hx' : f T.x ≠ f P.x := by
    simpa only [map_sub, sub_ne_zero] using hx
  simpa [affineTriple] using hx'.symm

/-- Unequal reduced affine y-coordinates give the same compatibility theorem.
This includes the residue-vertical branch when the reduced x-coordinates
coincide. -/
theorem mapClass_affine_add_of_y_ne (f : R →+* S) {A B : R}
    (P T : CurvePoint R A B)
    (hy : f (T.y - P.y) ≠ 0) :
    mapClass f
      (WeierstrassCurve.Projective.addMap
        (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
        (⟦affineTriple P⟧ : WeierstrassCurve.Projective.PointClass R)
        ⟦affineTriple T⟧) =
      WeierstrassCurve.Projective.addMap
        ((⟨0, 0, 0, A, B⟩ : WeierstrassCurve R).map f)
        (mapClass f ⟦affineTriple P⟧)
        (mapClass f ⟦affineTriple T⟧) := by
  apply mapClass_addMap_of_mapped_not_equiv
  apply WeierstrassCurve.Projective.not_equiv_of_Y_ne
  have hy' : f T.y ≠ f P.y := by
    simpa only [map_sub, sub_ne_zero] using hy
  simpa [affineTriple] using hy'.symm

#print axioms mapClass_addMap_of_mapped_not_equiv
#print axioms mapClass_affine_add_of_x_ne
#print axioms mapClass_affine_add_of_y_ne

end XedniProjectiveAddMapDistinct
