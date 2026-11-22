import SourceChordEquation
import Mathlib.Tactic

/-! The source homogeneous chord representative is nonsingular when its
residue is a nonzero projective zero representative. -/
namespace XedniSourceChordNonsingular

open XedniRegularChainReduction XedniResidueVerticalObstruction
open XedniSourceChordEquation XedniResidueProjectiveZero

variable {R F : Type*} [CommRing R] [Field F]
variable (f : R →+* F) {A B : R}

/-- Coordinate reduction of the source homogeneous chord triple is exactly
the residue triple used in the projective-zero theorem. -/
theorem map_sourceChordTriple (P T : CurvePoint R A B) :
    f ∘ sourceChordTriple P T = chordResidueTriple f P T := by
  funext i
  fin_cases i <;> rfl

/-- A residue-vertical chord whose reduced y-difference is nonzero has a
nonsingular homogeneous representative over the source ring. -/
theorem sourceChordTriple_nonsingular (P T : CurvePoint R A B)
    (hx : f (T.x - P.x) = 0) (hy : f (T.y - P.y) ≠ 0) :
    WeierstrassCurve.Projective.Nonsingular
      (⟨0, 0, 0, A, B⟩ : WeierstrassCurve R) (sourceChordTriple P T) := by
  let W : WeierstrassCurve R := ⟨0, 0, 0, A, B⟩
  let C := sourceChordTriple P T
  have hEq : WeierstrassCurve.Projective.Equation W C :=
    sourceChordTriple_on_curve P T
  obtain ⟨h0, h1, h2⟩ := homogeneous_chord_at_infinity f P T hx hy
  have hc0 : f (C 0) = 0 := by simpa [C, sourceChordTriple] using h0
  have hc1 : f (C 1) ≠ 0 := by simpa [C, sourceChordTriple] using h1
  have hc2 : f (C 2) = 0 := by simpa [C, sourceChordTriple] using h2
  have hDerivative : C 1 ^ 2 - (2 * A * C 0 * C 2 + 3 * B * C 2 ^ 2) ≠ 0 := by
    intro hzero
    have hmap := congrArg f hzero
    have hsquare : f (C 1) ^ 2 = 0 := by
      simpa [map_sub, map_add, map_mul, map_pow, hc0, hc2] using hmap
    exact (pow_ne_zero 2 hc1) hsquare
  rw [WeierstrassCurve.Projective.nonsingular_iff]
  refine ⟨hEq, Or.inr (Or.inr ?_)⟩
  simpa [W] using hDerivative

#print axioms map_sourceChordTriple
#print axioms sourceChordTriple_nonsingular

end XedniSourceChordNonsingular
