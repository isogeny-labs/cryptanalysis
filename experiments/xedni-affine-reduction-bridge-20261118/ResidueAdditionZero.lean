import SourceChordDistinctAddition
import Mathlib.Tactic

/-! A residue-vertical source chord is an actual source projective addition
representative, and its coordinatewise reduction is the residue zero class. -/
namespace XedniResidueAdditionZero

open XedniRegularChainReduction XedniRegularGroupLaw
open XedniResidueVerticalObstruction XedniResidueProjectiveZero
open XedniSourceChordEquation XedniSourceChordNonsingular
open XedniSourceChordAddition
open WeierstrassCurve.Projective

variable {R F : Type*} [CommRing R] [Field F]
variable (f : R →+* F) {A B : R}

/-- A nonzero source y-difference selects mathlib's chord branch, including
the case of equal source x-coordinates. -/
theorem source_add_eq_neg_chord_of_y_ne (P T : CurvePoint R A B)
    (hy : P.y ≠ T.y) :
    WeierstrassCurve.Projective.add (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
      (affineTriple P) (affineTriple T) = -sourceChordTriple P T := by
  have hneq : ¬affineTriple P ≈ affineTriple T := by
    apply WeierstrassCurve.Projective.not_equiv_of_Y_ne
    simpa [affineTriple] using hy
  rw [WeierstrassCurve.Projective.add_of_not_equiv hneq]
  exact addXYZ_eq_neg_sourceChordTriple P T

/-- At a residue-vertical chord, coordinatewise reduction of the source
addition representative gives the residue projective zero class. -/
theorem reduced_source_add_class_eq_zero (P T : CurvePoint R A B)
    (hx : f (T.x - P.x) = 0) (hy : f (T.y - P.y) ≠ 0) :
    (⟦f ∘ WeierstrassCurve.Projective.add
        (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
        (affineTriple P) (affineTriple T)⟧ :
      WeierstrassCurve.Projective.PointClass F) = ⟦![0, 1, 0]⟧ := by
  have hySource : P.y ≠ T.y := by
    intro h
    apply hy
    simp [h]
  have hadd := source_add_eq_neg_chord_of_y_ne P T hySource
  have hmap :
      f ∘ WeierstrassCurve.Projective.add
        (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
        (affineTriple P) (affineTriple T) =
        -chordResidueTriple f P T := by
    rw [hadd]
    rw [← map_sourceChordTriple f P T]
    ext i
    simp
  rw [hmap]
  have hunit : IsUnit (-1 : F) := (isUnit_one : IsUnit (1 : F)).neg
  have hneg :
      (⟦-chordResidueTriple f P T⟧ : WeierstrassCurve.Projective.PointClass F) =
        ⟦chordResidueTriple f P T⟧ := by
    simpa only [neg_one_smul] using
      (WeierstrassCurve.Projective.smul_eq (chordResidueTriple f P T) hunit)
  have hY : f (chordYNumerator P T) ≠ 0 :=
    (homogeneous_chord_at_infinity f P T hx hy).2.1
  calc
    (⟦-chordResidueTriple f P T⟧ : WeierstrassCurve.Projective.PointClass F) =
        ⟦chordResidueTriple f P T⟧ := hneg
    _ = ⟦![0, 1, 0]⟧ := by
      rw [chordResidueTriple_eq_smul_zero f P T hx hy]
      exact WeierstrassCurve.Projective.smul_eq ![0, 1, 0] (Ne.isUnit hY)

/-- The reduced source addition representative defines the nonsingular
projective zero point of the reduced short-Weierstrass curve. -/
theorem reduced_source_add_point_zero (P T : CurvePoint R A B)
    (hx : f (T.x - P.x) = 0) (hy : f (T.y - P.y) ≠ 0) :
    ∃ h : WeierstrassCurve.Projective.NonsingularLift
        (shortCurve (f A) (f B))
        (⟦f ∘ WeierstrassCurve.Projective.add
          (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
          (affineTriple P) (affineTriple T)⟧ :
          WeierstrassCurve.Projective.PointClass F),
      (⟨h⟩ : WeierstrassCurve.Projective.Point (shortCurve (f A) (f B))) = 0 := by
  have hclass := reduced_source_add_class_eq_zero f P T hx hy
  have hNS : WeierstrassCurve.Projective.NonsingularLift
      (shortCurve (f A) (f B))
      (⟦f ∘ WeierstrassCurve.Projective.add
        (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R)
        (affineTriple P) (affineTriple T)⟧ :
        WeierstrassCurve.Projective.PointClass F) := by
    rw [hclass]
    exact WeierstrassCurve.Projective.nonsingular_zero
  refine ⟨hNS, ?_⟩
  apply WeierstrassCurve.Projective.Point.ext
  exact hclass

#print axioms source_add_eq_neg_chord_of_y_ne
#print axioms reduced_source_add_class_eq_zero
#print axioms reduced_source_add_point_zero

end XedniResidueAdditionZero
