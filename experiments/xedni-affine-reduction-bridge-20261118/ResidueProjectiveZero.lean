import ResidueVerticalObstruction
import Mathlib.Tactic

/-! The homogeneous residue-vertical chord defines the actual nonsingular
projective zero point over the residue field. -/
namespace XedniResidueProjectiveZero

open XedniRegularChainReduction XedniRegularGroupLaw
open XedniResidueVerticalObstruction

variable {R F : Type*} [CommRing R] [Field F]
variable (f : R →+* F) {A B : R}

/-- The reduced homogeneous chord coordinates in standard projective form. -/
def chordResidueTriple (P T : CurvePoint R A B) : Fin 3 → F :=
  ![f (chordXNumerator P T * (T.x - P.x)),
    f (chordYNumerator P T), f ((T.x - P.x) ^ 3)]

/-- At a residue-vertical chord with nonzero numerator, the reduced triple
is a nonzero scalar multiple of the projective zero representative. -/
theorem chordResidueTriple_eq_smul_zero (P T : CurvePoint R A B)
    (hx : f (T.x - P.x) = 0) (hy : f (T.y - P.y) ≠ 0) :
    chordResidueTriple f P T =
      f (chordYNumerator P T) • ![0, 1, 0] := by
  obtain ⟨hX, hY, hZ⟩ := homogeneous_chord_at_infinity f P T hx hy
  ext i
  fin_cases i <;> simp [chordResidueTriple, hX, hZ]

/-- The chord triple is a nonsingular projective representative over the
residue field and its projective point equals the point at infinity. -/
theorem chordResidueTriple_projective_zero (P T : CurvePoint R A B)
    (hx : f (T.x - P.x) = 0) (hy : f (T.y - P.y) ≠ 0) :
    ∃ h : WeierstrassCurve.Projective.NonsingularLift
        (shortCurve (f A) (f B)) ⟦chordResidueTriple f P T⟧,
      (⟨h⟩ : WeierstrassCurve.Projective.Point (shortCurve (f A) (f B))) = 0 := by
  let W := shortCurve (f A) (f B)
  let C := chordResidueTriple f P T
  have hY : f (chordYNumerator P T) ≠ 0 :=
    (homogeneous_chord_at_infinity f P T hx hy).2.1
  have hC : C = f (chordYNumerator P T) • ![0, 1, 0] :=
    chordResidueTriple_eq_smul_zero f P T hx hy
  have hNS : WeierstrassCurve.Projective.Nonsingular W C := by
    rw [hC]
    exact (WeierstrassCurve.Projective.nonsingular_smul _
      (Ne.isUnit hY)).mpr WeierstrassCurve.Projective.nonsingular_zero
  have hLift : WeierstrassCurve.Projective.NonsingularLift W ⟦C⟧ := hNS
  refine ⟨hLift, ?_⟩
  apply WeierstrassCurve.Projective.Point.ext
  change (⟦C⟧ : WeierstrassCurve.Projective.PointClass F) = ⟦![0, 1, 0]⟧
  exact Quotient.eq.mpr <|
    WeierstrassCurve.Projective.equiv_zero_of_Z_eq_zero hNS (by simp [C, chordResidueTriple,
      map_pow, hx])

#print axioms chordResidueTriple_eq_smul_zero
#print axioms chordResidueTriple_projective_zero

end XedniResidueProjectiveZero
